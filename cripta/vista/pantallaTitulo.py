"""PantallaTitulo: la pantalla de bienvenida, antes del menú (§10.2).

La entrada de la cripta (fondo armado con las baldosas de 0x72 en
texturas.fondo_titulo): muro de ladrillo con estandartes y una gran puerta,
dos antorchas que parpadean, brasas que suben, el héroe frente a la puerta
con el esqueleto guardián y una rata a los lados, el título con un mensaje
de bienvenida y una frase motivadora que cambia cada pocos segundos.

ENTER entra al menú principal (Comando("entrar")); ESC sale del juego, como
en cualquier pantalla (D45). Nada más hace algo.

DECISIÓN: las frases son una tupla fija y las brasas una ListaEnlazada de
tuplas armadas una sola vez (sin listas de Python, D27). Cada cuadro solo
dibuja: O(brasas) por cuadro. El azar (qué frase sale primero, dónde nace
cada brasa) es presentación pura y no toca la semilla del juego (§2.6).
"""
from __future__ import annotations

import math
import random
import time

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo, texturas
from .comando import Comando
from .pantallaBase import _PantallaCripta

FRASES = (
    "La oscuridad no dura para siempre: lleva siempre una antorcha.",
    "Cada sala superada es un paso más hacia la salida.",
    "Valiente no es quien no tiene miedo, sino quien avanza igual.",
    "Una llave a la vez, una puerta a la vez.",
    "Hasta el guardián más antiguo tiene un punto débil.",
    "Si caes, levántate: el pergamino recuerda que siempre hay otra oportunidad.",
    "El mayor tesoro de la cripta es salir con vida para contarlo.",
    "Piensa antes de cada paso: en la cripta, el tiempo también es un enemigo.",
)
_SEGUNDOS_POR_FRASE = 7.0
_FUNDIDO = 0.8
_BRASAS = 46
_COLOR_LLAMA = (245, 150, 50)


class PantallaTitulo(_PantallaCripta):

    def __init__(self, vista_arcade):
        super().__init__(vista_arcade)
        self._inicio = time.perf_counter()
        self._primera_frase = random.Random().randrange(len(FRASES))
        self._brasas = ListaEnlazada()      # (x, y0, velocidad, fase, tamaño)
        self._textos = ListaEnlazada()      # arcade.Text fijos
        self._frase = None                  # arcade.Text de la frase actual
        self._indice_frase = -1
        self._entrar = None                 # arcade.Text de "Presiona ENTER"
        self._antorchas = ListaEnlazada()   # (x, y) de cada antorcha
        self._geometria = None

    @property
    def frase_actual(self) -> str:
        return self._frase.text if self._frase is not None else ""

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar()

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("entrar"))

    # ------------------------------------------------------------------
    # Armado (una vez)
    # ------------------------------------------------------------------

    def _armar(self) -> None:
        ancho, alto = self.window.width, self.window.height
        razon = self.window.get_pixel_ratio()
        escala = max(1, round(2.7 * razon))
        ancho_px, alto_px = int(ancho * razon), int(alto * razon)
        columnas, filas, fila_piso, columna_puerta = texturas.geometria_titulo(
            ancho_px, alto_px, escala)
        baldosa = 16 * escala / razon                    # una baldosa en px lógicos
        self._fondo = (ancho_px, alto_px, escala)
        centro_puerta = (columna_puerta + 1) * baldosa
        piso = alto - fila_piso * baldosa                # y donde empieza el piso
        self._geometria = (baldosa, centro_puerta, piso)
        altura_antorcha = alto - (fila_piso - 2.6) * baldosa
        for lado in (-1, 1):
            self._antorchas.agregar_al_final((centro_puerta + lado * 2.9 * baldosa,
                                              altura_antorcha))

        azar = random.Random(11)
        for _ in range(_BRASAS):
            self._brasas.agregar_al_final((azar.uniform(0, ancho), azar.uniform(0, alto),
                                           azar.uniform(14, 38), azar.uniform(0, 6.3),
                                           azar.choice((3, 3, 4, 5))))

        textos = ListaEnlazada()
        sombra, frente = estilo.titulo("CRIPTA", ancho / 2, alto - alto * 0.13,
                                       max(28, int(alto * 0.1)))
        textos.agregar_al_final(sombra)
        textos.agregar_al_final(frente)
        textos.agregar_al_final(estilo.texto(
            "Bienvenido, aventurero", ancho / 2, alto - alto * 0.235, max(12, int(alto * 0.03)),
            estilo.TEXTO, anchor_x="center", anchor_y="center", bold=True))
        textos.agregar_al_final(estilo.texto(
            "Desciende a la cripta, enfrenta a sus guardianes y encuentra la salida.",
            ancho / 2, alto - alto * 0.285, max(10, int(alto * 0.019)), estilo.TEXTO_SUAVE,
            anchor_x="center", anchor_y="center"))
        textos.agregar_al_final(estilo.texto(
            "Proyecto de Estructuras de Datos II · Ciclo 2026", ancho / 2, 14, 10,
            estilo.TEXTO_SUAVE, anchor_x="center", anchor_y="center"))
        self._textos = textos
        self._frase = arcade.Text("", ancho / 2, alto * 0.205, estilo.TEXTO,
                                  max(11, int(alto * 0.022)), anchor_x="center",
                                  anchor_y="center", italic=True)
        self._entrar = estilo.texto("Presiona ENTER para entrar", ancho / 2, alto * 0.095,
                                    max(12, int(alto * 0.026)), estilo.DORADO,
                                    anchor_x="center", anchor_y="center", bold=True)
        self._actualizar_frase(0.0)

    def _actualizar_frase(self, t: float) -> float:
        """Cambia de frase cada _SEGUNDOS_POR_FRASE y devuelve su opacidad
        (0 a 1) para el fundido de entrada y salida."""
        numero = int(t // _SEGUNDOS_POR_FRASE)
        indice = (self._primera_frase + numero) % len(FRASES)
        if indice != self._indice_frase:
            self._indice_frase = indice
            self._frase.text = f"“{FRASES[indice]}”"
        dentro = t - numero * _SEGUNDOS_POR_FRASE
        if dentro < _FUNDIDO:
            return dentro / _FUNDIDO
        if dentro > _SEGUNDOS_POR_FRASE - _FUNDIDO:
            return max(0.0, (_SEGUNDOS_POR_FRASE - dentro) / _FUNDIDO)
        return 1.0

    # ------------------------------------------------------------------
    # Dibujo (cada cuadro)
    # ------------------------------------------------------------------

    def on_draw(self) -> None:
        self.clear()
        t = time.perf_counter() - self._inicio
        ancho, alto = self.window.width, self.window.height
        ancho_px, alto_px, escala = self._fondo
        arcade.draw_texture_rect(texturas.fondo_titulo(ancho_px, alto_px, escala),
                                 arcade.LBWH(0, 0, ancho, alto), pixelated=True)
        for x, y in self._antorchas:
            self._dibujar_antorcha(x, y, t)
        self._dibujar_personajes(t)
        # viñeta: los bordes se pierden en la oscuridad
        arcade.draw_texture_rect(texturas.oscuridad(True),
                                 arcade.LBWH(-ancho * 0.2, -alto * 0.2, ancho * 1.4, alto * 1.4),
                                 alpha=170)
        self._dibujar_brasas(t, alto)
        arcade.draw_lrbt_rectangle_filled(0, ancho, 0, 28, (8, 6, 7, 220))   # franja de créditos
        for texto in self._textos:
            texto.draw()
        self._dibujar_frase_y_entrar(t, ancho, alto)

    def _dibujar_antorcha(self, x: float, y: float, t: float) -> None:
        baldosa = self._geometria[0]
        parpadeo = math.sin(t * 9 + x) * 0.5 + math.sin(t * 23 + x * 0.3) * 0.3
        tam = baldosa * (5.2 + parpadeo * 0.25)
        arcade.draw_texture_rect(texturas.resplandor(), arcade.XYWH(x, y, tam, tam),
                                 alpha=int(max(0, min(255, 190 + parpadeo * 50))))
        # soporte de hierro y mango
        arcade.draw_lrbt_rectangle_filled(x - baldosa * 0.22, x + baldosa * 0.22,
                                          y - baldosa * 0.62, y - baldosa * 0.5, (70, 66, 70))
        arcade.draw_line(x, y - baldosa * 0.55, x, y + baldosa * 0.1, (120, 78, 36),
                         max(3, baldosa * 0.14))
        r = baldosa * 0.32
        escala_llama = 1 + math.sin(t * 17 + x) * 0.14 + math.sin(t * 7.3) * 0.08
        mecer = math.sin(t * 5.1 + x) * r * 0.3
        base = y + baldosa * 0.12
        arcade.draw_triangle_filled(x - r * 0.7, base, x + r * 0.7, base,
                                    x + mecer, base + r * 2.2 * escala_llama, (230, 90, 25))
        arcade.draw_triangle_filled(x - r * 0.45, base, x + r * 0.45, base,
                                    x + mecer * 0.6, base + r * 1.6 * escala_llama, (250, 165, 45))
        arcade.draw_circle_filled(x, base + r * 0.25, r * 0.45, (255, 228, 120))

    def _dibujar_personajes(self, t: float) -> None:
        baldosa, centro, piso = self._geometria
        # el héroe frente a la puerta, con la skin elegida en el menú
        alto_heroe = baldosa * 2.4
        ancho_heroe = alto_heroe * 16 / 28
        y_heroe = piso - baldosa * 0.95
        arcade.draw_ellipse_filled(centro, y_heroe - alto_heroe * 0.46, ancho_heroe * 1.1,
                                   baldosa * 0.3, (0, 0, 0, 130))
        arcade.draw_texture_rect(texturas.heroe(self._vista_arcade.skin, t, False),
                                 arcade.XYWH(centro, y_heroe, ancho_heroe, alto_heroe),
                                 pixelated=True)
        # el esqueleto guardián a la izquierda y una rata a la derecha
        lado = baldosa * 1.5
        x_esqueleto = centro - baldosa * 4.6
        arcade.draw_ellipse_filled(x_esqueleto, y_heroe - lado * 0.45, lado * 0.8, baldosa * 0.25,
                                   (0, 0, 0, 120))
        arcade.draw_texture_rect(texturas.esqueleto(t), arcade.XYWH(x_esqueleto, y_heroe - lado * 0.1,
                                                                   lado, lado), pixelated=True)
        lado_rata = baldosa * 1.6
        x_rata = centro + baldosa * 4.4 + math.sin(t * 0.9) * baldosa * 0.4
        arcade.draw_texture_rect(texturas.rata(t), arcade.XYWH(x_rata, y_heroe - lado_rata * 0.05,
                                                               lado_rata, lado_rata),
                                 pixelated=True)

    def _dibujar_brasas(self, t: float, alto: float) -> None:
        for x, y0, velocidad, fase, tamano in self._brasas:
            y = (y0 + t * velocidad) % alto
            x_actual = x + math.sin(t * 1.3 + fase) * 10
            # se apagan a medida que suben
            alfa = int(230 * (1 - y / alto) + 40 * math.sin(t * 3 + fase))
            if alfa <= 0:
                continue
            arcade.draw_lrbt_rectangle_filled(x_actual, x_actual + tamano, y, y + tamano,
                                              (_COLOR_LLAMA[0], _COLOR_LLAMA[1], _COLOR_LLAMA[2],
                                               min(255, alfa)))

    def _dibujar_frase_y_entrar(self, t: float, ancho: float, alto: float) -> None:
        opacidad = self._actualizar_frase(t)
        mitad = min(ancho * 0.44, self._frase.content_width / 2 + 28)
        y = self._frase.y
        arcade.draw_lrbt_rectangle_filled(ancho / 2 - mitad, ancho / 2 + mitad, y - 24, y + 24,
                                          (16, 11, 12, 200))
        arcade.draw_lrbt_rectangle_outline(ancho / 2 - mitad, ancho / 2 + mitad, y - 24, y + 24,
                                           estilo.DORADO_OSCURO, 2)
        self._frase.color = (estilo.TEXTO[0], estilo.TEXTO[1], estilo.TEXTO[2],
                             int(255 * opacidad))
        self._frase.draw()
        # fondo para "Presiona ENTER"
        y_entrar = self._entrar.y
        mitad_entrar = self._entrar.content_width / 2 + 30
        arcade.draw_lrbt_rectangle_filled(ancho / 2 - mitad_entrar, ancho / 2 + mitad_entrar,
                                          y_entrar - 20, y_entrar + 20, (16, 11, 12, 210))
        arcade.draw_lrbt_rectangle_outline(ancho / 2 - mitad_entrar, ancho / 2 + mitad_entrar,
                                           y_entrar - 20, y_entrar + 20, estilo.DORADO, 2)
        # "Presiona ENTER" late suavemente
        pulso = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 3.2))
        self._entrar.color = (estilo.DORADO[0], estilo.DORADO[1], estilo.DORADO[2],
                              int(255 * pulso))
        self._entrar.draw()
