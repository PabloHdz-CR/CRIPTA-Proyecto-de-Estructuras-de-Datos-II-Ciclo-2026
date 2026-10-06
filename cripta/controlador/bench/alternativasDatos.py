"""Alternativa descartada para la caché de fichas (§4.4), SOLO para medir.

El juego NO usa nada de este archivo (usa CacheFichas, con desalojo LRU).
Existe para poder medir directamente lo que se descartó (D31), con las
mismas estructuras propias que el resto del programa.
"""
from ...modelo.estructuras.listaDoble import ListaDoble

CLAVES_CACHE = ("lru", "fifo")


class _EntradaCache:
    def __init__(self, id_ficha, ficha):
        self.id_ficha = id_ficha
        self.ficha = ficha
        self.fijaciones = 0

    def en_uso(self):
        return self.fijaciones > 0


class CacheFichasFIFO:
    """Caché con desalojo FIFO: se descarta la entrada que entró primero, sin
    importar si se ha vuelto a usar. Misma interfaz pública que CacheFichas
    (D31), para poder intercambiarlas en las mediciones sin cambiar el
    código que las ejerce.

    La diferencia con CacheFichas está en una sola línea: obtener() aquí NO
    mueve la entrada al frente. El frente siempre es "lo insertado más
    recientemente"; el fondo, "lo insertado hace más tiempo", y eso nunca
    cambia con el uso.
    """

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._entradas = ListaDoble()
        self.aciertos = 0
        self.fallos = 0

    @property
    def capacidad(self):
        return self._capacidad

    def __len__(self):
        return len(self._entradas)

    def obtener(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        return nodo.dato.ficha          # SIN mover_al_inicio: esa es la diferencia con LRU

    def contiene(self, id_ficha):
        return self._buscar_nodo(id_ficha) is not None

    def ver(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        return nodo.dato.ficha if nodo is not None else None

    def insertar(self, id_ficha, ficha):
        existente = self._buscar_nodo(id_ficha)
        if existente is not None:
            existente.dato.ficha = ficha
            return None             # FIFO: reemplazar NO renueva su posición
        desalojado = None
        if len(self._entradas) >= self._capacidad:
            desalojado = self._desalojar_uno()
        self._entradas.agregar_al_inicio(_EntradaCache(id_ficha, ficha))
        return desalojado

    def _desalojar_uno(self):
        nodo = self._entradas.ultimo()
        while nodo is not None:
            if not nodo.dato.en_uso():
                id_desalojado = nodo.dato.id_ficha
                self._entradas.eliminar_nodo(nodo)
                return id_desalojado
            nodo = self._entradas.anterior_de(nodo)
        return None

    def fijar(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            raise ValueError(f"'{id_ficha}' no está en la caché: no se puede fijar")
        nodo.dato.fijaciones += 1

    def soltar_referencia(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            raise ValueError(f"'{id_ficha}' no está en la caché: no se puede soltar")
        if nodo.dato.fijaciones == 0:
            raise ValueError(f"'{id_ficha}' no tiene ninguna referencia fijada")
        nodo.dato.fijaciones -= 1

    def esta_en_uso(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        return nodo is not None and nodo.dato.en_uso()

    def _buscar_nodo(self, id_ficha):
        nodo = self._entradas.primero()
        while nodo is not None:
            if nodo.dato.id_ficha == id_ficha:
                return nodo
            nodo = self._entradas.siguiente_de(nodo)
        return None


def nombre_cache(clave):
    if clave == "lru":
        return "LRU (decisión)"
    if clave == "fifo":
        return "FIFO"
    raise ValueError(f"Clave de caché desconocida: {clave}")


def crear_cache(clave, capacidad):
    if clave == "lru":
        from ...modelo.datos.cacheFichas import CacheFichas
        return CacheFichas(capacidad)
    if clave == "fifo":
        return CacheFichasFIFO(capacidad)
    raise ValueError(f"Clave de caché desconocida: {clave}")