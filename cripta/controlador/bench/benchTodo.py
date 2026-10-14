"""Corre TODAS las mediciones del programa, una tras otra.

Desde la carpeta que contiene 'cripta':
    python -m cripta.controlador.bench.benchTodo            (completo)
    python -m cripta.controlador.bench.benchTodo --rapido   (versión corta)

Más adelante el modo --bench del programa llamará a ejecutar_todo().
"""
import sys

from . import (
    benchAgenda, benchBitacora, benchCache, benchGuardado, benchHistorial,
    benchListaDoble, benchOrdenamiento)
from .reporte import Reporte



def ejecutar_todo(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    benchAgenda.ejecutar(reporte, rapido)
    benchListaDoble.ejecutar(reporte, rapido)
    benchHistorial.ejecutar(reporte, rapido)
    benchBitacora.ejecutar(reporte, rapido)
    benchCache.ejecutar(reporte, rapido)
    benchOrdenamiento.ejecutar(reporte, rapido)
    benchGuardado.ejecutar(reporte, rapido)
    return reporte


def main():
    ejecutar_todo(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()