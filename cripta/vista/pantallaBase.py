"""_PantallaCripta: lo que comparten las 4 pantallas de VistaArcade (§6, §10.2).

Cada pantalla real (PantallaMenu, PantallaJuego, PantallaPuntajes,
PantallaFin) interpreta sus propias teclas de forma distinta -- las flechas
significan "mover cursor" en el Menú, pero "moverse por la sala" en el Juego.
Por eso el mapeo de teclas NO vive en VistaArcade (como en el esqueleto del
Paso 3): cada pantalla decide las suyas en tecla_propia().

Lo único que SÍ es igual en las 4 pantallas es ESCAPE -> salir, así que esta
clase base lo atiende una sola vez y no deja que las subclases se lo tengan
que acordar cada una por su lado.
"""
from __future__ import annotations

import arcade

from .comando import Comando


class _PantallaCripta(arcade.View):

    def __init__(self, vista_arcade):
        super().__init__()
        self._vista_arcade = vista_arcade

    def on_show_view(self) -> None:
        self.window.background_color = arcade.color.BLACK

    def on_key_press(self, symbol, modifiers) -> None:
        if symbol == arcade.key.ESCAPE:
            self._vista_arcade._encolar(Comando("salir"))
            return
        self.tecla_propia(symbol, modifiers)

    def tecla_propia(self, symbol, modifiers) -> None:
        """Las subclases la sobreescriben con sus teclas propias. Por
        defecto no hace nada (una pantalla sin controles propios, como el
        relleno del Paso 3, simplemente ignora cualquier tecla que no sea
        ESCAPE)."""