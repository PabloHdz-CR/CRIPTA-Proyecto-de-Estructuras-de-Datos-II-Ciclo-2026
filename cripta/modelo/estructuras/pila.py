from .listaEnlazada import ListaEnlazada


class Pila:
    """Pila LIFO: el último en entrar es el primero en salir.

    Se apoya en una ListaEnlazada: se apila y se desapila por la cabeza, ambas
    operaciones en O(1). Sirve, por ejemplo, para deshacer los cambios de una
    acción en orden inverso al que se hicieron.
    """

    def __init__(self):
        self._elementos = ListaEnlazada()

    def esta_vacia(self):
        return self._elementos.esta_vacia()

    def __len__(self):
        return len(self._elementos)

    def apilar(self, dato):
        self._elementos.agregar_al_inicio(dato)

    def desapilar(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos.eliminar_primero()

    def ver_tope(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos.ver_primero()

    def vaciar(self):
        self._elementos.vaciar()

    def __iter__(self):
        """Del tope hacia el fondo."""
        return iter(self._elementos)