import threading

from ..modelo.puertos.errores import PresupuestoAgotado


class ContadorSolicitudes:
    """Lleva la cuenta de las solicitudes HTTP frente al presupuesto.

    Lo usa ClienteHttp: antes de cada intento real (incluidos los reintentos
    por HTTP 429) llama a registrar_intento(). Si el presupuesto ya se conoce
    y está agotado, se lanza PresupuestoAgotado SIN enviar nada.

    Es seguro entre hilos: el hilo de FuenteAsincrona escribe y el hilo del
    juego lee. Toda operación usa el mismo cerrojo.

    Ojo: el Lock de threading NO es reentrante. Un método que ya tiene el
    cerrojo no puede llamar a otro método que también lo pida (se
    bloquearía para siempre). Por eso 'restantes' calcula directamente.
    """

    def __init__(self):
        self._cerrojo = threading.Lock()
        self._usadas = 0
        self._presupuesto = None  # None = todavía no se conoce

    def registrar_intento(self, operacion):
        """Cuenta un intento de solicitud, o lanza PresupuestoAgotado.

        Comprobar el margen y sumar ocurren dentro del mismo cerrojo, así dos
        hilos no pueden gastar la última solicitud a la vez. Si se lanza la
        excepción, NO se suma: la solicitud no se envía.
        """
        with self._cerrojo:
            if self._presupuesto is not None and self._usadas >= self._presupuesto:
                raise PresupuestoAgotado(operacion, self._usadas, self._presupuesto)
            self._usadas += 1

    def establecer_presupuesto(self, presupuesto):
        """Guarda el presupuesto_solicitudes de la cripta actual."""
        if presupuesto < 0:
            raise ValueError("El presupuesto no puede ser negativo")
        with self._cerrojo:
            self._presupuesto = presupuesto

    def reiniciar(self):
        """Empieza una partida nueva: cuenta en 0 y presupuesto desconocido."""
        with self._cerrojo:
            self._usadas = 0
            self._presupuesto = None

    def solicitudes_realizadas(self):
        with self._cerrojo:
            return self._usadas

    def presupuesto(self):
        """Devuelve el presupuesto, o None si todavía no se conoce."""
        with self._cerrojo:
            return self._presupuesto

    def restantes(self):
        """Solicitudes que quedan, o None si el presupuesto no se conoce."""
        with self._cerrojo:
            if self._presupuesto is None:
                return None
            faltan = self._presupuesto - self._usadas
            if faltan < 0:
                return 0
            return faltan