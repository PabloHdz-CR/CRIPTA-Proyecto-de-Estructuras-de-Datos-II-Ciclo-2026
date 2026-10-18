"""ControladorReplay: reproduce el log de una partida EN LA VENTANA, paso a
paso, para analizarla (§4.11). Es la contraparte visual de ModoReplay
(--replay), que reproduce todo de una vez con VistaNula.

Comandos mientras se reproduce:
    "replay_pausa"               pausa / continúa
    "replay_paso"                avanza una acción (también en pausa)
    "replay_atras"               retrocede una acción y queda en pausa
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

DECISIÓN: retroceder un paso RECONSTRUYE la partida: una Partida nueva con
la misma semilla que vuelve a aplicar las primeras k-1 acciones. Como la
partida es determinista (§2.6), llega exactamente al estado del paso k-1.
Alternativa descartada: Diario.deshacer (el del pergamino), que solo
recuerda 5 acciones, excluye los pergaminos que puede traer el log y
mezclaría el retroceso del jugador con el del visor. Otra descartada:
guardar una foto del estado en cada paso, que es una copia del estado
(prohibida por §4.6).

Complejidad: leer el log es O(A); cada paso es una acción del modelo (un
ciclo de eventos, < 20 ms por §5.2) más armar la foto; retroceder desde el
paso k cuesta O(k) acciones. Memoria O(A).
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
        self._encabezado = None          # del log: la semilla, para reconstruir
        self._lista_acciones = None      # ListaEnlazada de Accion del log
        self._acciones = None            # iterador sobre esa lista (la próxima por aplicar)
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

        self._encabezado = encabezado
        self._lista_acciones = acciones
        self._total = len(acciones)
        try:
            self._reconstruir(0)
        except ErrorCripta as error:
            return self._no_se_puede(f"No se pudo iniciar la reproducción: {error}")
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
        elif verbo == "replay_atras":
            self._retroceder()
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

    def _retroceder(self) -> None:
        """Vuelve al paso anterior y queda en pausa (para mirarlo con calma).
        En el paso 0 no hace nada. Tras un rechazo, permite volver atrás
        para ver cómo se llegó ahí."""
        if self._paso == 0:
            return
        try:
            self._reconstruir(self._paso - 1)
        except ErrorCripta as error:
            self._detener(f"No se pudo volver al paso {self._paso - 1}: {error}")
            return
        self._pausado = True
        self._detenido = False
        self._mostrar()

    def _reconstruir(self, pasos: int) -> None:
        """Partida nueva con la semilla del log y sus primeras `pasos`
        acciones aplicadas (ya se aceptaron la primera vez: la partida es
        determinista). Deja el iterador en la acción siguiente. O(pasos)."""
        partida = Partida(self._servicio)
        partida.conectar_diario(Diario())             # el log puede traer PERGAMINO
        partida.iniciar(self._encabezado.semilla)
        acciones = iter(self._lista_acciones)
        for _ in range(pasos):
            partida.aplicar_accion(next(acciones))
        self.partida = partida
        self._acciones = acciones
        self._paso = pasos
        # Las etiquetas ("Rata gigante #1") se vuelven a asignar desde cero,
        # igual que la primera vez que se llegó a este paso.
        self._constructor = ConstructorEstadoVista(MapaEtiquetas())

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
