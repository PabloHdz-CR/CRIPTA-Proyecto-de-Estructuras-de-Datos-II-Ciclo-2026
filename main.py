"""Bootstrap de Cripta. Cede el control a FabricaAplicacion (D44).

    python main.py [--offline] [--cache-size N] [--forzar]
    python main.py --replay partidas/x.log
    python main.py --verificar ID [--offline[=CARPETA]]
    python main.py --bench [--rapido]
"""
from __future__ import annotations

import sys

from cripta.controlador.fabricaAplicacion import FabricaAplicacion


def _salida_utf8() -> None:
    """La salida de texto va en UTF-8 aunque se redirija a un archivo.

    En Windows, con la salida redirigida (py main.py --bench > archivo.txt),
    Python usa la página de códigos del sistema (cp1252), que no tiene
    caracteres como "≤" o "µ" de los reportes, y el programa terminaba con
    UnicodeEncodeError. Solo cambia la codificación de stdout y stderr; el
    modelo no se entera. Si el flujo no es un archivo de texto del sistema
    (por ejemplo, uno que una prueba puso en su lugar), se deja como está.
    """
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is not None:
            reconfigurar(encoding="utf-8")


def ejecutar() -> None:
    _salida_utf8()
    FabricaAplicacion().ejecutar()


if __name__ == "__main__":
    ejecutar()
