import time

from cripta.controlador.bench import benchOrdenamiento as bo
from cripta.controlador.bench.reporte import Reporte
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.ordenamiento import insercion, inversiones_adyacentes, mezcla


def datos_de(lista_enlazada):
    r = []
    for d in lista_enlazada:
        r.append(d)
    return r


# 1. Los generadores producen listas del tamaño pedido, con valores válidos
import random
azar = random.Random(1)
al_azar = bo._lista_al_azar(azar, 50)
assert len(al_azar) == 50

casi = bo._lista_casi_ordenada(azar, 100, proporcion_desorden=0.05)
assert len(casi) == 100
assert sorted(datos_de(casi)) == list(range(100))      # son los mismos valores, reordenados

lejos = bo._lista_casi_ordenada_lejos(azar, 100, intercambios=5)
assert len(lejos) == 100
assert sorted(datos_de(lejos)) == list(range(100))

# 2. ElementoContado cuenta comparaciones reales y es reiniciable
a, b = bo.ElementoContado(1), bo.ElementoContado(2)
bo.ElementoContado.comparaciones = 0
assert (a < b) is True
assert bo.ElementoContado.comparaciones == 1
lista = ListaEnlazada()
lista.agregar_todos([bo.ElementoContado(3), bo.ElementoContado(1), bo.ElementoContado(2)])
comparaciones = bo._comparaciones_de(insercion, lista)
assert comparaciones > 0

# 3. ElementoCostoso ordena igual que un entero normal (el costo no cambia el resultado)
costosos = ListaEnlazada()
costosos.agregar_todos([bo.ElementoCostoso(3), bo.ElementoCostoso(1), bo.ElementoCostoso(2)])
resultado = insercion(costosos)
assert [e.valor for e in resultado] == [1, 2, 3]

# 4. El caso "casi ordenado LOCAL" (vecinos) hace que inserción le gane claramente a mezcla
azar2 = random.Random(2026)
lista_local = bo._lista_casi_ordenada(azar2, 3000, proporcion_desorden=0.02)
assert inversiones_adyacentes(lista_local) / len(lista_local) <= 0.1   # el selector la trataría como casi ordenada
t0 = time.perf_counter(); insercion(lista_local); tiempo_insercion = time.perf_counter() - t0
t0 = time.perf_counter(); mezcla(lista_local); tiempo_mezcla = time.perf_counter() - t0
assert tiempo_insercion < tiempo_mezcla, (
    "con desorden local, inserción debería ganarle a mezcla (el atajo de la cola debe funcionar)")

# 5. El caso límite (intercambios lejanos): la inserción es mucho más lenta que
#    la mezcla, a pesar de que el heurístico de inversiones adyacentes diga "casi ordenada"
azar3 = random.Random(2026)
lista_lejos = bo._lista_casi_ordenada_lejos(azar3, 4000, intercambios=160)
proporcion = inversiones_adyacentes(lista_lejos) / len(lista_lejos)
assert proporcion <= 0.1, "este caso debe seguir pareciendo 'casi ordenada' para el heurístico"
t0 = time.perf_counter(); insercion(lista_lejos); tiempo_insercion = time.perf_counter() - t0
t0 = time.perf_counter(); mezcla(lista_lejos); tiempo_mezcla = time.perf_counter() - t0
assert tiempo_insercion > 3 * tiempo_mezcla, (
    "el caso límite debe mostrar a inserción considerablemente más lenta que mezcla, "
    "aunque el heurístico la clasifique como casi ordenada")

# 6. El benchmark completo (versión rápida) corre y llena sus 7 tablas
inicio = time.perf_counter()
reporte = bo.ejecutar(Reporte(imprimir=False), rapido=True)
assert time.perf_counter() - inicio < 120
assert len(reporte.tablas) == 7
# tabla 4: inserción siempre hace más comparaciones que mezcla con datos al azar
for fila in reporte.tablas.obtener(3)[2]:
    assert int(fila[1]) >= int(fila[2])

print("Sección 6.2 OK")