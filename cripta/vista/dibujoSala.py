"""DibujoSala: la parte gráfica de PantallaJuego (§10.2).

Dibuja la sala actual vista desde arriba (con el muro norte de frente, como
en el pixel art de 0x72): el fondo (armado una vez por sala en texturas.py),
las puertas según su estado, los objetos del suelo, los enemigos con su
barra de vida y su etiqueta ("Rata gigante #1"), el caballero del jugador
y la luz de la antorcha.

Animación: dibujar(t) recibe los segundos transcurridos desde que llegó
este EstadoVista. Comparando con el EstadoVista ANTERIOR (si lo hay) se
anima lo que cambió en el último turno:
  - fundido desde negro al entrar a una sala nueva;
  - destello rojo y número flotante en el enemigo o jugador que recibió
    daño, y barras de vida que bajan de a poco;
  - el enemigo derrotado se desvanece en vez de desaparecer de golpe.
Y en todo momento: llama y luz de la antorcha que parpadean, enemigos que
se balancean y objetos que flotan.

DECISIÓN: esta clase solo LEE los EstadoVista; no encola comandos ni
conoce teclas (eso es de PantallaJuego). Todo lo que depende de comparar
estados se calcula una sola vez en el constructor (O(e·e') con e y e' los
enemigos de antes y de ahora, decenas a lo sumo); cada cuadro solo dibuja,
O(enemigos + objetos).

DECISIÓN: cadenas de if por clase de objeto y por tipo de enemigo (no
dict, §7): son pocas clases fijas.
"""
from __future__ import annotations

import math

import arcade

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import texturas
from .estadoVista import SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE, SALIDA_SIN_SALIDA

_COLOR_PUERTA_ABIERTA = (70, 170, 90)
_COLOR_RESALTE = arcade.color.YELLOW
_SIN_TINTE = arcade.color.WHITE
_TINTE_DANO = arcade.types.Color(255, 70, 70)

_MAX_EN_FILA = 6

# Duraciones de las animaciones de cambio, en segundos.
DURACION_BARRA = 0.5
_DURACION_FUNDIDO = 0.35
_DURACION_DESTELLO = 0.45
_DURACION_CAIDA = 0.7
_DURACION_NUMERO = 0.9


def valor_animado(previo, actual, t: float, duracion: float = DURACION_BARRA) -> float:
    """Interpola de `previo` a `actual` en `duracion` segundos (con
    desaceleración al final). Sin previo, devuelve el actual."""
    if previo is None or t >= duracion:
        return actual
    f = t / duracion
    f = 1 - (1 - f) * (1 - f)
    return previo + (actual - previo) * f


def misma_sala(estado, anterior) -> bool:
    return (anterior is not None and anterior.id_cripta == estado.id_cripta
            and anterior.sala.nombre == estado.sala.nombre)


class DibujoSala:

    def __init__(self, estado, izquierda: float, abajo: float, lado: float,
                 anterior=None, escala_pixeles: float = 1.0,
                 skin: str = texturas.SKIN_POR_DEFECTO):
        self._estado = estado
        self._skin = skin
        self._izq = izquierda
        self._abajo = abajo
        self._lado = lado
        # Un "pixel" del pixel art (el fondo mide 192 px de 0x72 por lado) y
        # el grosor de cada muro, tomados del fondo para que todo coincida.
        self._u = lado / texturas.PIXELES_FONDO
        self._norte = lado * texturas.FRACCION_NORTE
        self._sur = lado * texturas.FRACCION_SUR
        self._muro = lado * texturas.FRACCION_LATERAL
        self._radio = max(lado * 0.055, 6)
        self._sala_nueva = not misma_sala(estado, anterior)
        self._jugador_herido = (anterior is not None
                                and estado.jugador.vida < anterior.jugador.vida)

        lado_px = max(int(lado * escala_pixeles), 16)
        self._fondo = texturas.fondo_sala(estado.sala.nombre, lado_px)

        self._vidas_previas = ListaEnlazada()   # vida anterior de cada enemigo (o None)
        self._caidos = ListaEnlazada()          # (etiqueta, x, y) derrotados este turno
        self._numeros = ListaEnlazada()         # (arcade.Text, x, y, color) daño flotante
        self._etiquetas = ListaEnlazada()       # de arcade.Text
        self._nombre = None                     # arcade.Text del nombre bajo el jugador
        self._comparar_con(anterior)
        self._armar_etiquetas()

    # ------------------------------------------------------------------
    # Comparación con el turno anterior (una vez, en el constructor)
    # ------------------------------------------------------------------

    def _comparar_con(self, anterior) -> None:
        enemigos = self._estado.sala.enemigos
        previos = anterior.sala.enemigos if misma_sala(self._estado, anterior) else None

        for indice, enemigo in enumerate(enemigos):
            previo = _buscar_por_etiqueta(previos, enemigo.etiqueta)
            vida_previa = previo.vida if previo is not None else None
            self._vidas_previas.agregar_al_final(vida_previa)
            if vida_previa is not None and enemigo.vida < vida_previa:
                x, y = self.posicion_enemigo(indice)
                self._agregar_numero(f"-{vida_previa - enemigo.vida}", x,
                                     y + self._radio * 1.6, (255, 230, 120))

        if previos is not None:
            cantidad_previa = len(previos)
            for indice, previo in enumerate(previos):
                if _buscar_por_etiqueta(enemigos, previo.etiqueta) is None:
                    x, y = self._posicion_en_fila(indice, cantidad_previa, 0.74)
                    self._caidos.agregar_al_final((previo.etiqueta, x, y))

        if self._jugador_herido:
            cx, cy = self._centro()
            dano = anterior.jugador.vida - self._estado.jugador.vida
            self._agregar_numero(f"-{dano}", cx, cy + self._radio * 1.8, (255, 90, 80))

    def _agregar_numero(self, texto: str, x: float, y: float, color) -> None:
        tamano = max(min(int(self._radio * 0.7), 18), 9)
        self._numeros.agregar_al_final((
            arcade.Text(texto, x, y, color, tamano, anchor_x="center", bold=True), x, y, color))

    # ------------------------------------------------------------------
    # Posiciones
    # ------------------------------------------------------------------

    def _centro(self):
        """Centro del piso (entre el muro norte y el reborde sur)."""
        piso_abajo = self._abajo + self._sur
        piso_arriba = self._abajo + self._lado - self._norte
        return self._izq + self._lado / 2, (piso_abajo + piso_arriba) / 2

    def _posicion_en_fila(self, indice: int, cantidad: int, altura: float):
        """Reparte `cantidad` elementos en una fila horizontal a `altura`
        (0..1 dentro de la sala). Más de _MAX_EN_FILA pasan a otra fila."""
        fila = indice // _MAX_EN_FILA
        en_fila = min(cantidad - fila * _MAX_EN_FILA, _MAX_EN_FILA)
        columna = indice % _MAX_EN_FILA
        util = self._lado - 2 * self._muro
        x = self._izq + self._muro + util * (columna + 1) / (en_fila + 1)
        y = self._abajo + self._lado * altura - fila * self._radio * 3.2
        return x, y

    def posicion_enemigo(self, indice: int):
        return self._posicion_en_fila(indice, len(self._estado.sala.enemigos), 0.74)

    def posicion_objeto(self, indice: int):
        return self._posicion_en_fila(indice, len(self._estado.sala.objetos), 0.26)

    # ------------------------------------------------------------------
    # Dibujo (cada cuadro)
    # ------------------------------------------------------------------

    def dibujar(self, t: float, enemigo_resaltado: int = -1, objeto_resaltado: int = -1) -> None:
        r = self._radio
        arcade.draw_texture_rect(self._fondo, arcade.LBWH(self._izq, self._abajo,
                                                          self._lado, self._lado),
                                 pixelated=True)
        self._dibujar_puertas()

        for indice, objeto in enumerate(self._estado.sala.objetos):
            x, y = self.posicion_objeto(indice)
            flota = math.sin(t * 2.2 + indice * 1.3) * r * 0.12
            _dibujar_sombra(x, y - r * 0.85, r * 0.9)
            if indice == objeto_resaltado:
                _dibujar_resalte(x, y, r * 1.5, t)
            dibujar_objeto(objeto.clase, x, y + flota, r)

        for etiqueta, x, y in self._caidos:
            if t < _DURACION_CAIDA:
                f = t / _DURACION_CAIDA
                _dibujar_enemigo(etiqueta, x, y - f * r * 0.6, r, self._u, t,
                                 int(255 * (1 - f)), _SIN_TINTE)

        for indice, (enemigo, vida_previa) in enumerate(
                zip(self._estado.sala.enemigos, self._vidas_previas)):
            x, y = self.posicion_enemigo(indice)
            y += math.sin(t * 3.4 + indice * 1.9) * r * 0.1
            herido = vida_previa is not None and enemigo.vida < vida_previa
            tinte = _SIN_TINTE
            if herido and t < _DURACION_DESTELLO and int(t * 14) % 2 == 0:
                tinte = _TINTE_DANO
            if indice == enemigo_resaltado:
                _dibujar_resalte(x, y, r * 1.7, t)
            _dibujar_enemigo(enemigo.etiqueta, x, y, r, self._u, t, 255, tinte)

        cx, cy = self._centro()
        encendida = self._estado.jugador.antorcha_encendida
        golpeado = self._jugador_herido and t < _DURACION_DESTELLO
        _dibujar_jugador(cx, cy, self._u, encendida, golpeado, t, self._skin)

        self._dibujar_luz(t, encendida)

        # Lo que va encima de la luz, para que siempre se lea.
        for indice, (enemigo, vida_previa) in enumerate(
                zip(self._estado.sala.enemigos, self._vidas_previas)):
            x, y = self.posicion_enemigo(indice)
            dibujar_barra(x - r, y + r * 1.45, r * 2, max(r * 0.28, 3),
                          valor_animado(vida_previa, enemigo.vida, t), enemigo.vida_max)
        for texto in self._etiquetas:
            texto.draw()
        self._dibujar_nombre()

        if self._jugador_herido and t < _DURACION_DESTELLO:
            alfa = int(110 * (1 - t / _DURACION_DESTELLO))
            arcade.draw_lrbt_rectangle_filled(self._izq, self._izq + self._lado, self._abajo,
                                              self._abajo + self._lado, (200, 0, 0, alfa))
        self._dibujar_numeros(t)
        if self._sala_nueva and t < _DURACION_FUNDIDO:
            alfa = int(255 * (1 - t / _DURACION_FUNDIDO))
            arcade.draw_lrbt_rectangle_filled(self._izq, self._izq + self._lado, self._abajo,
                                              self._abajo + self._lado, (0, 0, 0, alfa))

    def _dibujar_nombre(self) -> None:
        """El nombre del jugador en una placa oscura, debajo de sus pies."""
        if self._nombre is None:
            return
        ancho = self._nombre.content_width + 12
        alto = self._nombre.content_height + 2
        x, y = self._nombre.x, self._nombre.y
        arcade.draw_lrbt_rectangle_filled(x - ancho / 2, x + ancho / 2, y - alto / 2,
                                          y + alto / 2, (10, 8, 8, 190))
        arcade.draw_lrbt_rectangle_outline(x - ancho / 2, x + ancho / 2, y - alto / 2,
                                           y + alto / 2, (150, 112, 48), 1)
        self._nombre.draw()

    def _dibujar_luz(self, t: float, encendida: bool) -> None:
        interior = arcade.LBWH(self._izq + self._muro, self._abajo + self._sur,
                               self._lado - 2 * self._muro,
                               self._lado - self._norte - self._sur)
        parpadeo = math.sin(t * 9.0) * 0.5 + math.sin(t * 23.0 + 1.3) * 0.3
        alfa = int(max(0, min(255, 225 - parpadeo * 22))) if encendida else 255
        arcade.draw_texture_rect(texturas.oscuridad(encendida), interior, alpha=alfa)
        if encendida:
            cx, cy = self._centro()
            tam = self._lado * (0.62 + parpadeo * 0.025)
            arcade.draw_texture_rect(texturas.resplandor(),
                                     arcade.XYWH(cx + self._radio * 0.85, cy, tam, tam),
                                     alpha=int(max(0, min(255, 200 + parpadeo * 40))))

    def _dibujar_numeros(self, t: float) -> None:
        if t >= _DURACION_NUMERO:
            return
        f = t / _DURACION_NUMERO
        for texto, x, y, color in self._numeros:
            texto.x = x
            texto.y = y + f * self._radio * 2.2
            texto.color = (color[0], color[1], color[2], int(255 * (1 - f * f)))
            texto.draw()

    def _dibujar_puertas(self) -> None:
        for salida in self._estado.sala.salidas:
            if salida is None:
                continue
            if salida.estado == SALIDA_ABIERTA:
                self._dibujar_puerta_abierta(salida.direccion)
            elif salida.estado == SALIDA_CERRADA_CON_LLAVE:
                self._dibujar_puerta_cerrada(salida.direccion)

    def _rect_puerta(self, direccion: str):
        """(izq, der, abajo, arriba) de la puerta en ese muro. La norte es
        la hoja de 0x72 completa (32x32 px, ocupa toda la cara de ladrillo);
        la sur y las laterales son huecos en el reborde, porque ese muro se
        ve desde arriba."""
        u = self._u
        cx, cy = self._centro()
        izq, der = self._izq, self._izq + self._lado
        abajo, arriba = self._abajo, self._abajo + self._lado
        if direccion == "N":
            return cx - 16 * u, cx + 16 * u, arriba - self._norte, arriba
        if direccion == "S":
            return cx - 16 * u, cx + 16 * u, abajo, abajo + self._sur + 10 * u
        if direccion == "E":
            return der - self._muro - 8 * u, der, cy - 16 * u, cy + 16 * u
        return izq, izq + self._muro + 8 * u, cy - 16 * u, cy + 16 * u

    def _frente_a_puerta(self, direccion: str):
        izq, der, abajo, arriba = self._rect_puerta(direccion)
        cx, cy = (izq + der) / 2, (abajo + arriba) / 2
        u = self._u
        if direccion == "N":
            return cx, abajo - 7 * u
        if direccion == "S":
            return cx, arriba + 7 * u
        if direccion == "E":
            return izq - 7 * u, cy
        return der + 7 * u, cy

    def _dibujar_puerta_abierta(self, direccion: str) -> None:
        izq, der, abajo, arriba = self._rect_puerta(direccion)
        if direccion == "N":
            arcade.draw_texture_rect(texturas.puerta(True), arcade.LRBT(izq, der, abajo, arriba),
                                     pixelated=True)
            return
        # Hueco oscuro en el reborde, con un umbral verde del lado de la sala.
        arcade.draw_lrbt_rectangle_filled(izq, der, abajo, arriba, (14, 10, 11))
        if direccion == "S":
            arcade.draw_line(izq, arriba, der, arriba, _COLOR_PUERTA_ABIERTA, 2)
        else:
            x = izq if direccion == "E" else der
            arcade.draw_line(x, abajo, x, arriba, _COLOR_PUERTA_ABIERTA, 2)

    def _dibujar_puerta_cerrada(self, direccion: str) -> None:
        # La norte se ve de frente; en las demas, la misma hoja de 0x72
        # aplastada sobre el hueco se lee como una puerta vista de canto.
        izq, der, abajo, arriba = self._rect_puerta(direccion)
        arcade.draw_texture_rect(texturas.puerta(False), arcade.LRBT(izq, der, abajo, arriba),
                                 pixelated=True)
        cx, cy = (izq + der) / 2, (abajo + arriba) / 2
        lado = 12 * self._u
        arcade.draw_texture_rect(texturas.llave(), arcade.XYWH(cx, cy, lado, lado))

    # ------------------------------------------------------------------
    # Etiquetas
    # ------------------------------------------------------------------

    def _armar_etiquetas(self) -> None:
        tamano = max(min(int(self._radio * 0.45), 11), 7)
        if self._estado.nombre_jugador:
            cx, cy = self._centro()
            pies = cy - 28 * self._u * 1.25 / 2          # el caballero mide 28 px de 0x72
            self._nombre = arcade.Text(self._estado.nombre_jugador, cx, pies - tamano,
                                       (232, 193, 92), tamano, anchor_x="center",
                                       anchor_y="center", bold=True)
        for indice, enemigo in enumerate(self._estado.sala.enemigos):
            x, y = self.posicion_enemigo(indice)
            self._etiquetas.agregar_al_final(arcade.Text(
                enemigo.etiqueta, x, y - self._radio * 2.0, arcade.color.WHITE, tamano,
                anchor_x="center"))
        for indice, objeto in enumerate(self._estado.sala.objetos):
            x, y = self.posicion_objeto(indice)
            self._etiquetas.agregar_al_final(arcade.Text(
                objeto.nombre, x, y - self._radio * 1.9, (215, 210, 200), tamano,
                anchor_x="center"))
        for salida in self._estado.sala.salidas:
            if salida is not None and salida.estado != SALIDA_SIN_SALIDA:
                # La letra va justo adentro de la sala, frente a la puerta.
                x, y = self._frente_a_puerta(salida.direccion)
                self._etiquetas.agregar_al_final(arcade.Text(
                    salida.direccion, x, y, arcade.color.WHITE, tamano,
                    anchor_x="center", anchor_y="center", bold=True))


def _buscar_por_etiqueta(enemigos, etiqueta: str):
    """O(e). None si no hay lista o no está."""
    if enemigos is None:
        return None
    for enemigo in enemigos:
        if enemigo.etiqueta == etiqueta:
            return enemigo
    return None


# ----------------------------------------------------------------------
# Figuras sueltas (también las usa PantallaJuego para el inventario)
# ----------------------------------------------------------------------

def dibujar_barra(izquierda: float, abajo: float, ancho: float, alto: float,
                  valor: float, maximo: int) -> None:
    """Barra de vida: verde > 50 %, amarilla > 25 %, roja en lo demás."""
    fraccion = 0 if maximo <= 0 else max(0.0, min(1.0, valor / maximo))
    if fraccion > 0.5:
        color = (80, 190, 90)
    elif fraccion > 0.25:
        color = (220, 190, 60)
    else:
        color = (210, 60, 50)
    arcade.draw_lrbt_rectangle_filled(izquierda - 1, izquierda + ancho + 1, abajo - 1,
                                      abajo + alto + 1, (0, 0, 0, 160))
    arcade.draw_lrbt_rectangle_filled(izquierda, izquierda + ancho, abajo, abajo + alto,
                                      (45, 22, 22))
    if fraccion > 0:
        arcade.draw_lrbt_rectangle_filled(izquierda, izquierda + ancho * fraccion,
                                          abajo, abajo + alto, color)
        # brillo superior
        arcade.draw_lrbt_rectangle_filled(izquierda, izquierda + ancho * fraccion,
                                          abajo + alto * 0.6, abajo + alto, (255, 255, 255, 45))


def _dibujar_sombra(x: float, y: float, ancho: float, alfa: int = 255) -> None:
    arcade.draw_ellipse_filled(x, y, ancho * 1.6, ancho * 0.45, (0, 0, 0, 110 * alfa // 255))


def _dibujar_resalte(x: float, y: float, radio: float, t: float) -> None:
    pulso = 1 + math.sin(t * 6) * 0.06
    arcade.draw_circle_outline(x, y, radio * pulso, _COLOR_RESALTE, 3)
    arcade.draw_circle_outline(x, y, radio * pulso + 3, (255, 255, 0, 80), 2)


def dibujar_objeto(clase: str, x: float, y: float, r: float) -> None:
    """Un ícono por clase de objeto (las clases del catálogo, §2.7)."""
    if clase == "arma":
        alto = r * 2.2               # espada oxidada de 0x72 (10x21 px)
        arcade.draw_texture_rect(texturas.espada(), arcade.XYWH(x, y, alto * 10 / 21, alto),
                                 angle=-35, pixelated=True)
    elif clase == "armadura":
        contorno = ((x - r * 0.75, y + r * 0.7), (x + r * 0.75, y + r * 0.7),
                    (x + r * 0.65, y - r * 0.2), (x, y - r * 0.85), (x - r * 0.65, y - r * 0.2))
        arcade.draw_polygon_filled(contorno, (150, 105, 60))
        arcade.draw_polygon_outline(contorno, (90, 60, 30), 2)
        arcade.draw_line(x, y + r * 0.7, x, y - r * 0.85, (110, 75, 40), 2)
    elif clase == "pocion" or clase == "antidoto":
        lado = r * 2.0               # frascos de 0x72 (16x16 px)
        arcade.draw_texture_rect(texturas.frasco(clase == "pocion"), arcade.XYWH(x, y, lado, lado),
                                 pixelated=True)
    elif clase == "llave":
        lado = r * 1.9
        arcade.draw_texture_rect(texturas.llave(), arcade.XYWH(x, y, lado, lado))
    elif clase == "antorcha":
        arcade.draw_line(x, y - r * 0.8, x, y + r * 0.2, (130, 85, 40), 4)
        _dibujar_llama(x, y + r * 0.35, r * 0.45, 0.0)
    elif clase == "pergamino_retroceso":
        arcade.draw_lrbt_rectangle_filled(x - r * 0.6, x + r * 0.6, y - r * 0.5, y + r * 0.5,
                                          (225, 210, 165))
        arcade.draw_circle_filled(x - r * 0.6, y, r * 0.2, (190, 170, 120))
        arcade.draw_circle_filled(x + r * 0.6, y, r * 0.2, (190, 170, 120))
        for i in range(3):
            yy = y + r * 0.25 - i * r * 0.25
            arcade.draw_line(x - r * 0.35, yy, x + r * 0.35, yy, (120, 100, 70), 1)
    else:
        arcade.draw_circle_filled(x, y, r * 0.5, (170, 170, 170))


def _dibujar_llama(x: float, y: float, r: float, t: float) -> None:
    """Llama en tres capas; con t > 0 cambia de tamaño y se mece."""
    escala = 1 + math.sin(t * 17) * 0.12 + math.sin(t * 7.3) * 0.08
    mecer = math.sin(t * 5.1) * r * 0.25
    alto = r * 1.3 * escala
    arcade.draw_triangle_filled(x - r * 0.6, y - r * 0.3, x + r * 0.6, y - r * 0.3,
                                x + mecer, y + alto, (230, 90, 25))
    arcade.draw_triangle_filled(x - r * 0.4, y - r * 0.25, x + r * 0.4, y - r * 0.25,
                                x + mecer * 0.6, y + alto * 0.75, (250, 160, 40))
    arcade.draw_circle_filled(x, y - r * 0.1, r * 0.42, (255, 225, 110))


def _dibujar_enemigo(etiqueta: str, x: float, y: float, r: float, u: float, t: float,
                     alfa: int, tinte) -> None:
    nombre = etiqueta.lower()
    if "rata" in nombre:
        # Rata de Imogia (16x16, de costado): ocupa la mitad de abajo del
        # cuadro, así que se sube medio cuadro para centrarla en (x, y).
        lado = 16 * u * 2.0
        _dibujar_sombra(x, y - lado * 0.22, lado * 0.42, alfa)
        arcade.draw_texture_rect(texturas.rata(t), arcade.XYWH(x, y + lado * 0.2, lado, lado),
                                 color=tinte, alpha=alfa, pixelated=True)
    elif "óseo" in nombre or "oseo" in nombre or "esqueleto" in nombre or "guardi" in nombre:
        lado = 16 * u * 1.7          # el esqueleto de 0x72 mide 16x16
        _dibujar_sombra(x, y - lado * 0.45, lado * 0.45, alfa)
        arcade.draw_texture_rect(texturas.esqueleto(t), arcade.XYWH(x, y, lado, lado),
                                 color=tinte, alpha=alfa, pixelated=True)
    else:
        _dibujar_sombra(x, y - r * 1.0, r * 1.0, alfa)
        arcade.draw_circle_filled(x, y, r, (tinte.r * 170 // 255, 50, 60, alfa))
        arcade.draw_circle_filled(x - r * 0.35, y + r * 0.2, r * 0.18, (255, 255, 255, alfa))
        arcade.draw_circle_filled(x + r * 0.35, y + r * 0.2, r * 0.18, (255, 255, 255, alfa))


def _dibujar_jugador(x: float, y: float, u: float, antorcha: bool, golpeado: bool,
                     t: float, skin: str = texturas.SKIN_POR_DEFECTO) -> None:
    """El caballero de 0x72 (16x28 px) con su animación de reposo, o el
    cuadro de golpe mientras dura el destello de daño."""
    escala = u * 1.25
    ancho, alto = 16 * escala, 28 * escala
    _dibujar_sombra(x, y - alto * 0.47, ancho * 0.5)
    arcade.draw_texture_rect(texturas.heroe(skin, t, golpeado), arcade.XYWH(x, y, ancho, alto),
                             pixelated=True)
    if antorcha:
        mano_x = x + ancho * 0.55
        arcade.draw_line(mano_x, y - alto * 0.15, mano_x, y + alto * 0.12, (120, 78, 36), 3)
        _dibujar_llama(mano_x, y + alto * 0.17, ancho * 0.22, t)
