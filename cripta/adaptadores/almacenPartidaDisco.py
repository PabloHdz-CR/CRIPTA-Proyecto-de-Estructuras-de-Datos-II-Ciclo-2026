"""AlmacenPartidaDisco: implementa el puerto AlmacenPartida con el formato
binario propio de PartidaBinaria (§4.10).

DECISIÓN: un archivo por cripta (`<carpeta>/<id>.bin`): guardar dos veces la
misma cripta sobrescribe, y saber si existe un guardado es O(1) (una consulta
al sistema de archivos), sin índice que mantener.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from ..modelo.puertos.almacenPartida import AlmacenPartida
from .nombresArchivo import nombre_seguro
from .partidaBinaria import PartidaBinaria

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.mundo.sala import Sala
    from ..modelo.nucleo.partida import Partida

CARPETA_POR_DEFECTO = "guardados"


class AlmacenPartidaDisco(AlmacenPartida):

    def __init__(self, carpeta: Union[str, Path] = CARPETA_POR_DEFECTO) -> None:
        self._carpeta = Path(carpeta)

    def _ruta(self, id_cripta: str) -> Path:
        return self._carpeta / f"{nombre_seguro(id_cripta)}.bin"

    def existe(self, id_cripta: str) -> bool:
        return self._ruta(id_cripta).exists()

    def guardar(self, partida: "Partida") -> str:
        self._carpeta.mkdir(parents=True, exist_ok=True)
        ruta = self._ruta(partida.datos.id)
        PartidaBinaria.guardar(partida, ruta)
        return str(ruta)

    def cargar(self, id_cripta: str, servicio: "ServicioDatos") -> "Partida":
        return PartidaBinaria.cargar(self._ruta(id_cripta), servicio)

    def cargar_sala(self, id_cripta: str, id_sala: int,
                    servicio: "ServicioDatos") -> "Sala":
        return PartidaBinaria.cargar_sala(self._ruta(id_cripta), id_sala, servicio)

    def borrar(self, id_cripta: str) -> None:
        """O(1). Si no existe, no pasa nada."""
        self._ruta(id_cripta).unlink(missing_ok=True)
