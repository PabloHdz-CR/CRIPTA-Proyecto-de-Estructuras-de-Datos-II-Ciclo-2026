
from .heapBinario import HeapBinario


class HeapMinimo(HeapBinario):
    """Montículo de mínimo: en la raíz siempre está el elemento MENOR.

    Los elementos se comparan solo con el operador <, así que cualquier clase
    que defina __lt__ sirve (números, texto, o el Evento de la agenda, que
    compara por (tiempo, secuencia)). Si dos elementos nunca son "iguales"
    según <, el orden de salida es totalmente determinista.

    Costos: insertar y extraer en O(log n); ver_minimo en O(1).
    """

    def _antes(self, a, b):
        return a < b

    def ver_minimo(self):
        return self.ver_primero()

    def extraer_minimo(self):
        return self.extraer()