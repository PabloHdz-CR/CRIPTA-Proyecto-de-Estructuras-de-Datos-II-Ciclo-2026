"""Puertos del log de partida (§4.11, guía §5.8): RegistroAcciones y
AlmacenRegistros, más el EncabezadoPartida que ambos comparten.

DECISIÓN: EncabezadoPartida vive en el puerto como dato puro (sin formato
de texto): el Controlador lo arma y ModoReplay lo lee sin saber que el log
es un archivo de texto. Cómo se escribe en disco lo decide RegistroArchivo.

DECISIÓN: además del log activo (uno por cripta, solo anexado, el que
continúa una partida cargada), cada partida TERMINADA archiva una copia con
un id propio (archivar()). El puntaje guarda ese id, y así la tabla de
puntajes puede reproducir exactamente esa partida aunque después se hayan
jugado otras en la misma cripta. Alternativa descartada: un log por partida
desde el inicio: guardar/cargar (respaldar/restaurar) trabajan sobre el log
de la cripta, y habría que rastrear qué log continúa cada guardado.

DECISIÓN: AlmacenRegistros existe porque el Controlador necesita un log
POR cripta elegida en el menú; en vez de que ControladorMenu arme rutas
(lógica de archivos), pide `registro_de(id_cripta)` y el adaptador decide
la convención de nombres. Costo O(1) por partida.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..estructuras.listaEnlazada import ListaEnlazada
    from ..nucleo.accion import Accion


class EncabezadoPartida:
    """id de cripta, versión de cripta, versión de catálogo y semilla: el
    mínimo que exige §4.11 para poder reproducir la partida."""

    def __init__(self, id_cripta: str, version_cripta: str,
                 version_catalogo: Optional[str], semilla: int) -> None:
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.semilla = semilla


class RegistroAcciones(ABC):
    """Log de SOLO anexado de una partida."""

    @abstractmethod
    def iniciar(self, encabezado: EncabezadoPartida) -> None:
        """Empieza un log nuevo con su encabezado (descarta el anterior)."""

    @abstractmethod
    def registrar_accion(self, accion: "Accion") -> None:
        """Anexa una acción aceptada. O(1): nunca relee lo anterior."""

    @abstractmethod
    def leer(self) -> "tuple[EncabezadoPartida, ListaEnlazada]":
        """(encabezado, ListaEnlazada de Accion) en el orden en que ocurrieron."""

    @abstractmethod
    def respaldar(self) -> None:
        """Toma una copia del log tal como está (al guardar la partida)."""

    @abstractmethod
    def restaurar(self) -> bool:
        """Reemplaza el log por el último respaldo (al cargar la partida).
        False si no hay respaldo."""

    def archivar(self) -> Optional[str]:
        """Guarda una copia del log tal como está (al terminar la partida)
        y devuelve su id, con el que AlmacenRegistros.registro_archivado la
        vuelve a abrir. No es abstracto: un registro que no sepa archivar
        devuelve None y esa partida simplemente no tiene replay."""
        return None


class AlmacenRegistros(ABC):

    @abstractmethod
    def registro_de(self, id_cripta: str) -> RegistroAcciones:
        """El log asociado a una cripta."""

    def registro_archivado(self, id_partida: str) -> Optional[RegistroAcciones]:
        """El log archivado de una partida terminada (ver archivar()), o
        None si no existe. No es abstracto: sin historial, no hay replay."""
        return None

    def existe_archivado(self, id_partida: str) -> bool:
        return False
