"""Puerto para copiar el estado completo de una Partida (004-linea-tiempo, R1).

Lo usa la línea de tiempo para sus puntos de control: el Modelo no conoce el
formato binario, solo este contrato. El adaptador es CopiadorBinario
(adaptadores/partidaBinaria.py).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class CopiadorEstado(ABC):
    """Toma una copia completa del estado de una Partida y la restaura en una
    Partida nueva e independiente. La copia incluye el azar (random.Random),
    la agenda con sus secuencias y el conocimiento del jugador, así que
    re-simular desde ella reproduce exactamente la partida (principio II)."""

    @abstractmethod
    def tomar(self, partida) -> bytes:
        """Los bytes del estado completo de 'partida', sin modificarla."""

    @abstractmethod
    def restaurar(self, datos: bytes, servicio):
        """Una Partida nueva con el estado de 'datos', que usa 'servicio' para
        resolver fichas. No tiene diario, línea, vista ni registro."""
