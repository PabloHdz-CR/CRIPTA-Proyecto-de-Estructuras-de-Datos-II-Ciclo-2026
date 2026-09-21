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
        texto = ""
        primero = True
        for dato in self:
            if not primero:
                texto += ", "
            texto += repr(dato)
            primero = False
        return "ListaEnlazada([" + texto + "])"

    def establecer(self, indice, dato):
        """Reemplaza el dato de la posición 'indice'. Cuesta O(indice)."""
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice}")
        actual = self._cabeza
        for _ in range(indice):
            actual = actual.siguiente
        actual.dato = dato

    def eliminar_en(self, indice):
        """Elimina y devuelve el dato de la posición 'indice'. Cuesta O(indice)."""
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice}")
        if indice == 0:
            return self.eliminar_primero()
        anterior = self._cabeza
        for _ in range(indice - 1):
            anterior = anterior.siguiente
        nodo = anterior.siguiente
        anterior.siguiente = nodo.siguiente
        if nodo is self._cola:
            self._cola = anterior
        self._tamano -= 1
        return nodo.dato

    def eliminar_ultimo(self):
        """Elimina y devuelve el último dato.

        En una lista SIMPLE cuesta O(n): hay que llegar hasta el penúltimo nodo
        para poder soltar el último (no hay puntero hacia atrás).
        """
        if self._tamano == 0:
            raise IndexError("La lista está vacía")
        return self.eliminar_en(self._tamano - 1)