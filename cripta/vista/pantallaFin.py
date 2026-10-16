"""PantallaFin: resultado de la partida que acaba de terminar (§10.2, Paso 7).

Muestra el resultado y dos recuadros: "Tu partida" (acciones, enemigos,
tiempo) y "Red y caché", el mismo resumen que ReporteFinal imprime en la
terminal (§5.1). Si el resultado no trae esos datos (p. ej. armado por
--replay), el segundo recuadro no se dibuja.

Solo lectura, igual que Puntajes: ENTER vuelve al menú (Comando("volver"));
ESCAPE sigue siendo "salir" (D45).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .pantallaBase import _PantallaCripta

_COLOR_RECUADRO = (28, 24, 24)


class PantallaFin(_PantallaCripta):

    def __init__(self, vista_arcade, resultado):
        super().__init__(vista_arcade)
        self._resultado = resultado        # ResultadoFinVisible
        self._textos = ListaEnlazada()
        self._recuadros = ListaEnlazada()   # de (izq, der, abajo, arriba)

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar_textos()

    def on_draw(self) -> None:
        self.clear()
        for izq, der, abajo, arriba in self._recuadros:
            arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, _COLOR_RECUADRO)
            arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, self._color_borde(), 2)
        for texto in self._textos:
            texto.draw()

    def _color_borde(self):
        return arcade.color.GOLD if self._es_victoria() else (170, 50, 50)

    def _es_victoria(self) -> bool:
        return self._resultado.resultado == "victoria"

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("volver"))

    def _armar_textos(self) -> None:
        alto = self.window.height
        ancho = self.window.width
        resultado = self._resultado
        textos = ListaEnlazada()
        recuadros = ListaEnlazada()
        centro = ancho / 2

        def agregar(texto_str, x, y, tamano, color, anchor_x="center", bold=False):
            textos.agregar_al_final(arcade.Text(texto_str, x, y, color, tamano,
                                                anchor_x=anchor_x, anchor_y="top", bold=bold))

        es_victoria = self._es_victoria()
        y = alto - alto * 0.08
        agregar("¡VICTORIA!" if es_victoria else "DERROTA", centro, y, 34,
                arcade.color.GOLD if es_victoria else arcade.color.RED, bold=True)
        y -= 56
        agregar("Escapaste de la cripta." if es_victoria else "La cripta te ha reclamado.",
                centro, y, 14, arcade.color.LIGHT_GRAY)
        y -= 44

        filas_partida = (
            ("Acciones", str(resultado.acciones)),
            ("Enemigos derrotados", str(resultado.enemigos_derrotados)),
            ("Tiempo", str(resultado.tiempo_final)),
        )
        y = self._recuadro(textos, recuadros, agregar, "Tu partida", filas_partida,
                           centro, y, ancho)

        if resultado.solicitudes_realizadas is not None:
            presupuesto = resultado.presupuesto
            restantes = ("-" if presupuesto is None
                         else str(presupuesto - resultado.solicitudes_realizadas))
            filas_red = (
                ("Solicitudes de red", str(resultado.solicitudes_realizadas)),
                ("Presupuesto", "sin red" if presupuesto is None else str(presupuesto)),
                ("Solicitudes restantes", restantes),
                ("Aciertos de caché", str(resultado.aciertos_cache)),
                ("Fallos de caché", str(resultado.fallos_cache)),
            )
            self._recuadro(textos, recuadros, agregar, "Red y caché", filas_red,
                           centro, y - 16, ancho)

        agregar("ENTER: volver al menú   ESC: salir", centro, 40, 13, arcade.color.LIGHT_GRAY)
        self._textos = textos
        self._recuadros = recuadros

    def _recuadro(self, textos, recuadros, agregar, titulo, filas, centro, arriba, ancho):
        """Un recuadro con título y filas "etiqueta ...... valor". Devuelve
        la y donde termina, para apilar el siguiente debajo."""
        ancho_recuadro = min(420, ancho - 40)
        izq, der = centro - ancho_recuadro / 2, centro + ancho_recuadro / 2
        alto_fila = 26
        abajo = arriba - 46 - alto_fila * len(filas)
        recuadros.agregar_al_final((izq, der, abajo, arriba))
        agregar(titulo, centro, arriba - 10, 16, arcade.color.WHITE, bold=True)
        y = arriba - 44
        for etiqueta, valor in filas:
            agregar(etiqueta, izq + 20, y, 14, arcade.color.LIGHT_GRAY, anchor_x="left")
            agregar(valor, der - 20, y, 14, arcade.color.WHITE, anchor_x="right", bold=True)
            y -= alto_fila
        return abajo
