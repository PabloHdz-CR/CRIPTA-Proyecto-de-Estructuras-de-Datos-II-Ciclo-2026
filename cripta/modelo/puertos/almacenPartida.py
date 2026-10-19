"""Puerto AlmacenPartida (§4.10, guía §5.8): guardar, cargar y cargar_sala.

DECISIÓN: el Controlador solo conoce este contrato; DÓNDE y CÓMO se guarda
(carpeta, nombre de archivo, formato binario con struct) es asunto del
adaptador (AlmacenPartidaDisco). Así ninguna clase del Controlador toca
Path, open() ni mkdir (regla de oro de §4 de la guía), y una prueba puede
inyectar un almacén en memoria sin cambiar el Controlador.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..datos.servicioDatos import ServicioDatos
    from ..mundo.sala import Sala
    from ..nucleo.partida import Partida


class AlmacenPartida(ABC):

    @abstractmethod
    def existe(self, id_cripta: str) -> bool:
        """True si hay una partida guardada de esa cripta."""

    @abstractmethod
    def guardar(self, partida: "Partida") -> str:
        """Persiste la partida y devuelve una descripción legible de dónde
        quedó (para el mensaje al jugador)."""

    @abstractmethod
    def cargar(self, id_cripta: str, servicio: "ServicioDatos") -> "Partida":
        """Reconstruye la partida. Requiere que el servicio ya haya hecho
        iniciar_cripta(id_cripta) para poder resolver fichas. Lanza
        ErrorCripta si el formato es incompatible (§4.10)."""

    @abstractmethod
    def cargar_sala(self, id_cripta: str, id_sala: int,
                    servicio: "ServicioDatos") -> "Sala":
        """Una sola sala, sin leer el resto del guardado (§4.10)."""

    def borrar(self, id_cripta: str) -> None:
        """Elimina el guardado de esa cripta, si lo hay (al terminar la
        partida que lo usaba). No es abstracto: un almacén que no sepa
        borrar simplemente lo deja."""
