"""Servicio de datos de solo lectura para las copias de la línea de tiempo
(004-linea-tiempo, research R5, FR-012)."""
from __future__ import annotations

from ..puertos.errores import ErrorCripta


class ServicioSoloLectura:
    """Lo que Partida le pide al servicio, sin red ni presupuesto.

    Re-simular solo entra a salas en las que la partida real ya entró, así que
    su contenido inicial está en la memoria del servicio real o, después de
    cargar una partida en otro proceso, en el registro de la línea de tiempo
    (que se guarda con ella). Las fichas salen de memoria o disco. Si algo
    falta, la consulta falla con un mensaje claro y nunca usa la red.
    """

    def __init__(self, servicio_real, linea) -> None:
        self._real = servicio_real
        self._linea = linea          # objeto con contenido_registrado(id), o None

    def asegurar_contenido(self, id_sala: int):
        contenido = None
        if self._linea is not None:
            contenido = self._linea.contenido_registrado(id_sala)
        if contenido is None:
            contenido = self._real.contenido_en_memoria(id_sala)
        if contenido is None:
            raise ErrorCripta(
                f"El contenido de la sala {id_sala} no está en memoria; la consulta de "
                "la línea de tiempo no usa la red")
        return contenido

    def precargar(self, id_sala: int) -> None:
        """La copia nunca precarga: no gasta presupuesto (FR-012)."""

    def resolver_fichas(self, ids):
        return self._real.resolver_fichas_sin_red(ids)

    def datos_cripta(self):
        return self._real.datos_cripta()

    def esqueleto(self):
        return self._real.esqueleto()
