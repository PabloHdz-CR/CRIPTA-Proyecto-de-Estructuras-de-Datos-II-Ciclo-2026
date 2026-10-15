"""PantallaMenu: elegir cripta, ver puntajes o salir (§10.2, Paso 4).

Lo que ControladorMenu (del lado de Controlador) necesita de esta pantalla:
que el jugador recorra la lista de criptas con las flechas y confirme con
ENTER. Esa confirmación arma un Comando "jugar" con el id de la cripta
elegida -- la Vista no decide si eso es una partida nueva o una cargada
("partida nueva o cargada" es trabajo de ControladorMenu, según la guía,
nunca de Vista). "P" pide la tabla de puntajes. ESCAPE (salir) lo atiende
_PantallaCripta, igual en las 4 pantallas.

self._filas (los arcade.Text ya armados, uno por cripta) es presentación
pura: no es una estructura de datos del juego, pero igual se arma con
ListaEnlazada y no con una lista nativa de Python, para respetar la regla
general del proyecto en todo cripta/ (prueba_reglas.py no hace excepción
para vista/).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta

_ALTO_FILA = 30
_MARGEN_SUPERIOR = 80


class PantallaMenu(_PantallaCripta):

    def __init__(self, vista_arcade, criptas):
        super().__init__(vista_arcade)
        self._criptas = criptas            # ListaEnlazada de CriptaVisible
        self._cantidad = len(criptas)
        self._indice = 0 if self._cantidad > 0 else -1
        self._titulo = None
        self._ayuda = None
        self._filas = ListaEnlazada()       # de arcade.Text, una por cripta

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar_textos()

    def on_draw(self) -> None:
        self.clear()
        self._titulo.draw()
        self._ayuda.draw()
        for fila in self._filas:
            fila.draw()

    def tecla_propia(self, symbol, modifiers) -> None:
        if self._cantidad == 0:
            return
        if symbol == arcade.key.UP:
            self._mover_cursor(-1)
        elif symbol == arcade.key.DOWN:
            self._mover_cursor(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            cripta = self._criptas.obtener(self._indice)
            self._vista_arcade._encolar(Comando("jugar", (cripta.id,)))
        elif symbol == arcade.key.P:
            self._vista_arcade._encolar(Comando("ver_puntajes"))

    @property
    def indice_seleccionado(self) -> int:
        """Expuesto solo para que la prueba confirme el cursor sin tener que
        adivinarlo a partir de los colores dibujados."""
        return self._indice

    def _mover_cursor(self, delta: int) -> None:
        nuevo = self._indice + delta
        if 0 <= nuevo < self._cantidad:
            self._indice = nuevo
            self._actualizar_colores()

    def _armar_textos(self) -> None:
        ancho = self.window.width
        alto = self.window.height
        self._titulo = arcade.Text("CRIPTA", ancho / 2, alto - 40,
                                    arcade.color.WHITE, 28, anchor_x="center")
        if self._cantidad == 0:
            self._ayuda = arcade.Text(
                "No hay criptas disponibles. ESC para salir.",
                ancho / 2, alto / 2, arcade.color.LIGHT_GRAY, 16,
                anchor_x="center")
            return
        self._ayuda = arcade.Text(
            "Flechas: elegir   ENTER: jugar   P: puntajes   ESC: salir",
            ancho / 2, 40, arcade.color.LIGHT_GRAY, 14, anchor_x="center")
        y = alto - _MARGEN_SUPERIOR
        for indice in range(self._cantidad):
            cripta = self._criptas.obtener(indice)
            texto = f"{cripta.nombre}  ({cripta.salas} salas, dificultad {cripta.dificultad})"
            self._filas.agregar_al_final(
                arcade.Text(texto, ancho / 2, y, arcade.color.WHITE, 18,
                            anchor_x="center"))
            y -= _ALTO_FILA
        self._actualizar_colores()

    def _actualizar_colores(self) -> None:
        for indice, fila in enumerate(self._filas):
            fila.color = arcade.color.YELLOW if indice == self._indice else arcade.color.WHITE