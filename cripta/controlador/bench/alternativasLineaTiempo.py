"""SOLO PARA MEDIR (004-linea-tiempo, T032): alternativas descartadas de la
línea de tiempo. El juego no usa nada de este archivo.

- Búsqueda lineal del bloque de un instante en una ListaEnlazada (contra la
  búsqueda binaria sobre el ArregloArbol, research R4).
- "Sin puntos de control" no necesita código propio: es la misma línea con K
  mayor que la partida (un solo punto de control, el de la primera acción),
  así cada consulta re-simula desde el principio (research R2).
"""
from __future__ import annotations

from ...modelo.estructuras.listaEnlazada import ListaEnlazada

K_SIN_PUNTOS_DE_CONTROL = 10 ** 9


class BloquesLineales:
    """Los mismos bloques en una ListaEnlazada: ubicar el de un instante
    recorre desde el primero. O(n) por consulta."""

    def __init__(self) -> None:
        self._bloques = ListaEnlazada()

    def agregar_al_final(self, bloque) -> None:
        self._bloques.agregar_al_final(bloque)

    def __len__(self) -> int:
        return len(self._bloques)

    def posicion_de_instante(self, t: int) -> int:
        """La posición (desde 1) del último bloque con tiempo_inicio ≤ t."""
        mejor = 1
        posicion = 0
        for bloque in self._bloques:
            posicion += 1
            if bloque.tiempo_inicio > t:
                break
            mejor = posicion
        return mejor
