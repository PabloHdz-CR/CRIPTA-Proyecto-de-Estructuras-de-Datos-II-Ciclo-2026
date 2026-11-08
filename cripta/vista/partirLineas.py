"""Partir una línea de texto en filas que quepan en un ancho (Vista).

Lo usan el panel de la tecla V (hudJuego) y PantallaResolubilidad para
mostrar el reporte de resolubilidad completo, sin recortar (003-resolubilidad,
contracts/vista.md). El texto canónico (textoResolubilidad,
contracts/reporte.md) no cambia: esto es solo presentación.

Reglas de partir_linea(texto, maximo, sangria):
  - ninguna fila supera 'maximo' caracteres;
  - se corta en el último espacio que cabe; si no hay ninguno (una palabra
    más larga que la fila), se corta la palabra;
  - las filas de continuación empiezan con 'sangria' (dos espacios);
  - no se pierde texto: la primera fila más las demás SIN la sangría, unidas,
    son exactamente la línea original. Por eso el espacio del corte queda al
    final de la fila anterior (no se ve) y no al principio de la siguiente;
  - los espacios del principio de la línea (la sangría propia del reporte,
    "  1. ...") no cuentan como lugar de corte.

Complejidad: O(largo de la línea). Sin list (D27): devuelve ListaEnlazada.
"""
from __future__ import annotations

from ..modelo.estructuras.listaEnlazada import ListaEnlazada

SANGRIA_CONTINUACION = "  "


def _espacios_iniciales(texto: str) -> int:
    cantidad = 0
    for caracter in texto:
        if caracter != " ":
            break
        cantidad += 1
    return cantidad


def partir_linea(texto: str, maximo: int, sangria: str = SANGRIA_CONTINUACION) -> ListaEnlazada:
    """Las filas de 'texto' con a lo sumo 'maximo' caracteres cada una."""
    # Una fila de continuación necesita lugar para la sangría y al menos un
    # carácter de texto.
    maximo = max(maximo, len(sangria) + 1)
    filas = ListaEnlazada()
    resto = texto
    primera = True
    while True:
        prefijo = "" if primera else sangria
        disponible = maximo - len(prefijo)
        if len(resto) <= disponible:
            filas.agregar_al_final(prefijo + resto)
            return filas
        protegidos = _espacios_iniciales(resto) if primera else 0
        espacio = resto.rfind(" ", protegidos, disponible)
        corte = espacio + 1 if espacio >= protegidos else disponible
        filas.agregar_al_final(prefijo + resto[:corte])
        resto = resto[corte:]
        primera = False


def partir_lineas(lineas, maximo: int, sangria: str = SANGRIA_CONTINUACION) -> ListaEnlazada:
    """Todas las filas de varias líneas, en orden."""
    filas = ListaEnlazada()
    for linea in lineas:
        for fila in partir_linea(linea, maximo, sangria):
            filas.agregar_al_final(fila)
    return filas


def unir_filas(filas, sangria: str = SANGRIA_CONTINUACION) -> str:
    """La línea original a partir de sus filas (para las pruebas): la primera
    tal cual y las demás sin la sangría."""
    texto = ""
    primera = True
    for fila in filas:
        texto += fila if primera else fila[len(sangria):]
        primera = False
    return texto
