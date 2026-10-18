"""GestorGuardado: guarda y carga partidas vía el puerto AlmacenPartida
(§4.10, guía §7), incluida la carga de una sala específica.

DECISIÓN: el Gestor NO sabe de rutas, carpetas ni formato binario: todo
eso vive en el adaptador AlmacenPartidaDisco, que inyecta FabricaAplicacion.
Su responsabilidad propia es COORDINAR el guardado de la partida con el del
log de acciones: los dos se toman en el mismo instante, así al cargar el log
vuelve a contener exactamente las acciones que llevan a ese estado y
--replay sigue siendo fiel (§4.11).

Complejidad: guardar/cargar son O(S) en el tamaño del estado (las salas
visitadas), dominadas por el adaptador; cargar_sala es O(tamaño de una sala)
gracias a la tabla de offsets del formato binario (§4.10). Respaldar el log
es O(A), A = acciones registradas, una vez por guardado.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.mundo.sala import Sala
    from ..modelo.nucleo.partida import Partida
    from ..modelo.puertos.almacenPartida import AlmacenPartida
    from ..modelo.puertos.registroAcciones import RegistroAcciones


class GestorGuardado:

    def __init__(self, almacen: "AlmacenPartida") -> None:
        self._almacen = almacen

    def existe_guardado(self, id_cripta: str) -> bool:
        return self._almacen.existe(id_cripta)

    def guardar(self, partida: "Partida", registro: "RegistroAcciones") -> str:
        """Guarda la partida y respalda el log. Devuelve dónde quedó."""
        ubicacion = self._almacen.guardar(partida)
        registro.respaldar()
        return ubicacion

    def cargar(self, id_cripta: str, servicio: "ServicioDatos",
               registro: "RegistroAcciones") -> "Partida":
        """Requiere que antes se haya hecho servicio.iniciar_cripta(id_cripta).
        Restaura el log al respaldo tomado junto con ese guardado."""
        partida = self._almacen.cargar(id_cripta, servicio)
        registro.restaurar()
        return partida

    def borrar(self, id_cripta: str) -> None:
        """Al terminar (ganar o morir) la partida que usaba ese guardado:
        si quedara, el menú reanudaría una partida que ya terminó."""
        self._almacen.borrar(id_cripta)

    def cargar_sala(self, id_cripta: str, id_sala: int,
                    servicio: "ServicioDatos") -> "Sala":
        """Una sola sala sin leer el archivo completo (§4.10)."""
        return self._almacen.cargar_sala(id_cripta, id_sala, servicio)
