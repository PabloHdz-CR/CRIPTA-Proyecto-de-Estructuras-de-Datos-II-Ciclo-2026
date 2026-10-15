"""Comando: lo que el jugador pidió, sin interpretar (§6, §10.2).

Vista NUNCA decide qué significa un comando -- eso es trabajo del
Controlador (TraductorComandos, que lo convierte en una Accion y resuelve
objetivos como "Rata gigante #1" -> el enemigo real). Vista solo junta el
verbo y los argumentos tal como el jugador los indicó (tecleados, o --en
VistaArcade-- elegidos con el teclado/mouse) y los empaqueta aquí.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Comando:
    """verbo: una palabra ("mover", "atacar", "recoger", "esperar", "salir"...).
    argumentos: tupla de textos, en el orden en que el Controlador los espera
    para ese verbo (p. ej. ("N",) para mover, ("Rata gigante #1",) para
    atacar). Una tupla (no ListaEnlazada): son pocos y de tamaño fijo por
    verbo, igual que Accion en el modelo."""
    verbo: str
    argumentos: tuple = field(default_factory=tuple)