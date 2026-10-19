"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta



class PantallaMenu(_PantallaCripta):

        super().__init__(vista_arcade)
        self._criptas = criptas            # ListaEnlazada de CriptaVisible
        self._cantidad = len(criptas)
        self._indice = 0 if self._cantidad > 0 else -1
        self._titulo = None

    def on_show_view(self) -> None:
        super().on_show_view()


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


    def _mover_cursor(self, delta: int) -> None:
        nuevo = self._indice + delta
        if 0 <= nuevo < self._cantidad:
            self._indice = nuevo

        if self._cantidad == 0:
                anchor_x="center")
            return
