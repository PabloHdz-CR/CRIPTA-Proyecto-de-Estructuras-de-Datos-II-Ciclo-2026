"""Enemigos (§2.2, §2.4)."""
from __future__ import annotations

from ..estructuras.listaEnlazada import ListaEnlazada
from ..nucleo.constantes import COSTO_PRIMERA_ACCION_ENEMIGO
from ..reloj.efecto import EfectoRegeneracion
from .actor import Actor


class Enemigo(Actor):
    def __init__(self, id_instancia: str, ficha, vida: int, sala: int, comportamiento) -> None:
        super().__init__(id_instancia, ficha.nombre, ficha, vida, ficha.vida_max,
                         ficha.ataque, ficha.defensa, ficha.velocidad, sala)
        self.comportamiento = comportamiento
        self.activo = False
        self.suelta = ListaEnlazada()      # fichas de lo que deja al morir
        # DECISIÓN (SUPUESTO): la ficha de enemigo del catálogo no trae campo de
        # regeneración; queda en 0 y el efecto existe por si el enunciado lo confirma.
        self.regeneracion = 0              # cura por pulso de 200; 0 = no regenera

    def activar(self, partida) -> None:
        """Pasa de dormido a activo y programa su primera acción (costo 100)."""
        sala = partida.mundo.sala(self.sala)
        partida.mutador.enemigo_activar(sala, self)
        partida.programar_accion(self, COSTO_PRIMERA_ACCION_ENEMIGO)
        if self.regeneracion > 0:
            EfectoRegeneracion(self, self.regeneracion).aplicar(partida)