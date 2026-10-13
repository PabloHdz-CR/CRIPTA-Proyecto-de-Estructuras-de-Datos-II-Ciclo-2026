"""Estrategias de los enemigos (§2.8, §2.9). decidir() devuelve una Accion."""
from __future__ import annotations

from ..nucleo.accion import Atacar, Esperar, Mover
from ..puertos.errores import ErrorCripta


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


def crear_comportamiento(nombre: str) -> Comportamiento:
    """Elige la estrategia por el texto de la ficha ('guardián', 'errante'...)."""
    # DECISIÓN: se compara por prefijo y en minúsculas para tolerar 'guardián' y
    # 'guardian' (con o sin tilde) sin depender de la forma exacta que mande el API.
    texto = nombre.lower()
    if texto.startswith("guard"):
        return Guardian()
    if texto.startswith("errante"):
        return Errante()
    if texto.startswith("rastread"):
        return Rastreador()
    raise ErrorCripta(f"Comportamiento de enemigo desconocido: '{nombre}'")