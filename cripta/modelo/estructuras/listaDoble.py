from .nodoDoble import NodoDoble


class ListaDoble:
    """Lista doblemente enlazada con referencia a la cabeza y a la cola.

    Cada nodo conoce a su vecino anterior y a su siguiente, por eso:
      - se recorre hacia adelante y hacia atrás,
      - se agrega y se elimina en cualquiera de los dos extremos en O(1),
      - dado un NodoDoble, se elimina, se inserta antes o después de él y se
        mueve al inicio en O(1), sin importar en qué posición esté.

    Los métodos que devuelven un NodoDoble lo entregan como "posición". Los que
    reciben uno comprueban que pertenezca a esta lista y que no haya sido
    eliminado; si no, lanzan ValueError.

    Los métodos de navegación (primero, ultimo, siguiente_de, anterior_de)
    devuelven None cuando no hay nodo, para poder recorrer con un while.
    No modifiques la lista mientras la recorres con for: el resultado no está
    definido (con nodos y while sí puedes, tomando el siguiente ANTES de eliminar).
    """

    def __init__(self):
        self._cabeza = None
        self._cola = None
        self._tamano = 0

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def esta_vacia(self):
        return self._tamano == 0

    def __len__(self):
        return self._tamano

    def ver_primero(self):
        if self._cabeza is None:
            raise IndexError("La lista está vacía")
        return self._cabeza._dato

    def ver_ultimo(self):
        if self._cola is None:
            raise IndexError("La lista está vacía")
        return self._cola._dato

    def obtener(self, indice):
        """Devuelve el dato de la posición 'indice', empezando por el extremo más
        cercano. Cuesta O(min(indice, tamaño - indice))."""
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice}")
        if indice <= self._tamano // 2:
            nodo = self._cabeza
            for _ in range(indice):
                nodo = nodo._siguiente
        else:
            nodo = self._cola
            for _ in range(self._tamano - 1 - indice):
                nodo = nodo._anterior
        return nodo._dato

    def buscar(self, dato):
        """Devuelve el primer nodo cuyo dato sea igual a 'dato', o None. O(n)."""
        nodo = self._cabeza
        while nodo is not None:
            if nodo._dato == dato:
                return nodo
            nodo = nodo._siguiente
        return None

    def contiene(self, dato):
        return self.buscar(dato) is not None

    # ------------------------------------------------------------------
    # Navegación por nodos
    # ------------------------------------------------------------------

    def primero(self):
        """El primer nodo, o None si la lista está vacía."""
        return self._cabeza

    def ultimo(self):
        """El último nodo, o None si la lista está vacía."""
        return self._cola

    def siguiente_de(self, nodo):
        """El nodo que sigue a 'nodo', o None si es el último. O(1)."""
        self._exigir_propio(nodo)
        return nodo._siguiente

    def anterior_de(self, nodo):
        """El nodo anterior a 'nodo', o None si es el primero. O(1)."""
        self._exigir_propio(nodo)
        return nodo._anterior

    # ------------------------------------------------------------------
    # Agregar: todas devuelven el nodo nuevo. O(1)
    # ------------------------------------------------------------------

    def agregar_al_inicio(self, dato):
        nuevo = NodoDoble(dato, self)
        nuevo._siguiente = self._cabeza
        if self._cabeza is None:
            self._cola = nuevo
        else:
            self._cabeza._anterior = nuevo
        self._cabeza = nuevo
        self._tamano += 1
        return nuevo

    def agregar_al_final(self, dato):
        nuevo = NodoDoble(dato, self)
        nuevo._anterior = self._cola
        if self._cola is None:
            self._cabeza = nuevo
        else:
            self._cola._siguiente = nuevo
        self._cola = nuevo
        self._tamano += 1
        return nuevo

    def insertar_despues_de(self, nodo, dato):
        self._exigir_propio(nodo)
        if nodo is self._cola:
            return self.agregar_al_final(dato)
        nuevo = NodoDoble(dato, self)
        nuevo._anterior = nodo
        nuevo._siguiente = nodo._siguiente
        nodo._siguiente._anterior = nuevo
        nodo._siguiente = nuevo
        self._tamano += 1
        return nuevo

    def insertar_antes_de(self, nodo, dato):
        self._exigir_propio(nodo)
        if nodo is self._cabeza:
            return self.agregar_al_inicio(dato)
        return self.insertar_despues_de(nodo._anterior, dato)

    # ------------------------------------------------------------------
    # Eliminar y mover: O(1)
    # ------------------------------------------------------------------

    def eliminar_nodo(self, nodo):
        """Elimina 'nodo' y devuelve su dato. El nodo deja de ser válido."""
        self._exigir_propio(nodo)
        self._desenlazar(nodo)
        nodo._lista = None
        return nodo._dato

    def eliminar_primero(self):
        if self._cabeza is None:
            raise IndexError("La lista está vacía")
        return self.eliminar_nodo(self._cabeza)

    def eliminar_ultimo(self):
        if self._cola is None:
            raise IndexError("La lista está vacía")
        return self.eliminar_nodo(self._cola)

    def mover_al_inicio(self, nodo):
        """Lleva 'nodo' al principio de la lista. El MISMO nodo sigue siendo
        válido, así quien lo guardó como posición no pierde su lugar."""
        self._exigir_propio(nodo)
        if nodo is self._cabeza:
            return
        self._desenlazar(nodo)
        nodo._siguiente = self._cabeza
        self._cabeza._anterior = nodo
        self._cabeza = nodo
        self._tamano += 1

    def vaciar(self):
        """Elimina todo. Cada nodo se invalida, así que ninguna posición vieja
        sirve después. Cuesta O(n)."""
        nodo = self._cabeza
        while nodo is not None:
            siguiente = nodo._siguiente
            nodo._lista = None
            nodo._anterior = None
            nodo._siguiente = None
            nodo = siguiente
        self._cabeza = None
        self._cola = None
        self._tamano = 0

    # ------------------------------------------------------------------
    # Recorridos
    # ------------------------------------------------------------------

    def __iter__(self):
        """Los datos, del primero al último."""
        nodo = self._cabeza
        while nodo is not None:
            yield nodo._dato
            nodo = nodo._siguiente

    def recorrer_al_reves(self):
        """Los datos, del último al primero."""
        nodo = self._cola
        while nodo is not None:
            yield nodo._dato
            nodo = nodo._anterior

    def __repr__(self):
        texto = ""
        primero = True
        for dato in self:
            if not primero:
                texto += ", "
            texto += repr(dato)
            primero = False
        return "ListaDoble([" + texto + "])"

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def es_consistente(self):
        """Comprueba que los punteros hacia adelante y hacia atrás coincidan, que
        cada nodo pertenezca a esta lista y que el tamaño sea el correcto.
        Está pensado para las pruebas: cuesta O(n)."""
        contados = 0
        anterior = None
        nodo = self._cabeza
        while nodo is not None:
            if nodo._lista is not self or nodo._anterior is not anterior:
                return False
            anterior = nodo
            nodo = nodo._siguiente
            contados += 1
            if contados > self._tamano:
                return False                  # hay un ciclo o el tamaño está mal
        return anterior is self._cola and contados == self._tamano

    def _exigir_propio(self, nodo):
        if not isinstance(nodo, NodoDoble) or nodo._lista is not self:
            raise ValueError("El nodo no pertenece a esta lista (o ya fue eliminado)")

    def _desenlazar(self, nodo):
        """Saca 'nodo' de la cadena: los vecinos pasan a apuntarse entre sí y se
        actualizan la cabeza y la cola. No invalida el nodo."""
        anterior = nodo._anterior
        siguiente = nodo._siguiente
        if anterior is None:
            self._cabeza = siguiente
        else:
            anterior._siguiente = siguiente
        if siguiente is None:
            self._cola = anterior
        else:
            siguiente._anterior = anterior
        nodo._anterior = None
        nodo._siguiente = None
        self._tamano -= 1