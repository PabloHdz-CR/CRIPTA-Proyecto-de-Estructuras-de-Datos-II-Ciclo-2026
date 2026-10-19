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

La sala la dibuja DibujoSala (muros, puertas, enemigos, objetos y el
jugador) y todo lo de alrededor HudJuego (encabezado con la vida,
estadísticas, salidas, efectos, inventario, bitácora y controles). Esta
clase se queda con las teclas y los modos. En modo objetivo, el enemigo u
objeto bajo el cursor se marca también en el dibujo.

Modo replay: si el EstadoVista trae `replay`, la pantalla muestra una
partida grabada y las teclas cambian: Espacio pausa o continúa, flecha
derecha avanza un paso, flecha izquierda retrocede uno (y pausa), flecha
arriba sube la velocidad y flecha abajo la baja (+/- también sirven)
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

from . import estilo
from .comando import Comando
from .dibujoSala import DibujoSala
from .estadoVista import SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE
from .hudJuego import Geometria, HudJuego
from .pantallaBase import _PantallaCripta

# Orden de la vista del inventario que recorre la tecla O (§4.5, §10.2):
# "real" es el orden del inventario; los otros son vistas ordenadas.
ORDENES_INVENTARIO = ("real", "peso", "valor", "nombre")


def _orden_siguiente(actual) -> str:
    """El criterio que sigue a `actual` (None = real), dando la vuelta."""
    actual = actual if actual else "real"
    for indice, criterio in enumerate(ORDENES_INVENTARIO):
        if criterio == actual:
            return ORDENES_INVENTARIO[(indice + 1) % len(ORDENES_INVENTARIO)]
    return ORDENES_INVENTARIO[0]


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
        self._aviso = None                # último error/aviso del Controlador
        self._aviso_desde = 0.0           # cuándo llegó (el cartel se desvanece)
        self._dibujo = None               # DibujoSala, se arma una vez
        self._hud = None                  # HudJuego, se rearma al cambiar el modo o el aviso

    def mostrar_aviso(self, texto: str) -> None:
        """Un rechazo o aviso (p. ej. "No hay salida hacia el S") se dibuja
        hasta el próximo EstadoVista, que trae una PantallaJuego nueva."""
        self._aviso = texto
        self._aviso_desde = time.perf_counter()
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
        ahora = time.perf_counter()
        t = ahora - self._inicio
        estilo.dibujar_fondo(self.window)
        if self._dibujo is not None:
            enemigo, objeto = self._resaltados()
            self._dibujo.dibujar(t, enemigo, objeto)
        if self._hud is not None:
            self._hud.dibujar(t, ahora - self._aviso_desde)

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

    def _alternar_bitacora(self) -> None:
        """L: bitácora completa (últimos 20 mensajes, §4.8) o resumida.
        Presentación pura: no es un Comando."""
        self._vista_arcade.alternar_bitacora()
        self._armar_textos()

    def _tecla_en_replay(self, symbol) -> None:
        if symbol == arcade.key.L:
            self._alternar_bitacora()
        elif symbol == arcade.key.SPACE:
            self._vista_arcade._encolar(Comando("replay_pausa"))
        elif symbol == arcade.key.RIGHT:
            self._vista_arcade._encolar(Comando("replay_paso"))
        elif symbol == arcade.key.LEFT:
            self._vista_arcade._encolar(Comando("replay_atras"))
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
        if symbol == arcade.key.TAB:
            # Tab recorre el inventario hacia adelante; Shift+Tab hacia atrás.
            verbo = ("inventario_anterior" if modifiers & arcade.key.MOD_SHIFT
                     else "inventario_siguiente")
            self._vista_arcade._encolar(Comando(verbo))
        elif symbol == arcade.key.O:
            criterio = _orden_siguiente(self._estado.inventario.criterio_orden)
            self._vista_arcade._encolar(Comando("ordenar_inventario", (criterio,)))
        elif symbol == arcade.key.L:
            self._alternar_bitacora()
        elif symbol == arcade.key.SPACE:
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

    # -- armado --

    def _armar_textos(self) -> None:
        geometria = Geometria(self.window.width, self.window.height)
        if self._dibujo is None:
            # Se arma una sola vez: entrar/salir del modo objetivo o recibir
            # un aviso rearma el HUD, pero no debe reiniciar el fondo ni las
            # animaciones de la sala.
            self._dibujo = DibujoSala(self._estado, geometria.mapa_izq, geometria.mapa_abajo,
                                      geometria.lado_mapa, self._anterior,
                                      self.window.get_pixel_ratio(), self._vista_arcade.skin)
        self._hud = HudJuego(self._estado, self._anterior, geometria, self._modo,
                             self._verbo_objetivo, self._lista_objetivo, self._cursor_objetivo,
                             self._aviso, self._vista_arcade.bitacora_completa)

    # -- textos de una línea (los usan las pruebas de vista) --

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
