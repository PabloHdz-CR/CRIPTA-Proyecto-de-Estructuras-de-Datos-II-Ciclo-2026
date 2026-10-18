"""PantallaJuego: la pantalla principal del juego (§10.2, Pasos 5a y 5b).

Dibuja el EstadoVista completo que arma el Controlador cada turno: sala,
salidas, enemigos y objetos en el suelo, estado del jugador, inventario,
efectos y mensajes. Entiende moverse (flechas) y esperar (espacio) en modo
normal.

Atacar/usar/equipar/soltar necesitan elegir un objetivo (un enemigo o un
objeto del inventario), así que la pantalla tiene un segundo modo, "modo
objetivo" (ver DECISIONES.md, entrada "elegir objetivo"): A/U/Q/S entran a
ese modo con la lista que corresponda; dentro de él las flechas mueven un
cursor sobre esa lista, ENTER confirma (arma el Comando y vuelve a modo
normal) y ESCAPE cancela (vuelve a modo normal SIN encolar nada -- distinto
de lo que hace ESCAPE en modo normal, donde sale del juego; por eso esta
clase sobreescribe on_key_press en vez de dejar que todo pase por
_PantallaCripta).

La sala se dibuja con figuras (DibujoSala): muros, puertas, enemigos,
objetos del suelo y el jugador. En modo objetivo, el enemigo u objeto bajo
el cursor se marca también en el dibujo.

Modo replay: si el EstadoVista trae `replay`, la pantalla muestra una
partida grabada y las teclas cambian: Espacio pausa o continúa, flecha
derecha avanza un paso, +/- (o flechas arriba/abajo) cambian la velocidad
y ESC vuelve al menú. Las teclas de juego no hacen nada.

Al ser un juego por turnos (no hace falta redibujar muchas veces por
segundo sin que nada cambie), VistaArcade arma una PantallaJuego nueva cada
vez que llega un EstadoVista (igual que con PantallaMenu), en vez de
mantener una sola instancia y actualizarla -- más simple, y reconstruir
unos pocos arcade.Text por turno no tiene costo real.
"""
from __future__ import annotations

import time

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .dibujoSala import DibujoSala, dibujar_barra, dibujar_objeto, valor_animado
from .estadoVista import SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE
from .pantallaBase import _PantallaCripta

_MARGEN = 20
_MENSAJES_VISIBLES = 5


def _direccion_de_flecha(symbol):
    """Flecha -> "N"/"S"/"E"/"O", o None si no es flecha. Cadena de if (no
    dict, §7): 4 comparaciones, O(1)."""
    if symbol == arcade.key.UP:
        return "N"
    if symbol == arcade.key.DOWN:
        return "S"
    if symbol == arcade.key.RIGHT:
        return "E"
    if symbol == arcade.key.LEFT:
        return "O"
    return None


class PantallaJuego(_PantallaCripta):

    def __init__(self, vista_arcade, estado, anterior=None):
        super().__init__(vista_arcade)
        self._estado = estado
        self._anterior = anterior         # EstadoVista del turno previo (animaciones)
        self._inicio = time.perf_counter()
        self._modo = "normal"            # "normal" o "objetivo"
        self._verbo_objetivo = None       # "atacar"/"usar"/"equipar"/"soltar"
        self._lista_objetivo = None       # ListaEnlazada: enemigos o inventario
        self._cursor_objetivo = 0
        self._textos = ListaEnlazada()    # de arcade.Text, presentación pura
        self._aviso = None                # último error/aviso del Controlador
        self._dibujo = None               # DibujoSala, se arma con el layout
        self._iconos = ListaEnlazada()    # de (clase, x, y, radio): íconos del panel
        self._barra_jugador = None        # (izq, abajo, ancho, alto)
        self._hud_replay = None           # (izq, der, abajo, arriba, avance) en modo replay

    def mostrar_aviso(self, texto: str) -> None:
        """Un rechazo o aviso (p. ej. "No hay salida hacia el S") se dibuja
        hasta el próximo EstadoVista, que trae una PantallaJuego nueva."""
        self._aviso = texto
        if self.window is not None:
            self._armar_textos()

    @property
    def modo(self) -> str:
        return self._modo

    @property
    def verbo_objetivo(self):
        return self._verbo_objetivo

    @property
    def cursor_objetivo(self) -> int:
        return self._cursor_objetivo

    def on_show_view(self) -> None:
        super().on_show_view()
        self._armar_textos()

    def on_draw(self) -> None:
        self.clear()
        t = time.perf_counter() - self._inicio
        if self._dibujo is not None:
            enemigo, objeto = self._resaltados()
            self._dibujo.dibujar(t, enemigo, objeto)
        if self._barra_jugador is not None:
            izq, abajo, ancho, alto = self._barra_jugador
            jugador = self._estado.jugador
            previa = self._anterior.jugador.vida if self._anterior is not None else None
            dibujar_barra(izq, abajo, ancho, alto, valor_animado(previa, jugador.vida, t),
                          jugador.vida_max)
        for clase, x, y, radio in self._iconos:
            dibujar_objeto(clase, x, y, radio)
        if self._hud_replay is not None:
            izq, der, abajo, arriba, avance = self._hud_replay
            arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, (40, 28, 10, 220))
            arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, (255, 200, 90), 2)
            # barra de avance del replay
            arcade.draw_lrbt_rectangle_filled(izq + 6, izq + 6 + (der - izq - 12) * avance,
                                              abajo + 5, abajo + 9, (255, 200, 90))
        for texto in self._textos:
            texto.draw()

    def _resaltados(self):
        """(índice de enemigo, índice de objeto del suelo) bajo el cursor
        del modo objetivo, para marcarlo también en el dibujo; -1 si no."""
        if self._modo != "objetivo":
            return -1, -1
        if self._verbo_objetivo == "atacar":
            return self._cursor_objetivo, -1
        if self._verbo_objetivo == "recoger":
            return -1, self._cursor_objetivo
        return -1, -1

    def on_key_press(self, symbol, modifiers) -> None:
        # En modo objetivo, ESCAPE cancela la selección (vuelve a modo
        # normal), no sale del juego -- por eso no se deja pasar a la clase
        # base, que SIEMPRE interpreta ESCAPE como "salir".
        if self._modo == "objetivo" and symbol == arcade.key.ESCAPE:
            self._salir_modo_objetivo()
            return
        super().on_key_press(symbol, modifiers)

    def tecla_propia(self, symbol, modifiers) -> None:
        if self._modo == "objetivo":
            self._tecla_en_modo_objetivo(symbol, modifiers)
        else:
            self._tecla_en_modo_normal(symbol, modifiers)

    # -- modo normal --

    def _tecla_en_replay(self, symbol) -> None:
        if symbol == arcade.key.SPACE:
            self._vista_arcade._encolar(Comando("replay_pausa"))
        elif symbol == arcade.key.RIGHT:
            self._vista_arcade._encolar(Comando("replay_paso"))
        elif symbol in (arcade.key.PLUS, arcade.key.EQUAL, arcade.key.NUM_ADD, arcade.key.UP):
            self._vista_arcade._encolar(Comando("replay_velocidad", ("+",)))
        elif symbol in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT, arcade.key.DOWN):
            self._vista_arcade._encolar(Comando("replay_velocidad", ("-",)))

    def _tecla_en_modo_normal(self, symbol, modifiers) -> None:
        if self._estado.replay is not None:
            self._tecla_en_replay(symbol)
            return
        # Shift + flecha abre la puerta en esa dirección (con la llave del
        # inventario); la flecha sola se mueve.
        if modifiers & arcade.key.MOD_SHIFT:
            direccion = _direccion_de_flecha(symbol)
            if direccion is not None:
                self._vista_arcade._encolar(Comando("abrir", (direccion,)))
                return
        if symbol == arcade.key.SPACE:
            self._vista_arcade._encolar(Comando("esperar"))
        elif symbol == arcade.key.R:
            self._entrar_modo_objetivo("recoger", self._estado.sala.objetos)
        elif symbol == arcade.key.P:
            self._vista_arcade._encolar(Comando("pergamino"))
        elif symbol == arcade.key.G:
            self._vista_arcade._encolar(Comando("guardar"))
        elif symbol == arcade.key.C:
            self._vista_arcade._encolar(Comando("cargar"))
        elif symbol == arcade.key.UP:
            self._vista_arcade._encolar(Comando("mover", ("N",)))
        elif symbol == arcade.key.DOWN:
            self._vista_arcade._encolar(Comando("mover", ("S",)))
        elif symbol == arcade.key.RIGHT:
            self._vista_arcade._encolar(Comando("mover", ("E",)))
        elif symbol == arcade.key.LEFT:
            self._vista_arcade._encolar(Comando("mover", ("O",)))
        elif symbol == arcade.key.A:
            self._entrar_modo_objetivo("atacar", self._estado.sala.enemigos)
        elif symbol == arcade.key.U:
            self._entrar_modo_objetivo("usar", self._estado.inventario.objetos)
        elif symbol == arcade.key.Q:
            self._entrar_modo_objetivo("equipar", self._estado.inventario.objetos)
        elif symbol == arcade.key.S:
            self._entrar_modo_objetivo("soltar", self._estado.inventario.objetos)

    # -- modo objetivo --

    def _entrar_modo_objetivo(self, verbo: str, lista) -> None:
        """No entra a modo objetivo si la lista está vacía (atacar sin
        enemigos, o usar/equipar/soltar con el inventario vacío): no hay
        nada que elegir."""
        if lista.esta_vacia():
            return
        self._modo = "objetivo"
        self._verbo_objetivo = verbo
        self._lista_objetivo = lista
        self._cursor_objetivo = 0
        self._armar_textos()

    def _tecla_en_modo_objetivo(self, symbol, modifiers) -> None:
        if symbol == arcade.key.UP:
            self._mover_cursor_objetivo(-1)
        elif symbol == arcade.key.DOWN:
            self._mover_cursor_objetivo(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            objetivo = self._lista_objetivo.obtener(self._cursor_objetivo)
            if self._verbo_objetivo == "atacar":
                argumento = objetivo.etiqueta     # TraductorComandos resuelve por etiqueta
            else:
                argumento = objetivo.id_objeto    # ...y por id_instancia para el inventario
            self._vista_arcade._encolar(Comando(self._verbo_objetivo, (argumento,)))
            self._salir_modo_objetivo()

    def _mover_cursor_objetivo(self, delta: int) -> None:
        cantidad = len(self._lista_objetivo)
        nuevo = self._cursor_objetivo + delta
        if 0 <= nuevo < cantidad:
            self._cursor_objetivo = nuevo
            self._armar_textos()

    def _salir_modo_objetivo(self) -> None:
        self._modo = "normal"
        self._verbo_objetivo = None
        self._lista_objetivo = None
        self._armar_textos()

    # -- armado del layout --
    #
    # La ventana se reparte en cuatro zonas (todas proporcionales al tamaño
    # de la ventana, así funciona igual en 1024x720 que en las pruebas de
    # 400x300):
    #   - encabezado: nombre de la sala y barra de vida del jugador;
    #   - izquierda: la sala dibujada (DibujoSala);
    #   - derecha: estadísticas, efectos, enemigos, suelo e inventario (o la
    #     lista para elegir objetivo, en modo objetivo);
    #   - abajo: aviso, últimos mensajes y la ayuda de teclas.

    def _armar_textos(self) -> None:
        ancho, alto = self.window.width, self.window.height
        arriba_contenido = alto - 80
        alto_inferior = 185
        lado = max(min(ancho * 0.5, arriba_contenido - alto_inferior - 10), 60)
        izq_mapa = _MARGEN
        abajo_mapa = arriba_contenido - lado
        if self._dibujo is None:
            # Se arma una sola vez: entrar/salir del modo objetivo o recibir
            # un aviso rearma los textos, pero no debe reiniciar el fondo ni
            # las animaciones.
            self._dibujo = DibujoSala(self._estado, izq_mapa, abajo_mapa, lado,
                                      self._anterior, self.window.get_pixel_ratio())
        self._iconos = ListaEnlazada()    # de (clase, x, y, radio)
        self._barra_jugador = (_MARGEN, alto - 62, min(260, ancho * 0.35), 16)

        textos = ListaEnlazada()
        self._agregar(textos, f"Sala: {self._estado.sala.nombre}", _MARGEN, alto - 14, 20,
                      arcade.color.WHITE, bold=True)
        jugador = self._estado.jugador
        self._agregar(textos, f"Vida {jugador.vida}/{jugador.vida_max}",
                      _MARGEN + self._barra_jugador[2] + 12, alto - 46, 13, arcade.color.WHITE)
        self._armar_hud_replay(textos, ancho, alto)

        x_panel = izq_mapa + lado + 30
        if self._modo == "objetivo":
            self._armar_panel_objetivo(textos, x_panel, arriba_contenido)
        else:
            self._armar_panel_normal(textos, x_panel, arriba_contenido)
        self._armar_zona_inferior(textos, alto_inferior)
        self._textos = textos

    def _armar_hud_replay(self, textos, ancho, alto) -> None:
        """Arriba a la derecha: REPLAY, el paso, la velocidad, si está en
        pausa y, debajo, qué partida es (quién, cripta, resultado, tiempo)."""
        replay = self._estado.replay
        self._hud_replay = None
        if replay is None:
            return
        estado = "en pausa" if replay.pausado else f"velocidad x{replay.velocidad}"
        contenido = f"REPLAY   paso {replay.paso}/{replay.total}   {estado}"
        derecha = ancho - _MARGEN - 12
        texto = arcade.Text(contenido, derecha, alto - 20, (255, 220, 120), 14,
                            anchor_x="right", anchor_y="top", bold=True)
        textos.agregar_al_final(texto)
        ancho_hud = texto.content_width
        abajo = alto - 60
        if replay.titulo:
            subtitulo = arcade.Text(replay.titulo, derecha, alto - 44, (235, 215, 170), 11,
                                    anchor_x="right", anchor_y="top")
            textos.agregar_al_final(subtitulo)
            ancho_hud = max(ancho_hud, subtitulo.content_width)
            abajo = alto - 76
        self._hud_replay = (ancho - _MARGEN - ancho_hud - 24, ancho - _MARGEN, abajo,
                            alto - 10, replay.paso / replay.total if replay.total else 1.0)

    def _agregar(self, textos, texto_str, x, y, tamano=13, color=arcade.color.LIGHT_GRAY,
                 bold=False) -> None:
        textos.agregar_al_final(arcade.Text(texto_str, x, y, color, tamano,
                                            anchor_y="top", bold=bold))

    def _armar_panel_normal(self, textos, x, y) -> None:
        estado = self._estado
        jugador = estado.jugador
        antorcha = "encendida" if jugador.antorcha_encendida else "apagada"
        lineas = (
            (f"Ataque {jugador.ataque_efectivo}   Defensa {jugador.defensa_efectiva}   "
             f"Velocidad {jugador.velocidad}", arcade.color.WHITE),
            (f"Antorcha: {antorcha}   Acciones: {jugador.acciones}", arcade.color.LIGHT_GRAY),
            (f"Enemigos derrotados: {jugador.enemigos_derrotados}", arcade.color.LIGHT_GRAY),
            (self._texto_salidas(), arcade.color.LIGHT_GRAY),
            (self._texto_efectos(), arcade.color.LIGHT_GRAY),
            (self._texto_enemigos(), arcade.color.LIGHT_GRAY),
            (self._texto_objetos_suelo(), arcade.color.LIGHT_GRAY),
        )
        for texto_str, color in lineas:
            self._agregar(textos, texto_str, x, y, 13, color)
            y -= 22

        inventario = estado.inventario
        y -= 8
        self._agregar(textos, f"Inventario ({len(inventario.objetos)}/{inventario.capacidad})",
                      x, y, 14, arcade.color.WHITE, bold=True)
        y -= 24
        if inventario.objetos.esta_vacia():
            self._agregar(textos, "vacío", x, y, 13)
            return
        for indice, objeto in enumerate(inventario.objetos):
            marca = "> " if indice == inventario.indice_actual else "  "
            equipado = " [equipado]" if objeto.equipado else ""
            self._iconos.agregar_al_final((objeto.clase, x + 10, y - 8, 9))
            self._agregar(textos, f"{marca}{objeto.nombre}{equipado}", x + 26, y, 13,
                          arcade.color.WHITE if objeto.equipado else arcade.color.LIGHT_GRAY)
            y -= 22

    def _armar_panel_objetivo(self, textos, x, y) -> None:
        self._agregar(textos, f"Elegir objetivo para: {self._verbo_objetivo}", x, y, 16,
                      arcade.color.WHITE, bold=True)
        y -= 28
        self._agregar(textos, "Flechas: elegir   ENTER: confirmar   ESC: cancelar", x, y, 12)
        y -= 30
        for indice, objetivo in enumerate(self._lista_objetivo):
            color = arcade.color.YELLOW if indice == self._cursor_objetivo else arcade.color.WHITE
            if self._verbo_objetivo != "atacar":
                self._iconos.agregar_al_final((objetivo.clase, x + 10, y - 9, 10))
            self._agregar(textos, self._texto_fila_objetivo(objetivo), x + 26, y, 15, color)
            y -= 26

    def _armar_zona_inferior(self, textos, alto_inferior) -> None:
        y = alto_inferior - 4
        if self._aviso:
            self._agregar(textos, self._aviso, _MARGEN, y, 14, arcade.color.ORANGE, bold=True)
        y -= 24
        mensajes = self._estado.mensajes
        omitir = len(mensajes) - _MENSAJES_VISIBLES
        for indice, mensaje in enumerate(mensajes):
            if indice >= omitir:
                self._agregar(textos, mensaje, _MARGEN, y, 12)
                y -= 18
        if self._estado.replay is not None:
            self._agregar(textos, "Espacio: pausa / continuar   Flecha derecha: un paso   "
                          "+/- o flechas arriba/abajo: velocidad", _MARGEN, 46, 11)
            self._agregar(textos, "ESC: salir del replay", _MARGEN, 26, 11)
            return
        self._agregar(textos, "Flechas: moverse   Shift+flecha: abrir puerta   "
                      "Espacio: esperar   R: recoger   A: atacar", _MARGEN, 46, 11)
        self._agregar(textos, "U: usar   Q: equipar   S: soltar   P: pergamino   "
                      "G: guardar   C: cargar   ESC: salir", _MARGEN, 26, 11)

    def _texto_fila_objetivo(self, objetivo) -> str:
        if self._verbo_objetivo == "atacar":
            return f"{objetivo.etiqueta} ({objetivo.vida}/{objetivo.vida_max})"
        equipado = " [equipado]" if objetivo.equipado else ""
        return f"{objetivo.nombre}{equipado}"

    def _texto_salidas(self) -> str:
        partes = (self._texto_una_salida(s) for s in self._estado.sala.salidas)
        return "Salidas: " + "  ".join(parte for parte in partes if parte)

    def _texto_una_salida(self, salida) -> str:
        if salida is None:
            return ""
        if salida.estado == SALIDA_ABIERTA:
            descripcion = "abierta"
        elif salida.estado == SALIDA_CERRADA_CON_LLAVE:
            descripcion = "cerrada con llave"
        else:
            descripcion = "sin salida"
        return f"{salida.direccion}: {descripcion}"

    def _texto_efectos(self) -> str:
        if self._estado.efectos.esta_vacia():
            return "Efectos: ninguno"
        return "Efectos: " + ", ".join(e.descripcion for e in self._estado.efectos)

    def _texto_enemigos(self) -> str:
        if self._estado.sala.enemigos.esta_vacia():
            return "Enemigos: ninguno"
        return "Enemigos: " + ", ".join(
            f"{e.etiqueta} ({e.vida}/{e.vida_max})" for e in self._estado.sala.enemigos)

    def _texto_objetos_suelo(self) -> str:
        if self._estado.sala.objetos.esta_vacia():
            return "En el suelo: nada"
        return "En el suelo: " + ", ".join(o.nombre for o in self._estado.sala.objetos)

    def _texto_inventario(self) -> str:
        """Resumen de una línea del inventario (el panel lo dibuja fila por
        fila con íconos; esto queda para quien lo quiera en texto)."""
        inventario = self._estado.inventario
        if inventario.objetos.esta_vacia():
            return f"Inventario (0/{inventario.capacidad}): vacío"
        descripcion = ", ".join(
            self._texto_objeto_inventario(indice, objeto)
            for indice, objeto in enumerate(inventario.objetos))
        return f"Inventario ({len(inventario.objetos)}/{inventario.capacidad}): {descripcion}"

    def _texto_objeto_inventario(self, indice, objeto) -> str:
        marca = ">" if indice == self._estado.inventario.indice_actual else " "
        equipado = " [equipado]" if objeto.equipado else ""
        return f"{marca}{objeto.nombre}{equipado}"
