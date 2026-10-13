"""Tabla hash propia: encadenamiento separado con cubetas de ListaEnlazada.

Sustituye a dict en todo el modelo (§3 lo prohíbe como índice). Las claves
pueden ser int (ids de sala) o str (ids de catálogo, ids de instancia).
"""
from __future__ import annotations

from .listaEnlazada import ListaEnlazada
from .vector import Vector

# DECISIÓN: cada entrada es un _Par mutable dentro de la cubeta, así reemplazar un
# valor no obliga a reconstruir la cubeta.
class _Par:
    def __init__(self, clave, valor) -> None:
        self.clave = clave
        self.valor = valor


class TablaHash:
    """Mapa clave -> valor.

    Costos (B = cubetas, proporcional a n): hallar la cubeta cuesta O(log B)
    porque el Vector no tiene arreglo (es un árbol de nodos); recorrer la
    cubeta cuesta O(1) en promedio por el factor de carga <= 3/4. Total:
    poner, obtener, contiene y eliminar O(log n) en promedio. Al superar 3/4 de
    carga el vector se duplica y se redistribuye todo: O(n log n) cada vez,
    amortizado O(log n) por inserción. Espacio O(n).

    Determinismo: el hash de str es FNV-1a propio (el hash() de Python cambia
    entre ejecuciones), así que el orden de iteración es reproducible.
    """

    CAPACIDAD_INICIAL = 16

    def __init__(self, capacidad_inicial: int = CAPACIDAD_INICIAL) -> None:
        if capacidad_inicial < 1:
            raise ValueError("La capacidad inicial debe ser al menos 1")
        # DECISIÓN: capacidad inicial pequeña (16) y crecimiento por duplicación: las
        # tablas del modelo son chicas (cientos de claves), no se reserva de más.
        self._cubetas = Vector(capacidad_inicial)
        self._tamano = 0

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._tamano

    def obtener(self, clave, por_defecto=None):
        par = self._buscar_par(clave)
        return por_defecto if par is None else par.valor

    def contiene(self, clave) -> bool:
        return self._buscar_par(clave) is not None

    # ------------------------------------------------------------------
    # Modificación
    # ------------------------------------------------------------------

    def poner(self, clave, valor) -> None:
        """Asocia clave con valor; si la clave ya existía, reemplaza el valor."""
        par = self._buscar_par(clave)
        if par is not None:
            par.valor = valor
            return
        # DECISIÓN: se crece al pasar de 3/4 de carga (aritmética entera, sin
        # flotantes). Mantiene las cubetas cortas y la duplicación da costo amortizado.
        if (self._tamano + 1) * 4 > len(self._cubetas) * 3:
            self._crecer()
        self._agregar_par(self._cubetas, _Par(clave, valor))
        self._tamano += 1

    def eliminar(self, clave) -> bool:
        """Quita la clave. Devuelve True si existía."""
        posicion = self._posicion(clave, len(self._cubetas))
        cubeta = self._cubetas.obtener(posicion)
        if cubeta is None:
            return False
        indice = 0
        for par in cubeta:
            if par.clave == clave:
                cubeta.eliminar_en(indice)
                self._tamano -= 1
                return True
            indice += 1
        return False

    # ------------------------------------------------------------------
    # Recorridos (orden por cubeta: reproducible, pero sin significado)
    # ------------------------------------------------------------------

    def __iter__(self):
        """Los pares (clave, valor)."""
        for cubeta in self._cubetas:
            if cubeta is not None:
                for par in cubeta:
                    yield (par.clave, par.valor)

    def claves(self):
        for clave, _ in self:
            yield clave

    def valores(self):
        for _, valor in self:
            yield valor

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(clave) -> int:
        # DECISIÓN: para enteros el hash es el propio valor (los ids de sala ya se
        # reparten bien). El % de Python deja el resultado >= 0 aun con negativos.
        if isinstance(clave, int):
            return clave
        if isinstance(clave, str):
            # DECISIÓN: FNV-1a de 32 bits hecho a mano. hash() de str cambia en cada
            # ejecución (PYTHONHASHSEED) y rompería el determinismo del recorrido.
            resultado = 2166136261
            for caracter in clave:
                resultado = ((resultado ^ ord(caracter)) * 16777619) & 0xFFFFFFFF
            return resultado
        raise TypeError(f"Clave no soportada por TablaHash: {type(clave).__name__}")

    @classmethod
    def _posicion(cls, clave, capacidad: int) -> int:
        return cls._hash(clave) % capacidad

    def _buscar_par(self, clave):
        cubeta = self._cubetas.obtener(self._posicion(clave, len(self._cubetas)))
        if cubeta is None:
            return None
        for par in cubeta:
            if par.clave == clave:
                return par
        return None

    def _agregar_par(self, cubetas: Vector, par: _Par) -> None:
        posicion = self._posicion(par.clave, len(cubetas))
        cubeta = cubetas.obtener(posicion)
        # DECISIÓN: encadenamiento separado (no direccionamiento abierto): eliminar es
        # trivial (sin lápidas) y una colisión no contamina otras cubetas. La cubeta
        # se crea al primer uso para no gastar una lista por cada cubeta vacía.
        if cubeta is None:
            cubeta = ListaEnlazada()
            cubetas.establecer(posicion, cubeta)
        cubeta.agregar_al_final(par)

    def _crecer(self) -> None:
        # DECISIÓN: se reutilizan los mismos _Par (no se copian): solo se recalcula
        # en qué cubeta cae cada uno.
        nuevas = Vector(len(self._cubetas) * 2)
        for cubeta in self._cubetas:
            if cubeta is not None:
                for par in cubeta:
                    self._agregar_par(nuevas, par)
        self._cubetas = nuevas