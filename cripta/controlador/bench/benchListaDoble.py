"""Mediciones del inventario (§4.5): ListaDoble (la decisión) contra ListaEnlazada.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchListaDoble            (completo)
    python -m cripta.controlador.bench.benchListaDoble --rapido   (versión corta)

Mide dos cosas, con 100 a 100 000 objetos en el inventario:
  1. Soltar objetos al principio, en el medio y al final. §4.5 exige que el
     costo NO dependa de la posición del objeto.
  2. Equipar un objeto (llevarlo al frente) desde el medio.
"""
import sys

from ...modelo.estructuras.listaDoble import ListaDoble
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .benchAgenda import listas_iguales
from .medidor import Medidor
from .reporte import Reporte

CLAVES = ("lista_doble", "lista_enlazada")
POSICIONES = ("inicio", "medio", "fin")


def nombre_de(clave):
    if clave == "lista_doble":
        return "ListaDoble por nodo (decisión)"
    if clave == "lista_enlazada":
        return "ListaEnlazada por índice"
    raise ValueError(f"Clave desconocida: {clave}")


def operaciones_para(n):
    """Cuántos objetos se sueltan (o equipan) en cada medición."""
    return min(100, n // 4)


def llenar(lista, n):
    for numero in range(n):
        lista.agregar_al_final(numero)


class EscenarioSoltar:
    """Un inventario de n objetos. Se sueltan K objetos consecutivos a partir de
    una posición (inicio, medio o fin), como hace el jugador con lo que está viendo."""

    def __init__(self, clave, posicion):
        self._clave = clave
        self._posicion = posicion
        self._lista = None
        self._nodo = None
        self._n = 0
        self._operaciones = 0

    def preparar(self, n):
        self._n = n
        self._operaciones = operaciones_para(n)
        if self._clave == "lista_doble":
            self._lista = ListaDoble()
            llenar(self._lista, n)
            self._nodo = self._nodo_inicial()
        else:
            self._lista = ListaEnlazada()
            llenar(self._lista, n)

    def _nodo_inicial(self):
        lista = self._lista
        if self._posicion == "inicio":
            return lista.primero()
        if self._posicion == "fin":
            return lista.ultimo()
        nodo = lista.primero()
        for _ in range(self._n // 2):
            nodo = lista.siguiente_de(nodo)
        return nodo

    def ejecutar(self):
        self._soltar(None)

    def ejecutar_y_registrar(self):
        """Devuelve, en una ListaEnlazada, los objetos soltados en orden."""
        soltados = ListaEnlazada()
        self._soltar(soltados)
        return soltados

    def resto(self):
        return self._lista

    def _soltar(self, registro):
        lista = self._lista
        if self._clave == "lista_doble":
            nodo = self._nodo
            for _ in range(self._operaciones):
                if self._posicion == "fin":
                    vecino = lista.anterior_de(nodo)      # el cursor retrocede
                else:
                    vecino = lista.siguiente_de(nodo)     # el cursor avanza
                dato = lista.eliminar_nodo(nodo)          # O(1)
                if registro is not None:
                    registro.agregar_al_final(dato)
                nodo = vecino
        else:
            for _ in range(self._operaciones):
                if self._posicion == "inicio":
                    indice = 0
                elif self._posicion == "fin":
                    indice = len(lista) - 1
                else:
                    indice = self._n // 2
                dato = lista.eliminar_en(indice)          # O(indice)
                if registro is not None:
                    registro.agregar_al_final(dato)


class EscenarioEquipar:
    """Un inventario de n objetos. Se equipan K objetos consecutivos desde el
    medio: cada uno se lleva al frente de la lista."""

    def __init__(self, clave):
        self._clave = clave
        self._lista = None
        self._nodos = ListaEnlazada()
        self._n = 0
        self._operaciones = 0

    def preparar(self, n):
        self._n = n
        self._operaciones = operaciones_para(n)
        if self._clave == "lista_doble":
            self._lista = ListaDoble()
            llenar(self._lista, n)
            self._nodos = ListaEnlazada()
            nodo = self._lista.primero()
            for _ in range(n // 2):
                nodo = self._lista.siguiente_de(nodo)
            for _ in range(self._operaciones):
                self._nodos.agregar_al_final(nodo)
                nodo = self._lista.siguiente_de(nodo)
        else:
            self._lista = ListaEnlazada()
            llenar(self._lista, n)

    def ejecutar(self):
        lista = self._lista
        if self._clave == "lista_doble":
            for nodo in self._nodos:
                lista.mover_al_inicio(nodo)               # O(1)
        else:
            medio = self._n // 2
            for desplazamiento in range(self._operaciones):
                dato = lista.eliminar_en(medio + desplazamiento)     # O(indice)
                lista.agregar_al_inicio(dato)

    def resto(self):
        return self._lista


def verificar_equivalencia():
    """Las dos estructuras deben dejar el inventario exactamente igual."""
    for posicion in POSICIONES:
        doble = EscenarioSoltar("lista_doble", posicion)
        simple = EscenarioSoltar("lista_enlazada", posicion)
        doble.preparar(300)
        simple.preparar(300)
        if not listas_iguales(doble.ejecutar_y_registrar(), simple.ejecutar_y_registrar()):
            raise RuntimeError(f"Soltar en '{posicion}' soltó objetos distintos")
        if not listas_iguales(doble.resto(), simple.resto()):
            raise RuntimeError(f"Soltar en '{posicion}' dejó inventarios distintos")
        if not doble.resto().es_consistente():
            raise RuntimeError("La ListaDoble quedó con punteros inconsistentes")
    doble = EscenarioEquipar("lista_doble")
    simple = EscenarioEquipar("lista_enlazada")
    doble.preparar(300)
    simple.preparar(300)
    doble.ejecutar()
    simple.ejecutar()
    if not listas_iguales(doble.resto(), simple.resto()):
        raise RuntimeError("Equipar dejó inventarios distintos")
    if not doble.resto().es_consistente():
        raise RuntimeError("La ListaDoble quedó con punteros inconsistentes al equipar")


def ejecutar(reporte=None, rapido=False):
    """Corre las mediciones del inventario. Devuelve el Reporte."""
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    tamanos = (100, 1000) if rapido else (100, 1000, 10000, 100000)

    reporte.titulo("Inventario: mediciones (§4.5)")
    verificar_equivalencia()
    reporte.nota("Verificación: ambas estructuras dejan el inventario exactamente igual.")

    # 1. Soltar objetos según su posición
    filas = ListaEnlazada()
    mayor = tamanos[len(tamanos) - 1]
    tiempo_inicio = 0.0
    tiempo_medio = 0.0
    tiempo_fin = 0.0
    for n in tamanos:
        operaciones = operaciones_para(n)
        for posicion in POSICIONES:
            tiempo_decision = None
            for clave in CLAVES:
                medicion = medidor.medir(EscenarioSoltar(clave, posicion), n)
                por_objeto = medicion.minimo / operaciones * 1e6          # microsegundos
                if clave == "lista_doble":
                    tiempo_decision = por_objeto
                    if n == mayor:                   # se guardan los del mayor tamaño
                        if posicion == "inicio":
                            tiempo_inicio = por_objeto
                        elif posicion == "medio":
                            tiempo_medio = por_objeto
                        else:
                            tiempo_fin = por_objeto
                filas.agregar_al_final((str(n), posicion, nombre_de(clave),
                                        f"{por_objeto:.2f}",
                                        f"{por_objeto / tiempo_decision:.1f}x"))
    reporte.tabla("1. Soltar un objeto, en microsegundos por objeto",
                  ("objetos", "posición", "estructura", "mínimo µs", "vs decisión"), filas)

    # 2. Equipar (llevar al frente) desde el medio
    filas = ListaEnlazada()
    for n in tamanos:
        operaciones = operaciones_para(n)
        tiempo_decision = None
        for clave in CLAVES:
            medicion = medidor.medir(EscenarioEquipar(clave), n)
            por_objeto = medicion.minimo / operaciones * 1e6
            if clave == "lista_doble":
                tiempo_decision = por_objeto
            filas.agregar_al_final((str(n), nombre_de(clave), f"{por_objeto:.2f}",
                                    f"{por_objeto / tiempo_decision:.1f}x"))
    reporte.tabla("2. Equipar un objeto del medio (llevarlo al frente), en microsegundos",
                  ("objetos", "estructura", "mínimo µs", "vs decisión"), filas)

    # 3. Lectura frente al requisito de §4.5: el costo no depende de la posición
    mejor = min(tiempo_inicio, tiempo_medio, tiempo_fin)
    peor = max(tiempo_inicio, tiempo_medio, tiempo_fin)
    reporte.nota("")
    reporte.nota(f"Con {mayor} objetos, soltar con ListaDoble cuesta {tiempo_inicio:.2f} µs al "
                 f"inicio, {tiempo_medio:.2f} µs en el medio y {tiempo_fin:.2f} µs al final: "
                 f"el peor caso es "
                 f"{peor / mejor:.1f} veces el mejor (§4.5 exige que no dependa de la posición).")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()