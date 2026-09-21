from .listaDoble import ListaDoble


class PilaAcotada:
    """Pila con capacidad máxima: al apilar en una pila llena, el elemento MÁS
    ANTIGUO (el del fondo) se descarta y se devuelve.

    Necesita quitar por el fondo y por el tope, por eso se apoya en una
    ListaDoble: el tope es la cabeza y el fondo es la cola, y las cuatro
    operaciones (apilar, desapilar, descartar el fondo, ver el tope) son O(1).
    Con una lista simple, descartar el fondo costaría O(n).

    No admite None: apilar devuelve None para decir "no se descartó nada".
    """

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._elementos = ListaDoble()

    @property
    def capacidad(self):
        return self._capacidad

    def esta_vacia(self):
        return self._elementos.esta_vacia()

    def esta_llena(self):
        return len(self._elementos) == self._capacidad

    def __len__(self):
        return len(self._elementos)

    def apilar(self, dato):
        """Apila 'dato'. Si la pila estaba llena, devuelve el elemento más
        antiguo que se descartó; si no, devuelve None."""
        if dato is None:
            raise ValueError("PilaAcotada no admite None (significa 'no se descartó nada')")
        descartado = None
        if self.esta_llena():
            descartado = self._elementos.eliminar_ultimo()
        self._elementos.agregar_al_inicio(dato)
        return descartado

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
        """Del tope (lo más reciente) hacia el fondo (lo más antiguo)."""
        return iter(self._elementos)