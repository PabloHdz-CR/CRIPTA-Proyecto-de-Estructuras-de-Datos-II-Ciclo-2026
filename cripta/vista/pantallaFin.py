"""PantallaFin: resultado de la partida que acaba de terminar (§10.2, Paso 7).

Solo lectura, igual que Puntajes: ENTER vuelve al menú (Comando("volver"));
ESCAPE sigue siendo "salir" (D45).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta


class PantallaFin(_PantallaCripta):

    def __init__(self, vista_arcade, resultado):
        super().__init__(vista_arcade)
        self._resultado = resultado        # ResultadoFinVisible
        self._textos = ListaEnlazada()

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar_textos()

    def on_draw(self) -> None:
        self.clear()
        for texto in self._textos:
            texto.draw()

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("volver"))

    def _armar_textos(self) -> None:
        alto = self.window.height
        ancho = self.window.width
        resultado = self._resultado
        textos = ListaEnlazada()
        y = alto - 80

        def agregar(texto_str, tamano=18, color=arcade.color.WHITE):
            nonlocal y
            textos.agregar_al_final(
                arcade.Text(texto_str, ancho / 2, y, color, tamano, anchor_x="center"))
            y -= tamano + 14

        es_victoria = resultado.resultado == "victoria"
        agregar("¡VICTORIA!" if es_victoria else "DERROTA", 32,
                arcade.color.GOLD if es_victoria else arcade.color.RED)
        agregar(f"Acciones: {resultado.acciones}", 16, arcade.color.LIGHT_GRAY)
        agregar(f"Enemigos derrotados: {resultado.enemigos_derrotados}", 16, arcade.color.LIGHT_GRAY)
        agregar(f"Tiempo: {resultado.tiempo_final}", 16, arcade.color.LIGHT_GRAY)
        agregar("ENTER: volver al menú   ESC: salir", 13, arcade.color.LIGHT_GRAY)

        self._textos = textos