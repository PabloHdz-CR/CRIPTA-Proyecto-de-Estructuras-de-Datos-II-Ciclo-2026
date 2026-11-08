"""PantallaResolubilidad: el reporte de una cripta no resoluble antes de la
partida (003-resolubilidad, FR-019, FR-020, contracts/vista.md).

Muestra las líneas de ReporteResolubilidadVisible completas: cada una se
parte en filas que caben en el ancho de la ventana (partir_linea, con
sangría de continuación y sin perder texto), con fuente monoespaciada, y
las filas se desplazan con las flechas (de a una) y RePág/AvPág (de a una
página).
  - Sin --forzar (puede_continuar False): ENTER y ESC mandan "volver".
  - Con --forzar (puede_continuar True): ENTER manda "aceptar_resolubilidad"
    (la partida empieza igual) y ESC manda "volver".

DECISIÓN: ESC vuelve al menú en vez de cerrar el juego (se sobreescribe
on_key_press), como en PantallaBenchmark: es una pantalla de consulta.

Complejidad: armar los textos es O(líneas) una vez; cada cuadro dibuja solo
las visibles.
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo
from .comando import Comando
from .pantallaBase import _PantallaCripta
from .partirLineas import partir_lineas

_ALTO_LINEA = 17
_MARGEN_TEXTO = 48              # de cada lado, dentro del panel
_TAMANO = 11


class PantallaResolubilidad(_PantallaCripta):
    """La pantalla de reporte; ver el docstring del módulo."""

    def __init__(self, vista_arcade, reporte):
        super().__init__(vista_arcade)
        self._reporte = reporte            # ReporteResolubilidadVisible
        self._textos = ListaEnlazada()     # arcade.Text, uno por fila
        self._filas = ListaEnlazada()      # las líneas ya partidas
        self._maximo_caracteres = 0
        self._cabecera = ListaEnlazada()
        self._desplazamiento = 0

    @property
    def reporte(self):
        return self._reporte

    @property
    def desplazamiento(self) -> int:
        return self._desplazamiento

    @property
    def filas(self) -> ListaEnlazada:
        """Las filas que se dibujan (las líneas del reporte ya partidas)."""
        return self._filas

    @property
    def maximo_caracteres(self) -> int:
        """Caracteres por fila según el ancho de la ventana."""
        return self._maximo_caracteres

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar()

    def on_key_press(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            verbo = "aceptar_resolubilidad" if self._reporte.puede_continuar else "volver"
            self._vista_arcade._encolar(Comando(verbo))
        elif symbol == arcade.key.ESCAPE:
            self._vista_arcade._encolar(Comando("volver"))
        elif symbol == arcade.key.DOWN:
            self._desplazar(1)
        elif symbol == arcade.key.UP:
            self._desplazar(-1)
        elif symbol == arcade.key.PAGEDOWN:
            self._desplazar(self._lineas_visibles())
        elif symbol == arcade.key.PAGEUP:
            self._desplazar(-self._lineas_visibles())

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y) -> None:
        self._desplazar(-int(scroll_y) * 3)

    def _lineas_visibles(self) -> int:
        return max(1, int((self.window.height - 150) // _ALTO_LINEA))

    def _desplazar(self, delta: int) -> None:
        maximo = max(0, len(self._textos) - self._lineas_visibles())
        self._desplazamiento = max(0, min(maximo, self._desplazamiento + delta))

    def _armar(self) -> None:
        ancho, alto = self.window.width, self.window.height
        cabecera = ListaEnlazada()
        sombra, frente = estilo.titulo("Reporte de resolubilidad", ancho / 2, alto - 40, 26)
        cabecera.agregar_al_final(sombra)
        cabecera.agregar_al_final(frente)
        if self._reporte.puede_continuar:
            aviso = "La cripta no se puede ganar, pero se abrió con --forzar."
            ayuda = "ENTER jugar de todos modos · ESC volver   Flechas/RePág/AvPág: desplazar"
        else:
            aviso = "La partida no empieza: la cripta no se puede ganar."
            ayuda = "ENTER volver al menú   Flechas/RePág/AvPág: desplazar"
        cabecera.agregar_al_final(estilo.texto(aviso, ancho / 2, alto - 74, 12,
                                               estilo.TEXTO_SUAVE, anchor_x="center"))
        cabecera.agregar_al_final(estilo.texto(ayuda, ancho / 2, 18, 12, estilo.TEXTO_SUAVE,
                                               anchor_x="center"))
        self._cabecera = cabecera
        ancho_caracter = estilo.ancho_caracter_mono(_TAMANO)
        self._maximo_caracteres = max(1, int((ancho - 2 * _MARGEN_TEXTO) / ancho_caracter))
        self._filas = partir_lineas(self._reporte.lineas, self._maximo_caracteres)
        textos = ListaEnlazada()
        primera = True
        for fila in self._filas:
            color = estilo.DORADO if primera else estilo.TEXTO
            textos.agregar_al_final(estilo.texto_mono(fila, 0, 0, _TAMANO, color,
                                                      anchor_y="top", bold=primera))
            primera = False
        self._textos = textos

    def on_draw(self) -> None:
        self.clear()
        estilo.dibujar_fondo(self.window)
        ancho, alto = self.window.width, self.window.height
        estilo.dibujar_panel(30, ancho - 30, 40, alto - 92)
        for texto in self._cabecera:
            texto.draw()
        visibles = self._lineas_visibles()
        y = alto - 104
        for indice, texto in enumerate(self._textos):
            if indice < self._desplazamiento:
                continue
            if indice >= self._desplazamiento + visibles:
                break
            texto.x = _MARGEN_TEXTO
            texto.y = y
            texto.draw()
            y -= _ALTO_LINEA
