"""Puerto AlmacenPuntajes (§2.12, guía §5.8): cargar y agregar.

DECISIÓN: el Controlador registra el puntaje al terminar la partida sin
saber que detrás hay un archivo JSON Lines (PuntajesArchivo).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..nucleo.puntajes import RegistroPuntaje, TablaPuntajes


class AlmacenPuntajes(ABC):

    @abstractmethod
    def agregar(self, registro: "RegistroPuntaje") -> None:
        """Anexa un registro. No relee los anteriores."""

    @abstractmethod
    def cargar(self) -> "TablaPuntajes":
        """Todos los registros guardados."""
