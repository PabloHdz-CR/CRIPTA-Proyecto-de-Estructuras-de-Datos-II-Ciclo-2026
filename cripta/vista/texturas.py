"""Texturas de la Vista: sprites que trae arcade y fondos generados (§10.2).

Dos fuentes, ninguna agrega archivos al repositorio:

- Sprites de ":resources:" (el paquete de Kenney, licencia CC0, que viene
  instalado DENTRO de arcade): jugador, rata, guardián y llave.
- Imágenes generadas con Pillow (dependencia de arcade): el fondo de cada
  sala (baldosas de piedra + muros de ladrillo) y las capas de luz de la
  antorcha.

DECISIÓN: el fondo de la sala se genera UNA vez por sala y se dibuja como
una sola textura por cuadro, en vez de ~100 figuras sueltas. Alternativa
descartada: arcade.shape_list.ShapeElementList, que solo se llena con
.append (prohibido por prueba_reglas, D27).

DECISIÓN: sin dict como caché (§7). Los sprites se guardan en atributos de
una clase (_Sprites), cargados la primera vez que se piden; los fondos
recuerdan solo el último generado (una sala a la vez): si se vuelve a pedir
el mismo, no se regenera. arcade.load_texture ya evita cargar dos veces el
mismo archivo.
"""
from __future__ import annotations

import random

import arcade
from PIL import Image, ImageDraw, ImageFilter

_RUTA = ":resources:images/"


class _Sprites:
    jugador = None
    jugador_paso = None
    rata = None
    guardian = None
    guardian_paso = None
    llave = None


def _cargar(ruta: str) -> arcade.Texture:
    return arcade.load_texture(_RUTA + ruta)


def jugador(paso: bool) -> arcade.Texture:
    if _Sprites.jugador is None:
        _Sprites.jugador = _cargar("animated_characters/male_adventurer/maleAdventurer_idle.png")
        _Sprites.jugador_paso = _cargar(
            "animated_characters/male_adventurer/maleAdventurer_walk1.png")
    return _Sprites.jugador_paso if paso else _Sprites.jugador


def rata() -> arcade.Texture:
    if _Sprites.rata is None:
        _Sprites.rata = _cargar("enemies/mouse.png")
    return _Sprites.rata


def guardian(paso: bool) -> arcade.Texture:
    if _Sprites.guardian is None:
        _Sprites.guardian = _cargar("animated_characters/zombie/zombie_idle.png")
        _Sprites.guardian_paso = _cargar("animated_characters/zombie/zombie_walk1.png")
    return _Sprites.guardian_paso if paso else _Sprites.guardian


def llave() -> arcade.Texture:
    if _Sprites.llave is None:
        _Sprites.llave = _cargar("items/keyYellow.png")
    return _Sprites.llave


# ----------------------------------------------------------------------
# Fondo de la sala
# ----------------------------------------------------------------------

class _UltimoFondo:
    clave = None
    textura = None


def fondo_sala(nombre_sala: str, lado_px: int, muro_px: int,
               baldosas: int) -> arcade.Texture:
    """Piso de baldosas irregulares y muros de ladrillo, con sombra en el
    borde interior. Cada sala tiene su propia variación (semilla = su
    nombre), pero siempre la misma para la misma sala."""
    clave = (nombre_sala, lado_px, muro_px, baldosas)
    if _UltimoFondo.clave == clave:
        return _UltimoFondo.textura

    # DECISIÓN: semilla determinista a partir del nombre (hash() de Python
    # cambia entre ejecuciones).
    semilla = 0
    for caracter in nombre_sala:
        semilla = (semilla * 31 + ord(caracter)) % 1000003
    azar = random.Random(semilla)

    imagen = Image.new("RGBA", (lado_px, lado_px), (30, 27, 25, 255))
    dibujo = ImageDraw.Draw(imagen)
    _pintar_piso(dibujo, azar, lado_px, muro_px, baldosas)
    _pintar_muros(imagen, lado_px, muro_px)
    _pintar_sombra_interior(imagen, lado_px, muro_px)

    textura = arcade.Texture(imagen, hash=f"cripta-fondo-{semilla}-{lado_px}-{muro_px}")
    _UltimoFondo.clave = clave
    _UltimoFondo.textura = textura
    return textura


def _pintar_piso(dibujo, azar, lado_px, muro_px, baldosas) -> None:
    interior = lado_px - 2 * muro_px
    paso = interior / baldosas
    junta = max(int(paso * 0.06), 1)
    for fila in range(baldosas):
        for columna in range(baldosas):
            x0 = muro_px + columna * paso + junta
            y0 = muro_px + fila * paso + junta
            x1 = muro_px + (columna + 1) * paso - junta
            y1 = muro_px + (fila + 1) * paso - junta
            base = azar.randint(62, 82)
            tono = (base, base - 6 + azar.randint(-3, 3), base - 12 + azar.randint(-3, 3), 255)
            dibujo.rounded_rectangle((x0, y0, x1, y1), radius=max(int(paso * 0.08), 1),
                                     fill=tono)
            # brillo arriba-izquierda y sombra abajo-derecha: relieve
            dibujo.line((x0 + 1, y0 + 1, x1 - 1, y0 + 1), fill=(base + 14, base + 10, base + 4, 255))
            dibujo.line((x0 + 1, y1 - 1, x1 - 1, y1 - 1), fill=(base - 22, base - 26, base - 30, 255))
            # manchas y grietas
            for _ in range(azar.randint(2, 6)):
                px = azar.uniform(x0 + 2, x1 - 2)
                py = azar.uniform(y0 + 2, y1 - 2)
                r = azar.uniform(0.5, paso * 0.05)
                oscuro = base - azar.randint(10, 22)
                dibujo.ellipse((px - r, py - r, px + r, py + r),
                               fill=(oscuro, oscuro - 4, oscuro - 8, 255))
            if azar.random() < 0.18:
                px, py = azar.uniform(x0, x1), azar.uniform(y0, y1)
                for _ in range(3):
                    nx = px + azar.uniform(-paso * 0.25, paso * 0.25)
                    ny = py + azar.uniform(-paso * 0.25, paso * 0.25)
                    dibujo.line((px, py, nx, ny), fill=(base - 30, base - 34, base - 38, 255),
                                width=1)
                    px, py = nx, ny


def _pintar_muros(imagen, lado_px, muro_px) -> None:
    ladrillo = Image.open(arcade.resources.resolve(_RUTA + "tiles/brickGrey.png")).convert("RGBA")
    ladrillo = ladrillo.resize((muro_px, muro_px), Image.LANCZOS)
    oscurecer = Image.new("RGBA", ladrillo.size, (32, 22, 16, 165))
    ladrillo = Image.alpha_composite(ladrillo, oscurecer)
    for i in range(0, lado_px, muro_px):
        imagen.paste(ladrillo, (i, 0))
        imagen.paste(ladrillo, (i, lado_px - muro_px))
        imagen.paste(ladrillo, (0, i))
        imagen.paste(ladrillo, (lado_px - muro_px, i))


def _pintar_sombra_interior(imagen, lado_px, muro_px) -> None:
    """Sombra que proyectan los muros sobre el piso: un marco negro
    difuminado justo adentro del muro."""
    sombra = Image.new("RGBA", (lado_px, lado_px), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(sombra)
    ancho = max(muro_px // 2, 2)
    dibujo.rectangle((muro_px, muro_px, lado_px - muro_px, lado_px - muro_px),
                     outline=(0, 0, 0, 170), width=ancho)
    sombra = sombra.filter(ImageFilter.GaussianBlur(ancho * 0.8))
    imagen.alpha_composite(sombra)
    # borde del muro, para separarlo del piso
    ImageDraw.Draw(imagen).rectangle(
        (muro_px - 1, muro_px - 1, lado_px - muro_px, lado_px - muro_px),
        outline=(20, 17, 15, 255), width=2)


# ----------------------------------------------------------------------
# Luz de la antorcha
# ----------------------------------------------------------------------

class _Luces:
    oscuridad_encendida = None
    oscuridad_apagada = None
    resplandor = None


def _degradado_radial(tamano: int, centro_claro: float, borde: float, color, alfa_max: int,
                      invertido: bool, hash_textura: str) -> arcade.Texture:
    """Textura cuadrada con un degradado circular. invertido=False: opaco
    al centro y transparente afuera (resplandor). invertido=True: al revés
    (oscuridad con un hueco de luz al centro)."""
    imagen = Image.new("RGBA", (tamano, tamano), (0, 0, 0, 0))
    pixeles = imagen.load()
    mitad = tamano / 2
    for y in range(tamano):
        for x in range(tamano):
            d = (((x - mitad) ** 2 + (y - mitad) ** 2) ** 0.5) / mitad
            if d <= centro_claro:
                f = 0.0
            elif d >= borde:
                f = 1.0
            else:
                f = (d - centro_claro) / (borde - centro_claro)
                f = f * f * (3 - 2 * f)      # suavizado (smoothstep)
            alfa = int(alfa_max * (f if invertido else 1 - f))
            pixeles[x, y] = (color[0], color[1], color[2], alfa)
    return arcade.Texture(imagen, hash=hash_textura)


def oscuridad(antorcha_encendida: bool) -> arcade.Texture:
    if _Luces.oscuridad_encendida is None:
        _Luces.oscuridad_encendida = _degradado_radial(
            128, 0.30, 1.15, (8, 5, 3), 200, True, "cripta-oscuridad-encendida")
        _Luces.oscuridad_apagada = _degradado_radial(
            128, 0.05, 0.70, (4, 4, 8), 225, True, "cripta-oscuridad-apagada")
    return _Luces.oscuridad_encendida if antorcha_encendida else _Luces.oscuridad_apagada


def resplandor() -> arcade.Texture:
    if _Luces.resplandor is None:
        _Luces.resplandor = _degradado_radial(
            128, 0.0, 1.0, (255, 160, 60), 70, False, "cripta-resplandor")
    return _Luces.resplandor
