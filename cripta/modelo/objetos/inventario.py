"""Inventario del jugador (§2.7, §4.5)."""
from __future__ import annotations

from ..estructuras.listaDoble import ListaDoble
from ..estructuras.listaEnlazada import ListaEnlazada
from ..ordenamiento import ClaveOrden, ordenar

CRITERIOS_ORDEN = ("peso", "valor", "nombre")


class Inventario:
    """Lista doblemente enlazada con cursor y tope de capacidad.

    Cada objeto ocupa una posición. Con ListaDoble: recorrer en ambos sentidos,
    soltar el objeto elegido y equipar (mover al frente) cuestan O(1) una vez
    hallado el nodo; hallarlo por id es O(n) con n <= inventario_max (pequeño).
    Una 'list' de Python costaría O(n) al soltar en el medio (alternativa a medir).

    'cache' es opcional: si se da (CacheFichas), cada objeto recogido FIJA su
    ficha para que no se desaloje mientras esté en el inventario.
    """

    def __init__(self, capacidad: int, cache=None) -> None:
        self._capacidad = capacidad
        self._cache = cache
        # DECISIÓN: ListaDoble y no list (§4.5): soltar o equipar un nodo ya hallado
        # es O(1); una list costaría O(n) al soltar en el medio. Alternativa a medir.
        self._objetos = ListaDoble()
        self._actual = None               # nodo bajo el cursor, o None

    @property
    def capacidad(self) -> int:
        return self._capacidad

    def __len__(self) -> int:
        return len(self._objetos)

    def __iter__(self):
        return iter(self._objetos)

    def esta_vacio(self) -> bool:
        return self._objetos.esta_vacia()

    def esta_lleno(self) -> bool:
        return len(self._objetos) >= self._capacidad

    # ------------------------------------------------------------------
    # Altas y bajas
    # ------------------------------------------------------------------

    def recoger(self, objeto) -> bool:
        """Agrega al final. Devuelve False (sin cambios) si está lleno."""
        if self.esta_lleno():
            return False
        nodo = self._objetos.agregar_al_final(objeto)
        if self._cache is not None:
            self._cache.fijar(objeto.ficha.id)
        if self._actual is None:
            self._actual = nodo
        return True

    def insertar_en(self, indice: int, objeto) -> None:
        """Reinserta en una posición concreta (lo usa el retroceso). O(indice)."""
        referencia = self._nodo_en(indice)
        if referencia is None:
            self._objetos.agregar_al_final(objeto)
        else:
            self._objetos.insertar_antes_de(referencia, objeto)
        if self._cache is not None:
            self._cache.fijar(objeto.ficha.id)
        if self._actual is None:
            self._actual = self._objetos.primero()

    def quitar(self, objeto) -> int:
        """Saca 'objeto' (soltar o consumir). Devuelve la posición que tenía.
        El cursor pasa al vecino. O(n) para hallarlo, O(1) para quitarlo."""
        nodo = self._buscar_nodo_de(objeto)
        if nodo is None:
            raise ValueError("El objeto no está en el inventario")
        # DECISIÓN: se devuelve la posición para que el Diario pueda reinsertar el
        # objeto exactamente donde estaba (insertar_en).
        indice = self.indice_de(objeto)
        if nodo is self._actual:
            vecino = self._objetos.siguiente_de(nodo)
            self._actual = vecino if vecino is not None else self._objetos.anterior_de(nodo)
        self._objetos.eliminar_nodo(nodo)
        if self._cache is not None:
            self._cache.soltar_referencia(objeto.ficha.id)
        return indice

    def mover_al_frente(self, objeto) -> int:
        """Equipar mueve el objeto al frente. Devuelve su posición anterior. O(1)
        tras hallar el nodo."""
        nodo = self._buscar_nodo_de(objeto)
        if nodo is None:
            raise ValueError("El objeto no está en el inventario")
        indice = self.indice_de(objeto)
        self._objetos.mover_al_inicio(nodo)
        return indice

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------

    def buscar(self, id_objeto: int):
        for objeto in self._objetos:
            if objeto.id_instancia == id_objeto:
                return objeto
        return None

    def indice_de(self, objeto) -> int:
        indice = 0
        for actual in self._objetos:
            if actual is objeto:
                return indice
            indice += 1
        return -1

    def buscar_llave(self, id_llave: str):
        """Primera llave del inventario que abre la salida con ese id."""
        for objeto in self._objetos:
            if objeto.clase == "llave" and objeto.abre_a(id_llave):
                return objeto
        return None

    def primer_pergamino(self):
        for objeto in self._objetos:
            if objeto.clase == "pergamino_retroceso":
                return objeto
        return None

    def cantidad_pergaminos(self) -> int:
        cantidad = 0
        for objeto in self._objetos:
            if objeto.clase == "pergamino_retroceso":
                cantidad += 1
        return cantidad

    # ------------------------------------------------------------------
    # Cursor
    # ------------------------------------------------------------------

    def actual(self):
        return self._actual.dato if self._actual is not None else None

    def siguiente(self):
        if self._actual is not None:
            vecino = self._objetos.siguiente_de(self._actual)
            if vecino is not None:
                self._actual = vecino
        return self.actual()

    def anterior(self):
        if self._actual is not None:
            vecino = self._objetos.anterior_de(self._actual)
            if vecino is not None:
                self._actual = vecino
        return self.actual()

    def enfocar(self, objeto) -> None:
        nodo = self._buscar_nodo_de(objeto)
        if nodo is None:
            raise ValueError("El objeto no está en el inventario")
        self._actual = nodo

    # ------------------------------------------------------------------
    # Vista ordenada (no altera el orden real)
    # ------------------------------------------------------------------

    def vista_ordenada(self, criterio: str) -> ListaEnlazada:
        """Objetos ordenados por peso, valor o nombre, en una lista NUEVA."""
        if criterio not in CRITERIOS_ORDEN:
            raise ValueError(f"Criterio de orden desconocido: {criterio}")
        # DECISIÓN: la vista se arma en una lista NUEVA; el orden real (que importa
        # para el cursor y para 'equipar mueve al frente') nunca se altera.
        claves = ListaEnlazada()
        for objeto in self._objetos:
            if criterio == "peso":
                clave = objeto.ficha.peso
            elif criterio == "valor":
                clave = objeto.ficha.valor
            else:
                clave = objeto.ficha.nombre
            claves.agregar_al_final(ClaveOrden(clave, objeto))
        resultado = ListaEnlazada()
        for envoltorio in ordenar(claves):
            resultado.agregar_al_final(envoltorio.valor)
        return resultado

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _buscar_nodo_de(self, objeto):
        nodo = self._objetos.primero()
        while nodo is not None:
            if nodo.dato is objeto:
                return nodo
            nodo = self._objetos.siguiente_de(nodo)
        return None

    def _nodo_en(self, indice: int):
        nodo = self._objetos.primero()
        for _ in range(indice):
            if nodo is None:
                return None
            nodo = self._objetos.siguiente_de(nodo)
        return nodo