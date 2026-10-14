import threading

from ..modelo.puertos.errores import PresupuestoAgotado


class ContadorSolicitudes:

    def __init__(self):
        self._cerrojo = threading.Lock()
        self._usadas = 0
        self._presupuesto = None

    def registrar_intento(self, operacion):
        with self._cerrojo:
            if self._presupuesto is not None and self._usadas >= self._presupuesto:
                raise PresupuestoAgotado(operacion, self._usadas, self._presupuesto)
            self._usadas += 1

    def establecer_presupuesto(self, presupuesto):
        if presupuesto < 0:
            raise ValueError("El presupuesto no puede ser negativo")
        with self._cerrojo:
            self._presupuesto = presupuesto

    def reiniciar(self):
        with self._cerrojo:
            self._usadas = 0
            self._presupuesto = None

    def solicitudes_realizadas(self):
        with self._cerrojo:
            return self._usadas

    def presupuesto(self):
        with self._cerrojo:
            return self._presupuesto

    def restantes(self):
        with self._cerrojo:
            if self._presupuesto is None:
                return None
            faltan = self._presupuesto - self._usadas
            if faltan < 0:
                return 0
            return faltan