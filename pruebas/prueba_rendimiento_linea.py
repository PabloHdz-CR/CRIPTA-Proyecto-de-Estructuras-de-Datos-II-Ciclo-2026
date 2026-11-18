"""T031 (004-linea-tiempo, US6): memoria acotada y consultas rápidas.

Nota (análisis I1): estas pruebas miden código de historias anteriores, así
que pueden pasar apenas se escriben; confirman el diseño (como T047 de 002).

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_rendimiento_linea
"""
import random
import time
import tracemalloc

from cripta.modelo.nucleo.accion import Esperar, Mover
from cripta.modelo.nucleo.lineaTiempo import K_POR_OMISION
from pruebas.apoyo_linea import cripta_linea, partida_con_linea, partida_referencia_inmortal
from pruebas.apoyo_niebla import cerrar_fuentes

LIMITE_MS = 50
ACCIONES = 5000


def jugar(partida, n, semilla):
    """n acciones del jugador al azar (70 % movimientos, 30 % esperas)."""
    azar = random.Random(semilla)
    while partida.jugador.acciones < n and not partida.terminada():
        sala = partida.mundo.sala(partida.jugador.sala)
        direcciones = [s.direccion for s in sala.salidas if s is not None and s.transitable()]
        accion = Mover(azar.choice(direcciones)) if direcciones and azar.random() < 0.7 else Esperar()
        partida.aplicar_accion(accion)


def caso_e1_consulta_menor_a_50_ms():
    """US6 escenario 1 (FR-019, SC-003) y FR-021: partida de 5000 acciones en
    la cripta de referencia con el K por omisión: la consulta peor (mínimo de
    3 repeticiones por instante) tarda menos de 50 ms, y ninguna consulta
    re-simula más de K acciones."""
    partida = partida_referencia_inmortal(semilla=123, k=K_POR_OMISION)
    jugar(partida, ACCIONES, 7)
    assert partida.jugador.acciones >= ACCIONES
    linea = partida.linea
    azar = random.Random(5)
    peor = 0.0
    for _ in range(30):
        t = azar.randint(0, partida.reloj)
        mejor = None
        for _ in range(3):
            inicio = time.perf_counter()
            linea.reconstruir_instante(t, partida)
            duracion = (time.perf_counter() - inicio) * 1000
            mejor = duracion if mejor is None else min(mejor, duracion)
            assert linea.ultimas_aplicadas <= linea.k, (
                f"FR-021: re-simuló {linea.ultimas_aplicadas} acciones (K = {linea.k})")
        peor = max(peor, mejor)
    for _ in range(10):
        linea.reconstruir_accion(azar.randint(1, linea.acciones + 1), partida)
        assert linea.ultimas_aplicadas <= linea.k, "FR-021 con #k"
    assert peor < LIMITE_MS, f"FR-019/SC-003: la consulta peor tardó {peor:.1f} ms"
    print(f"    consulta peor con K = {linea.k}: {peor:.1f} ms en {ACCIONES} acciones")


def memoria_de_la_linea(k, acciones):
    """Memoria viva que dejó jugar 'acciones' con la línea de K (tracemalloc)."""
    partida = partida_con_linea(cripta_linea(3, lado=6), k=k, semilla=3)
    tracemalloc.start()
    jugar(partida, acciones, 11)
    actual, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return actual


def caso_e2_memoria():
    """US6 escenario 2 (FR-020, SC-007): en 500 acciones, la línea con K = 25
    usa menos de la mitad de la memoria que con K = 1, y crece con las
    acciones. K = 1 con 5000 acciones queda para el bench (análisis G2)."""
    con_k1 = memoria_de_la_linea(1, 500)
    con_k25 = memoria_de_la_linea(25, 500)
    assert con_k25 * 2 < con_k1, f"SC-007: K=25 {con_k25} bytes contra K=1 {con_k1} bytes"
    mitad = memoria_de_la_linea(25, 250)
    assert mitad < con_k25, f"FR-020: no creció con las acciones ({mitad} y {con_k25})"
    print(f"    memoria en 500 acciones: K=1 {con_k1 // 1024} KiB, K=25 {con_k25 // 1024} KiB")


CASOS = (caso_e1_consulta_menor_a_50_ms, caso_e2_memoria)
# US6 escenario 3 (FR-023, recorte del pergamino constante): caso_recorte_constante
# de prueba_linea_pergamino (T019).

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}", flush=True)
    finally:
        cerrar_fuentes()
    print(f"prueba_rendimiento_linea OK ({len(CASOS)} casos)")
