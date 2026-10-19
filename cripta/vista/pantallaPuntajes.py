"""PantallaPuntajes: tabla de resultados guardados (§10.2, Paso 6).

"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta



class PantallaPuntajes(_PantallaCripta):

    def __init__(self, vista_arcade, puntajes):
        super().__init__(vista_arcade)
        self._puntajes = puntajes          # ListaEnlazada de PuntajeVisible

    def on_show_view(self) -> None:
        super().on_show_view()

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("volver"))
        else:


    def _texto_fila(self, puntaje) -> str:
        return (f"{puntaje.nombre:<15} {puntaje.id_cripta:<9} "
                f"{puntaje.acciones:>8}  {puntaje.enemigos_derrotados:>10}  "
                f"{puntaje.tiempo_final:>6}  {puntaje.resultado}")