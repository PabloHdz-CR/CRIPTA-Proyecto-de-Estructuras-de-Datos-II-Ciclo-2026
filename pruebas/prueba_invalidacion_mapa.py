"""§5.2 y §6.3 de la Parte II (D99): la tabla "Invalidación del mapa" de
benchCazador existe, con la cripta de referencia, y la decisión (reutilizar
el mapa mientras la clave coincida) decide lo mismo que recalcular siempre
haciendo menos recálculos.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_invalidacion_mapa
"""
from cripta.controlador.bench import benchCazador
from cripta.controlador.bench.reporte import Reporte

reporte = Reporte(imprimir=False)
benchCazador.seccion_invalidacion(reporte, (benchCazador.cripta_de_referencia(),),
                                  cantidades=(20,), rapido=True)
assert len(reporte.tablas) == 1
titulo, encabezados, filas = reporte.tablas.obtener(0)
assert "Invalidación del mapa" in titulo, titulo
assert len(filas) == 2, len(filas)                       # puertas estables e inestables
for fila in filas:
    assert fila[10] == "sí", f"misma decisión: {fila}"
    assert float(fila[5]) < float(fila[6]), f"la decisión recalcula menos: {fila}"
    assert float(fila[5]) >= 1.0, "el jugador se mueve: al menos un recálculo por ciclo"
estables, inestables = filas.obtener(0), filas.obtener(1)
assert estables[2].startswith("estables") and inestables[2].startswith("inestables")
assert float(inestables[5]) > float(estables[5]), "con puertas inestables hay más recálculos"

print("prueba_invalidacion_mapa OK")
