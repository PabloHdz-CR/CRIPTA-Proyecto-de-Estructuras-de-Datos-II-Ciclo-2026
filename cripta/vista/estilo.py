"""Estilo común de las pantallas de menú (§10.2): fondo, paneles, teclas.

Presentación pura: no conoce comandos ni datos del juego. La usan
PantallaMenu, PantallaFin, PantallaPuntajes y PantallaBenchmark para que
se vean como parte del mismo juego que la sala de 0x72.
"""
from __future__ import annotations

import arcade

from . import texturas

DORADO = (232, 193, 92)
DORADO_OSCURO = (150, 112, 48)
TEXTO = (236, 228, 214)
TEXTO_SUAVE = (170, 160, 146)
TEXTO_APAGADO = (110, 102, 92)
NARANJA = (240, 150, 60)
VERDE = (110, 200, 120)
ROJO = (225, 80, 70)
_PANEL = (22, 17, 18, 225)
_PANEL_RESALTADO = (44, 33, 26, 235)
_BORDE = (88, 70, 58)
_TECLA = (58, 48, 42)
_TECLA_BORDE = (130, 112, 92)


def dibujar_fondo(ventana) -> None:
    """Piso de 0x72 a pantalla completa con viñeta oscura en los bordes."""
    escala = max(1, round(3 * ventana.get_pixel_ratio()))
    ancho_px = int(ventana.width * ventana.get_pixel_ratio())
    alto_px = int(ventana.height * ventana.get_pixel_ratio())
    arcade.draw_texture_rect(texturas.fondo_pantalla(ancho_px, alto_px, escala),
                             arcade.LBWH(0, 0, ventana.width, ventana.height), pixelated=True)
    arcade.draw_texture_rect(texturas.oscuridad(True),
                             arcade.LBWH(-ventana.width * 0.15, -ventana.height * 0.15,
                                         ventana.width * 1.3, ventana.height * 1.3),
                             alpha=200)


def dibujar_panel(izq: float, der: float, abajo: float, arriba: float,
                  resaltado: bool = False, color_borde=None) -> None:
    arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba,
                                      _PANEL_RESALTADO if resaltado else _PANEL)
    borde = color_borde if color_borde is not None else (DORADO if resaltado else _BORDE)
    arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, borde, 3 if resaltado else 2)
    # esquinas remachadas, como en las puertas de la cripta
    for x, y in ((izq + 6, abajo + 6), (der - 6, abajo + 6), (izq + 6, arriba - 6),
                 (der - 6, arriba - 6)):
        arcade.draw_circle_filled(x, y, 2.5, borde)


def dibujar_tecla(centro_x: float, centro_y: float, ancho: float, alto: float = 24) -> None:
    """El recuadro de una tecla (el texto lo dibuja la pantalla encima)."""
    izq, der = centro_x - ancho / 2, centro_x + ancho / 2
    abajo, arriba = centro_y - alto / 2, centro_y + alto / 2
    arcade.draw_lrbt_rectangle_filled(izq, der, abajo - 3, arriba - 3, (20, 16, 14))
    arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, _TECLA)
    arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, _TECLA_BORDE, 1)


def texto(contenido: str, x: float, y: float, tamano: int = 14, color=TEXTO,
          anchor_x: str = "left", anchor_y: str = "baseline", bold: bool = False) -> arcade.Text:
    return arcade.Text(contenido, x, y, color, tamano, anchor_x=anchor_x, anchor_y=anchor_y,
                       bold=bold)


def titulo(contenido: str, x: float, y: float, tamano: int):
    """Título dorado con sombra: devuelve (sombra, título) para dibujar en ese orden."""
    sombra = arcade.Text(contenido, x + 3, y - 3, (30, 18, 10), tamano, anchor_x="center",
                         anchor_y="center", bold=True)
    frente = arcade.Text(contenido, x, y, DORADO, tamano, anchor_x="center",
                         anchor_y="center", bold=True)
    return sombra, frente


# Cazador (001-terreno-cazador, FR-024): se distingue por un marcador de forma
# (el prefijo en la etiqueta y un anillo alrededor de su figura en la sala),
# no solo por el color. El color es un refuerzo.
PREFIJO_CAZADOR = "» "
COLOR_CAZADOR = (245, 140, 40)


def etiqueta_enemigo(enemigo) -> str:
    """La etiqueta que se muestra de un ActorVisible: con el prefijo del
    cazador si lo es."""
    return PREFIJO_CAZADOR + enemigo.etiqueta if enemigo.es_cazador else enemigo.etiqueta
