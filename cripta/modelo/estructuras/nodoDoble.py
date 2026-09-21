class NodoDoble:
    """Nodo de una lista doblemente enlazada.

    Además de guardar el dato y los punteros a sus dos vecinos, un NodoDoble
    hace de "posición" dentro de su lista: quien lo recibe (por ejemplo, el
    inventario, para recordar qué objeto está viendo) puede leer su dato, pero
    solo la ListaDoble puede tocar los punteros.

    Cada nodo recuerda a qué lista pertenece (_lista). Cuando lo eliminan, o
    cuando la lista se vacía, _lista vuelve a ser None y la lista deja de
    aceptarlo: así no se puede usar un nodo viejo ni el de otra lista.
    """

    def __init__(self, dato, lista):
        self._dato = dato
        self._anterior = None
        self._siguiente = None
        self._lista = lista

    @property
    def dato(self):
        """El dato guardado. Solo lectura: para cambiarlo, elimina y vuelve a agregar."""
        return self._dato

    def __repr__(self):
        return f"NodoDoble({self._dato!r})"