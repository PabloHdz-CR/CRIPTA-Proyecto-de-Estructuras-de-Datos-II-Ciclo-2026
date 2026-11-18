from .nodoHeap import NodoHeap


class ArregloArbol:
    """Arreglo de acceso por posición hecho con un árbol binario COMPLETO de
    nodos, sin list de Python (004-linea-tiempo, research R4).

    Las posiciones se numeran desde 1, por niveles, igual que en HeapBinario:
    la raíz es la 1 y los hijos de la posición p son 2p y 2p + 1. Para llegar
    a la posición p se escribe p en binario, se ignora el primer bit (el de la
    raíz) y cada bit siguiente dice hacia dónde bajar (0 = izquierda,
    1 = derecha). Como el árbol se llena por niveles, la posición i es también
    el i-ésimo elemento agregado: el árbol se usa como un arreglo.

    Costos: obtener(i), agregar_al_final y quitar_ultimo O(log n); len O(1);
    recorrer en orden O(n log n) (cada posición se busca bajando).
    """

    def __init__(self) -> None:
        self._raiz = None
        self._tamano = 0

    def __len__(self) -> int:
        return self._tamano

    def esta_vacio(self) -> bool:
        return self._tamano == 0

    def obtener(self, posicion: int):
        """El dato de la posición (1 = el primero agregado). O(log n)."""
        if posicion < 1 or posicion > self._tamano:
            raise IndexError(f"Posición {posicion} fuera del arreglo de {self._tamano}")
        return self._nodo_en(posicion).dato

    def ultimo(self):
        """El dato de la última posición. O(log n)."""
        return self.obtener(self._tamano)

    def agregar_al_final(self, dato) -> None:
        """Agrega 'dato' en la posición len + 1. O(log n)."""
        posicion = self._tamano + 1
        if posicion == 1:
            self._raiz = NodoHeap(dato)
            self._tamano = 1
            return
        padre = self._nodo_en(posicion // 2)
        nuevo = NodoHeap(dato, padre)
        if posicion % 2 == 0:
            padre.izquierdo = nuevo
        else:
            padre.derecho = nuevo
        self._tamano = posicion

    def quitar_ultimo(self):
        """Saca y devuelve el dato de la última posición. O(log n)."""
        if self._tamano == 0:
            raise IndexError("El arreglo está vacío")
        ultimo = self._nodo_en(self._tamano)
        if self._tamano == 1:
            self._raiz = None
        else:
            padre = ultimo.padre
            if padre.izquierdo is ultimo:
                padre.izquierdo = None
            else:
                padre.derecho = None
            ultimo.padre = None
        self._tamano -= 1
        return ultimo.dato

    def __iter__(self):
        """Recorre los datos en orden de posición (del primero al último)."""
        for posicion in range(1, self._tamano + 1):
            yield self._nodo_en(posicion).dato

    def pasos_hasta(self, posicion: int) -> int:
        """Cuántos nodos se recorren para llegar a 'posición' (para las pruebas
        de costo, FR-023): a lo sumo log2(posición) + 1."""
        pasos = 1
        mascara = 1
        while mascara * 2 <= posicion:
            mascara *= 2
            pasos += 1
        return pasos

    def _nodo_en(self, posicion: int):
        """El nodo de esa posición (1 = raíz), bajando desde la raíz por los
        bits de la posición. O(log n)."""
        nodo = self._raiz
        mascara = 1
        while mascara * 2 <= posicion:
            mascara *= 2          # mascara = bit más alto de la posición
        mascara //= 2             # se salta ese primer bit: es el de la raíz
        while mascara > 0:
            if posicion & mascara:
                nodo = nodo.derecho
            else:
                nodo = nodo.izquierdo
            mascara //= 2
        return nodo
