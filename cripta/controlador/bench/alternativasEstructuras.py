"""Alternativas descartadas del Paso 4 (pila del retroceso y bitácora), SOLO para medir.

El juego NO usa nada de este archivo. Existe para poder medir directamente lo
que se descartó (lo exige §8 del enunciado). Igual que el resto del programa,
todas están hechas con NUESTRAS estructuras: no se usan las colecciones de Python.
"""
from ...modelo.estructuras.cola import Cola
from ...modelo.estructuras.colaAcotada import ColaAcotada
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.estructuras.pilaAcotada import PilaAcotada

CLAVES_PILA = (
    "pila_acotada_doble",       # la decisión: PilaAcotada sobre ListaDoble
    "pila_acotada_simple",      # descartada: la misma pila sobre lista simple
)

CLAVES_BITACORA = (
    "cola_acotada",             # la decisión: ColaAcotada de 20 mensajes
    "cola_sin_tope",            # descartada: cola que crece y se recorta al mostrar
)


class PilaAcotadaSimple:
    """PilaAcotada apoyada en una ListaEnlazada SIMPLE: descartar el fondo cuesta
    O(capacidad), porque hay que llegar hasta el penúltimo nodo."""

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._elementos = ListaEnlazada()

    def __len__(self):
        return len(self._elementos)

    def esta_vacia(self):
        return self._elementos.esta_vacia()

    def esta_llena(self):
        return len(self._elementos) == self._capacidad

    def apilar(self, dato):
        if dato is None:
            raise ValueError("No admite None")
        descartado = None
        if self.esta_llena():
            descartado = self._elementos.eliminar_ultimo()      # O(n)
        self._elementos.agregar_al_inicio(dato)
        return descartado

    def desapilar(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos.eliminar_primero()

    def ver_tope(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos.ver_primero()

    def __iter__(self):
        return iter(self._elementos)


def _ultimos_de(secuencia, total, cantidad):
    """Los últimos 'cantidad' elementos de una secuencia de 'total' elementos,
    en una ListaEnlazada, del más antiguo al más reciente. Recorre la secuencia
    entera: cuesta O(total)."""
    resultado = ListaEnlazada()
    a_saltar = total - cantidad
    posicion = 0
    for elemento in secuencia:
        if posicion >= a_saltar:
            resultado.agregar_al_final(elemento)
        posicion += 1
    return resultado


class BitacoraAcotada:
    """La DECISIÓN: bitácora sobre una ColaAcotada. Nunca hay más de 'capacidad'
    mensajes, así que mostrar los últimos recorre a lo sumo 'capacidad' nodos."""

    def __init__(self, capacidad):
        self._cola = ColaAcotada(capacidad)

    def __len__(self):
        return len(self._cola)

    def agregar(self, mensaje):
        self._cola.encolar(mensaje)

    def ultimos(self, cantidad):
        return _ultimos_de(self._cola, len(self._cola), cantidad)


class BitacoraSinTope:
    """Alternativa (c) de D30: una Cola SIN tope, que crece con cada mensaje y solo
    se recorta al mostrar. Mostrar los últimos recorre TODOS los mensajes."""

    def __init__(self):
        self._cola = Cola()

    def __len__(self):
        return len(self._cola)

    def agregar(self, mensaje):
        self._cola.encolar(mensaje)

    def ultimos(self, cantidad):
        return _ultimos_de(self._cola, len(self._cola), cantidad)


def nombre_pila(clave):
    if clave == "pila_acotada_doble":
        return "PilaAcotada sobre ListaDoble (decisión)"
    if clave == "pila_acotada_simple":
        return "PilaAcotada sobre lista simple"
    raise ValueError(f"Clave de pila desconocida: {clave}")


def nombre_bitacora(clave):
    if clave == "cola_acotada":
        return "ColaAcotada de 20 (decisión)"
    if clave == "cola_sin_tope":
        return "cola sin tope, se recorta al mostrar"
    raise ValueError(f"Clave de bitácora desconocida: {clave}")


def crear_pila_acotada(clave, capacidad):
    """Se usa if/elif y no un diccionario de funciones: §7 prohíbe dict como
    tabla de búsqueda."""
    if clave == "pila_acotada_doble":
        return PilaAcotada(capacidad)
    if clave == "pila_acotada_simple":
        return PilaAcotadaSimple(capacidad)
    raise ValueError(f"Clave de pila desconocida: {clave}")


def crear_bitacora(clave, capacidad):
    if clave == "cola_acotada":
        return BitacoraAcotada(capacidad)
    if clave == "cola_sin_tope":
        return BitacoraSinTope()
    raise ValueError(f"Clave de bitácora desconocida: {clave}")