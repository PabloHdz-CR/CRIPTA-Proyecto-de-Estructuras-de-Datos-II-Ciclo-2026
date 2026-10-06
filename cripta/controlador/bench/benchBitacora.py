"""Mediciones de la bitácora en pantalla (§4.8): ColaAcotada de 20 mensajes
(la decisión) contra una cola sin tope que solo se recorta al mostrar.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchBitacora            (completo)
    python -m cripta.controlador.bench.benchBitacora --rapido   (versión corta)

Mide, según cuántos mensajes se hayan generado en la partida:
  1. Cuánto cuesta mostrar los últimos 20.
  2. Cuánto cuesta agregar un mensaje.
  3. Cuánta memoria usa: contando nodos (exacto, no depende de tu computadora)
     y con tracemalloc (bytes reales).
"""
import random
import sys
import tracemalloc

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .alternativasEstructuras import (CLAVES_BITACORA, crear_bitacora,
                                       nombre_bitacora)
from .benchAgenda import listas_iguales
from .medidor import Medidor
from .reporte import Reporte

CAPACIDAD = 20                 # §4.8: la pantalla muestra los últimos 20 mensajes
MENSAJE = "mensaje de prueba"  # el mismo texto siempre: se mide solo la estructura


def mostrados_para(n):
    """Cuántas veces se muestra la bitácora por medición."""
    return max(20, 200000 // n)


class EscenarioMostrar:
    """La bitácora ya tiene n mensajes; se muestran los últimos 20, varias veces."""

    def __init__(self, clave):
        self._clave = clave
        self._bitacora = None
        self._veces = 0

    def preparar(self, n):
        self._veces = mostrados_para(n)
        self._bitacora = crear_bitacora(self._clave, CAPACIDAD)
        for _ in range(n):
            self._bitacora.agregar(MENSAJE)

    def ejecutar(self):
        bitacora = self._bitacora
        for _ in range(self._veces):
            bitacora.ultimos(CAPACIDAD)


class EscenarioAgregar:
    """La bitácora ya tiene n mensajes; se agregan 5 000 más."""

    def __init__(self, clave):
        self._clave = clave
        self._bitacora = None

    def preparar(self, n):
        self._bitacora = crear_bitacora(self._clave, CAPACIDAD)
        for _ in range(n):
            self._bitacora.agregar(MENSAJE)

    def ejecutar(self):
        bitacora = self._bitacora
        for _ in range(5000):
            bitacora.agregar(MENSAJE)


def memoria(clave, n):
    """Devuelve (nodos, bytes) después de agregar n mensajes. Los bytes salen de
    tracemalloc, así que esta medición se hace aparte de las de tiempo."""
    tracemalloc.start()
    try:
        bitacora = crear_bitacora(clave, CAPACIDAD)
        for _ in range(n):
            bitacora.agregar(MENSAJE)
        actual, _ = tracemalloc.get_traced_memory()
        nodos = len(bitacora)
    finally:
        tracemalloc.stop()
    return nodos, actual


def verificar_equivalencia():
    """Las dos bitácoras deben mostrar exactamente los mismos últimos 20 mensajes."""
    for n in (5, 20, 21, 500):
        mostrados = ListaEnlazada()
        for clave in CLAVES_BITACORA:
            bitacora = crear_bitacora(clave, CAPACIDAD)
            for numero in range(1, n + 1):
                bitacora.agregar(f"mensaje {numero}")
            mostrados.agregar_al_final(bitacora.ultimos(CAPACIDAD))
        if not listas_iguales(mostrados.obtener(0), mostrados.obtener(1)):
            raise RuntimeError(f"Las bitácoras muestran mensajes distintos con {n} mensajes")


def ejecutar(reporte=None, rapido=False):
    """Corre las mediciones de la bitácora. Devuelve el Reporte."""
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    tamanos = (100, 1000, 5000) if rapido else (100, 1000, 10000, 100000)

    reporte.titulo("Bitácora en pantalla: mediciones (§4.8)")
    verificar_equivalencia()
    reporte.nota("Verificación: ambas bitácoras muestran exactamente los mismos mensajes.")

    # 1. Mostrar los últimos 20
    filas = ListaEnlazada()
    for n in tamanos:
        veces = mostrados_para(n)
        tiempo_decision = None
        for clave in CLAVES_BITACORA:
            medicion = medidor.medir(EscenarioMostrar(clave), n)
            por_vez = medicion.minimo / veces * 1e6                        # microsegundos
            if clave == "cola_acotada":
                tiempo_decision = por_vez
            filas.agregar_al_final((str(n), nombre_bitacora(clave), f"{por_vez:.1f}",
                                    f"{por_vez / tiempo_decision:.1f}x"))
    reporte.tabla("1. Mostrar los últimos 20 mensajes, en microsegundos",
                  ("mensajes", "estructura", "mínimo µs", "vs decisión"), filas)

    # 2. Agregar un mensaje
    filas = ListaEnlazada()
    for n in tamanos:
        tiempo_decision = None
        for clave in CLAVES_BITACORA:
            medicion = medidor.medir(EscenarioAgregar(clave), n)
            por_mensaje = medicion.minimo / 5000 * 1e6
            if clave == "cola_acotada":
                tiempo_decision = por_mensaje
            filas.agregar_al_final((str(n), nombre_bitacora(clave), f"{por_mensaje:.2f}",
                                    f"{por_mensaje / tiempo_decision:.1f}x"))
    reporte.tabla("2. Agregar un mensaje, en microsegundos",
                  ("mensajes", "estructura", "mínimo µs", "vs decisión"), filas)

    # 3. Memoria
    filas = ListaEnlazada()
    for n in tamanos:
        for clave in CLAVES_BITACORA:
            nodos, bytes_usados = memoria(clave, n)
            filas.agregar_al_final((str(n), nombre_bitacora(clave), str(nodos),
                                    f"{bytes_usados / 1024:.1f}"))
    reporte.tabla("3. Memoria según los mensajes generados (nodos exactos; KiB con tracemalloc)",
                  ("mensajes", "estructura", "nodos", "KiB"), filas)

    reporte.nota("")
    reporte.nota("La ColaAcotada nunca pasa de 20 nodos: su memoria es constante (§4.8). "
                 "La cola sin tope crece con cada mensaje y mostrar los últimos 20 "
                 "recorre todos.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()