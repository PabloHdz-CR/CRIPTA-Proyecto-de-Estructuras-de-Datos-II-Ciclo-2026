class NodoHeap:
    """Nodo de un árbol binario: dato, hijo izquierdo, hijo derecho y padre.

    A diferencia de Nodo (lista enlazada), este tiene tres punteros. El puntero
    al padre permite subir en el montículo sin volver a bajar desde la raíz.
    """

    def __init__(self, dato, padre=None):
        self.dato = dato
        self.izquierdo = None
        self.derecho = None
        self.padre = padre