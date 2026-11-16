"""ViajeIrA: un viaje «ir a» en curso (002-niebla-guerra, FR-018, FR-023 a
FR-025, FR-028, FR-029; research R6).

No es estado del juego: no se guarda, no se revierte y no está en el log
(el log tiene los movimientos individuales, FR-026). Lo guarda el
Controlador mientras dura el viaje y lo consulta antes de cada paso.
"""
from __future__ import annotations

from typing import Optional

# Motivos de detención (FR-025), con el texto que muestra la interfaz.
LLEGADA = "llegada"
ENEMIGOS = "enemigos en la sala"
DANO = "daño recibido"
SIN_RUTA = "sin ruta conocida"
FIN = "partida terminada"
PERGAMINO = "pergamino de retroceso"
INTERRUMPIDO = "interrumpido"

# Rechazos de la orden (FR-018). El mismo texto para una sala desconocida,
# avistada o inexistente: no revela si la sala existe.
RECHAZO_NO_EXPLORADA = "Esa sala no está explorada."
RECHAZO_SALA_ACTUAL = "Ya estás en esa sala."
RECHAZO_SIN_RUTA = "No hay ruta conocida hasta esa sala."


class ViajeIrA:
    """Destino, pasos dados y motivo de detención (None mientras sigue)."""

    def __init__(self, destino) -> None:
        self._destino = destino
        self._pasos = 0
        self._motivo: Optional[str] = None

    @property
    def destino(self):
        """La Sala de destino (explorada al dar la orden)."""
        return self._destino

    @property
    def pasos(self) -> int:
        return self._pasos

    @property
    def motivo(self) -> Optional[str]:
        return self._motivo

    @property
    def en_curso(self) -> bool:
        return self._motivo is None

    def detener(self, motivo: str) -> None:
        """Termina el viaje con ese motivo (el primero que ocurre gana)."""
        if self._motivo is None:
            self._motivo = motivo

    def evaluar(self, resultado, partida) -> None:
        """Después de un paso aplicado (FR-024): ¿terminó la partida, entró a
        una sala con enemigos, recibió daño o llegó? En ese orden, porque un
        paso que mata al jugador o gana la partida termina todo, y uno que
        entra al destino con enemigos o con daño se detiene por eso. O(1)."""
        self._pasos += 1
        if partida.terminada():
            self.detener(FIN)
        elif resultado.entro_con_enemigos:
            self.detener(ENEMIGOS)
        elif resultado.dano_recibido:
            self.detener(DANO)
        elif partida.jugador.sala == self._destino.id:
            self.detener(LLEGADA)
