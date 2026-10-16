"""ControladorMenu: pantalla de entrada (§10.2). Muestra criptas, crea una
partida nueva o reanuda una guardada, le cede los Comando al
ControladorJuego durante la partida y atiende "ver_puntajes", "volver" y
"salir". Nunca interpreta verbos de juego.

Comandos del menú:
    "jugar" (id_cripta)            reanuda si hay guardado; si no, nueva
    "jugar" (id_cripta, "nueva")   siempre nueva (ignora el guardado)
    "jugar" (id_cripta, "cargar")  solo reanuda; error si no hay guardado
    "ver_puntajes", "volver", "salir"

DECISIÓN: el segundo argumento de "jugar" es opcional para no romper la
Vista actual (PantallaMenu todavía solo manda el id). Sin él se reanuda si
existe guardado, que es lo que el jugador espera al volver a una cripta.
"""
from __future__ import annotations

from random import SystemRandom
from typing import TYPE_CHECKING, Optional

from ..modelo.puertos.errores import ErrorCripta
from .constructorEstadoVista import ConstructorEstadoVista
from .controladorJuego import ControladorJuego
from .mapaEtiquetas import MapaEtiquetas

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.puertos.almacenPuntajes import AlmacenPuntajes
    from ..modelo.puertos.registroAcciones import AlmacenRegistros
    from ..vista.comando import Comando
    from ..vista.vistaJuego import VistaJuego
    from .gestorGuardado import GestorGuardado
    from .reporteFinal import ReporteFinal

SEMILLA_MAXIMA = 2 ** 31 - 1
MODO_NUEVA = "nueva"
MODO_CARGAR = "cargar"


class ControladorMenu:

    def __init__(self, servicio: "ServicioDatos", vista: "VistaJuego",
                 gestor_guardado: "GestorGuardado", almacen_puntajes: "AlmacenPuntajes",
                 almacen_registros: "AlmacenRegistros", reporte_final: "ReporteFinal",
                 nombre_jugador: str = "Jugador",
                 semilla_fija: Optional[int] = None) -> None:
        self._servicio = servicio
        self._vista = vista
        self._gestor_guardado = gestor_guardado
        self._almacen_puntajes = almacen_puntajes
        self._almacen_registros = almacen_registros
        self._reporte_final = reporte_final
        self._nombre_jugador = nombre_jugador
        self._semilla_fija = semilla_fija
        # Solo traduce ResumenCriptaDTO y RegistroPuntaje: su mapa queda vacío.
        self._constructor = ConstructorEstadoVista(MapaEtiquetas())
        # DECISIÓN: SystemRandom SOLO para ELEGIR la semilla de una partida
        # nueva; toda la aleatoriedad del juego sale del random.Random(semilla)
        # propio de Partida (§2.6). La semilla queda en el log y en el
        # guardado: la partida es reproducible.
        self._generador_semillas = SystemRandom()
        self._juego: Optional[ControladorJuego] = None
        self._terminado = False

    def iniciar(self) -> None:
        self._mostrar_menu()

    def terminado(self) -> bool:
        return self._terminado

    def procesar(self, comando: Optional["Comando"]) -> None:
        """O(1) salvo lo que haga la pantalla pedida. No bloquea (D43)."""
        if comando is None:
            return
        if self._juego is not None:
            self._procesar_en_partida(comando)
            return
        verbo = comando.verbo
        argumentos = comando.argumentos
        if verbo == "salir":
            self._terminado = True
        elif verbo == "jugar" and 1 <= len(argumentos) <= 2:
            modo = argumentos[1] if len(argumentos) == 2 else None
            self._empezar_partida(argumentos[0], modo)
        elif verbo == "ver_puntajes":
            self._mostrar_puntajes()
        elif verbo == "volver":
            self._mostrar_menu()
        else:
            self._vista.mostrar_error(f"No reconozco el comando '{verbo}' en el menú.")

    def _procesar_en_partida(self, comando: "Comando") -> None:
        self._juego.procesar(comando)
        if self._juego.quiere_salir():
            # §10.2: terminar la sesión de forma controlada (el bucle de
            # FabricaAplicacion cierra la vista en su finally).
            self._terminado = True
            self._juego = None
        elif self._juego.terminado():
            self._juego = None
            # DECISIÓN: el conteo se reinicia AL TERMINAR la partida: la lista
            # de criptas del menú siguiente cuenta en el presupuesto de la
            # PRÓXIMA partida (§5.1: "incluyendo la lista de criptas").
            self._servicio.reiniciar_sesion()

    def _mostrar_menu(self) -> None:
        try:
            resumenes = self._servicio.listar_criptas()
        except ErrorCripta as error:
            self._vista.mostrar_error(f"No se pudo obtener la lista de criptas: {error}")
            return
        self._vista.mostrar_menu(self._constructor.criptas_visibles(resumenes))

    def _mostrar_puntajes(self) -> None:
        tabla = self._almacen_puntajes.cargar()
        self._vista.mostrar_puntajes(self._constructor.puntajes_visibles(tabla))

    def _empezar_partida(self, id_cripta: str, modo: Optional[str]) -> None:
        if modo not in (None, MODO_NUEVA, MODO_CARGAR):
            self._vista.mostrar_error(f"Modo desconocido '{modo}': usa nueva o cargar.")
            return
        hay_guardado = self._gestor_guardado.existe_guardado(id_cripta)
        if modo == MODO_CARGAR and not hay_guardado:
            self._vista.mostrar_error(f"No hay ninguna partida guardada de '{id_cripta}'.")
            return

        juego = ControladorJuego(
            self._servicio, self._vista, self._almacen_registros.registro_de(id_cripta),
            self._gestor_guardado, self._almacen_puntajes, self._reporte_final,
            self._nombre_jugador)
        try:
            if hay_guardado and modo != MODO_NUEVA:
                try:
                    juego.continuar_cargada(id_cripta)
                    self._juego = juego
                    return
                except (OSError, ValueError, ErrorCripta) as error:
                    if modo == MODO_CARGAR:
                        self._vista.mostrar_error(f"No se pudo cargar la partida: {error}")
                        return
                    # Sin modo explícito: se informa y se cae a partida nueva.
                    self._vista.mostrar_error(
                        f"No se pudo cargar la partida guardada ({error}); se empieza una nueva.")
            juego.iniciar_nueva(id_cripta, self._nueva_semilla())
        except ErrorCripta as error:
            self._vista.mostrar_error(f"No se pudo iniciar la cripta '{id_cripta}': {error}")
            return
        self._juego = juego

    def _nueva_semilla(self) -> int:
        if self._semilla_fija is not None:
            return self._semilla_fija
        return self._generador_semillas.randrange(SEMILLA_MAXIMA)
