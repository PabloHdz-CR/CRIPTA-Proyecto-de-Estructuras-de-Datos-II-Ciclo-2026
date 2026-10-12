"""Efectos activos sobre un actor (§2.10, §4.1).

Un Efecto guarda su evento pendiente, así cancelarlo no obliga a recorrer la
agenda. Todo cambio pasa por partida.mutador (punto único de mutación).
"""
from __future__ import annotations

from ..nucleo.constantes import INTERVALO_REGENERACION, INTERVALO_VENENO
from .eventos import (
    EventoApagarAntorcha, EventoCambioVelocidad, EventoRegeneracion, EventoVeneno)


class Efecto:
    TIPO = "efecto"

    def __init__(self, actor) -> None:
        self.actor = actor
        # DECISIÓN: el efecto guarda su (único) evento pendiente, así cancelarlo no
        # obliga a recorrer la agenda (§4.1).
        self.evento = None            # el evento pendiente de este efecto

    def aplicar(self, partida) -> None:
        partida.mutador.efecto_agregar(self.actor, self)
        self.al_aplicar(partida)

    def cancelar(self, partida) -> None:
        """Interrumpe el efecto (antídoto, reemplazo o muerte)."""
        self._cancelar_evento(partida)
        self.al_terminar(partida)
        partida.mutador.efecto_quitar(self.actor, self)

    def terminar(self, partida) -> None:
        """Fin natural: el evento que lo llama ya salió de la agenda."""
        partida.mutador.asignar(self, "evento", None)
        self.al_terminar(partida)
        partida.mutador.efecto_quitar(self.actor, self)

    def programar_evento(self, partida, evento) -> None:
        partida.mutador.agenda_programar(evento)
        partida.mutador.asignar(self, "evento", evento)

    def _cancelar_evento(self, partida) -> None:
        if self.evento is not None:
            partida.mutador.agenda_cancelar(self.evento)
            partida.mutador.asignar(self, "evento", None)

    def al_aplicar(self, partida) -> None:
        """Gancho de cada tipo de efecto."""

    def al_terminar(self, partida) -> None:
        """Gancho: limpieza al terminar o cancelarse."""


class EfectoVeneno(Efecto):
    TIPO = "veneno"

    def al_aplicar(self, partida) -> None:
        self.programar_evento(partida, EventoVeneno(
            partida.reloj + INTERVALO_VENENO, self.actor, self, 1))


class EfectoVelocidad(Efecto):
    TIPO = "velocidad"

    def __init__(self, actor, modificador: int, duracion: int) -> None:
        super().__init__(actor)
        self.modificador = modificador
        self.duracion = duracion

    def al_aplicar(self, partida) -> None:
        # DECISIÓN (SUPUESTO): modificador_velocidad se SUMA a la velocidad base; el
        # enunciado dado no aclara si es suma o multiplicador. Se parte de la base y
        # no de la velocidad actual para que dos pociones no se acumulen.
        partida.cambiar_velocidad(
            self.actor, max(1, self.actor.velocidad_base + self.modificador))
        self.programar_evento(partida, EventoCambioVelocidad(
            partida.reloj + self.duracion, self.actor, self))

    def al_terminar(self, partida) -> None:
        if self.actor.vivo:
            partida.cambiar_velocidad(self.actor, self.actor.velocidad_base)


class EfectoAntorcha(Efecto):
    TIPO = "antorcha"

    def __init__(self, jugador, duracion: int) -> None:
        super().__init__(jugador)
        self.duracion = duracion

    def al_aplicar(self, partida) -> None:
        partida.mutador.asignar(self.actor, "antorcha_encendida", True)
        self.programar_evento(partida, EventoApagarAntorcha(
            partida.reloj + self.duracion, self.actor, self))

    def al_terminar(self, partida) -> None:
        partida.mutador.asignar(self.actor, "antorcha_encendida", False)


class EfectoRegeneracion(Efecto):
    TIPO = "regeneracion"

    def __init__(self, actor, cantidad: int) -> None:
        super().__init__(actor)
        self.cantidad = cantidad

    def al_aplicar(self, partida) -> None:
        self.programar_evento(partida, EventoRegeneracion(
            partida.reloj + INTERVALO_REGENERACION, self.actor, self, self.cantidad))