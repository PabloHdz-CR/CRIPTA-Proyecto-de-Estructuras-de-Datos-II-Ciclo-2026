"""Texturas de la Vista: sprites de pixel art y fondos generados (§10.2).

Tres fuentes:

- "16x16 DungeonTileset II" de 0x72 (licencia CC0, ver
  recursos/dungeon_0x72/LICENCIA.txt): piso, muros, estandartes, calaveras,
  puertas, las skins del héroe (caballero, caballera, elfa, mago, lagarto,
  enano), el esqueleto (guardián óseo), frascos, la espada y los corazones.
  Solo se copiaron al proyecto los cuadros que se usan.
- Pixel art propio (pixelTigre.py): el tigre humanoide, skin por defecto.
- "8 bit art pack rat monster" de Imogia Games (licencia CC BY 4.0, ver
  recursos/rata_imogia/LICENCIA.txt): la rata gigante, que 0x72 no trae.
- Sprites de ":resources:" (Kenney, CC0, vienen DENTRO de arcade): la llave,
  que tampoco trae 0x72.
- Imágenes generadas con Pillow (dependencia de arcade): el fondo de cada
  sala armado con las baldosas de 0x72, y las capas de luz de la antorcha.

DECISIÓN: el fondo de la sala se arma UNA vez por sala (12x12 baldosas de
16 px) y se dibuja como una sola textura por cuadro, en vez de 144 sprites
sueltos. Alternativa descartada: arcade.shape_list.ShapeElementList o
SpriteList, que solo se llenan con .append (prohibido por prueba_reglas,
D27).

DECISIÓN: el pixel art se escala con vecino más cercano (Image.NEAREST y
pixelated=True al dibujar) para que no se vea borroso.

DECISIÓN: sin dict como caché (§7). Los sprites se guardan en atributos de
una clase (_Sprites), cargados la primera vez que se piden; las animaciones
son tuplas de cuadros (inmutables, permitidas). Los fondos recuerdan solo el
último generado (una sala a la vez).
"""
from __future__ import annotations

import random
from pathlib import Path

import arcade
from PIL import Image

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from . import pixelTigre

_RUTA_KENNEY = ":resources:images/"
_CARPETA_0X72 = Path(__file__).resolve().parent / "recursos" / "dungeon_0x72"
_TIRA_RATA = (Path(__file__).resolve().parent / "recursos" / "rata_imogia"
              / "MOB-8Bit-Rat-Var-04-byImogiaGames.png")

# Geometría del fondo en baldosas de 16 px (también la usa DibujoSala para
# saber dónde terminan los muros).
BALDOSAS = 12
PIXELES_FONDO = BALDOSAS * 16
FRACCION_NORTE = 32 / PIXELES_FONDO     # dos filas: borde superior + cara de ladrillo
FRACCION_SUR = 4 / PIXELES_FONDO        # el reborde inferior mide 4 px
FRACCION_LATERAL = 4 / PIXELES_FONDO    # los bordes laterales miden 4 px
_CUADROS_POR_SEGUNDO = 6


def _archivo_0x72(nombre: str) -> Path:
    return _CARPETA_0X72 / f"{nombre}.png"


def _cargar_0x72(nombre: str) -> arcade.Texture:
    return arcade.load_texture(_archivo_0x72(nombre))


def _cargar_kenney(ruta: str) -> arcade.Texture:
    return arcade.load_texture(_RUTA_KENNEY + ruta)


class _Sprites:
    esqueleto = None          # tupla de 4 cuadros
    frasco_rojo = None
    frasco_verde = None
    espada = None
    puerta_cerrada = None
    puerta_abierta = None
    rata = None               # tupla de 2 cuadros (de costado)
    llave = None
    calavera = None


def _cuadros(prefijo: str):
    return (_cargar_0x72(f"{prefijo}_f0"), _cargar_0x72(f"{prefijo}_f1"),
            _cargar_0x72(f"{prefijo}_f2"), _cargar_0x72(f"{prefijo}_f3"))


def _cuadro_actual(cuadros, t: float):
    return cuadros[int(t * _CUADROS_POR_SEGUNDO) % len(cuadros)]


# ----------------------------------------------------------------------
# Skins del héroe
# ----------------------------------------------------------------------

# (id, nombre visible, prefijo de 0x72). El tigre no tiene prefijo: es
# pixel art propio (pixelTigre.py). Todas miden 16x28 y tienen 4 cuadros de
# reposo y uno de golpe, así se dibujan igual.
SKINS = (
    ("tigre", "Tigre", None),
    ("caballero", "Caballero", "knight_m"),
    ("caballera", "Caballera", "knight_f"),
    ("elfa", "Elfa", "elf_f"),
    ("mago", "Mago", "wizzard_m"),
    ("lagarto", "Lagarto", "lizard_m"),
    ("enano", "Enano", "dwarf_m"),
)
SKIN_POR_DEFECTO = "tigre"


class _Heroes:
    # DECISIÓN: sin dict (§7): una ListaEnlazada de (id, cuadros, golpe)
    # con las skins ya cargadas. Son 7 a lo sumo: buscar es O(7).
    cargados = None


def nombre_skin(id_skin: str) -> str:
    for clave, nombre, _ in SKINS:
        if clave == id_skin:
            return nombre
    return id_skin


def skin_vecina(id_skin: str, paso: int) -> str:
    """La skin siguiente (paso 1) o anterior (paso -1), dando la vuelta."""
    cantidad = len(SKINS)
    for indice, (clave, _, _) in enumerate(SKINS):
        if clave == id_skin:
            return SKINS[(indice + paso) % cantidad][0]
    return SKIN_POR_DEFECTO


def _cargar_heroe(id_skin: str):
    for clave, _, prefijo in SKINS:
        if clave != id_skin:
            continue
        if prefijo is None:
            imagenes = pixelTigre.imagenes_reposo()
            cuadros = tuple(arcade.Texture(imagenes[i], hash=f"cripta-tigre-f{i}")
                            for i in range(4))
            golpe = arcade.Texture(pixelTigre.imagen_golpe(), hash="cripta-tigre-golpe")
        else:
            cuadros = _cuadros(f"{prefijo}_idle_anim")
            golpe = _cargar_0x72(f"{prefijo}_hit_anim_f0")
        return cuadros, golpe
    return _cargar_heroe(SKIN_POR_DEFECTO)


def heroe(id_skin: str, t: float, golpeado: bool) -> arcade.Texture:
    """El cuadro del héroe con esa skin: el de golpe, o el de reposo que
    toca según el tiempo. Cada skin se carga la primera vez que se pide."""
    if _Heroes.cargados is None:
        _Heroes.cargados = ListaEnlazada()
    for clave, cuadros, golpe in _Heroes.cargados:
        if clave == id_skin:
            return golpe if golpeado else _cuadro_actual(cuadros, t)
    cuadros, golpe = _cargar_heroe(id_skin)
    _Heroes.cargados.agregar_al_final((id_skin, cuadros, golpe))
    return golpe if golpeado else _cuadro_actual(cuadros, t)


def esqueleto(t: float) -> arcade.Texture:
    if _Sprites.esqueleto is None:
        _Sprites.esqueleto = _cuadros("skelet_idle_anim")
    return _cuadro_actual(_Sprites.esqueleto, t)


def frasco(rojo: bool) -> arcade.Texture:
    if _Sprites.frasco_rojo is None:
        _Sprites.frasco_rojo = _cargar_0x72("flask_red")
        _Sprites.frasco_verde = _cargar_0x72("flask_green")
    return _Sprites.frasco_rojo if rojo else _Sprites.frasco_verde


def espada() -> arcade.Texture:
    if _Sprites.espada is None:
        _Sprites.espada = _cargar_0x72("weapon_rusty_sword")
    return _Sprites.espada


def puerta(abierta: bool) -> arcade.Texture:
    if _Sprites.puerta_cerrada is None:
        _Sprites.puerta_cerrada = _cargar_0x72("doors_leaf_closed")
        _Sprites.puerta_abierta = _cargar_0x72("doors_leaf_open")
    return _Sprites.puerta_abierta if abierta else _Sprites.puerta_cerrada


def rata(t: float) -> arcade.Texture:
    """La tira de Imogia trae 4 cuadros de 16x16: los dos primeros son la
    rata de costado (los que combinan con la perspectiva de 0x72), los dos
    últimos vista desde arriba. Se recortan al cargar; el archivo no se toca."""
    if _Sprites.rata is None:
        tira = Image.open(_TIRA_RATA).convert("RGBA")
        _Sprites.rata = (
            arcade.Texture(tira.crop((0, 0, 16, 16)), hash="cripta-rata-imogia-f0"),
            arcade.Texture(tira.crop((16, 0, 32, 16)), hash="cripta-rata-imogia-f1"))
    # Dos cuadros: se alternan más lento que los de 0x72 (que tienen cuatro).
    return _Sprites.rata[int(t * _CUADROS_POR_SEGUNDO / 2) % 2]


def llave() -> arcade.Texture:
    if _Sprites.llave is None:
        _Sprites.llave = _cargar_kenney("items/keyYellow.png")
    return _Sprites.llave


# ----------------------------------------------------------------------
# Fondo de la sala
# ----------------------------------------------------------------------

class _UltimoFondo:
    clave = None
    textura = None


def fondo_sala(nombre_sala: str, lado_px: int) -> arcade.Texture:
    """Piso de baldosas, muro norte de ladrillo con estandartes, bordes
    laterales y reborde sur. Cada sala tiene su propia variación (semilla =
    su nombre), pero siempre la misma para la misma sala."""
    escala = max(1, round(lado_px / PIXELES_FONDO))
    clave = (nombre_sala, escala)
    if _UltimoFondo.clave == clave:
        return _UltimoFondo.textura

    # DECISIÓN: semilla determinista a partir del nombre (hash() de Python
    # cambia entre ejecuciones).
    semilla = 0
    for caracter in nombre_sala:
        semilla = (semilla * 31 + ord(caracter)) % 1000003
    azar = random.Random(semilla)

    imagen = Image.new("RGBA", (PIXELES_FONDO, PIXELES_FONDO), (12, 9, 10, 255))
    _armar_sala(imagen, azar)
    if escala > 1:
        imagen = imagen.resize((PIXELES_FONDO * escala, PIXELES_FONDO * escala), Image.NEAREST)

    textura = arcade.Texture(imagen, hash=f"cripta-fondo-0x72-{semilla}-{escala}")
    _UltimoFondo.clave = clave
    _UltimoFondo.textura = textura
    return textura


def _armar_sala(imagen, azar) -> None:
    ultima = BALDOSAS - 1

    def poner(nombre: str, columna: int, fila: int) -> None:
        baldosa = Image.open(_archivo_0x72(nombre)).convert("RGBA")
        imagen.alpha_composite(baldosa, (columna * 16, fila * 16))

    # Piso (también debajo de los bordes, que son transparentes por dentro).
    for fila in range(2, BALDOSAS):
        for columna in range(BALDOSAS):
            if azar.random() < 0.85:
                poner("floor_1", columna, fila)
            else:
                poner(f"floor_{azar.randint(2, 8)}", columna, fila)

    # Muro norte: borde superior + cara de ladrillo.
    for columna in range(1, ultima):
        poner("wall_top_mid", columna, 0)
        poner("wall_mid", columna, 1)
    poner("wall_top_left", 0, 0)
    poner("wall_top_right", ultima, 0)
    poner("wall_left", 0, 1)
    poner("wall_right", ultima, 1)

    # Estandartes en la cara de ladrillo, lejos del centro (ahí va la
    # puerta norte, si la hay). Un solo color por sala.
    colores = ("red", "blue", "green", "yellow")
    color = colores[azar.randint(0, 3)]
    for columna in (2, 3, 8, 9):
        if azar.random() < 0.35:
            poner(f"wall_banner_{color}", columna, 1)

    # Bordes laterales y reborde sur.
    for fila in range(2, ultima):
        poner("wall_edge_mid_left", 0, fila)
        poner("wall_edge_mid_right", ultima, fila)
    for columna in range(1, ultima):
        poner("wall_top_mid", columna, ultima)
    poner("wall_edge_bottom_left", 0, ultima)
    poner("wall_edge_bottom_right", ultima, ultima)

    # Alguna calavera en un rincón, como adorno.
    for _ in range(azar.randint(0, 2)):
        columna = azar.choice((1, 2, 9, 10))
        fila = azar.choice((3, 9, 10))
        poner("skull", columna, fila)


class _UltimoFondoPantalla:
    clave = None
    textura = None


def fondo_pantalla(ancho_px: int, alto_px: int, escala: int) -> arcade.Texture:
    """Piso de 0x72 cubriendo toda la ventana, oscurecido, para los menús.
    Siempre la misma semilla: el menú se ve igual en cada visita."""
    escala = max(1, escala)
    clave = (ancho_px, alto_px, escala)
    if _UltimoFondoPantalla.clave == clave:
        return _UltimoFondoPantalla.textura
    azar = random.Random(72)
    columnas = ancho_px // (16 * escala) + 1
    filas = alto_px // (16 * escala) + 1
    imagen = Image.new("RGBA", (columnas * 16, filas * 16), (12, 9, 10, 255))
    for fila in range(filas):
        for columna in range(columnas):
            nombre = "floor_1" if azar.random() < 0.8 else f"floor_{azar.randint(2, 8)}"
            baldosa = Image.open(_archivo_0x72(nombre)).convert("RGBA")
            imagen.alpha_composite(baldosa, (columna * 16, fila * 16))
    oscurecer = Image.new("RGBA", imagen.size, (8, 5, 6, 150))
    imagen = Image.alpha_composite(imagen, oscurecer)
    imagen = imagen.resize((imagen.width * escala, imagen.height * escala), Image.NEAREST)
    imagen = imagen.crop((0, 0, ancho_px, alto_px))
    textura = arcade.Texture(imagen, hash=f"cripta-fondo-pantalla-{ancho_px}-{alto_px}-{escala}")
    _UltimoFondoPantalla.clave = clave
    _UltimoFondoPantalla.textura = textura
    return textura


class _Corazones:
    lleno = None
    medio = None
    vacio = None


def corazon(fraccion: float) -> arcade.Texture:
    """Corazón de la interfaz de 0x72 según la vida que queda: lleno, medio
    (menos de la mitad) o vacío (sin vida)."""
    if _Corazones.lleno is None:
        _Corazones.lleno = _cargar_0x72("ui_heart_full")
        _Corazones.medio = _cargar_0x72("ui_heart_half")
        _Corazones.vacio = _cargar_0x72("ui_heart_empty")
    if fraccion <= 0:
        return _Corazones.vacio
    return _Corazones.medio if fraccion < 0.5 else _Corazones.lleno


def calavera() -> arcade.Texture:
    if _Sprites.calavera is None:
        _Sprites.calavera = _cargar_0x72("skull")
    return _Sprites.calavera


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
