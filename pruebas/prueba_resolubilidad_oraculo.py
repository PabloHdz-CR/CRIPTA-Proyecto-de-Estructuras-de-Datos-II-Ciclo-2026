"""La verificación contra el oráculo en criptas al azar (003-resolubilidad,
T013, research.md R13).

FR-001, FR-007, FR-009, FR-011 a FR-016. Para 200 criptas pequeñas
generadas con random.Random(semilla), semillas fijas 0 a 199, el resultado
estructurado del programa (a_tuplas) debe ser igual al del oráculo, campo por
campo. Compara el resultado, no el texto: el texto exacto lo cubre
prueba_resolubilidad_reporte.

Uso: py -m pruebas.prueba_resolubilidad_oraculo
"""
import sys

from pruebas.apoyo_resolubilidad import a_tuplas, generar_cripta, verificar
from pruebas.oraculo_resolubilidad import oraculo

SEMILLAS = range(200)
CAMPOS = ("veredicto", "motivo", "sala_salida_solo_sin_puerta", "orden",
          "no_obtenibles", "frontera", "ciclos")


def main():
    resolubles = 0
    con_ciclos = 0
    for semilla in SEMILLAS:
        cripta = generar_cripta(semilla)
        esperado = oraculo(cripta)
        obtenido = a_tuplas(verificar(cripta))
        if obtenido != esperado:
            for nombre, valor_obtenido, valor_esperado in zip(CAMPOS, obtenido, esperado):
                if valor_obtenido != valor_esperado:
                    print(f"Semilla {semilla}: el campo '{nombre}' difiere del oráculo.")
                    print(f"  cripta:   {cripta!r}")
                    print(f"  programa: {valor_obtenido!r}")
                    print(f"  oráculo:  {valor_esperado!r}")
                    break
            sys.exit(1)
        resolubles += esperado[0] == "RESOLUBLE"
        con_ciclos += len(esperado[6]) > 0
    # Que la muestra ejercite las dos ramas (si el generador cambiara y
    # dejara de producir ciclos, la prueba no probaría la fase 2).
    assert resolubles >= 10 and con_ciclos >= 20, (resolubles, con_ciclos)
    print(f"prueba_resolubilidad_oraculo: {len(SEMILLAS)} criptas iguales al oráculo "
          f"({resolubles} resolubles, {con_ciclos} con ciclos)")


if __name__ == "__main__":
    main()
