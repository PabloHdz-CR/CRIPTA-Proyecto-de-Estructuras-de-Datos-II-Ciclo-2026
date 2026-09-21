from .cola import Cola
from .nodoHeap import NodoHeap


class HeapBinario:
    """Montículo (heap) binario hecho con nodos enlazados, sin arreglos.

    Es un árbol binario COMPLETO: todos los niveles están llenos salvo quizá el
    último, que se llena de izquierda a derecha. Las posiciones se numeran desde
    1, por niveles: la raíz es la 1 y los hijos de la posición p son 2p y 2p + 1.

    Cómo se llega a la posición p sin recorrer todo el árbol: se escribe p en
    binario, se ignora el primer bit (el de la raíz) y cada bit siguiente dice
    hacia dónde bajar (0 = izquierda, 1 = derecha). Por ejemplo, 5 = 101: se
    ignora el 1, luego 0 (izquierda) y 1 (derecha). Cuesta O(log n) pasos.

    Esta clase no sabe si es de mínimo o de máximo: eso lo decide _antes(),
    que las subclases sobrescriben. No es estable: dos elementos que no se
    puedan distinguir con < pueden salir en cualquier orden.
    """

    def __init__(self):
        self._raiz = None
        self._tamano = 0

    def _antes(self, a, b):
        """True si 'a' debe estar más cerca de la raíz que 'b'."""
        raise NotImplementedError("Cada tipo de montículo define su criterio")

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def esta_vacio(self):
        return self._tamano == 0

    def __len__(self):
        return self._tamano

    def ver_primero(self):
        """Devuelve el elemento de la raíz sin sacarlo. O(1)."""
        if self._raiz is None:
            raise IndexError("El montículo está vacío")
        return self._raiz.dato

    def vaciar(self):
        self._raiz = None
        self._tamano = 0

    # ------------------------------------------------------------------
    # Insertar y extraer: O(log n)
    # ------------------------------------------------------------------

    def insertar(self, dato):
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
        self._subir(nuevo)

    def extraer(self):
        """Saca y devuelve el elemento de la raíz."""
        if self._raiz is None:
            raise IndexError("El montículo está vacío")
        primero = self._raiz.dato
        if self._tamano == 1:
            self._raiz = None
            self._tamano = 0
            return primero
        # El último nodo (posición = tamaño) pasa su dato a la raíz y se elimina.
        ultimo = self._nodo_en(self._tamano)
        self._raiz.dato = ultimo.dato
        padre = ultimo.padre
        if padre.izquierdo is ultimo:
            padre.izquierdo = None
        else:
            padre.derecho = None
        ultimo.padre = None
        self._tamano -= 1
        self._bajar(self._raiz)
        return primero

    # ------------------------------------------------------------------
    # Recorrido y verificación
    # ------------------------------------------------------------------

    def __iter__(self):
        """Recorre todos los elementos por niveles, SIN ningún orden útil.

        Sirve para guardar el estado (por ejemplo, la agenda de eventos
        pendientes) o para contar. O(n).
        """
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

    def es_consistente(self):
        """Comprueba que el árbol sea completo, que cada hijo apunte a su padre,
        que ningún hijo deba ir antes que su padre y que el tamaño coincida.
        Está pensado para las pruebas: cuesta O(n)."""
        if self._raiz is None:
            return self._tamano == 0
        if self._raiz.padre is not None:
            return False
        contados = 0
        hubo_hueco = False   # tras el primer hijo ausente, ya no puede haber más
        pendientes = Cola()
        pendientes.encolar(self._raiz)
        while not pendientes.esta_vacia():
            nodo = pendientes.desencolar()
            contados += 1
            for hijo in (nodo.izquierdo, nodo.derecho):
                if hijo is None:
                    hubo_hueco = True
                    continue
                if hubo_hueco:
                    return False                      # el árbol no es completo
                if hijo.padre is not nodo:
                    return False                      # puntero al padre mal puesto
                if self._antes(hijo.dato, nodo.dato):
                    return False                      # un hijo iría antes que su padre
                pendientes.encolar(hijo)
        return contados == self._tamano

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _nodo_en(self, posicion):
        """Devuelve el nodo de esa posición (1 = raíz) bajando desde la raíz."""
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

    def _subir(self, nodo):
        """Sube el dato de 'nodo' mientras deba ir antes que el de su padre."""
        while nodo.padre is not None and self._antes(nodo.dato, nodo.padre.dato):
            self._intercambiar(nodo, nodo.padre)
            nodo = nodo.padre

    def _bajar(self, nodo):
        """Baja el dato de 'nodo' mientras algún hijo deba ir antes que él."""
        while True:
            elegido = nodo
            if nodo.izquierdo is not None and self._antes(nodo.izquierdo.dato, elegido.dato):
                elegido = nodo.izquierdo
            if nodo.derecho is not None and self._antes(nodo.derecho.dato, elegido.dato):
                elegido = nodo.derecho
            if elegido is nodo:
                return
            self._intercambiar(nodo, elegido)
            nodo = elegido

    def _intercambiar(self, a, b):
        """Intercambia los DATOS de dos nodos; los nodos y sus punteros no se mueven."""
        a.dato, b.dato = b.dato, a.dato