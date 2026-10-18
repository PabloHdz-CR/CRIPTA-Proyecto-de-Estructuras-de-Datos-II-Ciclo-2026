"""PantallaFin: resultado de la partida que acaba de terminar (§10.2, Paso 7).

Muestra el resultado y dos recuadros: "Tu partida" (acciones, enemigos,
tiempo) y "Red y caché", el mismo resumen que ReporteFinal imprime en la
terminal (§5.1). Si el resultado no trae esos datos (p. ej. armado por
--replay), el segundo recuadro no se dibuja.

Si hay un log de la partida, R pide verla en replay (Comando("ver_replay")).
Cuando el resultado viene de un replay, la pantalla lo dice y muestra si el
replay llegó exactamente al mismo final que la partida original.

Solo lectura, igual que Puntajes: ENTER vuelve al menú (Comando("volver"));
ESCAPE sigue siendo "salir" (D45).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo
from .comando import Comando
from .pantallaBase import _PantallaCripta

RESULTADO_VICTORIA = "victoria"
RESULTADO_DERROTA = "derrota"


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
        estilo.dibujar_fondo(self.window)
        for izq, der, abajo, arriba in self._recuadros:
            estilo.dibujar_panel(izq, der, abajo, arriba, color_borde=self._color_borde())
        for texto in self._textos:
            texto.draw()

    def _color_borde(self):
        if self._es_victoria():
            return estilo.DORADO
        if self._resultado.resultado == RESULTADO_DERROTA:
            return (170, 50, 50)
        return (120, 110, 100)

    def _es_victoria(self) -> bool:
        return self._resultado.resultado == RESULTADO_VICTORIA

    def tecla_propia(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self._vista_arcade._encolar(Comando("volver"))
        elif symbol == arcade.key.R and self._resultado.puede_ver_replay:
            self._vista_arcade._encolar(Comando("ver_replay"))

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
        y = alto - alto * 0.06
        if resultado.es_replay:
            agregar("REPLAY", centro, y, 14, estilo.TEXTO_SUAVE, bold=True)
            y -= 26
        if es_victoria:
            titulo, color, frase = "¡VICTORIA!", estilo.DORADO, "Escapaste de la cripta."
        elif resultado.resultado == RESULTADO_DERROTA:
            titulo, color, frase = "DERROTA", estilo.ROJO, "La cripta te ha reclamado."
        else:
            titulo, color, frase = ("FIN DEL REGISTRO", estilo.TEXTO,
                                    "La partida grabada no había terminado.")
        agregar(titulo, centro, y, 34, color, bold=True)
        y -= 52
        agregar(frase, centro, y, 14, estilo.TEXTO_SUAVE)
        y -= 30
        if resultado.es_replay:
            if resultado.coincide is True:
                agregar("El replay llegó exactamente al mismo final que la partida.",
                        centro, y, 14, estilo.VERDE, bold=True)
            elif resultado.coincide is False:
                agregar("El replay terminó distinto a la partida: el log no la reproduce.",
                        centro, y, 14, estilo.ROJO, bold=True)
            else:
                agregar("Replay de una partida grabada (sin resultado con qué compararlo).",
                        centro, y, 13, estilo.TEXTO_SUAVE)
            y -= 30
        y -= 10

        filas_partida = (
            ("Acciones", str(resultado.acciones)),
            ("Enemigos derrotados", str(resultado.enemigos_derrotados)),
            ("Tiempo", str(resultado.tiempo_final)),
        )
        titulo_recuadro = "La partida reproducida" if resultado.es_replay else "Tu partida"
        y = self._recuadro(textos, recuadros, agregar, titulo_recuadro, filas_partida,
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

        # Un replay vuelve a donde se pidió (menú o puntajes): por eso dice
        # solo "volver".
        ayuda = "ENTER: volver" if resultado.es_replay else "ENTER: volver al menú"
        if resultado.puede_ver_replay:
            ayuda += "   R: ver de nuevo" if resultado.es_replay else "   R: ver el replay"
        ayuda += "   ESC: volver" if resultado.es_replay else "   ESC: salir"
        agregar(ayuda, centro, 40, 13, estilo.TEXTO_SUAVE)
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
        agregar(titulo, centro, arriba - 10, 16, estilo.DORADO, bold=True)
        y = arriba - 44
        for etiqueta, valor in filas:
            agregar(etiqueta, izq + 20, y, 14, estilo.TEXTO_SUAVE, anchor_x="left")
            agregar(valor, der - 20, y, 14, estilo.TEXTO, anchor_x="right", bold=True)
            y -= alto_fila
        return abajo
