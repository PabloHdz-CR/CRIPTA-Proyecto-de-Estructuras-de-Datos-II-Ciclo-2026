
from __future__ import annotations

from ..nucleo.constantes import ID_JUGADOR
from ..objetos.equipo import Equipo
from ..objetos.inventario import Inventario
from .actor import Actor


class Jugador(Actor):
    def __init__(self, estadisticas, sala: int, capacidad_inventario: int, cache=None) -> None:
        super().__init__(ID_JUGADOR, "Jugador", None, estadisticas.vida_max,
                         estadisticas.vida_max, estadisticas.ataque, estadisticas.defensa,
                         estadisticas.velocidad, sala)
        self.inventario = Inventario(capacidad_inventario, cache)
        self.equipo = Equipo()
        self.antorcha_encendida = False
        # DECISIÓN: los contadores viven en el jugador y se cambian con el Mutador,
        # así el retroceso los revierte como cualquier otro valor.
        self.acciones = 0
        self.enemigos_derrotados = 0

    def ataque_efectivo(self) -> int:
        return self.ataque + self.equipo.bono_ataque()

    def defensa_efectiva(self) -> int:
        return self.defensa + self.equipo.bono_defensa()