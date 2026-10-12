"""Evento: unidad de la agenda (§2.3)."""
from __future__ import annotations

import copy


class Evento:
    """Algo que ocurrirá en un instante del reloj virtual.

    Se ordena por (tiempo, secuencia): la secuencia la asigna la Agenda al
    programarlo y desempata de forma determinista. Cancelar un evento solo
    levanta la bandera 'cancelado' (cancelación perezosa, O(1)); la Agenda lo
    descarta cuando le toca salir.
    """

    def __init__(self, tiempo: int, duenio=None) -> None:
        self.tiempo = tiempo
        self.secuencia = -1
        self.duenio = duenio
        self.cancelado = False
        # DECISIÓN: 'en_agenda' existe para que el retroceso sepa si un evento
        # cancelado ya fue purgado del montículo y hay que reinsertarlo.
        self.en_agenda = False     # True mientras está dentro del montículo

    def __lt__(self, otro: "Evento") -> bool:
        # DECISIÓN: el orden (tiempo, secuencia) vive en el propio evento: HeapMinimo
        # solo necesita '<' y la agenda no depende de los tipos de evento. La
        # secuencia nunca se repite, así que no hay empates: orden determinista.
        if self.tiempo != otro.tiempo:
            return self.tiempo < otro.tiempo
        return self.secuencia < otro.secuencia

    def ejecutar(self, partida) -> None:
        raise NotImplementedError("Cada evento define qué hace al ejecutarse")

    def duplicar(self, nuevo_tiempo: int) -> "Evento":
        """Copia sin programar, con otro tiempo, para reprogramar."""
        # DECISIÓN: copy.copy y no un constructor por clase: cualquier evento nuevo
        # se puede reprogramar sin escribir código extra.
        copia = copy.copy(self)
        copia.tiempo = nuevo_tiempo
        copia.secuencia = -1
        copia.cancelado = False
        copia.en_agenda = False
        return copia