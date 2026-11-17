"""T004 (004-linea-tiempo, FR-023): ArregloArbol, el arreglo por árbol
completo donde se guardan los bloques de la línea de tiempo.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_arreglo_arbol
"""
import random

from cripta.modelo.estructuras.arregloArbol import ArregloArbol


def contenido(arreglo):
    return [dato for dato in arreglo]


def caso_basico():
    """FR-023: obtener, agregar al final, quitar el último y el tamaño."""
    arreglo = ArregloArbol()
    assert len(arreglo) == 0 and contenido(arreglo) == []
    for numero in range(1, 11):
        arreglo.agregar_al_final(numero * 10)
    assert len(arreglo) == 10
    for posicion in range(1, 11):
        assert arreglo.obtener(posicion) == posicion * 10, posicion
    assert contenido(arreglo) == [n * 10 for n in range(1, 11)]
    assert arreglo.quitar_ultimo() == 100 and len(arreglo) == 9
    assert arreglo.ultimo() == 90
    for indice_malo in (0, 10, -1):
        try:
            arreglo.obtener(indice_malo)
            raise AssertionError(f"FR-023: obtener({indice_malo}) debió fallar")
        except IndexError:
            pass
    while len(arreglo) > 0:
        arreglo.quitar_ultimo()
    try:
        arreglo.quitar_ultimo()
        raise AssertionError("quitar_ultimo de un arreglo vacío debió fallar")
    except IndexError:
        pass


def caso_al_azar():
    """FR-023: 10 000 operaciones con semilla contra una lista de referencia."""
    azar = random.Random(4004)
    arreglo = ArregloArbol()
    referencia = []
    for paso in range(10_000):
        if referencia and azar.random() < 0.35:
            assert arreglo.quitar_ultimo() == referencia.pop(), paso
        else:
            arreglo.agregar_al_final(paso)
            referencia.append(paso)
        if referencia and paso % 37 == 0:
            posicion = azar.randint(1, len(referencia))
            assert arreglo.obtener(posicion) == referencia[posicion - 1], paso
    assert len(arreglo) == len(referencia)
    assert contenido(arreglo) == referencia


def caso_costo_logaritmico():
    """FR-023: llegar a cualquier posición recorre a lo sumo log2(n) + 1 nodos."""
    arreglo = ArregloArbol()
    n = 100_000
    for numero in range(n):
        arreglo.agregar_al_final(numero)
    pasos = arreglo.pasos_hasta(n)
    assert pasos <= n.bit_length(), f"FR-023: {pasos} pasos para llegar a la posición {n}"


CASOS = (caso_basico, caso_al_azar, caso_costo_logaritmico)

if __name__ == "__main__":
    for caso in CASOS:
        caso()
        print(f"[OK   ] {caso.__name__}")
    print(f"prueba_arreglo_arbol OK ({len(CASOS)} casos)")
