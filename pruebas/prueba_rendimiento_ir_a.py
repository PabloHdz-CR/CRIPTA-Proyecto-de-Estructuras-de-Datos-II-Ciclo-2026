"""Rendimiento de «ir a» (T043 de specs/002-niebla-guerra/tasks.md).

Cubre FR-031 y SC-004 (US6 escenario 1): con el mapa conocido completo de la
cripta de referencia (la de más salas de datos_offline/, elegida en
ejecución, principio IV) y los recuerdos iguales al estado real, el PEOR paso
de «ir a» sobre al menos 200 pares con semilla fija, tomando el mínimo de 5
repeticiones por par (como Medidor), tarda menos de 5 ms.
"""
import random
import time

from cripta.controlador.bench.benchCazador import cripta_de_referencia
from cripta.modelo.mundo.buscadorRuta import BuscadorRuta
from cripta.modelo.mundo.conocimiento import ABIERTA, CERRADA, EXPLORADA
from cripta.modelo.mundo.mundo import Mundo

LIMITE_MS = 5.0
PARES = 200
REPETICIONES = 5


class _Datos:
    def __init__(self, inicial, salida):
        self.sala_inicial = inicial
        self.sala_salida = salida
        self.llave_salida = "x"
        self.inventario_max = 10
        self.jugador = None


def mundo_conocido(cripta):
    mundo = Mundo(_Datos(cripta.salas.ver_primero().id, cripta.sala_salida))
    mundo.agregar_esqueleto(cripta.salas)
    mundo.enlazar()
    for sala in mundo:
        sala.conocimiento = EXPLORADA
        for salida in sala.salidas:
            if salida is not None:
                salida.recordada = CERRADA if salida.cerrada else ABIERTA
    return mundo


def main():
    cripta = cripta_de_referencia()
    mundo = mundo_conocido(cripta)
    salas = [s for s in mundo]
    buscador = BuscadorRuta(mundo)
    azar = random.Random(20261115)
    peor = 0.0
    con_ruta = 0
    for _ in range(PARES):
        origen, destino = azar.sample(salas, 2)
        mejor = None
        for _ in range(REPETICIONES):
            inicio = time.perf_counter()
            paso = buscador.primer_paso(origen, destino)
            ms = (time.perf_counter() - inicio) * 1000
            mejor = ms if mejor is None or ms < mejor else mejor
        con_ruta += paso is not None
        peor = max(peor, mejor)
    assert con_ruta > 0, "ningún par con ruta: la medición no ejercita nada"
    assert peor < LIMITE_MS, (
        f"FR-031/SC-004: el peor paso de «ir a» tardó {peor:.3f} ms (límite {LIMITE_MS} ms) "
        f"en {cripta.nombre}")
    print(f"prueba_rendimiento_ir_a OK ({cripta.nombre}: peor paso {peor:.3f} ms en "
          f"{PARES} pares, {con_ruta} con ruta; límite {LIMITE_MS} ms)")


main()
