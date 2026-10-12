"""Eventos concretos de la agenda (§2.3, §2.10)."""
from __future__ import annotations

from ..nucleo.constantes import (
    CURA_REGENERACION, DANO_VENENO, DURACION_VENENO, INTERVALO_REGENERACION,
    INTERVALO_VENENO)
from .evento import Evento


class EventoAccionActor(Evento):
    """Turno de un actor. El del jugador NO se ejecuta aquí: la Partida lo
    deja primero en la agenda y espera su decisión. El de un enemigo decide
    según su comportamiento, actúa y se reprograma."""

    def ejecutar(self, partida) -> None:
        actor = self.duenio
        # DECISIÓN: el turno del jugador nunca se ejecuta aquí: Partida lo deja en la
        # cima y espera su decisión. Por eso este return sin hacer nada.
        if not actor.vivo or actor is partida.jugador:
            return
        accion = actor.comportamiento.decidir(actor, partida)
        partida.ejecutar_accion_enemigo(actor, accion)
        if actor.vivo and not partida.terminada():
            partida.programar_accion(actor, accion.costo_base)


class EventoVeneno(Evento):
    """Un pulso de veneno. Pulsos en +80, +160, ... hasta +400 inclusive."""

    def __init__(self, tiempo: int, actor, efecto, numero: int) -> None:
        super().__init__(tiempo, actor)
        self.efecto = efecto
        self.numero = numero

    def ejecutar(self, partida) -> None:
        actor = self.duenio
        partida.avisar(f"El veneno hace daño a {actor.nombre}.")
        partida.danar(actor, DANO_VENENO)
        if not actor.vivo:
            return
        # DECISIÓN: un solo evento vivo por efecto, que programa al siguiente (no los 5
        # pulsos de golpe): cancelar el veneno es cancelar UN evento. Pulsos en +80,
        # +160, +240, +320 y +400: el último cae exactamente en +400 (propuesta de §12).
        if self.numero * INTERVALO_VENENO < DURACION_VENENO:
            self.efecto.programar_evento(partida, EventoVeneno(
                self.tiempo + INTERVALO_VENENO, actor, self.efecto, self.numero + 1))
        else:
            self.efecto.terminar(partida)


class EventoCambioVelocidad(Evento):
    """Fin de un efecto de velocidad: restaura la velocidad base. El inicio
    ocurre en el instante de usar la poción (Partida.aplicar_velocidad)."""

    def __init__(self, tiempo: int, actor, efecto) -> None:
        super().__init__(tiempo, actor)
        self.efecto = efecto

    def ejecutar(self, partida) -> None:
        self.efecto.terminar(partida)


class EventoApagarAntorcha(Evento):
    def __init__(self, tiempo: int, jugador, efecto) -> None:
        super().__init__(tiempo, jugador)
        self.efecto = efecto

    def ejecutar(self, partida) -> None:
        partida.avisar("La antorcha se apaga.")
        self.efecto.terminar(partida)


class EventoRegeneracion(Evento):
    """Cura cada 200 unidades sin pasar de vida_max."""

    def __init__(self, tiempo: int, actor, efecto, cantidad: int = CURA_REGENERACION) -> None:
        super().__init__(tiempo, actor)
        self.efecto = efecto
        self.cantidad = cantidad

    def ejecutar(self, partida) -> None:
        actor = self.duenio
        partida.curar(actor, self.cantidad)
        self.efecto.programar_evento(partida, EventoRegeneracion(
            self.tiempo + INTERVALO_REGENERACION, actor, self.efecto, self.cantidad))


class EventoRearmeTrampa(Evento):
    # DECISIÓN: el rearme es un evento de la agenda (no una comparación de tiempo al
    # volver a entrar): ocurre en su instante exacto y en orden (tiempo, secuencia).
    def ejecutar(self, partida) -> None:
        trampa = self.duenio
        partida.mutador.asignar(trampa, "armada", True)
        partida.mutador.asignar(trampa, "evento_rearme", None)


class EventoCierrePuerta(Evento):
    """Cierre automático de una salida (§2.5)."""

    def ejecutar(self, partida) -> None:
        salida = self.duenio
        partida.mutador.asignar(salida, "cerrada", True)
        partida.mutador.asignar(salida, "evento_cierre", None)
        partida.avisar(f"La puerta hacia el {salida.direccion} se cierra sola.")