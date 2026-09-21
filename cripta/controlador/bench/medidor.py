import gc
import time


class Medicion:
    """Resultado de medir un escenario varias veces (tiempos en segundos)."""

    def __init__(self, minimo, promedio, maximo, repeticiones):
        self.minimo = minimo
        self.promedio = promedio
        self.maximo = maximo
        self.repeticiones = repeticiones


class Medidor:
    """Mide cuánto tarda un escenario, repitiéndolo varias veces.

    Un escenario es un objeto con dos métodos:
        preparar(n)   arma el estado inicial (NO se cronometra)
        ejecutar()    hace el trabajo a medir (SÍ se cronometra)

    Cada repetición empieza con preparar(n), así todas parten del mismo estado.
    El dato más fiable es el MÍNIMO: los demás tiempos incluyen ruido del
    sistema (otros programas, el planificador). El recolector de basura se
    desactiva mientras se cronometra para que no meta pausas al azar.
    """

    def __init__(self, repeticiones=5):
        if repeticiones < 1:
            raise ValueError("Se necesita al menos una repetición")
        self._repeticiones = repeticiones

    def medir(self, escenario, n):
        minimo = None
        maximo = None
        suma = 0.0
        for _ in range(self._repeticiones):
            escenario.preparar(n)
            gc.collect()
            gc.disable()
            try:
                inicio = time.perf_counter()
                escenario.ejecutar()
                fin = time.perf_counter()
            finally:
                gc.enable()
            tiempo = fin - inicio
            suma += tiempo
            if minimo is None or tiempo < minimo:
                minimo = tiempo
            if maximo is None or tiempo > maximo:
                maximo = tiempo
        return Medicion(minimo, suma / self._repeticiones, maximo, self._repeticiones)