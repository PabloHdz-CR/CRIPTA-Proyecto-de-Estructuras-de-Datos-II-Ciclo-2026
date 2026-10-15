"""PantallaPuntajes: tabla de resultados guardados (§10.2, Paso 6).

Solo lectura: no hay cursor que mover ni objetivo que elegir (el orden ya
viene decidido por el Controlador -- ConstructorEstadoVista/TablaPuntajes,
ver estadoVista.py). ENTER vuelve al menú (arma Comando("volver"), un verbo
nuevo que hay que avisarle al compañero); ESCAPE sigue significando "salir"
del juego, igual que en cualquier pantalla (D45).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta

_MARGEN = 20
_ALTO_FILA = 26


class PantallaPuntajes(_PantallaCripta):

    def __init__(self, vista_arcade, puntajes):
        super().__init__(vista_arcade)
        self._puntajes = puntajes          # ListaEnlazada de PuntajeVisible
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
        textos = ListaEnlazada()
        y = alto - _MARGEN

        def agregar(texto_str, tamano=16, color=arcade.color.WHITE):
            nonlocal y
            textos.agregar_al_final(arcade.Text(texto_str, _MARGEN, y, color, tamano))
            y -= _ALTO_FILA

        agregar("PUNTAJES", 24)
        if self._puntajes.esta_vacia():
            agregar("Todavía no hay puntajes guardados.", 14, arcade.color.LIGHT_GRAY)
        else:
            agregar("Nombre          Cripta    Acciones  Derrotados  Tiempo  Resultado",
                    13, arcade.color.LIGHT_GRAY)
            for puntaje in self._puntajes:
                agregar(self._texto_fila(puntaje), 13)
        agregar("ENTER: volver al menú   ESC: salir", 13, arcade.color.LIGHT_GRAY)

        self._textos = textos

    def _texto_fila(self, puntaje) -> str:
        return (f"{puntaje.nombre:<15} {puntaje.id_cripta:<9} "
                f"{puntaje.acciones:>8}  {puntaje.enemigos_derrotados:>10}  "
                f"{puntaje.tiempo_final:>6}  {puntaje.resultado}")