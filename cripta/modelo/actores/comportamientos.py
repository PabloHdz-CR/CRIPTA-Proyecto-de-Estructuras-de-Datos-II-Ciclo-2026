"""Estrategias de los enemigos (§2.8, §2.9). decidir() devuelve una Accion."""
from __future__ import annotations

from ..nucleo.accion import Atacar, Esperar, Mover
from ..puertos.errores import DatosInvalidos, ErrorCripta


class Comportamiento:
    NOMBRE = "comportamiento"

    def decidir(self, enemigo, partida):
        """Si comparte sala con el jugador, ataca; si no, aplica su estrategia."""
        if enemigo.sala == partida.jugador.sala and partida.jugador.vivo:
            return Atacar(partida.jugador.id_instancia)
        return self.decidir_sin_jugador(enemigo, partida)

    def decidir_sin_jugador(self, enemigo, partida):
        raise NotImplementedError


class Guardian(Comportamiento):
    NOMBRE = "guardian"

    def decidir_sin_jugador(self, enemigo, partida):
        return Esperar()


class Errante(Comportamiento):
    NOMBRE = "errante"

    def decidir_sin_jugador(self, enemigo, partida):
        abiertas = partida.mundo.sala(enemigo.sala).vecinas_abiertas()
        if abiertas.esta_vacia():
            return Esperar()
        # DECISIÓN: exactamente UN sorteo por decisión, del Random propio: el número
        # de sorteos es predecible y el replay reproduce la misma partida.
        elegida = partida.azar.randrange(len(abiertas))   # un solo sorteo, del Random propio
        return Mover(abiertas.obtener(elegida).direccion)


class Rastreador(Comportamiento):
    """Examina solo las vecinas abiertas: O(salidas), sin recorrer el mundo."""

    NOMBRE = "rastreador"

    def decidir_sin_jugador(self, enemigo, partida):
        mejor_salida = None
        mejor_rastro = None
        for salida in partida.mundo.sala(enemigo.sala).vecinas_abiertas():
            rastro = partida.mundo.sala(salida.destino).rastro_fresco(partida.reloj)
            if rastro is None:
                continue
            # Más fresco = instante mayor; empate: menor id de sala destino.
            if (mejor_rastro is None or rastro > mejor_rastro
                    or (rastro == mejor_rastro and salida.destino < mejor_salida.destino)):
                mejor_salida = salida
                mejor_rastro = rastro
        if mejor_salida is None:
            return Esperar()
        return Mover(mejor_salida.direccion)


class Cazador(Comportamiento):
    """Persigue al jugador por la ruta de costo mínimo si no supera su rango
    (001-terreno-cazador, FR-009 a FR-016).

    Comportamiento.decidir ya resuelve "comparte sala con el jugador vivo,
    entonces ataca" (FR-010). Si no, consulta el mapa de distancias compartido
    de la partida, que asegura cota >= rango, y examina solo las salidas de su
    sala y sus destinos (FR-026(a)): O(salidas).

    No usa azar (FR-018): orden fijo N, S, E, O y desempate por menor id.
    """

    NOMBRE = "cazador"

    def __init__(self, rango: int) -> None:
        self._rango = rango

    @property
    def rango(self) -> int:
        """Costo máximo de ruta que está dispuesto a recorrer (entero >= 0)."""
        return self._rango

    def decidir_sin_jugador(self, enemigo, partida):
        """Un paso por una ruta de costo d hacia el jugador si d <= rango
        (FR-013); si no hay ruta o d > rango, Esperar (FR-012).

        d = min sobre las salidas abiertas u → v de costo + dist(v, jugador)
        (FR-011, FR-014). Ante un empate gana la vecina de menor id y, si dos
        salidas llevan a la misma vecina, la primera en el orden N, S, E, O:
        solo se reemplaza la candidata si la nueva es estrictamente mejor por
        (t, id de la vecina). Una salida cerrada es intransitable (FR-016).
        """
        mapa = partida.mapa_distancias
        mapa.asegurar(partida.jugador.sala, self._rango)
        mejor_salida = None
        mejor_t = None
        mejor_id = None
        for salida in partida.mundo.sala(enemigo.sala).salidas:      # N, S, E, O
            if salida is None or salida.cerrada:
                continue
            vecina = salida.sala_destino
            resto = mapa.distancia(vecina)
            if resto is None:
                continue
            t = salida.costo + resto
            if (mejor_t is None or t < mejor_t
                    or (t == mejor_t and vecina.id < mejor_id)):
                mejor_salida = salida
                mejor_t = t
                mejor_id = vecina.id
        if mejor_salida is None or mejor_t > self._rango:
            return Esperar()
        return Mover(mejor_salida.direccion)


def crear_comportamiento(nombre: str, rango: int = None) -> Comportamiento:
    """Elige la estrategia por el texto de la ficha ('guardián', 'errante'...).
    El rango solo lo usa el cazador, para quien es obligatorio (FR-009)."""
    # DECISIÓN: se compara por prefijo y en minúsculas para tolerar 'guardián' y
    # 'guardian' (con o sin tilde) sin depender de la forma exacta que mande el API.
    texto = nombre.lower()
    if texto.startswith("guard"):
        return Guardian()
    if texto.startswith("errante"):
        return Errante()
    if texto.startswith("rastread"):
        return Rastreador()
    if texto.startswith("cazad"):
        if rango is None:
            raise DatosInvalidos(
                f"El comportamiento '{nombre}' es de un cazador y necesita un rango")
        return Cazador(rango)
    raise ErrorCripta(f"Comportamiento de enemigo desconocido: '{nombre}'")