"""Agenda de eventos (§4.1): cola de prioridad por (tiempo, secuencia)."""
from __future__ import annotations

from ..estructuras.heapMinimo import HeapMinimo


class Agenda:
    """Montículo mínimo de nodos enlazados con cancelación perezosa.

    Costos (n = eventos pendientes): programar y extraer_siguiente O(log n);
    ver_siguiente O(1) amortizado; cancelar O(1) (solo marca). Obtener el
    siguiente NUNCA examina todos los pendientes. Espacio O(n): los eventos
    cancelados ocupan lugar hasta que les toca salir (límite conocido).
    """

    def __init__(self) -> None:
        # DECISIÓN: heap binario propio y no una lista ordenada: extraer el mínimo es
        # O(log n) en vez de pagar O(n) al insertar. Hipótesis de §11 a medir en --bench.
        self._monticulo = HeapMinimo()
        self._secuencia = 0

    @property
    def secuencia(self) -> int:
        """Próxima secuencia a asignar. Se guarda y restaura al retroceder."""
        return self._secuencia

    @secuencia.setter
    def secuencia(self, valor: int) -> None:
        self._secuencia = valor

    def __len__(self) -> int:
        """Eventos dentro del montículo, incluidos los cancelados sin purgar."""
        return len(self._monticulo)

    def programar(self, evento) -> None:
        evento.secuencia = self._secuencia
        self._secuencia += 1
        self._insertar(evento)

    def reinsertar(self, evento) -> None:
        """Devuelve a la agenda un evento con su (tiempo, secuencia) original.
        Lo usa el retroceso. No toca el contador de secuencia."""
        self._insertar(evento)

    def ver_siguiente(self):
        """El próximo evento NO cancelado (sin sacarlo), o None."""
        while not self._monticulo.esta_vacio():
            primero = self._monticulo.ver_minimo()
            if not primero.cancelado:
                return primero
            # DECISIÓN: la purga ocurre aquí, al consultar, y no en cancelar(): el costo
            # solo se paga si el evento cancelado llega a la cima del montículo.
            self._monticulo.extraer_minimo().en_agenda = False
        return None

    def extraer_siguiente(self):
        """Saca y devuelve el próximo evento no cancelado, o None."""
        if self.ver_siguiente() is None:
            return None
        evento = self._monticulo.extraer_minimo()
        evento.en_agenda = False
        return evento

    def cancelar(self, evento) -> None:
        # DECISIÓN: cancelación perezosa. Sacar un nodo del medio del heap es caro y
        # delicado; marcar es O(1) y el evento se descarta cuando le toca salir.
        evento.cancelado = True

    def reactivar(self, evento) -> None:
        """Deshace cancelar(); si el evento ya fue purgado, lo reinserta."""
        evento.cancelado = False
        if not evento.en_agenda:
            self._insertar(evento)

    def reprogramar(self, evento, nuevo_tiempo: int):
        """Cancela 'evento' y programa una copia con otro tiempo y secuencia
        nueva. Devuelve la copia (quien guardaba el evento debe actualizarla)."""
        # DECISIÓN: nunca se cambia el tiempo de un evento que está DENTRO del heap
        # (rompería el orden): se cancela y se programa una copia con secuencia nueva,
        # que es justo lo que exige §2.3 al cambiar la velocidad.
        self.cancelar(evento)
        nuevo = evento.duplicar(nuevo_tiempo)
        self.programar(nuevo)
        return nuevo

    def _insertar(self, evento) -> None:
        evento.en_agenda = True
        self._monticulo.insertar(evento)