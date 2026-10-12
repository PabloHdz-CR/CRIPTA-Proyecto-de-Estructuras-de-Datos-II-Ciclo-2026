"""Trampas (§2.10)."""
from __future__ import annotations

from ..nucleo.constantes import REARME_TRAMPA
from ..reloj.eventos import EventoRearmeTrampa


class Trampa:
    """Se activa al entrar el jugador a la sala, justo después del movimiento
    y antes del siguiente evento: hace daño fijo (sin defensa), se desarma y
    programa su rearme (300 salvo que la ficha diga otro valor)."""

    def __init__(self, id_instancia: str, ficha, sala: int) -> None:
        self.id_instancia = id_instancia
        self.ficha = ficha
        self.sala = sala
        self.armada = True
        self.evento_rearme = None

    @property
    def nombre(self) -> str:
        return self.ficha.nombre

    def activar(self, partida) -> None:
        if not self.armada:
            return
        mutador = partida.mutador
        mutador.asignar(self, "armada", False)
        # DECISIÓN: el rearme usa el valor de la ficha si lo trae y 300 si no (§2.10).
        rearme = self.ficha.rearme if self.ficha.rearme is not None else REARME_TRAMPA
        evento = EventoRearmeTrampa(partida.reloj + rearme, self)
        mutador.agenda_programar(evento)
        mutador.asignar(self, "evento_rearme", evento)
        partida.avisar(f"¡{self.nombre}! Recibes {self.ficha.dano} de daño.")
        # DECISIÓN (SUPUESTO): daño fijo de la ficha, sin restar defensa: la trampa no
        # es un ataque y §2.6 define la fórmula solo para el combate.
        partida.danar(partida.jugador, self.ficha.dano)