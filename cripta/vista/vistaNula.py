"""VistaNula: implementación vacía de VistaJuego (§6).

La necesitan --replay y --bench: corren la partida sin que nadie la mire, así
que no tiene sentido dibujar nada ni esperar teclas. pedir_comando() siempre
devuelve None (nunca hay un jugador real pidiendo algo); el que mueve la
partida en ese modo es el propio Controlador, reproduciendo una bitácora o
corriendo una simulación, no un humano tecleando.

Guarda lo último que recibió en cada mostrar_* (no para mostrarlo: por si una
prueba quiere confirmar qué le llegó al final, sin tener que fingir una
pantalla real).
"""
from __future__ import annotations

from .vistaJuego import VistaJuego


class VistaNula(VistaJuego):

    def __init__(self):
        self.ultimo_estado = None
        self.ultimos_mensajes = None
        self.ultimo_menu = None
        self.ultimos_puntajes = None
        self.ultimo_fin = None
        self.ultimo_error = None
        self.mostro_titulo = False

    def mostrar_estado(self, estado) -> None:
        self.ultimo_estado = estado

    def mostrar_titulo(self) -> None:
        self.mostro_titulo = True

    def mostrar_mensajes(self, mensajes) -> None:
        self.ultimos_mensajes = mensajes

    def pedir_comando(self):
        return None

    def mostrar_menu(self, criptas) -> None:
        self.ultimo_menu = criptas

    def mostrar_puntajes(self, puntajes) -> None:
        self.ultimos_puntajes = puntajes

    def mostrar_fin(self, resultado) -> None:
        self.ultimo_fin = resultado

    def mostrar_error(self, mensaje: str) -> None:
        self.ultimo_error = mensaje

    def actualizar(self) -> None:
        """No hay ventana que bombear: no hacer nada."""