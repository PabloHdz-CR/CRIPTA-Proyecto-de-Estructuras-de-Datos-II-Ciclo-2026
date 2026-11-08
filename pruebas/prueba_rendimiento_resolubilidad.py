"""Rendimiento de la verificación (003-resolubilidad, T047).

FR-032 a FR-035, SC-002, SC-003. Escenarios:
  - H5.E1: la cripta de referencia (la de más salas de datos_offline/,
    elegida en ejecución, sin ids) se verifica en menos de 200 ms, sin red ni
    renderizado. MIENTRAS datos_offline/ NO TENGA llaves.json, se salta con
    "SIN DATOS" (tasks.md T047); T063 la vuelve obligatoria;
  - H5.E2: en cadenas de 100, 200 y 400 llaves, resolubles y con ciclo, el
    reporte de la verificación es igual al de la alternativa ingenua;
  - H5.E3: al duplicar las llaves, el cociente de SALIDAS EXAMINADAS es
    <= 2,5 en la verificación y >= 3,5 en la ingenua (se mide el contador,
    no el tiempo).

Uso: py -m pruebas.prueba_rendimiento_resolubilidad
"""
from cripta.controlador.bench import benchResolubilidad as bench

LIMITE_MS = 200.0
TAMANOS = (100, 200, 400)


def h5_e1_referencia():
    referencia = bench.medir_referencia(repeticiones=5)
    if referencia.sin_datos:
        print(f"H5.E1 SIN DATOS: datos_offline/ no tiene llaves.json; se salta ({referencia.motivo})")
        return
    assert referencia.ms_minimo < LIMITE_MS, (
        f"la verificación de la cripta de referencia ({referencia.salas} salas) tardó "
        f"{referencia.ms_minimo:.2f} ms, no menos de {LIMITE_MS} ms")
    print(f"H5.E1: {referencia.salas} salas, {referencia.ms_minimo:.2f} ms (< {LIMITE_MS} ms)")


def h5_e2_y_e3_cadenas():
    for con_ciclo in (False, True):
        mediciones = [bench.medir_cadena(llaves, con_ciclo, repeticiones=1) for llaves in TAMANOS]
        for medicion in mediciones:
            # H5.E2 (FR-035): mismo veredicto, orden y reporte.
            assert medicion.mismo_reporte, (medicion.llaves, con_ciclo)
        for chica, grande in zip(mediciones, mediciones[1:]):
            # H5.E3 (FR-033, SC-003): cocientes de salidas examinadas.
            verificacion = grande.salidas_verificacion / chica.salidas_verificacion
            ingenua = grande.salidas_ingenua / chica.salidas_ingenua
            assert verificacion <= 2.5, (chica.llaves, grande.llaves, con_ciclo, verificacion)
            assert ingenua >= 3.5, (chica.llaves, grande.llaves, con_ciclo, ingenua)
            print(f"H5.E3 {'ciclo' if con_ciclo else 'resoluble'} {chica.llaves}->{grande.llaves}: "
                  f"verificación x{verificacion:.2f}, ingenua x{ingenua:.2f}")


def main():
    h5_e1_referencia()
    h5_e2_y_e3_cadenas()
    print("prueba_rendimiento_resolubilidad OK")


if __name__ == "__main__":
    main()
