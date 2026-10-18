"""PantallaBenchmark y PantallaEspera (§5.3, §10.2).

PantallaBenchmark muestra en la ventana las mismas tablas que --bench
imprime en la terminal (las arma Reporte), con desplazamiento: flechas de a
una línea, RePág/AvPág de a una página. ENTER o ESC vuelven al menú.

PantallaEspera es un aviso mientras el Controlador mide (unos segundos).

DECISIÓN: ESC aquí vuelve al menú en vez de cerrar el juego (por eso se
sobreescribe on_key_press): es una pantalla de consulta, igual que el modo
objetivo de PantallaJuego.

Complejidad: armar las líneas es O(celdas) una sola vez; cada cuadro dibuja
solo las líneas visibles.
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo
from .comando import Comando
from .pantallaBase import _PantallaCripta

_FUENTE_MONO = ("Consolas", "Courier New", "monospace")
_ALTO_LINEA = 17
_TAMANO = 11


def _celda(texto: str, ancho: int, primera: bool) -> str:
    return texto.ljust(ancho) if primera else texto.rjust(ancho)


def _lineas_de_tabla(encabezados, filas) -> ListaEnlazada:
    """Las mismas columnas alineadas que Reporte imprime en la terminal."""
    anchos = ListaEnlazada()
    for columna in range(len(encabezados)):
        ancho = len(encabezados[columna])
        for fila in filas:
            if len(fila[columna]) > ancho:
                ancho = len(fila[columna])
        anchos.agregar_al_final(ancho)
    lineas = ListaEnlazada()
    for celdas in _filas_con_encabezado(encabezados, filas):
        texto = ""
        for columna, ancho in enumerate(anchos):
            if columna > 0:
                texto += " | "
            texto += _celda(celdas[columna], ancho, columna == 0)
        lineas.agregar_al_final(texto)
        if celdas is encabezados:
            separador = ""
            for columna, ancho in enumerate(anchos):
                if columna > 0:
                    separador += "-+-"
                separador += "-" * ancho
            lineas.agregar_al_final(separador)
    return lineas


def _partir(texto: str, ancho: int) -> ListaEnlazada:
    """Parte una nota larga en líneas de a lo sumo `ancho` caracteres,
    cortando en espacios. O(largo)."""
    lineas = ListaEnlazada()
    resto = texto
    while len(resto) > ancho:
        corte = resto.rfind(" ", 0, ancho)
        if corte <= 0:
            corte = ancho
        lineas.agregar_al_final(resto[:corte])
        resto = resto[corte:].lstrip()
    lineas.agregar_al_final(resto)
    return lineas


def _filas_con_encabezado(encabezados, filas):
    yield encabezados
    for fila in filas:
        yield fila


class PantallaBenchmark(_PantallaCripta):

    def __init__(self, vista_arcade, resultado):
        super().__init__(vista_arcade)
        self._resultado = resultado        # BenchmarkVisible
        self._lineas = ListaEnlazada()     # (texto, color, negrita)
        self._textos = ListaEnlazada()     # arcade.Text, uno por línea
        self._desplazamiento = 0
        self._cabecera = ListaEnlazada()

    @property
    def desplazamiento(self) -> int:
        return self._desplazamiento

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar()

    def on_key_press(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ESCAPE, arcade.key.ENTER, arcade.key.RETURN):
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
        resultado = self._resultado
        cabecera = ListaEnlazada()
        tipo = "rápido" if resultado.rapido else "completo"
        sombra, frente = estilo.titulo("Benchmark de estructuras", ancho / 2, alto - 40, 26)
        cabecera.agregar_al_final(sombra)
        cabecera.agregar_al_final(frente)
        cabecera.agregar_al_final(estilo.texto(
            f"Modo {tipo}, {resultado.segundos:.1f} s. Mismas mediciones que "
            f"py main.py --bench (cargas sintéticas, sin red).", ancho / 2, alto - 74, 12,
            estilo.TEXTO_SUAVE, anchor_x="center"))
        cabecera.agregar_al_final(estilo.texto(
            "Flechas o rueda: desplazar   RePág/AvPág: página   ENTER/ESC: volver",
            ancho / 2, 18, 12, estilo.TEXTO_SUAVE, anchor_x="center"))
        self._cabecera = cabecera

        textos = ListaEnlazada()
        if not resultado.notas.esta_vacia():
            textos.agregar_al_final(self._linea("Notas", estilo.DORADO, True))
            # El ancho en caracteres sale del ancho del panel y de la fuente
            # monoespaciada (unos 0.62 del tamaño en px por carácter).
            caracteres = max(30, int((ancho - 120) / (_TAMANO * 1.33 * 0.62)))
            for nota in resultado.notas:
                for parte in _partir(nota, caracteres):
                    textos.agregar_al_final(self._linea("  " + parte, estilo.TEXTO_SUAVE, False))
            textos.agregar_al_final(self._linea("", estilo.TEXTO, False))
        for titulo_tabla, encabezados, filas in resultado.tablas:
            textos.agregar_al_final(self._linea(titulo_tabla, estilo.DORADO, True))
            primera = True
            for linea in _lineas_de_tabla(encabezados, filas):
                color = estilo.TEXTO if primera else estilo.TEXTO_SUAVE
                textos.agregar_al_final(self._linea("  " + linea, color, False))
                primera = False
            textos.agregar_al_final(self._linea("", estilo.TEXTO, False))
        self._textos = textos

    def _linea(self, contenido: str, color, negrita: bool) -> arcade.Text:
        return arcade.Text(contenido, 0, 0, color, _TAMANO, font_name=_FUENTE_MONO,
                           bold=negrita, anchor_y="top")

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
            texto.x = 48
            texto.y = y
            texto.draw()
            y -= _ALTO_LINEA
        total = len(self._textos)
        if total > visibles:
            # barra de desplazamiento
            alto_barra = alto - 150
            fraccion = visibles / total
            inicio = self._desplazamiento / total
            arriba = alto - 104 - inicio * alto_barra
            arcade.draw_lrbt_rectangle_filled(ancho - 46, ancho - 40,
                                              arriba - fraccion * alto_barra, arriba,
                                              estilo.DORADO_OSCURO)


class PantallaEspera(_PantallaCripta):
    """Un aviso centrado mientras el Controlador trabaja. No acepta teclas
    (ESC incluido): el trabajo termina solo y la reemplaza otra pantalla."""

    def __init__(self, vista_arcade, texto: str):
        super().__init__(vista_arcade)
        self._contenido = texto
        self._texto = None

    def on_show_view(self) -> None:
        super().on_show_view()
        self._texto = estilo.texto(self._contenido, self.window.width / 2,
                                   self.window.height / 2, 18, estilo.DORADO,
                                   anchor_x="center", anchor_y="center", bold=True)

    def on_key_press(self, symbol, modifiers) -> None:
        return

    def on_draw(self) -> None:
        self.clear()
        estilo.dibujar_fondo(self.window)
        self._texto.draw()
