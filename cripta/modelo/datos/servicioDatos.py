"""Orquesta caché, disco y red para resolver los datos de una cripta (§4.2, §4.3).

Es el ÚNICO punto por el que el modelo pide datos: el resto del modelo nunca
toca FuenteDatos, FuenteAsincrona, CacheFichas ni AlmacenLocal directamente.
Así, --offline (que cambia la fuente síncrona/asíncrona que se le inyecta)
no obliga a tocar nada más (§6).

Dos fuentes de datos recibidas por inyección:
  - 'sincrona' (FuenteDatos): lista de criptas, datos generales, versiones.
    Son consultas puntuales al inicio, no vale la pena hacerlas asíncronas.
  - 'asincrona' (FuenteAsincrona): esqueleto, contenido y catálogo, que se
    piden en lotes y pueden tardar sin congelar el juego.
"""
from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.errores import ErrorCripta
from ..puertos.fuenteDatos import LIMITE_LOTE
from .esqueletoCripta import EsqueletoCripta
from .planificadorPrecarga import PlanificadorPrecarga


def _ids_lista(elementos):
    copia = ListaEnlazada()
    copia.agregar_todos(elementos)
    return copia


class ServicioDatos:

    def __init__(self, sincrona, asincrona, cache, almacen_local, planificador=None):
        self._sincrona = sincrona
        self._asincrona = asincrona
        self._cache = cache
        self._almacen = almacen_local
        self._planificador = planificador if planificador is not None else PlanificadorPrecarga()
        self._datos_cripta = None
        self._esqueleto = EsqueletoCripta()
        self._version_catalogo = None
        self._id_cripta = None
        self._paginas_descargadas = 0
        self._solicitudes_esqueleto_pendientes = ListaEnlazada()
        self._solicitudes_contenido_pendientes = ListaEnlazada()
        self._solicitudes_catalogo_pendientes = ListaEnlazada()
        self._ids_catalogo_en_vuelo = ListaEnlazada()    # evita pedir dos veces el mismo id

    # ------------------------------------------------------------------
    # Arranque de una partida
    # ------------------------------------------------------------------

    def listar_criptas(self):
        return self._sincrona.listar_criptas()

    def iniciar_cripta(self, id_cripta):
        """Descarga los datos generales y TODO el esqueleto (por páginas, en
        paralelo vía la fuente asíncrona). Bloquea hasta tenerlo completo:
        el esqueleto es liviano (§3.2) y hace falta para poder planificar
        cualquier movimiento desde el principio."""
        self._id_cripta = id_cripta
        self._datos_cripta = self._sincrona.datos_generales(id_cripta)
        try:
            self._version_catalogo = self._sincrona.version_catalogo()
        except ErrorCripta:
            self._version_catalogo = None    # sin red: se resuelve todo desde caché/disco

        self._esqueleto = EsqueletoCripta()
        self._paginas_descargadas = 0
        total_paginas = self._datos_cripta.paginas
        solicitudes = ListaEnlazada()
        for pagina in range(1, total_paginas + 1):
            solicitudes.agregar_al_final(self._asincrona.enviar_esqueleto(id_cripta, pagina))
        for solicitud in solicitudes:
            solicitud.esperar()
            self._esqueleto.agregar_pagina(solicitud.resultado())
            self._paginas_descargadas += 1
        return self._datos_cripta

    def datos_cripta(self):
        return self._datos_cripta

    def esqueleto(self):
        return self._esqueleto

    # ------------------------------------------------------------------
    # Contenido de salas: precarga sin bloquear, y espera cuando hace falta
    # ------------------------------------------------------------------

    def precargar(self, id_sala_actual):
        """Pide por adelantado hasta un lote de salas vecinas que todavía no se
        hayan solicitado (§4.2). NO bloquea: solo envía la solicitud."""
        lote = self._planificador.siguiente_lote(self._esqueleto, id_sala_actual, LIMITE_LOTE)
        if lote.esta_vacia():
            return
        solicitud = self._asincrona.enviar_contenido(self._id_cripta, lote)
        self._solicitudes_contenido_pendientes.agregar_al_final(solicitud)

    def contenido_listo(self, id_sala):
        """True si el contenido de esa sala ya está disponible en memoria (sin
        necesidad de esperar)."""
        self._incorporar_contenido_disponible()
        entrada = self._esqueleto.buscar(id_sala)
        return entrada is not None and entrada.contenido is not None

    def asegurar_contenido(self, id_sala):
        """Devuelve el ContenidoSalaDTO de esa sala. Si ya está en memoria, no
        gasta nada. Si no, lo pide y ESPERA (bloquea) hasta tenerlo: el
        enunciado exige que el jugador nunca quede en una sala cuyo contenido
        se desconoce (§2.4), así que, llegado el caso, hay que esperar."""
        entrada = self._esqueleto.buscar(id_sala)
        if entrada is None:
            raise ErrorCripta(f"La sala {id_sala} no existe en el esqueleto de esta cripta")
        if entrada.contenido is not None:
            return entrada.contenido

        # ¿Ya hay una solicitud en camino que la incluya? Si no, se pide ahora.
        self._incorporar_contenido_disponible()
        if entrada.contenido is not None:
            return entrada.contenido
        if not entrada.solicitada:
            lote = ListaEnlazada()
            lote.agregar_al_final(id_sala)
            entrada.solicitada = True
            solicitud = self._asincrona.enviar_contenido(self._id_cripta, lote)
            self._solicitudes_contenido_pendientes.agregar_al_final(solicitud)

        # Bloquea hasta que ALGUNA solicitud pendiente traiga esta sala.
        while entrada.contenido is None:
            self._esperar_una_pendiente(self._solicitudes_contenido_pendientes)
            self._incorporar_contenido_disponible()
        return entrada.contenido

    def _incorporar_contenido_disponible(self):
        """Recoge, EN ORDEN DE ENVÍO, las solicitudes de contenido que ya
        terminaron, y vuelca sus resultados en el esqueleto. El orden importa
        para el determinismo de red (§2.4): nunca se procesa una respuesta más
        rápida antes que una más lenta que se pidió primero."""
        nuevas_pendientes = ListaEnlazada()
        for solicitud in self._solicitudes_contenido_pendientes:
            if not solicitud.lista():
                nuevas_pendientes.agregar_al_final(solicitud)
                continue
            for contenido in solicitud.resultado():
                entrada = self._esqueleto.buscar(contenido.sala)
                if entrada is not None:
                    entrada.contenido = contenido
        self._solicitudes_contenido_pendientes = nuevas_pendientes

    def _esperar_una_pendiente(self, solicitudes):
        """Bloquea hasta que la MÁS ANTIGUA solicitud pendiente de la lista
        termine (tiempo real; no mueve el reloj virtual del juego)."""
        if solicitudes.esta_vacia():
            raise ErrorCripta("No hay ninguna solicitud pendiente que esperar")
        solicitudes.ver_primero().esperar()

    # ------------------------------------------------------------------
    # Catálogo (§4.3): resolución en lotes, sin pedir dos veces el mismo id
    # ------------------------------------------------------------------

    def resolver_fichas(self, ids):
        """Devuelve, en una ListaEnlazada, la ficha de cada id pedido (en el
        MISMO orden que 'ids'). Resuelve cada una en cascada: memoria, disco,
        red — y si viene de disco o de red, la guarda en memoria (y en disco,
        si vino de red) para la próxima vez.

        Cada id se consulta en la caché EXACTAMENTE UNA VEZ con obtener()
        (lo que cuenta como acierto o fallo de verdad, para no maquillar la
        estadística de §4.4): si faltaba y se acaba de insertar tras resolver
        por disco o por red, el valor final se lee con ver() (silenciosa),
        nunca con obtener() de nuevo.
        """
        resueltas = ListaEnlazada()      # la ficha si ya se resolvió, o None
        faltantes = ListaEnlazada()
        for id_ficha in ids:
            ficha = self._cache.obtener(id_ficha)
            if ficha is None and self._almacen is not None and self._version_catalogo is not None:
                ficha = self._almacen.cargar_ficha(id_ficha, self._version_catalogo)
                if ficha is not None:
                    self._cache.insertar(id_ficha, ficha)
            resueltas.agregar_al_final(ficha)
            if ficha is None and not faltantes.contiene(id_ficha):
                faltantes.agregar_al_final(id_ficha)

        if not faltantes.esta_vacia():
            self._pedir_fichas_por_red(faltantes)

        resultado = ListaEnlazada()
        iter_ids = iter(ids)
        for ficha in resueltas:
            id_ficha = next(iter_ids)
            if ficha is None:
                ficha = self._cache.ver(id_ficha)        # NO cuenta como acierto
            if ficha is None:
                raise ErrorCripta(f"No se pudo resolver la ficha '{id_ficha}'")
            resultado.agregar_al_final(ficha)
        return resultado

    def _pedir_fichas_por_red(self, ids_faltantes):
        """Parte 'ids_faltantes' en lotes de hasta 10 y los pide, esperando a
        que TODOS terminen antes de volver (porque resolver_fichas necesita
        el resultado ya). Cada ficha recibida se guarda en memoria y en disco."""
        solicitudes = ListaEnlazada()
        lote = ListaEnlazada()
        for id_ficha in ids_faltantes:
            lote.agregar_al_final(id_ficha)
            if len(lote) == LIMITE_LOTE:
                solicitudes.agregar_al_final(self._asincrona.enviar_catalogo(lote))
                lote = ListaEnlazada()
        if not lote.esta_vacia():
            solicitudes.agregar_al_final(self._asincrona.enviar_catalogo(lote))

        for solicitud in solicitudes:
            solicitud.esperar()
            for ficha in solicitud.resultado():
                self._cache.insertar(ficha.id, ficha)
                if self._almacen is not None and self._version_catalogo is not None:
                    self._almacen.guardar_ficha(ficha, self._version_catalogo)

    def resolver_ficha_y_dependientes(self, id_ficha):
        """Resuelve una ficha y, si es de un enemigo, también las fichas de lo
        que 'suelta' (§4.3: un id descubierto en cadena). Devuelve una
        ListaEnlazada con la ficha pedida primero y sus dependientes después."""
        principal = self.resolver_fichas(_ids_lista((id_ficha,))).obtener(0)
        resultado = ListaEnlazada()
        resultado.agregar_al_final(principal)
        if principal.clase == "enemigo" and not principal.suelta.esta_vacia():
            dependientes = self.resolver_fichas(principal.suelta)
            for ficha in dependientes:
                resultado.agregar_al_final(ficha)
        return resultado

    # ------------------------------------------------------------------
    # Presupuesto y cierre
    # ------------------------------------------------------------------

    def version_catalogo(self):
        """Versión del catálogo de esta sesión (o None sin red). La usa el
        encabezado del log de partida (§4.11)."""
        return self._version_catalogo

    def solicitudes_realizadas(self):
        return self._sincrona.solicitudes_realizadas()

    def presupuesto(self):
        return self._sincrona.presupuesto()

    def aciertos_cache(self):
        return self._cache.aciertos

    def fallos_cache(self):
        return self._cache.fallos

    def reiniciar_sesion(self):
        """Empieza una partida nueva: el conteo de solicitudes vuelve a 0 (la
        caché de memoria y el almacén en disco NO se vacían: siguen siendo
        válidos para la próxima partida, si la versión del catálogo coincide)."""
        self._sincrona.reiniciar_conteo()
        self._datos_cripta = None
        self._esqueleto = EsqueletoCripta()
        self._id_cripta = None
        self._solicitudes_contenido_pendientes = ListaEnlazada()