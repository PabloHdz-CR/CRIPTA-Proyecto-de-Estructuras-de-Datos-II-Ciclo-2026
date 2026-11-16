"""Equivalencia del buscador de «ir a» con el oráculo (T024 de
specs/002-niebla-guerra/tasks.md).

Cubre SC-006 (FR-019, FR-020, FR-021): en al menos 1000 pares de salas de
criptas sintéticas con conocimiento al azar (salas exploradas, avistadas y
desconocidas; caras recordadas abiertas, cerradas y no observadas), el primer
paso de BuscadorRuta coincide con el del oráculo Bellman-Ford
(pruebas/oraculo_ir_a.py).

Además (SC-002, FR-015, FR-021; research R10), cada búsqueda corre
instrumentada: leer el estado real de una puerta (`Salida.cerrada`) o buscar
una sala por id (`Mundo.sala`) hace fallar la prueba, y toda sala que la
búsqueda tocó (su sello de ruta es el de esa búsqueda) debe estar explorada.
"""
import random

from cripta.modelo.mundo.buscadorRuta import BuscadorRuta
from cripta.modelo.mundo.conocimiento import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, NO_OBSERVADA
from cripta.modelo.mundo.mundo import Mundo
from cripta.modelo.mundo.salida import Salida
from cripta.modelo.puertos.dto import DIRECCIONES

from pruebas import oraculo_ir_a
from pruebas.apoyo_niebla import cerrar_fuentes, malla_n, partida_sobre, sala_n, sn
from pruebas.apoyo_terreno import cripta_al_azar

PARES_MINIMOS = 1000
SEMILLA = 2026_11_15


def descripcion_desde_terreno(descripcion):
    return tuple(sala_n(i, *[sn(d, destino, costo, cerrada) for d, destino, costo, cerrada in salidas])
                 for i, salidas in descripcion)


def malla_empatada(azar):
    """Malla 4×4 con costos iguales: muchos empates (FR-020)."""
    return malla_n(4, costo=azar.choice((None, 50)))


def conocimiento_al_azar(partida, azar):
    for sala in partida.mundo:
        sala.conocimiento = azar.choice((DESCONOCIDA, AVISTADA) + (EXPLORADA,) * 8)
        for salida in sala.salidas:
            if salida is not None:
                salida.recordada = azar.choice((NO_OBSERVADA, CERRADA) + (ABIERTA,) * 8)


class _Prohibido(Exception):
    pass


def _cerrada_prohibida(self):
    raise _Prohibido("el buscador leyó Salida.cerrada (estado real)")


def _sala_prohibida(self, id_sala):
    raise _Prohibido("el buscador buscó una sala por id (Mundo.sala)")


def primer_paso_instrumentado(buscador, mundo, origen, destino):
    """Corre el buscador con `cerrada` y `Mundo.sala` prohibidos y comprueba
    que solo tocó salas exploradas. Devuelve la dirección o None."""
    propiedad = Salida.cerrada
    sala_original = Mundo.sala
    Salida.cerrada = property(_cerrada_prohibida, propiedad.fset)
    Mundo.sala = _sala_prohibida
    try:
        salida = buscador.primer_paso(origen, destino)
    finally:
        Salida.cerrada = propiedad
        Mundo.sala = sala_original
    sello = mundo.sello_ruta
    for sala in mundo:
        if sala.sello_ruta == sello:
            assert sala.conocimiento == EXPLORADA, (
                f"SC-002/FR-021: la búsqueda tocó la sala {sala.id}, que no está explorada")
    if salida is None:
        return None
    for indice, candidata in enumerate(origen.salidas):
        if candidata is salida:
            return DIRECCIONES[indice]
    raise AssertionError("el primer paso no es una salida de la sala de origen")


def main():
    azar = random.Random(SEMILLA)
    pares = 0
    con_ruta = 0
    criptas = 0
    while pares < PARES_MINIMOS:
        if criptas % 3 == 2:
            descripcion = malla_empatada(azar)
        else:
            descripcion = descripcion_desde_terreno(cripta_al_azar(azar))
        partida = partida_sobre(descripcion, diario=False)
        criptas += 1
        conocimiento_al_azar(partida, azar)
        mundo = partida.mundo
        buscador = BuscadorRuta(mundo)
        exploradas = [s for s in mundo if s.conocimiento == EXPLORADA]
        if len(exploradas) < 2:
            cerrar_fuentes()
            continue
        for _ in range(6):
            origen, destino = azar.sample(exploradas, 2)
            esperado = oraculo_ir_a.primer_paso(mundo, origen, destino)
            obtenido = primer_paso_instrumentado(buscador, mundo, origen, destino)
            assert obtenido == esperado, (
                f"SC-006: cripta {criptas}, {origen.id} -> {destino.id}: "
                f"buscador {obtenido}, oráculo {esperado}")
            pares += 1
            con_ruta += esperado is not None
        cerrar_fuentes()
    assert con_ruta >= PARES_MINIMOS // 4, f"pocos pares con ruta ({con_ruta}): el azar no ejercita"
    print(f"prueba_ir_a_equivalencia OK ({pares} pares en {criptas} criptas, {con_ruta} con ruta)")


main()
