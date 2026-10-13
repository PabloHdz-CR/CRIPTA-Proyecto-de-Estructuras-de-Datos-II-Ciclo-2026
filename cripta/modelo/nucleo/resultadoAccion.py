"""Resultado de aplicar una acción (§2.3, Apéndice B)."""
from __future__ import annotations

from ..estructuras.listaEnlazada import ListaEnlazada


class ResultadoAccion:
    """Aceptada o rechazada. Un rechazo NO consume tiempo ni cambia el estado."""

    def __init__(self, aceptada: bool, motivo: str = None, mensajes=None) -> None:
        self.aceptada = aceptada
        self.motivo = motivo
        self.mensajes = mensajes if mensajes is not None else ListaEnlazada()

    @classmethod
    def aceptada_con(cls, mensajes) -> "ResultadoAccion":
        return cls(True, None, mensajes)

    @classmethod
    def rechazada(cls, motivo: str) -> "ResultadoAccion":
        resultado = cls(False, motivo)
        resultado.mensajes.agregar_al_final(motivo)
        return resultado