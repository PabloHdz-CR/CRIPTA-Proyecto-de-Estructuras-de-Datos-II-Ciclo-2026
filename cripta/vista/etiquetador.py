"""Etiquetador: convierte enemigos reales en nombres que el jugador reconoce
("Rata gigante #1", "Rata gigante #2"...), uno por cada tipo de enemigo que
aparece en la cripta (§6, lo usa el Controlador al armar ActorVisible).

No importa nada del modelo: solo recibe el "nombre base" como texto (el
Controlador ya tradujo la clase del Enemigo a ese texto) y lleva la cuenta.
Los contadores son independientes por nombre_base: la primera "Rata gigante"
es #1 sin importar cuántos "Esqueleto" hayan aparecido antes.

Usa ListaEnlazada (no dict) para los contadores: son pocos (un contador por
tipo distinto de enemigo visto, normalmente un puñado), así que una búsqueda
lineal no es un problema real, y mantiene la regla de no usar estructuras
nativas de Python en cripta/.
"""
from __future__ import annotations

from ..modelo.estructuras.listaEnlazada import ListaEnlazada


class _Contador:
    """Nodo mutable interno: nombre_base + cuántas veces se etiquetó ya."""

    def __init__(self, nombre_base: str):
        self.nombre_base = nombre_base
        self.valor = 0


class Etiquetador:

    def __init__(self):
        self._contadores = ListaEnlazada()

    def etiqueta(self, nombre_base: str) -> str:
        """Devuelve "<nombre_base> #<n>", incrementando el contador de ese
        nombre_base cada vez que se llama (empieza en #1)."""
        contador = self._buscar(nombre_base)
        if contador is None:
            contador = _Contador(nombre_base)
            self._contadores.agregar_al_final(contador)
        contador.valor += 1
        return f"{nombre_base} #{contador.valor}"

    def reiniciar(self) -> None:
        """Borra todos los contadores (una cripta nueva empieza de cero)."""
        self._contadores = ListaEnlazada()

    def _buscar(self, nombre_base: str):
        for contador in self._contadores:
            if contador.nombre_base == nombre_base:
                return contador
        return None