"""Acciones del juego (§2.3): objetos inmutables con tipo, argumentos y costo base.

Las acciones llevan el id EXPLÍCITO del objetivo (id de instancia), nunca "el
objeto bajo el cursor": así el log de partida basta para reproducirla (--replay).
"""
from __future__ import annotations

from dataclasses import dataclass

from .constantes import (
    COSTO_ABRIR, COSTO_ATACAR, COSTO_EQUIPAR, COSTO_ESPERAR, COSTO_MOVER,
    COSTO_RECOGER, COSTO_SOLTAR, COSTO_USAR)


# DECISIÓN: dataclass congelado: la acción es un valor inmutable que sirve igual
# para el jugador y para los enemigos (mismo vocabulario), y su texto() es lo que
# se anexa al log de partida.
@dataclass(frozen=True)
class Accion:
    NOMBRE = "accion"       # sin anotación: constantes de clase, no campos
    COSTO_BASE = 0

    @property
    def costo_base(self) -> int:
        return self.COSTO_BASE

    def texto(self) -> str:
        """Una línea para el log: NOMBRE y argumentos."""
        partes = self.NOMBRE
        for valor in self.__dict__.values():
            partes += f" {valor}"
        return partes


@dataclass(frozen=True)
class Mover(Accion):
    direccion: str
    NOMBRE = "MOVER"
    COSTO_BASE = COSTO_MOVER


@dataclass(frozen=True)
class AbrirPuerta(Accion):
    direccion: str
    NOMBRE = "ABRIR"
    COSTO_BASE = COSTO_ABRIR


@dataclass(frozen=True)
class Atacar(Accion):
    objetivo: str            # id de instancia del enemigo
    NOMBRE = "ATACAR"
    COSTO_BASE = COSTO_ATACAR


@dataclass(frozen=True)
class Esperar(Accion):
    NOMBRE = "ESPERAR"
    COSTO_BASE = COSTO_ESPERAR


@dataclass(frozen=True)
class Recoger(Accion):
    id_objeto: int           # id de instancia del objeto en el suelo
    NOMBRE = "RECOGER"
    COSTO_BASE = COSTO_RECOGER


@dataclass(frozen=True)
class Soltar(Accion):
    id_objeto: int
    NOMBRE = "SOLTAR"
    COSTO_BASE = COSTO_SOLTAR


@dataclass(frozen=True)
class Usar(Accion):
    id_objeto: int
    NOMBRE = "USAR"
    COSTO_BASE = COSTO_USAR


@dataclass(frozen=True)
class Equipar(Accion):
    id_objeto: int
    NOMBRE = "EQUIPAR"
    COSTO_BASE = COSTO_EQUIPAR


@dataclass(frozen=True)
class UsarPergamino(Accion):
    """No consume tiempo ni cuenta como acción (§2.11)."""
    NOMBRE = "PERGAMINO"
    COSTO_BASE = 0