"""ControladorMenu: pantalla de entrada (§10.2). Muestra criptas, crea una
partida nueva o reanuda una guardada, le cede los Comando al
ControladorJuego durante la partida y atiende "ver_puntajes", "volver" y
"salir". Nunca interpreta verbos de juego.

Comandos del menú:
    "jugar" (id_cripta)            reanuda si hay guardado; si no, nueva
    "jugar" (id_cripta, "nueva")   siempre nueva (ignora el guardado)
    "jugar" (id_cripta, "cargar")  solo reanuda; error si no hay guardado
    "ver_puntajes", "volver", "salir"
    "cambiar_nombre" (texto)       nombre con el que se juega y se puntúa
    "ver_replay_partida" (id)      (desde puntajes) reproduce esa partida
    "ver_replay" ()                (desde la pantalla de fin) la partida que
                                   acaba de terminar
    En los dos casos el replay se compara al final con el puntaje guardado.
    "benchmark" ()                 corre --bench --rapido y muestra los resultados

DECISIÓN: el segundo argumento de "jugar" es opcional para no romper la
Vista actual (PantallaMenu todavía solo manda el id). Sin él se reanuda si
existe guardado, que es lo que el jugador espera al volver a una cripta.
"""
from __future__ import annotations

import time
from random import SystemRandom
from typing import TYPE_CHECKING, Callable, Optional

from ..modelo.puertos.errores import ErrorCripta
from ..vista.estadoVista import BenchmarkVisible
from .bench.reporte import Reporte
from .constructorEstadoVista import ConstructorEstadoVista
from .controladorJuego import ControladorJuego
from .controladorReplay import ControladorReplay
from .mapaEtiquetas import MapaEtiquetas
from .modoBench import ModoBench

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.nucleo.puntajes import RegistroPuntaje
    from ..modelo.puertos.almacenPuntajes import AlmacenPuntajes
    from ..modelo.puertos.registroAcciones import AlmacenRegistros
    from ..vista.comando import Comando
    from ..vista.vistaJuego import VistaJuego
    from .gestorGuardado import GestorGuardado
    from .reporteFinal import ReporteFinal

SEMILLA_MAXIMA = 2 ** 31 - 1
MODO_NUEVA = "nueva"
MODO_CARGAR = "cargar"
NOMBRE_POR_DEFECTO = "Jugador"
LARGO_MAXIMO_NOMBRE = 16


class ControladorMenu:

    def __init__(self, servicio: "ServicioDatos", vista: "VistaJuego",
                 gestor_guardado: "GestorGuardado", almacen_puntajes: "AlmacenPuntajes",
                 almacen_registros: "AlmacenRegistros", reporte_final: "ReporteFinal",
                 nombre_jugador: str = NOMBRE_POR_DEFECTO,
                 semilla_fija: Optional[int] = None,
                 modo_bench: Optional[ModoBench] = None,
                 reloj: Optional[Callable[..., float]] = None) -> None:
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
        self._replay: Optional[ControladorReplay] = None
        self._modo_bench = modo_bench if modo_bench is not None else ModoBench()
        # Reloj real para el ritmo del replay; las pruebas inyectan uno falso.
        self._reloj = reloj if reloj is not None else time.perf_counter
        # La última partida terminada: su cripta y su resultado, para que
        # "ver_replay" desde la pantalla de fin compruebe que el replay
        # llega al mismo final.
        self._ultimo_registro: Optional["RegistroPuntaje"] = None
        # A dónde vuelve el replay al terminar: a puntajes si se pidió desde
        # ahí, al menú si se pidió desde la pantalla de fin.
        self._replay_desde_puntajes = False
        self._terminado = False

    def iniciar(self) -> None:
        self._mostrar_menu()

    def terminado(self) -> bool:
        return self._terminado

    @property
    def nombre_jugador(self) -> str:
        return self._nombre_jugador

    def procesar(self, comando: Optional["Comando"]) -> None:
        """O(1) salvo lo que haga la pantalla pedida. No bloquea (D43)."""
        if self._replay is not None:
            # DECISIÓN: el replay recibe también los None: avanza por tiempo.
            self._replay.procesar(comando)
            if self._replay.terminado():
                self._replay = None
                if self._replay_desde_puntajes:
                    self._mostrar_puntajes()
                else:
                    self._mostrar_menu()
            return
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
        elif verbo == "cambiar_nombre" and len(argumentos) == 1:
            self._cambiar_nombre(argumentos[0])
        elif verbo == "ver_replay" and len(argumentos) == 0:
            self._ver_replay(self._ultimo_registro, desde_puntajes=False)
        elif verbo == "ver_replay_partida" and len(argumentos) == 1:
            self._ver_replay(self._buscar_puntaje(argumentos[0]), desde_puntajes=True)
        elif verbo == "benchmark":
            self._correr_benchmark()
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
            self._ultimo_registro = self._juego.registro_final
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
        self._vista.mostrar_nombre_jugador(self._nombre_jugador)
        self._vista.mostrar_menu(self._constructor.criptas_visibles(resumenes))

    def _mostrar_puntajes(self) -> None:
        tabla = self._almacen_puntajes.cargar()
        self._vista.mostrar_puntajes(self._constructor.puntajes_visibles(
            tabla, almacen_registros=self._almacen_registros))

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

    def _cambiar_nombre(self, texto: str) -> None:
        """Sin espacios a los lados y a lo sumo LARGO_MAXIMO_NOMBRE
        caracteres; vacío vuelve al nombre por defecto. O(largo)."""
        limpio = str(texto).strip()[:LARGO_MAXIMO_NOMBRE].strip()
        self._nombre_jugador = limpio if limpio else NOMBRE_POR_DEFECTO
        self._mostrar_menu()

    def _buscar_puntaje(self, id_partida: str) -> Optional["RegistroPuntaje"]:
        """El puntaje guardado con ese id de partida. O(p)."""
        for registro in self._almacen_puntajes.cargar():
            if registro.id_partida == id_partida:
                return registro
        return None

    def _ver_replay(self, esperado: Optional["RegistroPuntaje"], desde_puntajes: bool) -> None:
        """Reproduce la partida de ese puntaje con SU log archivado, y al
        final compara contra él (resultado, acciones, enemigos y tiempo)."""
        registro = None
        if esperado is not None and esperado.id_partida:
            registro = self._almacen_registros.registro_archivado(esperado.id_partida)
        if registro is None:
            self._vista.mostrar_error("Esa partida no tiene un replay guardado.")
            return
        titulo = (f"{esperado.nombre} · {esperado.id_cripta} · {esperado.resultado} · "
                  f"tiempo {esperado.tiempo_final}")
        # El nombre del replay es el de QUIEN jugó esa partida, no el actual.
        replay = ControladorReplay(
            self._servicio, self._vista, registro, resultado_esperado=esperado,
            nombre_jugador=esperado.nombre, reloj=self._reloj, titulo=titulo)
        if replay.iniciar():
            self._replay = replay
            self._replay_desde_puntajes = desde_puntajes
        # Si no se pudo, iniciar() ya mostró el motivo y se queda donde estaba.

    def _correr_benchmark(self) -> None:
        """--bench --rapido dentro de la ventana (unos segundos). Las
        mediciones son las mismas que en la terminal (§5.3): cargas
        sintéticas, sin red ni caché real."""
        self._vista.mostrar_espera("Midiendo las estructuras (benchmark rápido)...")
        self._vista.actualizar()             # que el aviso se vea antes de medir
        inicio = time.perf_counter()
        reporte = self._modo_bench.ejecutar(True, Reporte(imprimir=False))
        segundos = time.perf_counter() - inicio
        self._vista.mostrar_benchmark(BenchmarkVisible(
            tablas=reporte.tablas, notas=reporte.notas, segundos=segundos, rapido=True))

    def _nueva_semilla(self) -> int:
        if self._semilla_fija is not None:
            return self._semilla_fija
        return self._generador_semillas.randrange(SEMILLA_MAXIMA)
