"""Oráculo independiente de la decisión del cazador (T006, research R9).

Calcula desde cero, en cada llamada, la acción que FR-010 a FR-014 exigen al
cazador. Es la referencia de prueba_cazador_equivalencia (T022, SC-002): si
las dos difieren, se corrige el código, nunca el oráculo.

Independencia (R9): solo lee Mundo.sala/Mundo.__iter__, Sala.id, Sala.salidas,
Salida.destino, Salida.cerrada y Salida.costo. No importa nada de
mapaDistancias.py, no usa cota, caché, sellos ni los campos de búsqueda de la
sala, y usa otro algoritmo (Bellman-Ford hacia adelante, no Dijkstra hacia
atrás). Las distancias van en una ListaEnlazada propia, sin dict.

Fórmula literal de FR-014, calculada desde las vecinas:
    para cada salida abierta u → v (en orden N, S, E, O):
        t = costo(u, v) + dist(v, jugador)       (Bellman-Ford desde v)
    d = min t
    Esperar (100) si no hay ninguna o d > rango; si no, Mover hacia la v de
    menor id entre las que alcanzan d y, si dos salidas llevan a esa misma v,
    la primera en el orden N, S, E, O.
"""
from __future__ import annotations

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.nucleo.accion import Atacar, Esperar, Mover
from cripta.modelo.puertos.dto import DIRECCIONES


class _Distancia:
    """Distancia provisional de una sala en un Bellman-Ford."""

    def __init__(self, id_sala: int) -> None:
        self.id_sala = id_sala
        self.valor = None                  # None = infinito


def _celda(distancias: ListaEnlazada, id_sala: int) -> _Distancia:
    for celda in distancias:
        if celda.id_sala == id_sala:
            return celda
    return None


class _Arista:
    """Una salida abierta, con las celdas de distancia de sus dos extremos."""

    def __init__(self, desde: _Distancia, hasta: _Distancia, costo: int) -> None:
        self.desde = desde
        self.hasta = hasta
        self.costo = costo


class _Grafo:
    """Las salas y las salidas ABIERTAS del mundo en este instante (FR-011),
    resueltas una sola vez: cada arista ya apunta a sus celdas, así cada ronda
    de Bellman-Ford no vuelve a buscar salas por id."""

    def __init__(self, mundo) -> None:
        self.celdas = ListaEnlazada()
        for sala in mundo:
            self.celdas.agregar_al_final(_Distancia(sala.id))
        self.aristas = ListaEnlazada()
        for sala in mundo:
            desde = _celda(self.celdas, sala.id)
            for salida in sala.salidas:
                if salida is None or salida.cerrada:
                    continue
                hasta = _celda(self.celdas, salida.destino)
                if hasta is not None:
                    self.aristas.agregar_al_final(_Arista(desde, hasta, salida.costo))

    def distancia(self, id_origen: int, id_destino: int):
        """Bellman-Ford sin cota desde id_origen: |salas| - 1 rondas de
        relajación sobre todas las aristas. None si no hay ruta."""
        for celda in self.celdas:
            celda.valor = None
        inicio = _celda(self.celdas, id_origen)
        destino = _celda(self.celdas, id_destino)
        if inicio is None or destino is None:
            return None
        inicio.valor = 0
        for _ in range(len(self.celdas) - 1):
            cambio = False
            for arista in self.aristas:
                if arista.desde.valor is None:
                    continue
                candidata = arista.desde.valor + arista.costo
                if arista.hasta.valor is None or candidata < arista.hasta.valor:
                    arista.hasta.valor = candidata
                    cambio = True
            if not cambio:
                break
        return destino.valor


def distancia(mundo, id_origen: int, id_destino: int):
    """Costo mínimo de id_origen a id_destino usando solo salidas abiertas en
    el sentido del recorrido (FR-011), o None si no hay ruta."""
    return _Grafo(mundo).distancia(id_origen, id_destino)


def decidir(mundo, sala_cazador: int, sala_jugador: int, jugador_vivo: bool,
            id_jugador, rango: int) -> tuple:
    """(acción, costo) que debe tomar un cazador de 'rango' en sala_cazador.

    - Comparte sala con el jugador vivo → Atacar (FR-010).
    - Si no, la fórmula de FR-014 desde cada vecina abierta (FR-011 a FR-014).
    El costo de Mover es el de la salida elegida (FR-013); el de Esperar, 100.
    """
    if jugador_vivo and sala_cazador == sala_jugador:
        accion = Atacar(id_jugador)
        return accion, accion.costo_base
    u = mundo.sala(sala_cazador)
    grafo = _Grafo(mundo)
    mejor_t = None
    mejor_id = None
    mejor_direccion = None
    mejor_costo = None
    for indice, direccion in enumerate(DIRECCIONES):
        salida = u.salidas[indice]
        if salida is None or salida.cerrada:
            continue
        resto = grafo.distancia(salida.destino, sala_jugador)
        if resto is None:
            continue
        t = salida.costo + resto
        # Estrictamente mejor por (t, id de la vecina): ante un empate total
        # queda la salida anterior en el orden N, S, E, O.
        if mejor_t is None or (t, salida.destino) < (mejor_t, mejor_id):
            mejor_t = t
            mejor_id = salida.destino
            mejor_direccion = direccion
            mejor_costo = salida.costo
    if mejor_t is None or mejor_t > rango:
        accion = Esperar()
        return accion, accion.costo_base
    return Mover(mejor_direccion), mejor_costo


def decidir_en_partida(partida, cazador, rango: int) -> tuple:
    """decidir() con la sala del cazador y el estado del jugador de la partida."""
    jugador = partida.jugador
    return decidir(partida.mundo, cazador.sala, jugador.sala, jugador.vivo,
                   jugador.id_instancia, rango)
