"""El tigre humanoide: skin del héroe dibujada como pixel art propio (§10.2).

Ningún paquete de recursos trae un tigre, así que se dibuja aquí, pixel a
pixel, con las reglas del estilo de 0x72 para que combine con el resto:
16x28 px, contorno oscuro de 1 px, cabeza grande, 2-3 tonos por color con
brillo en un borde, mirando a la derecha. Es diseño propio del equipo: no
tiene licencia de terceros.

Animación (como los personajes de 0x72): 4 cuadros de reposo -- base,
respira (el torso baja 1 px y la cola se mece) dos veces, y un parpadeo -- y
un cuadro de golpe (todo más claro y los ojos entrecerrados).

DECISIÓN: el dibujo es un patrón de texto (una letra por pixel) y la paleta
una tupla de pares (letra, color): sin dict (§7). Traducir una letra a su
color recorre la paleta (16 entradas), y cada cuadro se genera una sola vez
al cargarlo. Los cuadros derivados (respirar, parpadear, golpe) se calculan
desde la pose base, así cualquier retoque del dibujo se aplica a todos.
"""
from __future__ import annotations

from PIL import Image

ANCHO = 16
ALTO = 28

PALETA = (
    (".", (0, 0, 0, 0)),
    ("k", (34, 24, 26, 255)),      # contorno
    ("O", (236, 140, 44, 255)),    # pelaje naranja
    ("o", (190, 96, 34, 255)),     # naranja en sombra
    ("h", (252, 188, 92, 255)),    # naranja con brillo
    ("W", (250, 238, 214, 255)),   # pelaje crema
    ("s", (52, 32, 30, 255)),      # rayas
    ("G", (156, 222, 92, 255)),    # ojo
    ("P", (226, 112, 122, 255)),   # nariz
    ("V", (66, 102, 168, 255)),    # chaleco
    ("v", (44, 68, 120, 255)),     # chaleco en sombra
    ("L", (122, 78, 42, 255)),     # cinturón
    ("Y", (236, 196, 84, 255)),    # hebilla
    ("M", (196, 204, 214, 255)),   # hombrera de metal
    ("m", (128, 136, 150, 255)),   # metal en sombra
)

# Pose base. Filas 0-5 vacías (como los personajes de 0x72, para que todos
# los héroes tengan la misma caja de 16x28 y el mismo punto de apoyo).
_BASE = (
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "...kk.....kk....",
    "..kskk...kksk...",
    "..kOhok.koOhk...",
    "..kOWOkkkOWOk...",
    "..kOOsOsOsOOOk..",
    ".kOOOsOsOsOOhOk.",
    ".kOOOOOOOOOOOhk.",
    ".kosOOOOOkkOOOk.",
    ".koOOOOOOkGWOWWk",
    ".kossOOOOOOWWWPk",
    ".koOOsOOOWWWWWkk",
    "..koOOOOWWkkWWk.",
    "k..kooOWWWWWWk..",
    "Ok..kkkWWWWkk...",
    "sOk.kMmkWWVVkk..",
    "kOOkOMMVWWVVhOk.",
    ".kOkOsVvWWvVsOk.",
    "..kkkLLLYYLLLkk.",
    "....kVVVVVVVVk..",
    "....kOsOkkOsOk..",
    "....kWWk..kWWk..",
    "....kkkk..kkkk..",
)

# La cola en la otra posición del vaivén: sube 1 px. Solo las columnas 0 a
# 2 de las filas 17 a 20 (la columna 2 de la fila 17 es el contorno de la
# cabeza y se conserva).
_COLA_MECIDA = (
    (17, "k.k"),
    (18, "Ok."),
    (19, "sOk"),
    (20, "kOk"),
)
_FILA_OJO = 14          # "kG": iris y pupila
_COLUMNA_OJO = 9        # el ojo ocupa las columnas 9 y 10 de las filas 13 y 14
_PRIMERA_FILA_PIERNAS = 23


def _reemplazar(fila: str, desde: int, texto: str) -> str:
    return fila[:desde] + texto + fila[desde + len(texto):]


def _con_cola_mecida(patron):
    filas = patron
    for numero, tramo in _COLA_MECIDA:
        filas = filas[:numero] + (_reemplazar(filas[numero], 0, tramo),) + filas[numero + 1:]
    return filas


def _respirando(patron):
    """El torso y la cabeza bajan 1 px; las piernas no se mueven."""
    arriba = patron[:_PRIMERA_FILA_PIERNAS - 1]
    return ("." * ANCHO,) + arriba + patron[_PRIMERA_FILA_PIERNAS:]


def _parpadeando(patron):
    """Ojo cerrado: la fila de arriba del ojo pasa a ser pelaje y la de
    abajo una línea oscura (el párpado)."""
    arriba = _reemplazar(patron[_FILA_OJO - 1], _COLUMNA_OJO, "OO")
    abajo = _reemplazar(patron[_FILA_OJO], _COLUMNA_OJO, "kk")
    return patron[:_FILA_OJO - 1] + (arriba, abajo) + patron[_FILA_OJO + 1:]


def patrones_reposo():
    """Los 4 cuadros de reposo, como tupla de patrones."""
    mecida = _con_cola_mecida(_BASE)
    return (_BASE, _respirando(mecida), _respirando(mecida), _parpadeando(_BASE))


def _color(letra: str):
    for clave, color in PALETA:
        if clave == letra:
            return color
    raise ValueError(f"Letra sin color en la paleta del tigre: {letra!r}")


def imagen(patron, aclarar: float = 0.0) -> Image.Image:
    """El patrón como imagen RGBA de 16x28. aclarar (0 a 1) mezcla cada
    color con blanco, salvo el contorno (para el cuadro de golpe)."""
    resultado = Image.new("RGBA", (ANCHO, ALTO))
    for y, fila in enumerate(patron):
        if len(fila) != ANCHO:
            raise ValueError(f"La fila {y} del tigre mide {len(fila)}, no {ANCHO}")
        for x, letra in enumerate(fila):
            r, g, b, a = _color(letra)
            if aclarar > 0 and letra != "k" and a > 0:
                r = int(r + (255 - r) * aclarar)
                g = int(g + (255 - g) * aclarar)
                b = int(b + (255 - b) * aclarar)
            resultado.putpixel((x, y), (r, g, b, a))
    return resultado


def imagenes_reposo():
    patrones = patrones_reposo()
    return (imagen(patrones[0]), imagen(patrones[1]), imagen(patrones[2]), imagen(patrones[3]))


def imagen_golpe() -> Image.Image:
    return imagen(_parpadeando(_BASE), aclarar=0.55)
