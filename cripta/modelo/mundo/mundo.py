"""Mundo: las salas de la cripta indexadas por id (§2.1, §3.3)."""
from __future__ import annotations

from ..estructuras.listaEnlazada import ListaEnlazada
from ..estructuras.tablaHash import TablaHash
from ..puertos.dto import DIRECCIONES
from ..puertos.errores import ErrorCripta
from .sala import Sala
from .salida import Salida


class Mundo:
    """Salas en una TablaHash id -> Sala (O(log n) promedio, ver TablaHash; los ids
    no tienen por qué ser consecutivos). Guarda también los datos fijos."""

    def __init__(self, datos) -> None:
        self.sala_inicial = datos.sala_inicial
        self.sala_salida = datos.sala_salida
        self.llave_salida = datos.llave_salida
        self.inventario_max = datos.inventario_max
        self.estadisticas_jugador = datos.jugador
        # DECISIÓN: TablaHash propia (id -> Sala). No se asume que los ids sean
        # consecutivos, así que no sirve usar el id como posición de un vector (§12).
        self._salas = TablaHash()

    def __len__(self) -> int:
        return len(self._salas)

    def sala(self, id_sala: int) -> Sala:
        sala = self._salas.obtener(id_sala)
        if sala is None:
            raise ErrorCripta(f"La sala {id_sala} no existe en esta cripta")
        return sala

    def existe(self, id_sala: int) -> bool:
        return self._salas.contiene(id_sala)

    def agregar_esqueleto(self, salas_dto) -> None:
        """Crea las Sala y Salida a partir de SalaDTO (una sola vez, al cargar)."""
        for sala_dto in salas_dto:
            self._salas.poner(sala_dto.id, Sala(
                sala_dto.id, sala_dto.nombre, self._construir_salidas(sala_dto.salidas)))

    def tiene_contenido(self, id_sala: int) -> bool:
        return self.sala(id_sala).contenido_cargado

    def incorporar_contenido(self, id_sala: int, enemigos, objetos, trampas) -> None:
        """Vuelca enemigos (dormidos), objetos del suelo y trampas ya construidos."""
        sala = self.sala(id_sala)
        # DECISIÓN: incorporar es idempotente: repetirlo no duplica enemigos ni
        # objetos (por si el servicio entrega dos veces la misma sala).
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
        # DECISIÓN: if/elif y no un dict dirección -> posición (§3 prohíbe dict como
        # tabla de búsqueda).
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