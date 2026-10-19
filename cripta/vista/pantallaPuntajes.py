"""PantallaPuntajes: tabla de resultados guardados (§10.2, Paso 6).

El orden ya viene decidido por el Controlador (ConstructorEstadoVista/
TablaPuntajes con el selector de §4.9), y esta pantalla lo respeta tal cual.
Las flechas (o la rueda) eligen una fila; la tabla se desplaza para que la
elegida siempre se vea. R reproduce ESA partida si tiene su log archivado
(Comando("ver_replay_partida", (id_partida,))). ENTER vuelve al menú
(Comando("volver")); ESCAPE sigue significando "salir" del juego, igual que
en cualquier pantalla (D45).

Se dibuja con el estilo de la cripta (estilo.py): un resumen arriba
(partidas, victorias, mejor tiempo), medallas para los tres primeros
puestos que sean victorias (el Modelo ya pone las victorias primero, D59),
filas alternadas y el resultado como una etiqueta de color.

DECISIÓN: el resumen lo calcula la Vista recorriendo la lista que ya le
llegó (O(p), p puntajes): es presentación de datos que ya tiene, no una
regla del juego, y no vale la pena un DTO nuevo para tres números.
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo
from .comando import Comando
from .pantallaBase import _PantallaCripta

RESULTADO_VICTORIA = "victoria"
_ALTO_FILA = 34
_MEDALLAS = ((232, 193, 92), (196, 200, 210), (196, 128, 72))     # oro, plata, bronce

# Columnas: (título, fracción del ancho de la tabla donde empieza, alineación)
_COLUMNAS = (("#", 0.0, "center"), ("Nombre", 0.07, "left"), ("Cripta", 0.29, "left"),
             ("Resultado", 0.47, "center"), ("Acciones", 0.63, "right"),
             ("Derrotados", 0.76, "right"), ("Tiempo", 0.88, "right"),
             ("Replay", 0.965, "center"))


class PantallaPuntajes(_PantallaCripta):

    def __init__(self, vista_arcade, puntajes):
        super().__init__(vista_arcade)
        self._puntajes = puntajes          # ListaEnlazada de PuntajeVisible
        self._cantidad = len(puntajes)
        self._desplazamiento = 0
        self._cursor = 0 if self._cantidad > 0 else -1
        self._aviso = None                 # arcade.Text, si R no tiene replay
        self._fijos = ListaEnlazada()      # arcade.Text que no se mueven
        self._filas = ListaEnlazada()      # (indice, puntaje, ListaEnlazada de arcade.Text)
        self._tarjetas = ListaEnlazada()   # (izq, der, abajo, arriba) del resumen

    @property
    def desplazamiento(self) -> int:
        return self._desplazamiento

    @property
    def cursor(self) -> int:
        return self._cursor

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar()

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("volver"))
        elif symbol == arcade.key.DOWN:
            self._mover_cursor(1)
        elif symbol == arcade.key.UP:
            self._mover_cursor(-1)
        elif symbol == arcade.key.R and self._cursor >= 0:
            puntaje = self._puntajes.obtener(self._cursor)
            if puntaje.tiene_replay:
                self._vista_arcade._encolar(Comando("ver_replay_partida", (puntaje.id_partida,)))
            else:
                self._avisar("Esa partida no tiene replay: se jugó antes de que se "
                             "guardara el historial de partidas.")

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y) -> None:
        self._mover_cursor(-int(scroll_y))

    def _mover_cursor(self, delta: int) -> None:
        """Mueve la fila elegida sin salirse de la tabla y desplaza la
        tabla para que siempre se vea. O(1)."""
        if self._cantidad == 0:
            return
        self._cursor = max(0, min(self._cantidad - 1, self._cursor + delta))
        visibles = self._filas_visibles()
        if self._cursor < self._desplazamiento:
            self._desplazamiento = self._cursor
        elif self._cursor >= self._desplazamiento + visibles:
            self._desplazamiento = self._cursor - visibles + 1

    def _avisar(self, texto: str) -> None:
        if self._aviso is not None:
            self._aviso.text = texto

    def _texto_fila(self, puntaje) -> str:
        """La fila en una sola línea de texto (la usa la prueba de vista)."""
        return (f"{puntaje.nombre:<15} {puntaje.id_cripta:<9} "
                f"{puntaje.acciones:>8}  {puntaje.enemigos_derrotados:>10}  "
                f"{puntaje.tiempo_final:>6}  {puntaje.resultado}")

    # ------------------------------------------------------------------
    # Armado
    # ------------------------------------------------------------------

    def _geometria(self):
        ancho, alto = self.window.width, self.window.height
        izq, der = 40, ancho - 40
        arriba = alto - 200
        abajo = 56
        return izq, der, abajo, arriba

    def _filas_visibles(self) -> int:
        izq, der, abajo, arriba = self._geometria()
        return max(1, int((arriba - abajo - 50) // _ALTO_FILA))

    def _armar(self) -> None:
        ancho, alto = self.window.width, self.window.height
        fijos = ListaEnlazada()
        sombra, frente = estilo.titulo("Salón de la fama", ancho / 2, alto - 46, 34)
        fijos.agregar_al_final(sombra)
        fijos.agregar_al_final(frente)
        fijos.agregar_al_final(estilo.texto(
            "Primero las victorias; en cada grupo, menos tiempo es mejor puesto", ancho / 2, alto - 84,
            12, estilo.TEXTO_SUAVE, anchor_x="center"))
        ayuda = "ENTER: volver al menú   ESC: salir"
        if self._cantidad > 0:
            ayuda = "Flechas: elegir partida   R: ver su replay   " + ayuda
        fijos.agregar_al_final(estilo.texto(ayuda, ancho / 2, 22, 12, estilo.TEXTO_SUAVE,
                                            anchor_x="center"))
        self._armar_resumen(fijos, ancho, alto)
        self._aviso = estilo.texto("", ancho / 2, 42, 12, estilo.NARANJA, anchor_x="center")

        izq, der, abajo, arriba = self._geometria()
        if self._cantidad == 0:
            fijos.agregar_al_final(estilo.texto(
                "Todavía no hay puntajes guardados.", ancho / 2, (abajo + arriba) / 2 + 12, 16,
                estilo.TEXTO, anchor_x="center", anchor_y="center", bold=True))
            fijos.agregar_al_final(estilo.texto(
                "Termina una partida (ganes o pierdas) para entrar al salón.", ancho / 2,
                (abajo + arriba) / 2 - 16, 12, estilo.TEXTO_SUAVE, anchor_x="center",
                anchor_y="center"))
        else:
            for titulo_columna, fraccion, alineacion in _COLUMNAS:
                fijos.agregar_al_final(estilo.texto(
                    titulo_columna, self._x_columna(fraccion, alineacion), arriba - 26, 12,
                    estilo.DORADO, anchor_x=alineacion, anchor_y="center", bold=True))
            self._armar_filas()
        self._fijos = fijos

    def _armar_resumen(self, fijos, ancho, alto) -> None:
        """Tres tarjetas: partidas, victorias y mejor tiempo. O(p)."""
        victorias = 0
        mejor = None
        for puntaje in self._puntajes:
            if puntaje.resultado == RESULTADO_VICTORIA:
                victorias += 1
                if mejor is None or puntaje.tiempo_final < mejor.tiempo_final:
                    mejor = puntaje
        datos = (
            ("Partidas", str(self._cantidad), ""),
            ("Victorias", str(victorias),
             f"{victorias * 100 // self._cantidad}% de las partidas" if self._cantidad else ""),
            ("Mejor victoria", f"{mejor.tiempo_final}" if mejor else "-",
             f"{mejor.nombre} en {mejor.id_cripta}" if mejor else "nadie ha escapado aún"),
        )
        tarjetas = ListaEnlazada()
        ancho_tarjeta = (ancho - 80 - 2 * 20) / 3
        x = 40
        for etiqueta, valor, detalle in datos:
            izq, der = x, x + ancho_tarjeta
            abajo, arriba = alto - 186, alto - 110
            tarjetas.agregar_al_final((izq, der, abajo, arriba))
            centro = (izq + der) / 2
            fijos.agregar_al_final(estilo.texto(etiqueta, centro, arriba - 18, 11,
                                                estilo.TEXTO_SUAVE, anchor_x="center",
                                                anchor_y="center"))
            fijos.agregar_al_final(estilo.texto(valor, centro, arriba - 42, 20, estilo.DORADO,
                                                anchor_x="center", anchor_y="center", bold=True))
            if detalle:
                fijos.agregar_al_final(estilo.texto(detalle, centro, abajo + 12, 10,
                                                    estilo.TEXTO_SUAVE, anchor_x="center",
                                                    anchor_y="center"))
            x = der + 20
        self._tarjetas = tarjetas

    @staticmethod
    def _con_medalla(indice: int, puntaje) -> bool:
        """Medalla solo para los tres primeros puestos que sean victorias:
        morir rápido no merece oro."""
        return indice < 3 and puntaje.resultado == RESULTADO_VICTORIA

    def _x_columna(self, fraccion: float, alineacion: str) -> float:
        izq, der, abajo, arriba = self._geometria()
        interior_izq, interior_der = izq + 24, der - 24
        x = interior_izq + (interior_der - interior_izq) * fraccion
        if alineacion == "center" and fraccion == 0.0:
            return interior_izq + 14
        return x

    def _armar_filas(self) -> None:
        filas = ListaEnlazada()
        for indice, puntaje in enumerate(self._puntajes):
            textos = ListaEnlazada()
            victoria = puntaje.resultado == RESULTADO_VICTORIA
            color_nombre = estilo.TEXTO if victoria else estilo.TEXTO_SUAVE
            celdas = (
                # en el podio el número va oscuro, sobre la medalla
                (str(indice + 1), _COLUMNAS[0],
                 (30, 20, 10) if self._con_medalla(indice, puntaje) else estilo.TEXTO, True),
                (puntaje.nombre, _COLUMNAS[1], color_nombre, victoria),
                (puntaje.id_cripta, _COLUMNAS[2], estilo.TEXTO_SUAVE, False),
                ("Victoria" if victoria else "Derrota", _COLUMNAS[3], (20, 16, 14), True),
                (str(puntaje.acciones), _COLUMNAS[4], estilo.TEXTO, False),
                (str(puntaje.enemigos_derrotados), _COLUMNAS[5], estilo.TEXTO, False),
                (str(puntaje.tiempo_final), _COLUMNAS[6], estilo.TEXTO, True),
                ("" if puntaje.tiene_replay else "-", _COLUMNAS[7], estilo.TEXTO_APAGADO, False),
            )
            for contenido, columna, color, negrita in celdas:
                _, fraccion, alineacion = columna
                textos.agregar_al_final(estilo.texto(
                    contenido, self._x_columna(fraccion, alineacion), 0, 13, color,
                    anchor_x=alineacion, anchor_y="center", bold=negrita))
            filas.agregar_al_final((indice, puntaje, textos))
        self._filas = filas

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def on_draw(self) -> None:
        self.clear()
        estilo.dibujar_fondo(self.window)
        for izq, der, abajo, arriba in self._tarjetas:
            estilo.dibujar_panel(izq, der, abajo, arriba)
        izq, der, abajo, arriba = self._geometria()
        estilo.dibujar_panel(izq, der, abajo, arriba)
        if self._cantidad > 0:
            arcade.draw_line(izq + 16, arriba - 44, der - 16, arriba - 44, estilo.DORADO_OSCURO, 2)
            self._dibujar_filas(izq, der, arriba - 50)
        for texto in self._fijos:
            texto.draw()
        if self._aviso is not None and self._aviso.text:
            self._aviso.draw()

    def _dibujar_filas(self, izq: float, der: float, tope: float) -> None:
        visibles = self._filas_visibles()
        y = tope - _ALTO_FILA / 2
        for indice, puntaje, textos in self._filas:
            if indice < self._desplazamiento:
                continue
            if indice >= self._desplazamiento + visibles:
                break
            victoria = puntaje.resultado == RESULTADO_VICTORIA
            elegida = indice == self._cursor
            if elegida:
                arcade.draw_lrbt_rectangle_filled(izq + 12, der - 12, y - _ALTO_FILA / 2 + 2,
                                                  y + _ALTO_FILA / 2 - 2, (232, 193, 92, 40))
                arcade.draw_lrbt_rectangle_outline(izq + 12, der - 12, y - _ALTO_FILA / 2 + 2,
                                                   y + _ALTO_FILA / 2 - 2, estilo.DORADO, 2)
            elif indice % 2 == 0:
                arcade.draw_lrbt_rectangle_filled(izq + 12, der - 12, y - _ALTO_FILA / 2 + 2,
                                                  y + _ALTO_FILA / 2 - 2, (255, 255, 255, 10))
            if puntaje.tiene_replay:
                # botón "play": un triángulo en la columna Replay
                x_play = self._x_columna(_COLUMNAS[7][1], "center")
                color_play = estilo.DORADO if elegida else estilo.TEXTO_SUAVE
                arcade.draw_triangle_filled(x_play - 6, y + 8, x_play - 6, y - 8, x_play + 9, y,
                                            color_play)
            if self._con_medalla(indice, puntaje):
                # medalla de oro, plata o bronce detrás del número del puesto
                x = self._x_columna(0.0, "center")
                arcade.draw_circle_filled(x, y, 13, _MEDALLAS[indice])
                arcade.draw_circle_outline(x, y, 13, (60, 40, 20), 2)
            # etiqueta del resultado
            x_resultado = self._x_columna(_COLUMNAS[3][1], "center")
            color = estilo.VERDE if victoria else estilo.ROJO
            arcade.draw_lrbt_rectangle_filled(x_resultado - 44, x_resultado + 44, y - 11, y + 11,
                                              color)
            for texto in textos:
                texto.y = y
                texto.draw()
            y -= _ALTO_FILA
        alto_barra = tope - 70
        if self._cantidad > visibles and alto_barra > 0:
            # indicador de desplazamiento a la derecha del panel (si hay lugar)
            fraccion = visibles / self._cantidad
            inicio = self._desplazamiento / self._cantidad
            arriba = tope - inicio * alto_barra
            arcade.draw_lrbt_rectangle_filled(der - 10, der - 5, arriba - fraccion * alto_barra,
                                              arriba, estilo.DORADO_OSCURO)
