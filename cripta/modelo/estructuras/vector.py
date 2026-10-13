"""Vector de tamaño fijo, hecho con nodos enlazados (sin list de Python).

Es un árbol binario COMPLETO de nodos, igual que HeapBinario: las posiciones se
numeran desde 1 por niveles (los hijos de p son 2p y 2p + 1) y se llega a la
posición p leyendo sus bits (se ignora el primero; 0 = izquierda, 1 = derecha).
Así se tiene acceso por índice sin ningún arreglo y sin recorrer todo.
"""
from __future__ import annotations

from .cola import Cola
from .nodoHeap import NodoHeap


class Vector:
    """Vector de tamaño fijo con acceso por índice.

    Costos (n = tamaño): crear O(n); obtener y establecer O(log n) (la altura
    del árbol); recorrer O(n). Espacio O(n). Una lista nativa daría O(1) por
    acceso, pero §3 la prohíbe como estructura general: este es el precio.
    """

    def __init__(self, tamano: int, valor_inicial=None) -> None:
        if tamano < 0:
            raise ValueError("El tamaño del vector no puede ser negativo")
        self._tamano = tamano
        # DECISIÓN: no se guarda una list, sino la raíz de un árbol de nodos. Es la
        # forma de tener 'índice -> elemento' sin arreglos (§3), al precio de O(log n).
        self._raiz = None
        self._construir(valor_inicial)

    def __len__(self) -> int:
        return self._tamano

    def obtener(self, indice: int):
        self._exigir_rango(indice)
        return self._nodo_en(indice + 1).dato

    def establecer(self, indice: int, valor) -> None:
        self._exigir_rango(indice)
        self._nodo_en(indice + 1).dato = valor

    def __iter__(self):
        """Los elementos en orden de índice (el orden por niveles del árbol
        completo coincide con el orden de posiciones). O(n)."""
        if self._raiz is None:
            return
        pendientes = Cola()
        pendientes.encolar(self._raiz)
        while not pendientes.esta_vacia():
            nodo = pendientes.desencolar()
            yield nodo.dato
            if nodo.izquierdo is not None:
                pendientes.encolar(nodo.izquierdo)
            if nodo.derecho is not None:
                pendientes.encolar(nodo.derecho)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _construir(self, valor_inicial) -> None:
        """Crea los nodos por niveles, de izquierda a derecha. O(n)."""
        if self._tamano == 0:
            return
        # DECISIÓN: se reutiliza NodoHeap (dato, izquierdo, derecho, padre) en vez de
        # crear otro tipo de nodo, y se construye por niveles con una Cola (sin
        # recursión) para no chocar con el límite de recursión de Python.
        self._raiz = NodoHeap(valor_inicial)
        creados = 1
        pendientes = Cola()
        pendientes.encolar(self._raiz)
        while creados < self._tamano:
            padre = pendientes.desencolar()
            padre.izquierdo = NodoHeap(valor_inicial, padre)
            pendientes.encolar(padre.izquierdo)
            creados += 1
            if creados < self._tamano:
                padre.derecho = NodoHeap(valor_inicial, padre)
                pendientes.encolar(padre.derecho)
                creados += 1

    def _nodo_en(self, posicion: int):
        """Nodo de esa posición (1 = raíz), bajando según los bits. O(log n)."""
        # DECISIÓN: mismo truco de bits que HeapBinario._nodo_en. Se repite aquí
        # (pocas líneas) en vez de heredar, porque un vector no es un montículo.
        nodo = self._raiz
        mascara = 1
        while mascara * 2 <= posicion:
            mascara *= 2          # bit más alto de la posición
        mascara //= 2             # se salta ese primer bit: es el de la raíz
        while mascara > 0:
            nodo = nodo.derecho if posicion & mascara else nodo.izquierdo
            mascara //= 2
        return nodo

    def _exigir_rango(self, indice: int) -> None:
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice}")