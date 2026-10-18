"""ControladorReplay: reproduce el log de una partida EN LA VENTANA, paso a
paso, para analizarla (§4.11). Es la contraparte visual de ModoReplay
(--replay), que reproduce todo de una vez con VistaNula.

Comandos mientras se reproduce:
    "replay_pausa"               pausa / continúa
    "replay_paso"                avanza una acción (también en pausa)
    "replay_velocidad" ("+"|"-") duplica o reduce a la mitad la velocidad
    "salir" / "volver"           deja el replay y vuelve al menú
Al terminar se muestra la pantalla de fin del replay; ahí "ver_replay" lo
vuelve a empezar y "volver"/"salir" vuelve al menú.

DECISIÓN: se reproduce con la MISMA Partida.aplicar_accion y la misma regla
de versiones que --replay (motivo_version_incompatible): el replay en la
ventana prueba lo mismo que el de la terminal, solo que se puede mirar.

DECISIÓN: si hay un resultado esperado (el de la partida que acaba de
terminar), al final se compara con el del replay: mismo resultado, mismas
acciones, mismos enemigos derrotados y mismo tiempo final. Así el jugador
ve en pantalla si el replay es fiel.

DECISIÓN: el ritmo lo marca un reloj real inyectado (time.perf_counter por
defecto) y no el reloj virtual del juego: solo decide CUÁNDO mostrar la
siguiente acción; el resultado no depende de él. Las pruebas inyectan un
reloj falso.

Complejidad: leer el log es O(A); cada paso es una acción del modelo (un
ciclo de eventos, < 20 ms por §5.2) más armar la foto. Memoria O(A).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable, Optional

from ..modelo.nucleo.diario import Diario
from ..modelo.nucleo.partida import Partida
from ..modelo.puertos.errores import ErrorCripta
from ..vista.estadoVista import InfoReplay, ResultadoFinVisible
from .constructorEstadoVista import ConstructorEstadoVista
from .mapaEtiquetas import MapaEtiquetas
from .modoReplay import motivo_version_incompatible

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.nucleo.puntajes import RegistroPuntaje
    from ..modelo.puertos.registroAcciones import RegistroAcciones
    from ..vista.comando import Comando
    from ..vista.vistaJuego import VistaJuego

SEGUNDOS_POR_PASO = 0.8          # a velocidad x1
ESPERA_INICIAL = 1.0             # se muestra la sala inicial antes de arrancar
VELOCIDAD_MAXIMA = 16
NOMBRE_REPLAY = "Replay"
RESULTADO_EN_CURSO = "en curso"


class ControladorReplay:

    def __init__(self, servicio: "ServicioDatos", vista: "VistaJuego",
                 registro: "RegistroAcciones",
                 resultado_esperado: Optional["RegistroPuntaje"] = None,
                 nombre_jugador: Optional[str] = None,
                 reloj: Callable[..., float] = time.perf_counter,
                 titulo: Optional[str] = None) -> None:
        self._servicio = servicio
        self._vista = vista
        self._registro = registro
        self._esperado = resultado_esperado
        self._nombre = nombre_jugador if nombre_jugador else NOMBRE_REPLAY
        self._reloj = reloj
        self._titulo = titulo           # qué partida es, para el HUD
        self._constructor = ConstructorEstadoVista(MapaEtiquetas())

        self.partida: Optional[Partida] = None
        self._acciones = None            # iterador sobre la ListaEnlazada de Accion
        self._total = 0
        self._paso = 0
        self._pausado = False
        self._velocidad = 1
        self._proximo = 0.0              # instante (reloj real) del próximo paso
        self._en_fin = False
        self._detenido = False           # se rechazó una acción o falló el modelo
        self._terminado = False

    # ------------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------------

    def iniciar(self) -> bool:
        """Lee el log, valida versiones y muestra la sala inicial. False si
        no se puede reproducir (el motivo ya se mostró)."""
        try:
            encabezado, acciones = self._registro.leer()
            datos = self._servicio.iniciar_cripta(encabezado.id_cripta)
        except (OSError, ErrorCripta, ValueError) as error:
            return self._no_se_puede(f"No se pudo leer el log o iniciar la cripta: {error}")

        motivo = motivo_version_incompatible(self._servicio, datos, encabezado)
        if motivo is not None:
            return self._no_se_puede(f"No se puede garantizar una reproducción fiel: {motivo}")

        self.partida = Partida(self._servicio)
        self.partida.conectar_diario(Diario())        # el log puede traer PERGAMINO
        try:
            self.partida.iniciar(encabezado.semilla)
        except ErrorCripta as error:
            return self._no_se_puede(f"No se pudo iniciar la reproducción: {error}")
        self._total = len(acciones)
        self._acciones = iter(acciones)
        self._proximo = self._reloj() + ESPERA_INICIAL
        self._mostrar()
        return True

    def terminado(self) -> bool:
        return self._terminado

    # ------------------------------------------------------------------
    # Bucle (se llama en cada vuelta, también con None: el ritmo es por tiempo)
    # ------------------------------------------------------------------

    def procesar(self, comando: Optional["Comando"]) -> None:
        if self._terminado:
            return
        if comando is not None:
            self._atender(comando)
            if self._terminado:
                return
        if self._en_fin or self._detenido or self._pausado:
            return
        if self._reloj() >= self._proximo:
            self._avanzar()

    def _atender(self, comando: "Comando") -> None:
        # DECISIÓN: cadena de if por verbo (no dict, §7). O(1).
        verbo = comando.verbo
        if verbo == "salir" or verbo == "volver":
            self._terminado = True
        elif self._en_fin:
            if verbo == "ver_replay":
                self._reiniciar()
        elif verbo == "replay_pausa":
            self._pausado = not self._pausado
            self._proximo = self._reloj() + self._intervalo()
            self._mostrar()
        elif verbo == "replay_paso":
            if not self._detenido:
                self._avanzar()
        elif verbo == "replay_velocidad":
            self._cambiar_velocidad(comando.argumentos)

    def _cambiar_velocidad(self, argumentos: tuple) -> None:
        signo = argumentos[0] if len(argumentos) == 1 else None
        if signo == "+" and self._velocidad < VELOCIDAD_MAXIMA:
            self._velocidad *= 2
        elif signo == "-" and self._velocidad > 1:
            self._velocidad //= 2
        self._proximo = self._reloj() + self._intervalo()
        self._mostrar()

    def _intervalo(self) -> float:
        return SEGUNDOS_POR_PASO / self._velocidad

    def _avanzar(self) -> None:
        accion = next(self._acciones, None)
        if accion is None or self.partida.terminada():
            self._terminar()
            return
        self._paso += 1
        try:
            resultado = self.partida.aplicar_accion(accion)
        except ErrorCripta as error:
            self._detener(f"Error durante la reproducción en el paso {self._paso}: {error}")
            return
        if not resultado.aceptada:
            # Un rechazo nunca se anexa al log: si aparece, el log no
            # corresponde a estos datos o a esta versión del programa.
            self._detener(f"La acción #{self._paso} del log ({accion.texto()}) fue rechazada "
                          f"al reproducir: {resultado.motivo}")
            return
        self._proximo = self._reloj() + self._intervalo()
        if self.partida.terminada() or self._paso >= self._total:
            # Se deja ver el último paso un momento antes de la pantalla de fin.
            self._mostrar()
            self._proximo = self._reloj() + self._intervalo()
            if self.partida.terminada():
                self._acciones = iter(())
            return
        self._mostrar()

    def _terminar(self) -> None:
        self._en_fin = True
        self._vista.mostrar_fin(self._resultado_visible())

    def _reiniciar(self) -> None:
        """Vuelve a empezar desde la sala inicial con el mismo log."""
        self._paso = 0
        self._pausado = False
        self._en_fin = False
        self._detenido = False
        if not self.iniciar():
            self._terminado = True

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _mostrar(self) -> None:
        info = InfoReplay(paso=self._paso, total=self._total, pausado=self._pausado,
                          velocidad=self._velocidad, titulo=self._titulo)
        self._vista.mostrar_estado(self._constructor.construir(
            self.partida, nombre_jugador=self._nombre, replay=info))

    def _detener(self, motivo: str) -> None:
        self._detenido = True
        self._pausado = True
        self._mostrar()
        self._vista.mostrar_error(motivo)

    def _no_se_puede(self, motivo: str) -> bool:
        self._vista.mostrar_error(motivo)
        self._terminado = True
        return False

    def _resultado_visible(self) -> ResultadoFinVisible:
        jugador = self.partida.jugador
        # Un log de una partida que quedó a medias (guardada y no terminada)
        # se reproduce completo pero no tiene fin: se muestra "en curso".
        resultado = self.partida.fin if self.partida.fin is not None else RESULTADO_EN_CURSO
        coincide = None
        if self._esperado is not None:
            coincide = (resultado == self._esperado.resultado
                        and jugador.acciones == self._esperado.acciones
                        and jugador.enemigos_derrotados == self._esperado.enemigos_derrotados
                        and self.partida.reloj == self._esperado.tiempo_final)
        return ResultadoFinVisible(
            resultado=resultado,
            acciones=jugador.acciones,
            enemigos_derrotados=jugador.enemigos_derrotados,
            tiempo_final=self.partida.reloj,
            puede_ver_replay=True,
            es_replay=True,
            coincide=coincide,
        )
