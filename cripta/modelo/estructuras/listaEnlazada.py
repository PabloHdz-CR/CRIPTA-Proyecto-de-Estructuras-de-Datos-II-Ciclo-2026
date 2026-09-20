from .nodo import Nodo


class ListaEnlazada:

    def __init__(self):
        self._cabeza = None
        self._cola = None
        self._tamano = 0

    def esta_vacia(self):
        return self._tamano == 0

    def __len__(self):
        return self._tamano

    def agregar_al_inicio(self, dato):
        self._cabeza = Nodo(dato, self._cabeza)
        if self._cola is None:
            self._cola = self._cabeza
        self._tamano += 1

    def agregar_al_final(self, dato):
        nuevo = Nodo(dato)
        if self._cola is None:
            self._cabeza = nuevo
        else:
            self._cola.siguiente = nuevo
        self._cola = nuevo
        self._tamano += 1

    def agregar_todos(self, secuencia):
        for dato in secuencia:
            self.agregar_al_final(dato)

    def ver_primero(self):
        if self._cabeza is None:
            raise IndexError("La lista está vacía")
        return self._cabeza.dato

    def eliminar_primero(self):
        if self._cabeza is None:
            raise IndexError("La lista está vacía")
        nodo = self._cabeza
        self._cabeza = nodo.siguiente
        if self._cabeza is None:
            self._cola = None
        self._tamano -= 1
        return nodo.dato

    def obtener(self, indice):
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice}")
        actual = self._cabeza
        for _ in range(indice):
            actual = actual.siguiente
        return actual.dato

    def contiene(self, dato):
        actual = self._cabeza
        while actual is not None:
            if actual.dato == dato:
                return True
            actual = actual.siguiente
        return False

    def vaciar(self):
        self._cabeza = None
        self._cola = None
        self._tamano = 0

    def __iter__(self):
        actual = self._cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __repr__(self):
        textos = []
        for dato in self:
            textos.append(repr(dato))
        return "ListaEnlazada([" + ", ".join(textos) + "])"