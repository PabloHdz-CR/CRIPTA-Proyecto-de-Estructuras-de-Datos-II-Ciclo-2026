from .cola import Cola


class ColaAcotada:
    """Cola con capacidad máxima: al encolar en una cola llena, el elemento MÁS
    ANTIGUO (el del frente) se descarta y se devuelve.

    Sirve para la bitácora en pantalla (§4.8): guarda solo los últimos N
    mensajes, la memoria es constante (nunca hay más de N nodos) y agregar un
    mensaje no desplaza a los demás: encolar y desencolar son O(1).

    No admite None: encolar devuelve None para decir "no se descartó nada".
    """

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._cola = Cola()

    @property
    def capacidad(self):
        return self._capacidad

    def esta_vacia(self):
        return self._cola.esta_vacia()

    def esta_llena(self):
        return len(self._cola) == self._capacidad

    def __len__(self):
        return len(self._cola)

    def encolar(self, dato):
        """Encola 'dato'. Si la cola estaba llena, devuelve el elemento más
        antiguo que se descartó; si no, devuelve None."""
        if dato is None:
            raise ValueError("ColaAcotada no admite None (significa 'no se descartó nada')")
        descartado = None
        if self.esta_llena():
            descartado = self._cola.desencolar()
        self._cola.encolar(dato)
        return descartado

    def desencolar(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._cola.desencolar()

    def ver_frente(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._cola.ver_frente()

    def vaciar(self):
        self._cola = Cola()

    def __iter__(self):
        """Del más antiguo al más reciente."""
        return iter(self._cola)