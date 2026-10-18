"""PantallaMenu: elegir cripta, nombre, replay, puntajes, benchmark (§10.2).

Lo que ControladorMenu necesita de esta pantalla: que el jugador recorra la
lista de criptas con las flechas y confirme con ENTER, que arma un Comando
"jugar" con el id de la cripta elegida -- la Vista no decide si eso es una
partida nueva o una cargada (trabajo de ControladorMenu). Además:
    N       escribir el nombre (ENTER confirma, ESC cancela) -> "cambiar_nombre"
    P       tabla de puntajes (ahí se elige qué partida ver en replay) -> "ver_puntajes"
    B       benchmark rápido                                 -> "benchmark"
    ESC     salir (lo atiende _PantallaCripta)

Se dibuja con el estilo de la cripta (estilo.py): fondo de baldosas de
0x72, tarjetas por cripta con su dificultad en calaveras, y a la derecha
el caballero con el nombre del jugador.

DECISIÓN: el replay se elige desde la tabla de puntajes, donde cada fila es
UNA partida (quién, cuándo terminó, resultado), y no desde aquí: una cripta
tiene muchas partidas y desde el menú no se sabría cuál se está viendo.

DECISIÓN: mientras se escribe el nombre, las letras van al nombre y NO se
interpretan como atajos (si no, escribir "Pablo" pediría los puntajes con
la P). Por eso esta clase sobreescribe on_key_press, igual que el modo
objetivo de PantallaJuego.

Todo lo que se dibuja se guarda en ListaEnlazada, no en listas de Python
(prueba_reglas.py revisa también vista/).
"""
from __future__ import annotations

import math
import time

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo, texturas
from .comando import Comando
from .pantallaBase import _PantallaCripta

LARGO_MAXIMO_NOMBRE = 16
_ALTO_TARJETA = 70
_SEPARACION = 10
_DURACION_AVISO = 4.0
_MAX_CALAVERAS = 5


class PantallaMenu(_PantallaCripta):

    def __init__(self, vista_arcade, criptas, nombre_jugador: str = "Jugador"):
        super().__init__(vista_arcade)
        self._criptas = criptas            # ListaEnlazada de CriptaVisible
        self._cantidad = len(criptas)
        self._indice = 0 if self._cantidad > 0 else -1
        self._nombre = nombre_jugador
        self._editando = False
        self._borrador = ""
        self._esperando_eco = False        # el on_text de la propia tecla N (ver on_text)
        self._aviso = None
        self._aviso_desde = 0.0
        self._inicio = time.perf_counter()
        self._primera = 0                  # primera tarjeta visible (desplazamiento)
        self._textos_fijos = ListaEnlazada()
        self._tarjetas = ListaEnlazada()   # (izq, der, abajo, arriba, indice, textos)
        self._texto_nombre = None
        self._texto_aviso = None
        self._titulo = None

    @property
    def indice_seleccionado(self) -> int:
        """Expuesto para que la prueba confirme el cursor."""
        return self._indice

    @property
    def editando_nombre(self) -> bool:
        return self._editando

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar()

    def mostrar_aviso(self, texto: str) -> None:
        self._aviso = texto
        self._aviso_desde = time.perf_counter()
        if self._texto_aviso is not None:
            self._texto_aviso.text = texto

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def on_key_press(self, symbol, modifiers) -> None:
        if self._editando:
            self._tecla_editando(symbol)
            return
        super().on_key_press(symbol, modifiers)

    def on_text(self, text) -> None:
        if not self._editando:
            return
        # DECISIÓN: pyglet manda on_key_press(N) y enseguida on_text("n") por
        # la misma tecla que abrió la edición. Se descarta ese eco: el primer
        # texto, solo si es una "n" y llega antes que cualquier otra tecla.
        # No depende del reloj (una ventana de tiempo fallaría en una
        # máquina lenta).
        eco = self._esperando_eco
        self._esperando_eco = False
        if eco and text.lower() == "n":
            return
        for caracter in text:
            if caracter.isprintable() and len(self._borrador) < LARGO_MAXIMO_NOMBRE:
                self._borrador += caracter
        self._refrescar_nombre()

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol == arcade.key.N:
            # El borrador empieza vacío: se escribe el nombre nuevo (el
            # actual queda de guía, en gris, hasta escribir algo).
            self._editando = True
            self._borrador = ""
            self._esperando_eco = True
            self._refrescar_nombre()
            return
        if symbol == arcade.key.B:
            self._vista_arcade._encolar(Comando("benchmark"))
            return
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

    def _tecla_editando(self, symbol) -> None:
        self._esperando_eco = False      # otra tecla: el eco de la N ya pasó
        if symbol == arcade.key.ESCAPE:
            self._editando = False
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._editando = False
            self._nombre = self._borrador.strip()[:LARGO_MAXIMO_NOMBRE].strip() or self._nombre
            self._vista_arcade._encolar(Comando("cambiar_nombre", (self._nombre,)))
        elif symbol == arcade.key.BACKSPACE:
            self._borrador = self._borrador[:-1]
        self._refrescar_nombre()

    def _mover_cursor(self, delta: int) -> None:
        nuevo = self._indice + delta
        if 0 <= nuevo < self._cantidad:
            self._indice = nuevo
            self._armar()

    # ------------------------------------------------------------------
    # Armado (una vez por cambio) y dibujo (cada cuadro)
    # ------------------------------------------------------------------

    def _armar(self) -> None:
        ancho, alto = self.window.width, self.window.height
        self._columna_izq = 40
        self._columna_der = ancho * 0.58
        self._tope_lista = alto - 150
        fijos = ListaEnlazada()
        self._titulo = estilo.titulo("CRIPTA", ancho / 2, alto - 58, 46)
        fijos.agregar_al_final(estilo.texto("Elige una cripta y entra si te atreves", ancho / 2,
                                            alto - 100, 13, estilo.TEXTO_SUAVE, anchor_x="center"))
        if self._cantidad == 0:
            fijos.agregar_al_final(estilo.texto(
                "No hay criptas disponibles. ESC para salir.", self._columna_izq,
                self._tope_lista - 30, 15, estilo.TEXTO_SUAVE))
        self._armar_tarjetas()
        self._armar_panel_jugador(fijos)
        self._textos_fijos = fijos
        self._texto_aviso = estilo.texto(self._aviso or "", ancho / 2, 22, 13, estilo.NARANJA,
                                         anchor_x="center")

    def _armar_tarjetas(self) -> None:
        tarjetas = ListaEnlazada()
        espacio = self._tope_lista - 50
        visibles = max(1, int(espacio // (_ALTO_TARJETA + _SEPARACION)))
        # Desplazamiento: la tarjeta elegida siempre queda a la vista.
        if self._indice >= self._primera + visibles:
            self._primera = self._indice - visibles + 1
        if self._indice < self._primera:
            self._primera = max(0, self._indice)
        izq, der = self._columna_izq, self._columna_der - 30
        arriba = self._tope_lista
        for indice, cripta in enumerate(self._criptas):
            if indice < self._primera or indice >= self._primera + visibles:
                continue
            abajo = arriba - _ALTO_TARJETA
            elegida = indice == self._indice
            textos = ListaEnlazada()
            textos.agregar_al_final(estilo.texto(
                cripta.nombre, izq + 44, arriba - 28, 17,
                estilo.DORADO if elegida else estilo.TEXTO, bold=True))
            textos.agregar_al_final(estilo.texto(
                f"{cripta.salas} salas", izq + 44, abajo + 14, 12, estilo.TEXTO_SUAVE))
            textos.agregar_al_final(estilo.texto(
                f"dificultad {cripta.dificultad}", der - 14, abajo + 14, 11,
                estilo.TEXTO_SUAVE, anchor_x="right"))
            tarjetas.agregar_al_final((izq, der, abajo, arriba, indice, cripta.dificultad, textos))
            arriba = abajo - _SEPARACION
        self._tarjetas = tarjetas

    def _armar_panel_jugador(self, fijos) -> None:
        ancho, alto = self.window.width, self.window.height
        izq, der = self._columna_der, ancho - 40
        self._panel_jugador = (izq, der, 60, self._tope_lista)
        centro = (izq + der) / 2
        fijos.agregar_al_final(estilo.texto("Tu héroe", centro, self._tope_lista - 26, 13,
                                            estilo.TEXTO_SUAVE, anchor_x="center"))
        self._centro_heroe = (centro, self._tope_lista - 120)
        self._texto_nombre = estilo.texto("", centro, self._tope_lista - 200, 18, estilo.DORADO,
                                          anchor_x="center", bold=True)
        self._caja_nombre = (izq + 24, der - 24, self._tope_lista - 214, self._tope_lista - 180)
        self._refrescar_nombre()
        acciones = (("ENTER", "Jugar la cripta elegida"), ("N", "Cambiar tu nombre"),
                    ("P", "Puntajes y replays"), ("B", "Benchmark de estructuras"),
                    ("ESC", "Salir"))
        self._teclas = ListaEnlazada()
        y = self._tope_lista - 252
        for tecla, descripcion in acciones:
            ancho_tecla = 22 + 9 * len(tecla)
            x_tecla = izq + 30 + ancho_tecla / 2
            self._teclas.agregar_al_final((x_tecla, y, ancho_tecla))
            fijos.agregar_al_final(estilo.texto(tecla, x_tecla, y, 11, estilo.TEXTO,
                                                anchor_x="center", anchor_y="center", bold=True))
            fijos.agregar_al_final(estilo.texto(descripcion, izq + 30 + ancho_tecla + 14, y, 13,
                                                estilo.TEXTO, anchor_y="center"))
            y -= 34

    def _refrescar_nombre(self) -> None:
        if self._texto_nombre is None:
            return
        if self._editando and self._borrador:
            self._texto_nombre.text = self._borrador
            self._texto_nombre.color = estilo.TEXTO
        elif self._editando:
            self._texto_nombre.text = self._nombre
            self._texto_nombre.color = estilo.TEXTO_APAGADO
        else:
            self._texto_nombre.text = self._nombre
            self._texto_nombre.color = estilo.DORADO

    def on_draw(self) -> None:
        self.clear()
        t = time.perf_counter() - self._inicio
        estilo.dibujar_fondo(self.window)
        sombra, frente = self._titulo
        sombra.draw()
        frente.draw()

        for izq, der, abajo, arriba, indice, dificultad, textos in self._tarjetas:
            elegida = indice == self._indice
            estilo.dibujar_panel(izq, der, abajo, arriba, resaltado=elegida)
            if elegida:
                # flecha que "late" al lado de la tarjeta elegida
                dx = math.sin(t * 5) * 3
                medio = (abajo + arriba) / 2
                arcade.draw_triangle_filled(izq + 14 + dx, medio + 9, izq + 14 + dx, medio - 9,
                                            izq + 28 + dx, medio, estilo.DORADO)
            for nivel in range(_MAX_CALAVERAS):
                # La calavera ocupa la parte de abajo de su baldosa de 16 px:
                # se dibuja grande y algo más arriba.
                x = izq + 150 + nivel * 26
                y = abajo + 26
                alfa = 255 if nivel < dificultad else 40
                arcade.draw_texture_rect(texturas.calavera(), arcade.XYWH(x, y, 34, 34),
                                         alpha=alfa, pixelated=True)
            for texto in textos:
                texto.draw()

        izq, der, abajo, arriba = self._panel_jugador
        estilo.dibujar_panel(izq, der, abajo, arriba)
        cx, cy = self._centro_heroe
        arcade.draw_ellipse_filled(cx, cy - 52, 64, 16, (0, 0, 0, 120))
        arcade.draw_texture_rect(texturas.caballero(t, False), arcade.XYWH(cx, cy, 64, 112),
                                 pixelated=True)
        caja_izq, caja_der, caja_abajo, caja_arriba = self._caja_nombre
        borde = estilo.DORADO if self._editando else (88, 70, 58)
        arcade.draw_lrbt_rectangle_filled(caja_izq, caja_der, caja_abajo, caja_arriba,
                                          (10, 8, 8, 230))
        arcade.draw_lrbt_rectangle_outline(caja_izq, caja_der, caja_abajo, caja_arriba, borde, 2)
        self._texto_nombre.y = caja_abajo + 10
        self._texto_nombre.draw()
        if self._editando and int(t * 2) % 2 == 0:
            # cursor parpadeante al final de lo escrito (o al inicio si no hay nada)
            if self._borrador:
                x = self._texto_nombre.x + self._texto_nombre.content_width / 2 + 3
            else:
                x = self._texto_nombre.x - self._texto_nombre.content_width / 2 - 3
            arcade.draw_line(x, caja_abajo + 7, x, caja_arriba - 7, estilo.TEXTO, 2)
        for x, y, ancho_tecla in self._teclas:
            estilo.dibujar_tecla(x, y, ancho_tecla)
        for texto in self._textos_fijos:
            texto.draw()
        if self._editando:
            self._texto_aviso.text = "Escribe tu nombre: ENTER confirma, ESC cancela"
            self._texto_aviso.color = estilo.TEXTO
            self._texto_aviso.draw()
        elif self._aviso and time.perf_counter() - self._aviso_desde < _DURACION_AVISO:
            self._texto_aviso.text = self._aviso
            self._texto_aviso.color = estilo.NARANJA
            self._texto_aviso.draw()
