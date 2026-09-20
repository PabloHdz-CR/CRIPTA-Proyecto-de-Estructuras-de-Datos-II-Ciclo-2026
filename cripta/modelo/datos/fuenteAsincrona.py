import threading

from ..estructuras.cola import Cola
from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.errores import ErrorCripta, ErrorDeRed
from ..puertos.fuenteDatos import validar_lote

OP_CONTENIDO = "contenido"
OP_CATALOGO = "catalogo"
OP_ESQUELETO = "esqueleto"


def _copiar(elementos):
    """Copia una colección de ids. Así, si quien la envió la modifica después,
    el hilo de fondo sigue viendo el pedido original."""
    copia = ListaEnlazada()
    copia.agregar_todos(elementos)
    return copia


class Solicitud:
    """Recibo de una consulta enviada al hilo de fondo.

    Guarda lo que se pidió y, cuando el hilo termina, el resultado o el error.
    Solo el hilo de fondo llama a _completar y _fallar.
    """

    def __init__(self, numero, operacion, id_cripta, pedido):
        self.numero = numero          # orden de envío: 1, 2, 3, ...
        self.operacion = operacion    # OP_CONTENIDO, OP_CATALOGO u OP_ESQUELETO
        self.id_cripta = id_cripta    # None en las consultas de catálogo
        self.pedido = pedido          # ids de salas, ids de catálogo o número de página
        self._terminada = threading.Event()
        self._resultado = None
        self._error = None

    def lista(self):
        """True si ya terminó (bien o con error). No bloquea."""
        return self._terminada.is_set()

    def esperar(self, tiempo_maximo=None):
        """Bloquea hasta que termine. Devuelve True si terminó, False si se
        agotó tiempo_maximo (en segundos). Es tiempo real: no mueve el reloj
        virtual del juego."""
        return self._terminada.wait(tiempo_maximo)

    def fallo(self):
        """Devuelve el error con que terminó, o None si salió bien. No lo lanza."""
        self._exigir_terminada()
        return self._error

    def resultado(self):
        """Devuelve el resultado, o relanza el error si la solicitud falló."""
        self._exigir_terminada()
        if self._error is not None:
            raise self._error
        return self._resultado

    def _exigir_terminada(self):
        if not self.lista():
            raise RuntimeError(
                f"La solicitud #{self.numero} todavía no termina: usa esperar() primero")

    def _completar(self, resultado):
        self._resultado = resultado
        self._terminada.set()

    def _fallar(self, error):
        self._error = error
        self._terminada.set()

    def __repr__(self):
        estado = "lista" if self.lista() else "pendiente"
        return f"Solicitud(#{self.numero} {self.operacion} {estado})"


class FuenteAsincrona:
    """Envuelve una FuenteDatos con UN hilo de fondo y una Cola FIFO propia.

    Quien la usa envía consultas y recibe una Solicitud. El hilo las atiende
    de una en una, en orden de envío, sobre la fuente síncrona.

    Reglas de diseño:
      - Sin cancelación: toda solicitud enviada se atiende. Así la cantidad de
        solicitudes gastadas depende solo de lo que se decidió enviar, no de
        la velocidad de la red.
      - Los errores del hilo de fondo se guardan en la Solicitud y se relanzan
        en el hilo que pide el resultado; el hilo de fondo nunca muere.
      - Para incorporar resultados al modelo se usa SIEMPRE recoger_listas():
        entrega las solicitudes terminadas en orden de envío y se detiene en
        la primera que aún no terminó. esperar() sirve solo para bloquear.
      - La Cola propia no es segura entre hilos: todo acceso a ella ocurre
        dentro de la Condition (que incluye su propio Lock).
    """

    def __init__(self, fuente):
        self._fuente = fuente
        self._condicion = threading.Condition()
        self._por_atender = Cola()   # las toma el hilo de fondo
        self._sin_recoger = Cola()   # en orden de envío, hasta que se recogen
        self._siguiente_numero = 1
        self._cerrada = False
        self._hilo = threading.Thread(
            target=self._trabajar, name="FuenteAsincrona", daemon=True)
        self._hilo.start()

    # ------------------------------------------------------------------
    # Envío de consultas (hilo del juego)
    # ------------------------------------------------------------------

    def enviar_contenido(self, id_cripta, ids_salas):
        validar_lote("descargar el contenido de las salas", ids_salas)
        return self._enviar(OP_CONTENIDO, id_cripta, _copiar(ids_salas))

    def enviar_catalogo(self, ids):
        validar_lote("descargar fichas del catálogo", ids)
        return self._enviar(OP_CATALOGO, None, _copiar(ids))

    def enviar_esqueleto(self, id_cripta, pagina):
        return self._enviar(OP_ESQUELETO, id_cripta, pagina)

    def _enviar(self, operacion, id_cripta, pedido):
        with self._condicion:
            if self._cerrada:
                raise ErrorDeRed(operacion, "la fuente asíncrona ya está cerrada")
            solicitud = Solicitud(self._siguiente_numero, operacion, id_cripta, pedido)
            self._siguiente_numero += 1
            self._por_atender.encolar(solicitud)
            self._sin_recoger.encolar(solicitud)
            self._condicion.notify()   # despierta al hilo de fondo
        return solicitud

    # ------------------------------------------------------------------
    # Recolección y estado (hilo del juego)
    # ------------------------------------------------------------------

    def recoger_listas(self):
        """Devuelve una ListaEnlazada de Solicitud terminadas, en orden de envío.

        Se detiene en la primera solicitud que aún no terminó, así una
        respuesta rápida nunca se adelanta a una anterior más lenta. Cada
        solicitud se entrega una sola vez.
        """
        listas = ListaEnlazada()
        with self._condicion:
            while (not self._sin_recoger.esta_vacia()
                   and self._sin_recoger.ver_frente().lista()):
                listas.agregar_al_final(self._sin_recoger.desencolar())
        return listas

    def pendientes(self):
        """Cuántas solicitudes enviadas aún no terminan."""
        with self._condicion:
            cantidad = 0
            for solicitud in self._sin_recoger:
                if not solicitud.lista():
                    cantidad += 1
            return cantidad

    def sin_recoger(self):
        """Cuántas solicitudes enviadas faltan por recoger (terminadas o no)."""
        with self._condicion:
            return len(self._sin_recoger)

    def activa(self):
        """True mientras el hilo de fondo sigue funcionando."""
        return self._hilo.is_alive()

    def cerrar(self, espera_maxima=15):
        """Detiene el hilo de fondo.

        Termina la solicitud que esté en curso y DESCARTA las pendientes,
        marcándolas con ErrorDeRed. Espera hasta espera_maxima segundos a que
        el hilo termine. Se puede llamar más de una vez.
        """
        with self._condicion:
            if not self._cerrada:
                self._cerrada = True
                while not self._por_atender.esta_vacia():
                    solicitud = self._por_atender.desencolar()
                    solicitud._fallar(ErrorDeRed(
                        solicitud.operacion,
                        "la fuente asíncrona se cerró antes de atender la solicitud"))
                self._condicion.notify_all()
        self._hilo.join(espera_maxima)

    # ------------------------------------------------------------------
    # Hilo de fondo
    # ------------------------------------------------------------------

    def _trabajar(self):
        while True:
            with self._condicion:
                # wait() suelta el cerrojo y duerme hasta un notify().
                # Se vuelve a comprobar la condición porque pueden ocurrir
                # despertares sin motivo.
                while self._por_atender.esta_vacia() and not self._cerrada:
                    self._condicion.wait()
                if self._cerrada:
                    return
                solicitud = self._por_atender.desencolar()
            # Se atiende FUERA del cerrojo: puede tardar segundos, y mientras
            # tanto el juego debe poder seguir enviando y consultando.
            self._atender(solicitud)

    def _atender(self, solicitud):
        try:
            if solicitud.operacion == OP_CONTENIDO:
                resultado = self._fuente.contenido(solicitud.id_cripta, solicitud.pedido)
            elif solicitud.operacion == OP_CATALOGO:
                resultado = self._fuente.catalogo(solicitud.pedido)
            else:
                resultado = self._fuente.esqueleto(solicitud.id_cripta, solicitud.pedido)
        except ErrorCripta as error:
            solicitud._fallar(error)
        except Exception as error:
            # Cualquier otra falla se convierte en ErrorDeRed para que el hilo
            # de fondo no muera y quien espera la solicitud no se quede colgado.
            solicitud._fallar(ErrorDeRed(
                solicitud.operacion, f"error inesperado: {error}"))
        else:
            solicitud._completar(resultado)