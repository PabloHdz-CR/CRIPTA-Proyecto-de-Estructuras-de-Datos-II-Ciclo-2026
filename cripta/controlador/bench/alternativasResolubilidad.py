"""La alternativa ingenua de la verificación de resolubilidad (FR-035,
research.md R11). Solo para --bench y sus pruebas: el juego no la usa.

Repite la fase 1 DESDE CERO por cada llave obtenida: en cada ronda recorre
toda la región alcanzable con las llaves que ya tiene, junta las disponibles
y elige la de menor id. Así obtiene el mismo orden que la verificación (la
regla de FR-009 es la misma), pero examina O(K · (S + E)) salidas en vez de
O(S + E). Reutiliza la fase 2 y el armado del resultado
(verificadorResolubilidad.resultado_desde), así que solo difiere en cómo
obtiene el orden y la región, y el reporte debe salir idéntico.
"""
from __future__ import annotations

from typing import Iterable

from ...modelo.estructuras.cola import Cola
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.puertos.dto import DatosCriptaDTO
from ...modelo.resolubilidad.grafoVerificacion import GrafoVerificacion, construir_grafo
from ...modelo.resolubilidad.resultadoResolubilidad import LlaveOrdenada, ResultadoResolubilidad
from ...modelo.resolubilidad.verificadorResolubilidad import (
    Contador, EstadoFase1, primera_ubicacion_alcanzada, requiere_llave_salida, resultado_desde)


def _ronda(grafo: GrafoVerificacion, contador: Contador) -> EstadoFase1:
    """Un recorrido completo desde la sala inicial con las llaves obtenidas
    hasta ahora, sin reutilizar nada de la ronda anterior."""
    for sala in grafo.salas:
        sala.alcanzada = False
    for llave in grafo.llaves:
        llave.pendientes = ListaEnlazada()
    estado = EstadoFase1()
    cola = Cola()
    grafo.inicial.alcanzada = True
    cola.encolar(grafo.inicial)
    while not cola.esta_vacia():
        sala = cola.desencolar()
        for arista in sala.salidas:
            contador.sumar()
            if arista.transitable():
                if requiere_llave_salida(arista, grafo):
                    estado.entra_por_puerta_salida = True
                if not arista.destino.alcanzada:
                    arista.destino.alcanzada = True
                    cola.encolar(arista.destino)
            elif arista.llave is not None:
                arista.llave.pendientes.agregar_al_final(arista)
            else:
                estado.sin_llave.agregar_al_final(arista)
    return estado


def _menor_disponible(grafo: GrafoVerificacion):
    """La llave no obtenida de menor id con alguna ubicación alcanzada (las
    llaves del grafo ya están en orden por id)."""
    for llave in grafo.llaves:
        if not llave.obtenida:
            for ubicacion in llave.ubicaciones:
                if ubicacion.sala.alcanzada:
                    return llave
    return None


def verificar_ingenua(datos: DatosCriptaDTO, salas: Iterable,
                      ubicaciones: Iterable) -> ResultadoResolubilidad:
    grafo = construir_grafo(datos, salas, ubicaciones)
    contador = Contador()
    orden = ListaEnlazada()
    while True:
        estado = _ronda(grafo, contador)
        llave = _menor_disponible(grafo)
        if llave is None:
            break
        llave.obtenida = True
        orden.agregar_al_final(LlaveOrdenada(llave.id, primera_ubicacion_alcanzada(llave)))
    estado.orden = orden
    return resultado_desde(datos, grafo, estado, contador)
