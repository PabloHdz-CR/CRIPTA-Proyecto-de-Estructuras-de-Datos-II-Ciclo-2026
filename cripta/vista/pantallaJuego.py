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

Al ser un juego por turnos (no hace falta redibujar muchas veces por
segundo sin que nada cambie), VistaArcade arma una PantallaJuego nueva cada
vez que llega un EstadoVista (igual que con PantallaMenu), en vez de
mantener una sola instancia y actualizarla -- más simple, y reconstruir
unos pocos arcade.Text por turno no tiene costo real.
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from .comando import Comando
from .estadoVista import SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE
from .pantallaBase import _PantallaCripta

_MARGEN = 20


class PantallaJuego(_PantallaCripta):

    def __init__(self, vista_arcade, estado):
        super().__init__(vista_arcade)
        self._estado = estado
        self._modo = "normal"            # "normal" o "objetivo"
        self._verbo_objetivo = None       # "atacar"/"usar"/"equipar"/"soltar"
        self._lista_objetivo = None       # ListaEnlazada: enemigos o inventario
        self._cursor_objetivo = 0
        self._textos = ListaEnlazada()    # de arcade.Text, presentación pura

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
        for texto in self._textos:
            texto.draw()

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

    def _tecla_en_modo_normal(self, symbol, modifiers) -> None:
        if symbol == arcade.key.SPACE:
            self._vista_arcade._encolar(Comando("esperar"))
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

    # -- armado de los textos --

    def _armar_textos(self) -> None:
        if self._modo == "objetivo":
            self._armar_textos_objetivo()
        else:
            self._armar_textos_normal()

    def _armar_textos_normal(self) -> None:
        estado = self._estado
        alto = self.window.height
        textos = ListaEnlazada()
        y = alto - _MARGEN

        def agregar(texto_str, tamano=14, color=arcade.color.WHITE):
            nonlocal y
            textos.agregar_al_final(arcade.Text(texto_str, _MARGEN, y, color, tamano))
            y -= tamano + 8

        agregar(f"Sala: {estado.sala.nombre}", 20)
        agregar(self._texto_salidas(), 14, arcade.color.LIGHT_GRAY)
        agregar(
            f"Vida: {estado.jugador.vida}/{estado.jugador.vida_max}   "
            f"Ataque: {estado.jugador.ataque_efectivo}   "
            f"Defensa: {estado.jugador.defensa_efectiva}   "
            f"Velocidad: {estado.jugador.velocidad}")
        antorcha = "encendida" if estado.jugador.antorcha_encendida else "apagada"
        agregar(
            f"Antorcha: {antorcha}   Acciones: {estado.jugador.acciones}   "
            f"Enemigos derrotados: {estado.jugador.enemigos_derrotados}",
            14, arcade.color.LIGHT_GRAY)
        agregar(self._texto_efectos(), 14, arcade.color.LIGHT_GRAY)
        agregar(self._texto_enemigos(), 14, arcade.color.LIGHT_GRAY)
        agregar(self._texto_objetos_suelo(), 14, arcade.color.LIGHT_GRAY)
        agregar(self._texto_inventario(), 14, arcade.color.LIGHT_GRAY)
        agregar("Comandos: A: atacar   U: usar   Q: equipar   S: soltar",
                12, arcade.color.LIGHT_GRAY)
        agregar("Mensajes:", 14)
        for mensaje in estado.mensajes:
            agregar(mensaje, 12, arcade.color.LIGHT_GRAY)

        self._textos = textos

    def _armar_textos_objetivo(self) -> None:
        alto = self.window.height
        textos = ListaEnlazada()
        y = alto - _MARGEN

        def agregar(texto_str, tamano=14, color=arcade.color.WHITE):
            nonlocal y
            textos.agregar_al_final(arcade.Text(texto_str, _MARGEN, y, color, tamano))
            y -= tamano + 8

        agregar(f"Elegir objetivo para: {self._verbo_objetivo}", 20)
        agregar("Flechas: elegir   ENTER: confirmar   ESC: cancelar",
                14, arcade.color.LIGHT_GRAY)
        for indice in range(len(self._lista_objetivo)):
            objetivo = self._lista_objetivo.obtener(indice)
            color = arcade.color.YELLOW if indice == self._cursor_objetivo else arcade.color.WHITE
            agregar(self._texto_fila_objetivo(objetivo), 16, color)

        self._textos = textos

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