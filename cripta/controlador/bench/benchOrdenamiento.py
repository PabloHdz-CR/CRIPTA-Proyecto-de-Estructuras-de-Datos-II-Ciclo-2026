"""Mediciones del módulo Ordenamiento (§4.9): inserción, mezcla y el selector
automático, en los tres escenarios que pide el enunciado: tamaños pequeños,
datos casi ordenados y comparaciones costosas.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchOrdenamiento            (completo)
    python -m cripta.controlador.bench.benchOrdenamiento --rapido   (versión corta)
"""
import random
import sys

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.ordenamiento import (insercion, inversiones_adyacentes, mezcla, ordenar,
                                    seleccionar_algoritmo)
from .medidor import Medidor
from .reporte import Reporte

SEMILLA = 2026


class ElementoContado:
    """Un entero que cuenta cuántas veces se le llamó __lt__. No agrega ningún
    costo artificial: sirve para medir CUÁNTAS comparaciones hace cada
    algoritmo (independiente de la velocidad de la máquina)."""

    comparaciones = 0

    def __init__(self, valor):
        self.valor = valor

    def __lt__(self, otro):
        ElementoContado.comparaciones += 1
        return self.valor < otro.valor


class ElementoCostoso:
    """Un entero cuyo __lt__ hace un trabajo artificial fijo antes de comparar,
    simulando comparar objetos "caros" (por ejemplo, dos fichas completas en
    vez de dos números). COSTO_ITERACIONES controla cuánto."""

    COSTO_ITERACIONES = 400

    def __init__(self, valor):
        self.valor = valor

    def __lt__(self, otro):
        acumulado = 0
        for numero in range(self.COSTO_ITERACIONES):
            acumulado += numero
        return self.valor < otro.valor


def _lista_al_azar(azar, n, clase=int):
    lista = ListaEnlazada()
    for _ in range(n):
        valor = azar.randint(-n, n)
        lista.agregar_al_final(clase(valor) if clase is not int else valor)
    return lista


def _lista_casi_ordenada(azar, n, proporcion_desorden, clase=int):
    """n elementos 0..n-1 en orden, con 'proporcion_desorden' de ellos
    intercambiados con su VECINO inmediato (desorden LOCAL)."""
    valores = ListaEnlazada()
    for i in range(n):
        valores.agregar_al_final(i)
    intercambios = int(n * proporcion_desorden)
    for _ in range(intercambios):
        i = azar.randrange(n - 1)
        a, b = valores.obtener(i), valores.obtener(i + 1)
        valores.establecer(i, b)
        valores.establecer(i + 1, a)
    lista = ListaEnlazada()
    for valor in valores:
        lista.agregar_al_final(clase(valor) if clase is not int else valor)
    return lista


def _lista_casi_ordenada_lejos(azar, n, intercambios, clase=int):
    """n elementos 0..n-1 en orden, con pocos intercambios entre posiciones
    AL AZAR en cualquier lugar (pueden quedar muy lejos entre sí)."""
    valores = ListaEnlazada()
    for i in range(n):
        valores.agregar_al_final(i)
    for _ in range(intercambios):
        i, j = azar.randrange(n), azar.randrange(n)
        a, b = valores.obtener(i), valores.obtener(j)
        valores.establecer(i, b)
        valores.establecer(j, a)
    lista = ListaEnlazada()
    for valor in valores:
        lista.agregar_al_final(clase(valor) if clase is not int else valor)
    return lista


class EscenarioOrdenar:
    """Ordena una lista ya generada (fija, para comparar algoritmos en
    igualdad de condiciones) con la función indicada."""

    def __init__(self, funcion, lista):
        self._funcion = funcion
        self._lista = lista

    def preparar(self, n):
        pass   # la lista ya viene armada; no hay nada que reconstruir

    def ejecutar(self):
        self._funcion(self._lista)


def _comparaciones_de(funcion, lista):
    ElementoContado.comparaciones = 0
    funcion(lista)
    return ElementoContado.comparaciones


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    azar = random.Random(SEMILLA)

    reporte.titulo("Ordenamiento: mediciones (§4.9)")

    # 1. Tamaños pequeños: inserción debería ganarle a mezcla
    filas = ListaEnlazada()
    tamanos_chicos = (5, 20, 32) if rapido else (5, 10, 20, 32, 50)
    for n in tamanos_chicos:
        lista = _lista_al_azar(azar, n)
        m_insercion = medidor.medir(EscenarioOrdenar(insercion, lista), n)
        m_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista), n)
        elegido = seleccionar_algoritmo(lista)
        filas.agregar_al_final((str(n), f"{m_insercion.minimo * 1e6:.2f}",
                                f"{m_mezcla.minimo * 1e6:.2f}", elegido))
    reporte.tabla("1. Tamaños pequeños: inserción contra mezcla, en microsegundos",
                  ("n", "inserción µs", "mezcla µs", "selector elige"), filas)

    # 2. Datos casi ordenados (desorden LOCAL) y grandes: inserción debería ganar
    filas = ListaEnlazada()
    tamanos_grandes = (1000, 5000) if rapido else (1000, 5000, 20000)
    for n in tamanos_grandes:
        lista = _lista_casi_ordenada(azar, n, proporcion_desorden=0.02)
        m_insercion = medidor.medir(EscenarioOrdenar(insercion, lista), n)
        m_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista), n)
        elegido = seleccionar_algoritmo(lista)
        filas.agregar_al_final((str(n), f"{m_insercion.minimo * 1000:.2f}",
                                f"{m_mezcla.minimo * 1000:.2f}", elegido))
    reporte.tabla("2. Grandes y casi ordenados (2% de pares movidos), en milisegundos",
                  ("n", "inserción ms", "mezcla ms", "selector elige"), filas)

    # 3. Grandes y MUY desordenados: mezcla debería ganarle a inserción
    filas = ListaEnlazada()
    for n in tamanos_grandes:
        lista = _lista_al_azar(azar, n)
        m_insercion = medidor.medir(EscenarioOrdenar(insercion, lista), n)
        m_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista), n)
        elegido = seleccionar_algoritmo(lista)
        filas.agregar_al_final((str(n), f"{m_insercion.minimo * 1000:.2f}",
                                f"{m_mezcla.minimo * 1000:.2f}", elegido))
    reporte.tabla("3. Grandes y desordenados al azar, en milisegundos",
                  ("n", "inserción ms", "mezcla ms", "selector elige"), filas)

    # 4. Comparaciones costosas: ¿cuántas comparaciones hace cada uno?
    filas = ListaEnlazada()
    tamanos_costo = (50, 200) if rapido else (50, 200, 1000)
    for n in tamanos_costo:
        lista_desordenada = _lista_al_azar(azar, n, clase=ElementoContado)
        comp_insercion = _comparaciones_de(insercion, lista_desordenada)
        comp_mezcla = _comparaciones_de(mezcla, lista_desordenada)
        filas.agregar_al_final((str(n), str(comp_insercion), str(comp_mezcla),
                                f"{comp_insercion / comp_mezcla:.1f}x"))
    reporte.tabla("4. Comparaciones hechas (datos al azar): inserción vs mezcla",
                  ("n", "comp. inserción", "comp. mezcla", "inserción / mezcla"), filas)

    # 5. El costo real de una comparación cara: tiempo total con ElementoCostoso
    filas = ListaEnlazada()
    for n in tamanos_costo:
        lista_costosa = _lista_al_azar(azar, n, clase=ElementoCostoso)
        m_insercion = medidor.medir(EscenarioOrdenar(insercion, lista_costosa), n)
        m_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista_costosa), n)
        filas.agregar_al_final((str(n), f"{m_insercion.minimo * 1000:.2f}",
                                f"{m_mezcla.minimo * 1000:.2f}",
                                f"{m_insercion.minimo / m_mezcla.minimo:.1f}x"))
    reporte.tabla("5. Comparaciones costosas (cada una hace trabajo artificial), en milisegundos",
                  ("n", "inserción ms", "mezcla ms", "inserción / mezcla"), filas)

    # 6. El selector automático contra "usar siempre mezcla"
    filas = ListaEnlazada()
    for n in tamanos_grandes:
        lista = _lista_casi_ordenada(azar, n, proporcion_desorden=0.02)
        m_selector = medidor.medir(EscenarioOrdenar(ordenar, lista), n)
        m_siempre_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista), n)
        filas.agregar_al_final((str(n), f"{m_selector.minimo * 1000:.2f}",
                                f"{m_siempre_mezcla.minimo * 1000:.2f}",
                                f"{m_siempre_mezcla.minimo / m_selector.minimo:.1f}x"))
    reporte.tabla("6. Selector automático contra 'usar siempre mezcla', en milisegundos "
                  "(datos casi ordenados)",
                  ("n", "selector ms", "siempre mezcla ms", "ganancia"), filas)

    # 7. CASO LÍMITE: pocos intercambios, pero lejanos entre sí
    filas = ListaEnlazada()
    for n in tamanos_grandes:
        intercambios = max(10, n // 25)       # suficientes para notar el límite
        lista = _lista_casi_ordenada_lejos(azar, n, intercambios=intercambios)
        inv = inversiones_adyacentes(lista)
        elegido = seleccionar_algoritmo(lista)
        m_insercion = medidor.medir(EscenarioOrdenar(insercion, lista), n)
        m_mezcla = medidor.medir(EscenarioOrdenar(mezcla, lista), n)
        filas.agregar_al_final((str(n), str(inv), elegido, f"{m_insercion.minimo * 1000:.2f}",
                                f"{m_mezcla.minimo * 1000:.2f}"))
    reporte.tabla("7. LÍMITE: intercambios LEJANOS entre sí (pocas inversiones adyacentes, "
                  "pero cada una viaja lejos), en milisegundos",
                  ("n", "inv. adyacentes", "selector elige", "inserción ms", "mezcla ms"), filas)

    reporte.nota("")
    reporte.nota("Con desorden LOCAL (vecinos intercambiados), inserción se acerca a O(n) porque "
                 "el bucle interno apenas avanza; con datos muy desordenados, mezcla se mantiene "
                 "en O(n log n) mientras inserción se acerca a O(n²). Cuando cada comparación es "
                 "cara, el número de comparaciones domina, y mezcla hace muchas menos (tabla 4).")
    reporte.nota("LÍMITE (tabla 7): con pocos intercambios pero LEJANOS, el conteo de inversiones "
                 "adyacentes (barato, O(n)) puede decir 'casi ordenada' sin que la inserción sea "
                 "rápida de verdad: el costo real depende de cuánto viaja cada elemento desplazado, "
                 "no solo de cuántos pares vecinos están invertidos.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()