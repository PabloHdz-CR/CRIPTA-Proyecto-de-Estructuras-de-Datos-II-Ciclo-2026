"""ControladorJuego: una partida en curso (§6, §9).

Recorrido de una acción:
  1. Vista produce un Comando.
  2. TraductorComandos lo convierte en Accion.
  3. Partida.aplicar_accion valida, ejecuta y procesa eventos (Modelo).
  4. Si fue aceptada, se anexa al log (puerto RegistroAcciones, §4.11).
  5. ConstructorEstadoVista arma el EstadoVista y Vista lo dibuja.

Complejidad por comando: O(1) de traducción (O(k) si es "atacar") + el ciclo
de eventos del Modelo (< 20 ms por §5.2) + O(1) de anexar al log + armar la
foto (ver ConstructorEstadoVista). El Controlador no agrega nada que crezca
con el tamaño de la cripta.

DECISIÓN: procesar(comando) NO bloquea: se llama una vez por vuelta del
bucle externo (D43/D44) y None no hace nada. Así la ventana sigue
respondiendo aunque el jugador no decida.

DECISIÓN: el Controlador solo conoce puertos (VistaJuego, RegistroAcciones,
AlmacenPuntajes) y GestorGuardado; nunca rutas, open() ni print (guía §4).

Verbos de SESIÓN (no consumen reloj virtual ni son acciones del jugador):
    "guardar", "cargar", "salir", "inventario_siguiente",
    "inventario_anterior", "ordenar_inventario" (peso/valor/nombre/real).
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Optional

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.nucleo.diario import Diario
from ..modelo.nucleo.partida import Partida
from ..modelo.objetos.inventario import CRITERIOS_ORDEN
from ..modelo.puertos.errores import ErrorCripta
from ..modelo.puertos.registroAcciones import EncabezadoPartida
from ..vista.estadoVista import ResultadoFinVisible
from .constructorEstadoVista import ConstructorEstadoVista
from .mapaEtiquetas import MapaEtiquetas
from .traductorComandos import ErrorTraduccion, TraductorComandos

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.nucleo.puntajes import RegistroPuntaje
    from ..modelo.puertos.almacenPuntajes import AlmacenPuntajes
    from ..modelo.puertos.registroAcciones import RegistroAcciones
    from ..vista.comando import Comando
    from ..vista.vistaJuego import VistaJuego
    from .gestorGuardado import GestorGuardado
    from .reporteFinal import ReporteFinal

ORDEN_REAL = "real"


class ControladorJuego:

    def __init__(self, servicio: "ServicioDatos", vista: "VistaJuego",
                 registro: "RegistroAcciones", gestor_guardado: "GestorGuardado",
                 almacen_puntajes: "AlmacenPuntajes", reporte_final: "ReporteFinal",
                 nombre_jugador: str = "Jugador") -> None:
        self._servicio = servicio
        self._vista = vista
        self._registro = registro
        self._gestor_guardado = gestor_guardado
        self._almacen_puntajes = almacen_puntajes
        self._reporte_final = reporte_final
        self._nombre_jugador = nombre_jugador

        # DECISIÓN: un único MapaEtiquetas compartido por Constructor y
        # Traductor: la etiqueta dibujada es la que se resuelve al atacar.
        self._mapa_etiquetas = MapaEtiquetas()
        self._constructor = ConstructorEstadoVista(self._mapa_etiquetas)
        self._traductor = TraductorComandos(self._mapa_etiquetas)

        self.partida: Optional[Partida] = None
        # Resultado de la partida terminada: ControladorMenu lo usa para
        # comprobar que el replay llega exactamente al mismo final.
        self.registro_final: Optional["RegistroPuntaje"] = None
        self._criterio_orden: Optional[str] = None
        self._terminado = False
        self._quiere_salir = False
        # True si ESTA partida se cargó del guardado o se guardó: solo
        # entonces el guardado es suyo y se borra al terminar (D64).
        self._usa_guardado = False

    # ------------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------------

    def iniciar_nueva(self, id_cripta: str, semilla: int) -> None:
        """Descarga datos generales y esqueleto y arranca una Partida (§2.3,
        §2.4). Puede lanzar ErrorCripta: quien llama decide cómo mostrarlo."""
        datos = self._servicio.iniciar_cripta(id_cripta)
        self.partida = Partida(self._servicio)
        # DECISIÓN: el Diario se conecta ANTES de iniciar, así el pergamino
        # puede deshacer desde la primera acción del jugador.
        self.partida.conectar_diario(Diario())
        self._mapa_etiquetas.reiniciar()
        self.partida.iniciar(semilla)
        # §4.11: el encabezado guarda todo lo necesario para reproducir.
        self._registro.iniciar(EncabezadoPartida(
            datos.id, datos.version, self._servicio.version_catalogo(), semilla))
        self._mostrar_estado_actual()

    def continuar_cargada(self, id_cripta: str) -> None:
        """Carga el guardado (§4.10). Antes resuelve el esqueleto, porque
        cargar la partida necesita resolver fichas."""
        self._servicio.iniciar_cripta(id_cripta)
        self._cargar_desde_guardado(id_cripta)

    def terminado(self) -> bool:
        return self._terminado

    def quiere_salir(self) -> bool:
        return self._quiere_salir

    # ------------------------------------------------------------------
    # Bucle
    # ------------------------------------------------------------------

    def procesar(self, comando: Optional["Comando"]) -> None:
        # DECISIÓN: cadena de if por verbo de sesión (no dict, §7); lo que no
        # es de sesión se le pasa al Traductor. O(1).
        if comando is None or self._terminado:
            return
        verbo = comando.verbo
        if verbo == "salir":
            self._quiere_salir = True
        elif verbo == "guardar":
            self._guardar()
        elif verbo == "cargar":
            self._cargar()
        elif verbo == "inventario_siguiente":
            # DECISIÓN: mover el cursor no es una acción del jugador (no
            # consume tiempo ni va al log): se llama directo al Inventario.
            # O(1) por ser lista doblemente enlazada (§4.5).
            self.partida.jugador.inventario.siguiente()
            self._mostrar_estado_actual()
        elif verbo == "inventario_anterior":
            self.partida.jugador.inventario.anterior()
            self._mostrar_estado_actual()
        elif verbo == "ordenar_inventario":
            self._ordenar_inventario(comando.argumentos)
        else:
            self._procesar_accion(comando)

    def _procesar_accion(self, comando: "Comando") -> None:
        try:
            accion = self._traductor.traducir(comando)
        except ErrorTraduccion as error:
            self._vista.mostrar_error(str(error))
            return

        try:
            resultado = self.partida.aplicar_accion(accion)
        except ErrorCripta as error:
            # DECISIÓN: Partida asegura el contenido de la sala destino ANTES
            # de mutar nada: un ErrorDeRed o PresupuestoAgotado aquí deja el
            # estado intacto. Se informa con contexto (§3.1) y no se cae.
            self._vista.mostrar_error(f"No se pudo completar la acción: {error}")
            return

        if not resultado.aceptada:
            # Ap. B: un rechazo no consume tiempo y NO va al log.
            self._vista.mostrar_error(resultado.motivo)
            return

        # DECISIÓN: se anexa TODA acción aceptada, incluido el pergamino: no
        # cuenta como acción del jugador (§2.11) pero --replay lo necesita
        # para llegar al mismo estado. Anexar es O(1).
        self._registro.registrar_accion(accion)
        self._vista.mostrar_mensajes(resultado.mensajes)

        if self.partida.terminada():
            self._finalizar()
        else:
            self._mostrar_estado_actual()

    # ------------------------------------------------------------------
    # Verbos de sesión
    # ------------------------------------------------------------------

    def _ordenar_inventario(self, argumentos: tuple) -> None:
        # DECISIÓN: el criterio es estado de PRESENTACIÓN del Controlador, no
        # del Modelo: no se guarda, no se revierte y no va al log.
        criterio = argumentos[0] if len(argumentos) == 1 else None
        if criterio == ORDEN_REAL:
            self._criterio_orden = None
        elif criterio in CRITERIOS_ORDEN:
            self._criterio_orden = criterio
        else:
            self._vista.mostrar_error(
                "Criterio de orden desconocido: usa peso, valor, nombre o real.")
            return
        self._mostrar_estado_actual()

    def _guardar(self) -> None:
        try:
            ubicacion = self._gestor_guardado.guardar(self.partida, self._registro)
        except (OSError, ErrorCripta, ValueError) as error:
            self._vista.mostrar_error(f"No se pudo guardar la partida: {error}")
            return
        self._usa_guardado = True
        self._vista.mostrar_mensajes(_un_mensaje(f"Partida guardada en {ubicacion}."))

    def _cargar(self) -> None:
        """Recarga el guardado de ESTA cripta sin volver a pedir el esqueleto:
        pedirlo gastaría presupuesto de red sin necesidad (§5.1)."""
        id_cripta = self.partida.datos.id
        if not self._gestor_guardado.existe_guardado(id_cripta):
            self._vista.mostrar_error("No hay ninguna partida guardada de esta cripta.")
            return
        try:
            self._cargar_desde_guardado(id_cripta)
        except (OSError, ErrorCripta, ValueError) as error:
            self._vista.mostrar_error(f"No se pudo cargar la partida: {error}")
            return
        self._vista.mostrar_mensajes(_un_mensaje("Partida cargada."))

    def _cargar_desde_guardado(self, id_cripta: str) -> None:
        self.partida = self._gestor_guardado.cargar(id_cripta, self._servicio, self._registro)
        self._usa_guardado = True
        # DECISIÓN: el historial de retroceso no se persiste (son referencias
        # a objetos vivos, y §4.6 prohíbe copias completas del estado): una
        # partida cargada empieza con el Diario vacío.
        self.partida.conectar_diario(Diario())
        self._mapa_etiquetas.reiniciar()
        self._criterio_orden = None
        self._mostrar_estado_actual()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _mostrar_estado_actual(self) -> None:
        self._vista.mostrar_estado(self._constructor.construir(
            self.partida, self._criterio_orden, nombre_jugador=self._nombre_jugador))

    def _finalizar(self) -> None:
        """Victoria o derrota (§2.12): puntaje, pantalla de fin y reporte de
        red y caché (§5.1)."""
        registro: "RegistroPuntaje" = self.partida.resultado(self._nombre_jugador)
        # DECISIÓN: el log de ESTA partida se archiva con un id propio y el
        # puntaje lo recuerda: así la tabla de puntajes puede reproducirla
        # aunque después se jueguen otras en la misma cripta.
        id_partida = self._registro.archivar()
        if id_partida is not None:
            registro = replace(registro, id_partida=id_partida)
        self.registro_final = registro
        self._almacen_puntajes.agregar(registro)
        # DECISIÓN (D64): una partida terminada no se puede seguir jugando:
        # si su guardado quedara, el menú la reanudaría. Solo se borra si
        # el guardado es de ESTA partida (se cargó o se guardó en ella): si
        # el jugador empezó una nueva con un guardado viejo y nunca guardó,
        # el viejo no se toca.
        if self._usa_guardado:
            try:
                self._gestor_guardado.borrar(self.partida.datos.id)
            except OSError:
                pass        # no poder borrarlo no impide terminar la partida
        self._vista.mostrar_fin(ResultadoFinVisible(
            resultado=registro.resultado,
            acciones=registro.acciones,
            enemigos_derrotados=registro.enemigos_derrotados,
            tiempo_final=registro.tiempo_final,
            solicitudes_realizadas=self._servicio.solicitudes_realizadas(),
            presupuesto=self._servicio.presupuesto(),
            aciertos_cache=self._servicio.aciertos_cache(),
            fallos_cache=self._servicio.fallos_cache(),
            puede_ver_replay=registro.id_partida is not None,
        ))
        self._reporte_final.imprimir(self._servicio)
        self._terminado = True


def _un_mensaje(texto: str) -> ListaEnlazada:
    mensajes = ListaEnlazada()
    mensajes.agregar_al_final(texto)
    return mensajes
