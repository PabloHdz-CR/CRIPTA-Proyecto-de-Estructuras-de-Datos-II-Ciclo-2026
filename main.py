"""Bootstrap de Cripta. Cede el control a FabricaAplicacion (D44).

    python main.py [--offline] [--cache-size N]
    python main.py --replay partidas/x.log
    python main.py --bench [--rapido]
"""
from __future__ import annotations

from cripta.controlador.fabricaAplicacion import FabricaAplicacion


def ejecutar() -> None:
    FabricaAplicacion().ejecutar()


if __name__ == "__main__":
    ejecutar()
