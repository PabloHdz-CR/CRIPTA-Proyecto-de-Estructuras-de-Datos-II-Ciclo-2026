"""Convención de nombres de archivo compartida por los adaptadores de disco."""
from __future__ import annotations


def nombre_seguro(texto: object) -> str:
    """Reemplaza lo que no sea letra, dígito, '-', '_' o '.' por '_': un id de
    cripta viene del API y no se puede confiar en que sea un nombre válido.
    O(n) en la longitud del id (n pequeño: decenas de caracteres)."""
    seguro = ""
    for caracter in str(texto):
        seguro += caracter if (caracter.isalnum() or caracter in "-_.") else "_"
    return seguro
