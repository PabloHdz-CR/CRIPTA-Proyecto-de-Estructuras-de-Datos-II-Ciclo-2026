"""HudJuego: todo lo que rodea a la sala en PantallaJuego (§10.2).

Encabezado (sala, tiempo, vida con corazón, antorcha y pergaminos),
columna derecha (estadísticas, salidas, efectos, lo que hay en la sala e
inventario, o la lista para elegir objetivo), bitácora y controles abajo,
y el cartel de aviso sobre el mapa. La sala en sí la dibuja DibujoSala.

DECISIÓN: separado de PantallaJuego para que la pantalla quede con las
teclas y los modos, y este módulo con la presentación. Igual que
DibujoSala, solo LEE el EstadoVista: no encola comandos.

DECISIÓN: el HUD se arma (textos y posiciones) cada vez que cambia algo
que se ve (un EstadoVista nuevo, entrar o salir del modo objetivo, un
aviso) y cada cuadro solo dibuja lo ya armado: O(elementos) por cuadro,
sin crear textos nuevos.

DECISIÓN: sin listas, dict ni lambda (D27). Lo que se dibuja se guarda en
ListaEnlazada de tuplas, y el tipo de figura se elige con una cadena de if.

La geometría es proporcional a la ventana; en ventanas muy chicas (las de
las pruebas, 400x300) los paneles que no caben simplemente no se dibujan.
"""
from __future__ import annotations

import math

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import estilo, texturas
from .dibujoSala import dibujar_barra, dibujar_objeto, valor_animado
from .estadoVista import SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE

_MARGEN = 20
_SEPARACION = 10
_DURACION_AVISO = 4.0
_MENSAJES_VISIBLES = 5          # en el panel de abajo (la L muestra los 20)
_MENSAJES_COMPLETOS = 20        # bitácora completa (§4.8)
_ROJO_SUAVE = (240, 140, 125)
_VERDE_SUAVE = (150, 215, 150)
_CELESTE = (120, 180, 240)

# Color de cada tipo de efecto (cadena de if en _color_efecto, no dict).
_COLOR_ANTORCHA = (245, 160, 60)
_COLOR_VENENO = (120, 200, 90)
_COLOR_VELOCIDAD = (110, 170, 245)
_COLOR_REGENERACION = (235, 110, 150)

_VERBOS = (("atacar", "Atacar: elige un enemigo"), ("usar", "Usar: elige un objeto"),
           ("equipar", "Equipar: elige un objeto"), ("soltar", "Soltar: elige un objeto"),
           ("recoger", "Recoger: elige del suelo"))


def _recortar(texto: str, maximo: int) -> str:
    if len(texto) <= maximo:
        return texto
    return texto[:max(1, maximo - 1)] + "…"


def _cabe(izq, der, abajo, arriba) -> bool:
    return der - izq > 8 and arriba - abajo > 8


def _titulo_verbo(verbo: str) -> str:
    for clave, titulo in _VERBOS:
        if clave == verbo:
            return titulo
    return f"Elige objetivo para: {verbo}"


def _color_efecto(tipo: str):
    if tipo == "antorcha":
        return _COLOR_ANTORCHA
    if tipo == "veneno":
        return _COLOR_VENENO
    if tipo == "velocidad":
        return _COLOR_VELOCIDAD
    if tipo == "regeneracion":
        return _COLOR_REGENERACION
    return estilo.TEXTO_SUAVE


def _color_mensaje(mensaje: str, es_ultimo: bool):
    """Daño recibido en rojo, logros (ataques, derrotas) en dorado, hallazgos
    en verde."""
    texto = mensaje.lower()
    if texto.startswith("atacas"):
        return estilo.DORADO                  # el daño que hace el jugador es un logro
    if "daño" in texto or "muere" in texto and "jugador" in texto or "has caído" in texto:
        return _ROJO_SUAVE
    if "derrot" in texto or "muere" in texto or "escapas" in texto or "victoria" in texto:
        return estilo.DORADO
    if "recoges" in texto or "enciendes" in texto or "bebes" in texto or "te equipas" in texto:
        return _VERDE_SUAVE
    return estilo.TEXTO if es_ultimo else estilo.TEXTO_SUAVE


class Geometria:
    """Dónde va cada zona, proporcional a la ventana."""

    def __init__(self, ancho: float, alto: float):
        self.ancho, self.alto = ancho, alto
        self.encabezado = (_MARGEN, ancho - _MARGEN, alto - 78, alto - 8)
        arriba = alto - 90
        abajo = 172 if alto > 400 else alto * 0.3
        self.lado_mapa = max(min(ancho * 0.46, arriba - abajo), 60)
        self.mapa_izq = _MARGEN
        self.mapa_abajo = arriba - self.lado_mapa
        self.mapa_arriba = arriba
        self.columna = (self.mapa_izq + self.lado_mapa + 18, ancho - _MARGEN,
                        self.mapa_abajo, arriba)
        self.inferior = (_MARGEN, ancho - _MARGEN, 12, self.mapa_abajo - 12)


class HudJuego:

    def __init__(self, estado, anterior, geometria: Geometria, modo: str = "normal",
                 verbo_objetivo=None, lista_objetivo=None, cursor_objetivo: int = 0,
                 aviso=None, bitacora_completa: bool = False):
        self._estado = estado
        self._anterior = anterior
        self._g = geometria
        self._modo = modo
        self._verbo = verbo_objetivo
        self._lista = lista_objetivo
        self._cursor = cursor_objetivo
        self._aviso = aviso
        self._bitacora_completa = bitacora_completa
        self._superpuestos = ListaEnlazada()  # (izq, der, abajo, arriba): panel sobre el mapa
        self._textos_superpuestos = ListaEnlazada()
        self._paneles = ListaEnlazada()     # (izq, der, abajo, arriba, resaltado)
        self._textos = ListaEnlazada()      # arcade.Text
        self._figuras = ListaEnlazada()     # (tipo, a, b, c, d, e, f): ver _dibujar_figura
        self._barra_vida = None             # (izq, abajo, ancho, alto)
        self._corazon = None                # (x, y, lado)
        self._cartel = None                 # (izq, der, abajo, arriba, arcade.Text)
        self._hud_replay = None             # (izq, der, abajo, arriba, avance)
        self._armar()

    # ------------------------------------------------------------------
    # Armado
    # ------------------------------------------------------------------

    def _texto(self, contenido, x, y, tamano=12, color=estilo.TEXTO, anchor_x="left",
               anchor_y="center", bold=False) -> arcade.Text:
        texto = estilo.texto(contenido, x, y, tamano, color, anchor_x=anchor_x,
                             anchor_y=anchor_y, bold=bold)
        self._textos.agregar_al_final(texto)
        return texto

    def _panel(self, izq, der, abajo, arriba, titulo=None, resaltado=False) -> bool:
        if not _cabe(izq, der, abajo, arriba):
            return False
        self._paneles.agregar_al_final((izq, der, abajo, arriba, resaltado))
        if titulo:
            self._texto(titulo, izq + 12, arriba - 14, 11, estilo.DORADO, bold=True)
        return True

    def _figura(self, tipo, a=0.0, b=0.0, c=0.0, d=0.0, e=None, f=None) -> None:
        self._figuras.agregar_al_final((tipo, a, b, c, d, e, f))

    def _armar(self) -> None:
        self._armar_encabezado()
        izq, der, abajo, arriba = self._g.columna
        y = self._armar_estadisticas(izq, der, arriba)
        if self._modo == "objetivo":
            self._armar_objetivo(izq, der, abajo, y)
        else:
            y = self._armar_salidas_y_efectos(izq, der, y)
            y = self._armar_en_la_sala(izq, der, y)
            self._armar_inventario(izq, der, abajo, y)
        self._armar_bitacora_y_controles()
        if self._bitacora_completa:
            self._armar_bitacora_completa()
        self._armar_cartel()

    def _armar_encabezado(self) -> None:
        izq, der, abajo, arriba = self._g.encabezado
        if not self._panel(izq, der, abajo, arriba):
            return
        estado = self._estado
        medio = (abajo + arriba) / 2
        self._texto(_recortar(estado.sala.nombre, 30), izq + 16, medio + 10, 19,
                    estilo.DORADO, bold=True)
        self._texto(f"{estado.id_cripta}   ·   tiempo {estado.reloj}", izq + 16, medio - 16, 11,
                    estilo.TEXTO_SUAVE)

        # Vida: corazón + barra animada con el número adentro.
        jugador = estado.jugador
        ancho_barra = min(260, (der - izq) * 0.3)
        x_barra = izq + (der - izq) * 0.38
        self._corazon = (x_barra - 22, medio, 30)
        self._barra_vida = (x_barra, medio - 10, ancho_barra, 20)
        self._texto(f"{jugador.vida} / {jugador.vida_max}", x_barra + ancho_barra / 2, medio, 12,
                    estilo.TEXTO, anchor_x="center", bold=True)
        self._texto("VIDA", x_barra, medio + 20, 9, estilo.TEXTO_SUAVE, bold=True)
        previo = self._anterior.jugador.vida if self._anterior is not None else None
        if previo is not None and previo != jugador.vida:
            cambio = jugador.vida - previo
            self._texto(f"{cambio:+d}", x_barra + ancho_barra + 10, medio, 13,
                        _VERDE_SUAVE if cambio > 0 else _ROJO_SUAVE, bold=True)

        if estado.replay is not None:
            self._armar_hud_replay(der, arriba)
            return
        # Antorcha y pergaminos, a la derecha.
        x = der - 16
        antorcha = "Antorcha encendida" if jugador.antorcha_encendida else "Sin antorcha"
        color = _COLOR_ANTORCHA if jugador.antorcha_encendida else estilo.TEXTO_APAGADO
        texto = self._texto(antorcha, x, medio + 10, 12, color, anchor_x="right", bold=True)
        self._figura("llama" if jugador.antorcha_encendida else "llama_apagada",
                     x - texto.content_width - 14, medio + 10, 8)
        pergaminos = estado.inventario.cantidad_pergaminos
        texto = self._texto(f"Pergaminos: {pergaminos}", x, medio - 14, 11,
                            estilo.TEXTO if pergaminos else estilo.TEXTO_APAGADO,
                            anchor_x="right")
        self._figura("objeto", x - texto.content_width - 14, medio - 14, 8,
                     e="pergamino_retroceso")

    def _armar_hud_replay(self, der, arriba) -> None:
        """REPLAY, paso, velocidad o pausa, y qué partida es."""
        replay = self._estado.replay
        estado = "en pausa" if replay.pausado else f"velocidad x{replay.velocidad}"
        texto = self._texto(f"REPLAY   paso {replay.paso}/{replay.total}   {estado}",
                            der - 24, arriba - 22, 13, (255, 220, 120), anchor_x="right",
                            bold=True)
        ancho_hud = texto.content_width
        if replay.titulo:
            subtitulo = self._texto(_recortar(replay.titulo, 48), der - 24, arriba - 44, 10,
                                    (235, 215, 170), anchor_x="right")
            ancho_hud = max(ancho_hud, subtitulo.content_width)
        avance = replay.paso / replay.total if replay.total else 1.0
        self._hud_replay = (der - ancho_hud - 36, der - 12, arriba - 62, arriba - 8, avance)

    def _armar_estadisticas(self, izq, der, arriba) -> float:
        """Cinco tarjetas: ataque, defensa, velocidad, acciones, derrotados.
        Si un valor cambió desde el turno anterior, se muestra la diferencia."""
        alto = 64
        abajo = arriba - alto
        jugador = self._estado.jugador
        previo = self._anterior.jugador if self._anterior is not None else None
        datos = (
            ("Ataque", jugador.ataque_efectivo, previo.ataque_efectivo if previo else None,
             "espada"),
            ("Defensa", jugador.defensa_efectiva, previo.defensa_efectiva if previo else None,
             "escudo"),
            ("Velocidad", jugador.velocidad, previo.velocidad if previo else None, "rayo"),
            ("Acciones", jugador.acciones, None, "reloj"),
            ("Derrotados", jugador.enemigos_derrotados,
             previo.enemigos_derrotados if previo else None, "calavera"),
        )
        ancho_tarjeta = (der - izq - 4 * 8) / 5
        x = izq
        for etiqueta, valor, valor_previo, icono in datos:
            if self._panel(x, x + ancho_tarjeta, abajo, arriba):
                self._figura(icono, x + 18, arriba - 22, 10)
                numero = self._texto(str(valor), x + ancho_tarjeta - 12, arriba - 24, 17,
                                     estilo.TEXTO, anchor_x="right", bold=True)
                self._texto(etiqueta, x + ancho_tarjeta / 2, abajo + 13, 10, estilo.TEXTO_SUAVE,
                            anchor_x="center")
                if valor_previo is not None and valor != valor_previo:
                    diferencia = valor - valor_previo
                    # a la izquierda del número, para no tapar la etiqueta
                    self._texto(f"{diferencia:+d}",
                                x + ancho_tarjeta - 18 - numero.content_width, arriba - 22, 10,
                                _VERDE_SUAVE if diferencia > 0 else _ROJO_SUAVE,
                                anchor_x="right", bold=True)
            x += ancho_tarjeta + 8
        return abajo - _SEPARACION

    def _armar_salidas_y_efectos(self, izq, der, arriba) -> float:
        alto = 100
        abajo = arriba - alto
        ancho_salidas = min(150, (der - izq) * 0.32)
        if self._panel(izq, izq + ancho_salidas, abajo, arriba, "Salidas"):
            self._armar_brujula(izq + ancho_salidas / 2, (abajo + arriba) / 2 - 8)
        x = izq + ancho_salidas + _SEPARACION
        if self._panel(x, der, abajo, arriba, "Efectos"):
            efectos = self._estado.efectos
            if efectos.esta_vacia():
                self._texto("Ningún efecto activo", x + 14, arriba - 42, 11, estilo.TEXTO_APAGADO)
            caracteres = max(10, int((der - x - 40) / 6.2))
            y = arriba - 40
            for indice, efecto in enumerate(efectos):
                if y < abajo + 12:
                    break
                self._figura("punto", x + 18, y, 5, e=_color_efecto(efecto.tipo))
                self._texto(_recortar(efecto.descripcion, caracteres), x + 30, y, 11,
                            _color_efecto(efecto.tipo))
                y -= 20
        return abajo - _SEPARACION

    def _armar_brujula(self, cx, cy) -> None:
        """Una cruz N/S/E/O: verde abierta, dorado con llave, gris sin salida.
        Debajo de la letra, el costo de cruzar esa salida (FR-023)."""
        celda = 24
        posiciones = (("N", 0, 1), ("S", 0, -1), ("E", 1, 0), ("O", -1, 0))
        estados = ListaEnlazada()
        for salida in self._estado.sala.salidas:
            if salida is not None:
                estados.agregar_al_final((salida.direccion, salida.estado, salida.costo))
        for direccion, dx, dy in posiciones:
            estado = None
            costo = None
            for direccion_salida, estado_salida, costo_salida in estados:
                if direccion_salida == direccion:
                    estado = estado_salida
                    costo = costo_salida
            if estado == SALIDA_ABIERTA:
                color, borde = (46, 92, 56), estilo.VERDE
            elif estado == SALIDA_CERRADA_CON_LLAVE:
                color, borde = (92, 72, 30), estilo.DORADO
            else:
                color, borde = (34, 30, 30), (70, 64, 60)
            x, y = cx + dx * (celda + 2), cy + dy * (celda + 2)
            self._figura("celda", x, y, celda, 0, color, borde)
            if costo is None:
                self._texto(direccion, x, y, 11,
                            estilo.TEXTO if estado in (SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE)
                            else estilo.TEXTO_APAGADO, anchor_x="center", bold=True)
            else:
                self._texto(direccion, x, y + 4, 10, estilo.TEXTO, anchor_x="center", bold=True)
                self._texto(str(costo), x, y - 7, 7, estilo.DORADO, anchor_x="center")
        self._figura("celda", cx, cy, celda - 8, 0, (24, 20, 20), (70, 64, 60))

    def _armar_en_la_sala(self, izq, der, arriba) -> float:
        alto = 100
        abajo = arriba - alto
        if not self._panel(izq, der, abajo, arriba, "En la sala"):
            return abajo - _SEPARACION
        sala = self._estado.sala
        y = arriba - 38
        if sala.enemigos.esta_vacia():
            self._texto("No hay enemigos a la vista", izq + 14, y, 11, _VERDE_SUAVE)
            y -= 20
        visibles = 0
        for enemigo in sala.enemigos:
            if visibles == 2:
                self._texto(f"y {len(sala.enemigos) - 2} más...", izq + 14, y, 10,
                            estilo.TEXTO_SUAVE)
                y -= 18
                break
            self._figura("calavera", izq + 20, y, 7)
            # FR-024: el cazador lleva un prefijo además del color.
            self._texto(_recortar(estilo.etiqueta_enemigo(enemigo), 22), izq + 34, y, 11,
                        estilo.COLOR_CAZADOR if enemigo.es_cazador else estilo.TEXTO)
            self._figura("barra", der - 150, y - 5, 90, 10, enemigo.vida, enemigo.vida_max)
            self._texto(f"{enemigo.vida}/{enemigo.vida_max}", der - 14, y, 10, estilo.TEXTO_SUAVE,
                        anchor_x="right")
            y -= 20
            visibles += 1
        if y >= abajo + 10:
            if sala.objetos.esta_vacia():
                self._texto("Nada en el suelo", izq + 14, y, 11, estilo.TEXTO_APAGADO)
            else:
                x = izq + 14
                texto = self._texto("Suelo:", x, y, 11, estilo.TEXTO_SUAVE)
                x += texto.content_width + 12
                for objeto in sala.objetos:
                    if x > der - 60:
                        self._texto("...", x, y, 11, estilo.TEXTO_SUAVE)
                        break
                    self._figura("objeto", x + 8, y, 8, e=objeto.clase)
                    texto = self._texto(_recortar(objeto.nombre, 16), x + 20, y, 11, estilo.TEXTO)
                    x += texto.content_width + 34
        return abajo - _SEPARACION

    def _armar_inventario(self, izq, der, abajo, arriba) -> None:
        inventario = self._estado.inventario
        titulo = f"Inventario  {len(inventario.objetos)}/{inventario.capacidad}"
        if not self._panel(izq, der, abajo, arriba, titulo):
            return
        objetos = inventario.objetos
        if objetos.esta_vacia():
            self._texto("Vacío. Usa R para recoger lo que hay en el suelo.", izq + 14,
                        arriba - 40, 11, estilo.TEXTO_APAGADO)
            return
        # El orden que se ve: el real o la vista ordenada que eligió el
        # jugador con O (el orden real no cambia, §4.5). El cursor marca el
        # objeto actual del inventario, esté donde esté en la vista.
        actual = (objetos.obtener(inventario.indice_actual)
                  if inventario.indice_actual >= 0 else None)
        criterio = inventario.criterio_orden or "real"
        self._texto(f"orden: {criterio}   (Tab / Shift+Tab · O ordena)", der - 14, arriba - 14, 10,
                    estilo.TEXTO_SUAVE, anchor_x="right")
        if inventario.vista_ordenada is not None:
            objetos = inventario.vista_ordenada
        indice_actual = -1
        for indice, objeto in enumerate(objetos):
            if actual is not None and objeto.id_objeto == actual.id_objeto:
                indice_actual = indice
        alto_fila = 21
        visibles = max(1, int((arriba - abajo - 34) // alto_fila))
        # La ventana de filas sigue al cursor del inventario.
        primera = 0
        if indice_actual >= visibles:
            primera = indice_actual - visibles + 1
        y = arriba - 38
        for indice, objeto in enumerate(objetos):
            if indice < primera:
                continue
            if indice >= primera + visibles:
                self._texto(f"y {len(objetos) - indice} más...", der - 14, abajo + 12, 10,
                            estilo.TEXTO_SUAVE, anchor_x="right")
                break
            elegido = indice == indice_actual
            if elegido:
                self._figura("fila", izq + 6, y - alto_fila / 2 + 1, der - 6, y + alto_fila / 2 - 1)
                self._figura("flecha", izq + 14, y, 5)
            self._figura("objeto", izq + 30, y, 8, e=objeto.clase)
            self._texto(_recortar(objeto.nombre, 26), izq + 44, y, 11,
                        estilo.TEXTO if elegido or objeto.equipado else estilo.TEXTO_SUAVE,
                        bold=elegido)
            if objeto.equipado:
                self._figura("etiqueta", der - 84, y - 8, der - 14, y + 8, (90, 70, 30))
                self._texto("EQUIPADO", der - 49, y, 8, estilo.DORADO, anchor_x="center",
                            bold=True)
            y -= alto_fila

    def _armar_objetivo(self, izq, der, abajo, arriba) -> None:
        if not self._panel(izq, der, abajo, arriba, _titulo_verbo(self._verbo), resaltado=True):
            return
        self._texto("Flecha arriba/abajo: elegir   ENTER: confirmar   ESC: cancelar", izq + 14,
                    abajo + 16, 10, estilo.TEXTO_SUAVE)
        alto_fila = 30
        y = arriba - 46
        for indice, objetivo in enumerate(self._lista):
            if y < abajo + 40:
                break
            elegido = indice == self._cursor
            if elegido:
                self._figura("fila", izq + 8, y - alto_fila / 2 + 2, der - 8, y + alto_fila / 2 - 2)
                self._figura("flecha", izq + 18, y, 6)
            color = estilo.DORADO if elegido else estilo.TEXTO
            if self._verbo == "atacar":
                self._figura("calavera", izq + 36, y, 8)
                if objetivo.es_cazador and not elegido:
                    color = estilo.COLOR_CAZADOR
                self._texto(estilo.etiqueta_enemigo(objetivo), izq + 52, y, 13, color,
                            bold=elegido)
                self._figura("barra", der - 170, y - 6, 110, 12, objetivo.vida, objetivo.vida_max)
                self._texto(f"{objetivo.vida}/{objetivo.vida_max}", der - 16, y, 11,
                            estilo.TEXTO_SUAVE, anchor_x="right")
            else:
                self._figura("objeto", izq + 36, y, 9, e=objetivo.clase)
                self._texto(objetivo.nombre, izq + 52, y, 13, color, bold=elegido)
                if objetivo.equipado:
                    self._texto("equipado", der - 16, y, 10, estilo.DORADO, anchor_x="right")
            y -= alto_fila

    def _armar_bitacora_y_controles(self) -> None:
        izq, der, abajo, arriba = self._g.inferior
        corte = izq + (der - izq) * 0.56
        if self._panel(izq, corte, abajo, arriba, "Bitácora"):
            mensajes = self._estado.mensajes
            total = len(mensajes)
            omitir = total - _MENSAJES_VISIBLES
            caracteres = max(20, int((corte - izq - 30) / 6.6))
            y = arriba - 38
            if total == 0:
                self._texto("Todavía no pasó nada.", izq + 14, y, 11, estilo.TEXTO_APAGADO)
            for indice, mensaje in enumerate(mensajes):
                if indice < omitir:
                    continue
                if y < abajo + 8:
                    break
                ultimo = indice == total - 1
                self._texto(_recortar(mensaje, caracteres), izq + 14, y, 11,
                            _color_mensaje(mensaje, ultimo), bold=ultimo)
                y -= 19
        x = corte + _SEPARACION
        if self._panel(x, der, abajo, arriba, "Controles"):
            self._armar_controles(x, der, abajo, arriba)

    def _armar_bitacora_completa(self) -> None:
        """L: los últimos 20 mensajes (§4.8), en un panel sobre el mapa."""
        izq = self._g.mapa_izq
        der = izq + self._g.lado_mapa
        abajo, arriba = self._g.mapa_abajo + 8, self._g.mapa_arriba - 8
        if not _cabe(izq, der, abajo, arriba):
            return
        self._superpuestos.agregar_al_final((izq + 8, der - 8, abajo, arriba))
        textos = self._textos_superpuestos
        textos.agregar_al_final(estilo.texto(
            "Bitácora: últimos 20 mensajes", izq + 22, arriba - 18, 12, estilo.DORADO,
            anchor_y="center", bold=True))
        textos.agregar_al_final(estilo.texto(
            "L para cerrar", der - 22, arriba - 18, 10, estilo.TEXTO_SUAVE, anchor_x="right",
            anchor_y="center"))
        mensajes = self._estado.mensajes
        total = len(mensajes)
        alto_fila = max(12, min(19, (arriba - abajo - 44) / _MENSAJES_COMPLETOS))
        caracteres = max(20, int((der - izq - 50) / 6.4))
        y = arriba - 42
        if total == 0:
            textos.agregar_al_final(estilo.texto("Todavía no pasó nada.", izq + 22, y, 11,
                                                 estilo.TEXTO_APAGADO, anchor_y="center"))
        # El Modelo ya entrega a lo sumo 20 (ColaAcotada, D30); igual se
        # muestran solo los últimos _MENSAJES_COMPLETOS por si llegaran más.
        omitir = total - _MENSAJES_COMPLETOS
        for indice, mensaje in enumerate(mensajes):
            if indice < omitir:
                continue
            ultimo = indice == total - 1
            textos.agregar_al_final(estilo.texto(
                f"{indice - max(omitir, 0) + 1:>2}. {_recortar(mensaje, caracteres)}", izq + 22, y, 11,
                _color_mensaje(mensaje, ultimo), anchor_y="center", bold=ultimo))
            y -= alto_fila

    def _controles(self):
        if self._estado.replay is not None:
            return (("Espacio", "Pausa / seguir"), ("Flecha izquierda", "Paso atrás"),
                    ("Flecha derecha", "Paso adelante"), ("Flecha arriba", "Más rápido"),
                    ("Flecha abajo", "Más lento"), ("L", "Bitácora (20)"),
                    ("ESC", "Salir del replay"))
        if self._modo == "objetivo":
            return (("Flecha arriba/abajo", "Elegir"), ("ENTER", "Confirmar"), ("ESC", "Cancelar"))
        return (("Flechas", "Moverse"), ("Shift+Flecha", "Abrir puerta"),
                ("Espacio", "Esperar"), ("R", "Recoger"), ("A", "Atacar"),
                ("U / Q / S", "Usar/equipar/soltar"), ("Tab / Shift+Tab", "Bajar / subir inventario"),
                ("O", "Ordenar inventario"), ("P", "Pergamino"), ("G / C", "Guardar/Cargar"),
                ("L", "Bitácora (20)"), ("ESC", "Volver al menú"))

    def _armar_controles(self, izq, der, abajo, arriba) -> None:
        controles = self._controles()
        filas = (len(controles) + 1) // 2
        alto_fila = max(14, min(21, (arriba - abajo - 32) / max(filas, 1)))
        ancho_columna = (der - izq - 20) / 2
        for indice, (tecla, descripcion) in enumerate(controles):
            columna = indice // filas
            fila = indice % filas
            x = izq + 12 + columna * ancho_columna
            y = arriba - 36 - fila * alto_fila
            ancho_tecla = 12 + 6.5 * len(tecla)
            self._figura("tecla", x + ancho_tecla / 2, y, ancho_tecla, 17)
            self._texto(tecla, x + ancho_tecla / 2, y, 9, estilo.TEXTO, anchor_x="center",
                        bold=True)
            self._texto(_recortar(descripcion, 22), x + ancho_tecla + 8, y, 10,
                        estilo.TEXTO_SUAVE)

    def _armar_cartel(self) -> None:
        if not self._aviso:
            return
        centro = self._g.mapa_izq + self._g.lado_mapa / 2
        texto = estilo.texto(_recortar(self._aviso, 70), centro, self._g.mapa_arriba - 26, 12,
                             estilo.TEXTO, anchor_x="center", anchor_y="center", bold=True)
        mitad = texto.content_width / 2 + 16
        self._cartel = (centro - mitad, centro + mitad, self._g.mapa_arriba - 42,
                        self._g.mapa_arriba - 10, texto)

    # ------------------------------------------------------------------
    # Dibujo (cada cuadro)
    # ------------------------------------------------------------------

    def dibujar(self, t: float, t_aviso: float) -> None:
        """t: segundos desde que llegó el estado; t_aviso: desde el aviso."""
        for izq, der, abajo, arriba, resaltado in self._paneles:
            estilo.dibujar_panel(izq, der, abajo, arriba, resaltado=resaltado)
        if self._barra_vida is not None:
            self._dibujar_vida(t)
        if self._hud_replay is not None:
            izq, der, abajo, arriba, avance = self._hud_replay
            arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, (40, 28, 10, 230))
            arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, (255, 200, 90), 2)
            arcade.draw_lrbt_rectangle_filled(izq + 6, izq + 6 + (der - izq - 12) * avance,
                                              abajo + 5, abajo + 9, (255, 200, 90))
        for figura in self._figuras:
            self._dibujar_figura(figura, t)
        for texto in self._textos:
            texto.draw()
        for izq, der, abajo, arriba in self._superpuestos:
            arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, (12, 9, 10, 238))
            arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba, estilo.DORADO, 2)
        for texto in self._textos_superpuestos:
            texto.draw()
        self._dibujar_cartel(t_aviso)

    def _dibujar_vida(self, t: float) -> None:
        jugador = self._estado.jugador
        previa = self._anterior.jugador.vida if self._anterior is not None else None
        izq, abajo, ancho, alto = self._barra_vida
        dibujar_barra(izq, abajo, ancho, alto, valor_animado(previa, jugador.vida, t),
                      jugador.vida_max)
        fraccion = jugador.vida / jugador.vida_max if jugador.vida_max else 0
        x, y, lado = self._corazon
        if 0 < fraccion < 0.3:
            # con poca vida, el corazón late
            lado *= 1 + 0.12 * max(0.0, math.sin(t * 8))
        arcade.draw_texture_rect(texturas.corazon(fraccion), arcade.XYWH(x, y, lado, lado),
                                 pixelated=True)

    def _dibujar_figura(self, figura, t: float) -> None:
        # DECISIÓN: cadena de if por tipo de figura (no dict, §7); pocas y fijas.
        tipo, a, b, c, d, e, f = figura
        if tipo == "objeto":
            dibujar_objeto(e, a, b, c)
        elif tipo == "espada":
            dibujar_objeto("arma", a, b, c)
        elif tipo == "escudo":
            dibujar_objeto("armadura", a, b, c)
        elif tipo == "calavera":
            # la calavera de 0x72 ocupa la parte de abajo de su baldosa: se
            # agranda y se sube para centrarla
            lado = c * 4.4
            arcade.draw_texture_rect(texturas.calavera(), arcade.XYWH(a, b + c * 0.9, lado, lado),
                                     pixelated=True)
        elif tipo == "rayo":
            arcade.draw_polygon_filled(
                ((a + c * 0.2, b + c), (a - c * 0.6, b - c * 0.1), (a, b - c * 0.1),
                 (a - c * 0.2, b - c), (a + c * 0.6, b + c * 0.1), (a, b + c * 0.1)),
                _COLOR_VELOCIDAD)
        elif tipo == "reloj":
            arcade.draw_triangle_filled(a - c * 0.6, b + c, a + c * 0.6, b + c, a, b, estilo.DORADO)
            arcade.draw_triangle_filled(a - c * 0.6, b - c, a + c * 0.6, b - c, a, b,
                                        estilo.DORADO_OSCURO)
        elif tipo == "llama":
            escala = 1 + 0.12 * math.sin(t * 15)
            arcade.draw_triangle_filled(a - c * 0.6, b - c * 0.5, a + c * 0.6, b - c * 0.5,
                                        a, b + c * escala, _COLOR_ANTORCHA)
            arcade.draw_circle_filled(a, b - c * 0.3, c * 0.4, (255, 225, 110))
        elif tipo == "llama_apagada":
            arcade.draw_line(a, b - c, a, b + c * 0.4, (110, 80, 50), 3)
        elif tipo == "punto":
            arcade.draw_circle_filled(a, b, c, e)
        elif tipo == "barra":
            dibujar_barra(a, b, c, d, e, f)
        elif tipo == "celda":
            mitad = c / 2
            arcade.draw_lrbt_rectangle_filled(a - mitad, a + mitad, b - mitad, b + mitad, e)
            arcade.draw_lrbt_rectangle_outline(a - mitad, a + mitad, b - mitad, b + mitad, f, 2)
        elif tipo == "fila":
            arcade.draw_lrbt_rectangle_filled(a, c, b, d, (232, 193, 92, 38))
            arcade.draw_lrbt_rectangle_outline(a, c, b, d, estilo.DORADO, 1)
        elif tipo == "flecha":
            arcade.draw_triangle_filled(a - c * 0.6, b + c, a - c * 0.6, b - c, a + c, b,
                                        estilo.DORADO)
        elif tipo == "etiqueta":
            arcade.draw_lrbt_rectangle_filled(a, c, b, d, e)
            arcade.draw_lrbt_rectangle_outline(a, c, b, d, estilo.DORADO, 1)
        elif tipo == "tecla":
            estilo.dibujar_tecla(a, b, c, d)

    def _dibujar_cartel(self, t_aviso: float) -> None:
        if self._cartel is None or t_aviso >= _DURACION_AVISO:
            return
        izq, der, abajo, arriba, texto = self._cartel
        # se desvanece en el último segundo
        alfa = 1.0 if t_aviso < _DURACION_AVISO - 1 else _DURACION_AVISO - t_aviso
        arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, (60, 30, 14, int(235 * alfa)))
        arcade.draw_lrbt_rectangle_outline(izq, der, abajo, arriba,
                                           (240, 150, 60, int(255 * alfa)), 2)
        texto.color = (236, 228, 214, int(255 * alfa))
        texto.draw()
