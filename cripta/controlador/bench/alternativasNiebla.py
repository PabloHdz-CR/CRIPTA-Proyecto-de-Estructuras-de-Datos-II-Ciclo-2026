"""Alternativas descartadas de 002-niebla-guerra, SOLO para medir (T045).

Cada una es la opción que el plan descartó en research.md, implementada con
las estructuras propias del proyecto para compararla en benchNiebla:

  - RutaHaciaAtras (R5): Dijkstra completo HACIA ATRÁS desde el destino por las
    entrantes conocidas y luego la fórmula del cazador en la sala de origen
    (reutilizar el patrón del mapa de distancias de 001).
  - ConsultaLineal (R1): el estado de una sala buscándola por id en una lista
    de conocidas, en vez de leer el campo del objeto.
  - RegistroOrdenado (R4, la orientación inicial del equipo): registro de
    conocidas que se mantiene ordenado por id insertando cada sala en su lugar.

No las usa el juego. Ninguna usa dict, set, list de Python ni heapq.
"""
from __future__ import annotations

from typing import Optional

from ...modelo.estructuras.heapMinimo import HeapMinimo
from ...modelo.estructuras.nodo import Nodo
from ...modelo.mundo.conocimiento import ABIERTA, EXPLORADA


class _EntradaAtras:
    __slots__ = ("costo", "sala")

    def __init__(self, costo: int, sala) -> None:
        self.costo = costo
        self.sala = sala

    def __lt__(self, otra: "_EntradaAtras") -> bool:
        if self.costo != otra.costo:
            return self.costo < otra.costo
        return self.sala.id < otra.sala.id


class RutaHaciaAtras:
    """Primer paso de «ir a» con un Dijkstra completo hacia atrás desde el
    destino (sin parada temprana) y la fórmula del cazador en el origen:
    min(costo(u, v) + dist(v)), desempatando por (id de v, dirección)."""

    def __init__(self) -> None:
        self._sello = 0
        self.salas_fijadas = 0

    @property
    def salas_fijadas_ultima(self) -> int:
        """Salas que fijó la última búsqueda (mismo nombre que en BuscadorRuta)."""
        return self.salas_fijadas

    def primer_paso(self, origen, destino) -> Optional[object]:
        self._sello += 1
        sello = self._sello
        self.salas_fijadas = 0
        heap = HeapMinimo()
        destino._alt_sello, destino._alt_costo = sello, 0
        heap.insertar(_EntradaAtras(0, destino))
        while not heap.esta_vacio():
            entrada = heap.extraer_minimo()
            sala = entrada.sala
            if entrada.costo != sala._alt_costo:
                continue
            self.salas_fijadas += 1
            for salida in sala.entrantes:
                previa = salida.origen
                if salida.recordada != ABIERTA or previa.conocimiento != EXPLORADA:
                    continue
                costo = sala._alt_costo + salida.costo
                if getattr(previa, "_alt_sello", 0) != sello or costo < previa._alt_costo:
                    previa._alt_sello, previa._alt_costo = sello, costo
                    heap.insertar(_EntradaAtras(costo, previa))
        mejor = None
        mejor_costo = 0
        mejor_clave = 0
        indice = 0
        for salida in origen.salidas:
            if salida is not None and salida.recordada == ABIERTA:
                vecina = salida.sala_destino
                if (vecina.conocimiento == EXPLORADA
                        and getattr(vecina, "_alt_sello", 0) == sello):
                    costo = salida.costo + vecina._alt_costo
                    clave = vecina.id * 4 + indice
                    if mejor is None or costo < mejor_costo or (
                            costo == mejor_costo and clave < mejor_clave):
                        mejor, mejor_costo, mejor_clave = salida, costo, clave
            indice += 1
        return mejor


class ConsultaLineal:
    """Estado de una sala buscándola por id en las conocidas (O(k))."""

    def __init__(self, conocidas) -> None:
        self._conocidas = conocidas

    def estado(self, id_sala: int) -> int:
        for sala in self._conocidas:
            if sala.id == id_sala:
                return sala.conocimiento
        return 0


class RegistroOrdenado:
    """Registro de conocidas mantenido en orden de id por inserción (O(k) por
    sala), con nodos propios."""

    def __init__(self) -> None:
        self._cabeza = None
        self._tamano = 0

    def agregar(self, sala) -> None:
        nuevo = Nodo(sala)
        if self._cabeza is None or sala.id < self._cabeza.dato.id:
            nuevo.siguiente = self._cabeza
            self._cabeza = nuevo
        else:
            actual = self._cabeza
            while actual.siguiente is not None and actual.siguiente.dato.id < sala.id:
                actual = actual.siguiente
            nuevo.siguiente = actual.siguiente
            actual.siguiente = nuevo
        self._tamano += 1

    def quitar(self, sala) -> None:
        """Quita la sala recorriendo hasta ella (O(k)); la usa el bench para
        medir muchas entradas sin que el registro crezca entre una y otra."""
        anterior = None
        actual = self._cabeza
        while actual is not None and actual.dato is not sala:
            anterior = actual
            actual = actual.siguiente
        if actual is None:
            return
        if anterior is None:
            self._cabeza = actual.siguiente
        else:
            anterior.siguiente = actual.siguiente
        self._tamano -= 1

    def __len__(self) -> int:
        return self._tamano
