"""Mediciones de la pila del retroceso (§4.6): PilaAcotada sobre ListaDoble
(la decisión) contra la misma pila sobre una lista SIMPLE.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchHistorial            (completo)
    python -m cripta.controlador.bench.benchHistorial --rapido   (versión corta)

El juego usa capacidad 5 (las últimas 5 acciones del jugador). Se mide esa y
capacidades mayores para ver de dónde viene la ventaja de la lista doble.
Cuando la pila está llena, cada apilar descarta el elemento del fondo:
en la lista doble es O(1), en la simple es O(capacidad).
"""
import random
import sys

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .alternativasEstructuras import CLAVES_PILA, crear_pila_acotada, nombre_pila
from .benchAgenda import listas_iguales
from .medidor import Medidor
from .reporte import Reporte

CAPACIDAD_REAL = 5            # las últimas 5 acciones del jugador (§2.11)


def operaciones_para(capacidad):
    """Cuántos apilar se hacen por medición: menos con capacidades grandes, para
    que las alternativas lentas no tarden demasiado."""
    return max(50, 200000 // capacidad)


class EscenarioApilarLlena:
    """Una pila ya llena: cada elemento que se apila descarta el más antiguo."""

    def __init__(self, clave):
        self._clave = clave
        self._pila = None
        self._operaciones = 0
        self._siguiente = 0

    def preparar(self, capacidad):
        self._operaciones = operaciones_para(capacidad)
        self._pila = crear_pila_acotada(self._clave, capacidad)
        for numero in range(1, capacidad + 1):
            self._pila.apilar(numero)
        self._siguiente = capacidad + 1

    def ejecutar(self):
        pila = self._pila
        numero = self._siguiente
        for _ in range(self._operaciones):
            pila.apilar(numero)
            numero += 1


def verificar_equivalencia():
    """Con la misma secuencia de apilar y desapilar, las dos pilas deben devolver
    lo mismo (incluidos los elementos descartados) y terminar con el mismo contenido."""
    for capacidad in (1, 5, 50):
        salidas = ListaEnlazada()          # una ListaEnlazada por cada estructura
        finales = ListaEnlazada()
        for clave in CLAVES_PILA:
            azar = random.Random(2026)
            pila = crear_pila_acotada(clave, capacidad)
            registro = ListaEnlazada()
            for numero in range(1, 2001):
                if pila.esta_vacia() or azar.random() < 0.7:
                    registro.agregar_al_final(pila.apilar(numero))    # el descartado o None
                else:
                    registro.agregar_al_final(pila.desapilar())
            contenido = ListaEnlazada()
            for elemento in pila:
                contenido.agregar_al_final(elemento)
            salidas.agregar_al_final(registro)
            finales.agregar_al_final(contenido)
        if not listas_iguales(salidas.obtener(0), salidas.obtener(1)):
            raise RuntimeError(f"Las pilas devolvieron cosas distintas con capacidad {capacidad}")
        if not listas_iguales(finales.obtener(0), finales.obtener(1)):
            raise RuntimeError(f"Las pilas terminaron distintas con capacidad {capacidad}")


def ejecutar(reporte=None, rapido=False):
    """Corre las mediciones de la pila del retroceso. Devuelve el Reporte."""
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    capacidades = (5, 50, 500) if rapido else (5, 50, 500, 5000, 50000)

    reporte.titulo("Pila del retroceso: mediciones (§4.6)")
    verificar_equivalencia()
    reporte.nota("Verificación: ambas pilas devuelven y descartan exactamente lo mismo.")

    filas = ListaEnlazada()
    tiempo_real_doble = 0.0
    tiempo_real_simple = 0.0
    for capacidad in capacidades:
        operaciones = operaciones_para(capacidad)
        tiempo_decision = None
        for clave in CLAVES_PILA:
            medicion = medidor.medir(EscenarioApilarLlena(clave), capacidad)
            por_apilar = medicion.minimo / operaciones * 1e6              # microsegundos
            if clave == "pila_acotada_doble":
                tiempo_decision = por_apilar
            if capacidad == CAPACIDAD_REAL:
                if clave == "pila_acotada_doble":
                    tiempo_real_doble = por_apilar
                else:
                    tiempo_real_simple = por_apilar
            filas.agregar_al_final((str(capacidad), nombre_pila(clave), f"{por_apilar:.2f}",
                                    f"{por_apilar / tiempo_decision:.1f}x"))
    reporte.tabla("Apilar en una pila llena (descarta el fondo), en microsegundos",
                  ("capacidad", "estructura", "mínimo µs", "vs decisión"), filas)

    reporte.nota("")
    reporte.nota(f"Con la capacidad real ({CAPACIDAD_REAL} acciones): {tiempo_real_doble:.2f} µs "
                 f"con lista doble y {tiempo_real_simple:.2f} µs con lista simple. La ventaja "
                 f"de la lista doble aparece al crecer la capacidad.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()