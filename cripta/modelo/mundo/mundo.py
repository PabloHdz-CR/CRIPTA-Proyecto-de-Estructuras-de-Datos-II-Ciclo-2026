"""Mundo: las salas de la cripta indexadas por id (§2.1, §3.3)."""
from __future__ import annotations

from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.dto import DIRECCIONES
from ..puertos.errores import ErrorCripta
from .sala import Sala
from .salida import Salida


class Mundo:
    """Salas en una ListaEnlazada, buscadas por id con recorrido lineal (O(salas),
    igual que EsqueletoCripta, D32): el equipo no usa una tabla hash como índice
    en ningún punto del programa. Con las decenas o pocos cientos de salas de
    una cripta esto es aceptable. Guarda también los datos fijos."""

    def __init__(self, datos) -> None:
        self.sala_inicial = datos.sala_inicial
        self.sala_salida = datos.sala_salida
        self.llave_salida = datos.llave_salida
        self.inventario_max = datos.inventario_max
        self.estadisticas_jugador = datos.jugador
        # DECISIÓN: ListaEnlazada y búsqueda lineal por id (no TablaHash): no se
        # asume que los ids sean consecutivos, y el proyecto no usa una tabla de
        # búsqueda propia como sustituto de dict (§7; ver D32 en EsqueletoCripta).
        self._salas = ListaEnlazada()

    def __len__(self) -> int:
        return len(self._salas)

    def __iter__(self):
        return iter(self._salas)

    def _buscar(self, id_sala: int):
        for sala in self._salas:
            if sala.id == id_sala:
                return sala
        return None

    def sala(self, id_sala: int) -> Sala:
        sala = self._buscar(id_sala)
        if sala is None:
            raise ErrorCripta(f"La sala {id_sala} no existe en esta cripta")
        return sala

    def existe(self, id_sala: int) -> bool:
        return self._buscar(id_sala) is not None

    def agregar_esqueleto(self, salas_dto) -> None:
        """Crea las Sala y Salida a partir de SalaDTO (una sola vez, al cargar)."""
        for sala_dto in salas_dto:
            self._salas.agregar_al_final(Sala(
                sala_dto.id, sala_dto.nombre, self._construir_salidas(sala_dto.salidas)))

    def tiene_contenido(self, id_sala: int) -> bool:
        return self.sala(id_sala).contenido_cargado

    def incorporar_contenido(self, id_sala: int, enemigos, objetos, trampas) -> None:
        """Vuelca enemigos (dormidos), objetos del suelo y trampas ya construidos."""
        sala = self.sala(id_sala)
        if sala.contenido_cargado:
            return
        for enemigo in enemigos:
            sala.agregar_dormido(enemigo)
        for objeto in objetos:
            sala.suelo.agregar_al_final(objeto)
        for trampa in trampas:
            sala.trampas.agregar_al_final(trampa)
        sala.contenido_cargado = True

    def vecinas(self, id_sala: int) -> ListaEnlazada:
        """Ids de las salas alcanzables por una salida abierta (orden N, S, E, O)."""
        ids = ListaEnlazada()
        for salida in self.sala(id_sala).vecinas_abiertas():
            ids.agregar_al_final(salida.destino)
        return ids

    @staticmethod
    def _construir_salidas(salidas_dto) -> tuple:
        norte = sur = este = oeste = None
        for dto in salidas_dto:
            salida = Salida(dto.direccion, dto.sala, dto.cerrada, dto.llave,
                            dto.cierre_automatico)
            if dto.direccion == DIRECCIONES[0]:
                norte = salida
            elif dto.direccion == DIRECCIONES[1]:
                sur = salida
            elif dto.direccion == DIRECCIONES[2]:
                este = salida
            elif dto.direccion == DIRECCIONES[3]:
                oeste = salida
        return (norte, sur, este, oeste)