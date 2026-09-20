from .listaEnlazada import ListaEnlazada


class Cola:
    def __init__(self):
        self._elementos = ListaEnlazada()

    def esta_vacia(self):
        return self._elementos.esta_vacia()

    def __len__(self):
        return len(self._elementos)

    def encolar(self, dato):
        self._elementos.agregar_al_final(dato)

    def desencolar(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._elementos.eliminar_primero()

    def ver_frente(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._elementos.ver_primero()

    def __iter__(self):
        return iter(self._elementos)