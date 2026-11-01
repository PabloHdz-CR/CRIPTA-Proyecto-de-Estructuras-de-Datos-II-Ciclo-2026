"""Ciclo de eventos con muchos cazadores por debajo de 20 ms
(001-terreno-cazador, Historia 4).

Requisitos que ejerce: FR-025 y SC-003. Importa los escenarios de
cripta/controlador/bench/benchCazador.py en su versión rápida y falla si el
MÍNIMO de las repeticiones de un ciclo completo de eventos (entre dos
decisiones del jugador) llega a 20 ms en:
  - 20, 50 y 100 cazadores en la cripta de referencia y en la malla de 1024
    salas;
  - 100 cazadores con rangos distintos (activados en orden creciente,
    decreciente y al azar), con la política de cota del juego.
Al fallar reporta la cifra medida. Se toma el mínimo, como Medidor, porque
los demás tiempos incluyen ruido de la máquina (plan.md, "Riesgos").

Escenario de aceptación: H4.E1 (la marca va en el caso).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_rendimiento_cazador
"""
from cripta.controlador.bench import benchCazador
from cripta.controlador.bench.medidor import Medidor

REPETICIONES = 7


def caso_h4_e1_ciclo_menor_a_20_ms():
    """H4.E1 (FR-025, SC-003): con 20, 50 y 100 cazadores (y con 100 de rangos
    distintos), el mínimo de un ciclo completo queda por debajo de 20 ms."""
    medidor = Medidor(REPETICIONES)
    fallidos = []
    medidos = 0
    for nombre, escenario in benchCazador.escenarios_rendimiento(rapido=True):
        medicion = medidor.medir(escenario, escenario.cantidad)
        milisegundos = medicion.minimo * 1000
        medidos += 1
        estado = "OK" if milisegundos < benchCazador.LIMITE_CICLO_MS else "FALLA"
        print(f"    {nombre:<52} {milisegundos:7.2f} ms  {estado}")
        if milisegundos >= benchCazador.LIMITE_CICLO_MS:
            fallidos.append(f"{nombre}: {milisegundos:.2f} ms")
    assert medidos >= 2 * 3 + 3, f"faltan escenarios: {medidos}"
    assert not fallidos, "ciclo de 20 ms o más en: " + "; ".join(fallidos)


CASOS = (caso_h4_e1_ciclo_menor_a_20_ms,)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:                  # se reportan todos los casos
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_rendimiento_cazador OK ({len(CASOS)} casos)")


main()
