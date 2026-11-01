import time
import tracemalloc

from cripta.controlador.bench import benchBitacora, benchHistorial, benchListaDoble
from cripta.controlador.bench.alternativasEstructuras import (
    BitacoraAcotada, BitacoraSinTope, PilaAcotadaSimple, crear_bitacora,
    crear_pila_acotada, nombre_bitacora, nombre_pila)
from cripta.controlador.bench.benchAgenda import listas_iguales
from cripta.controlador.bench.benchListaDoble import (
    EscenarioEquipar, EscenarioSoltar, operaciones_para)
from cripta.controlador.bench.benchTodo import ejecutar_todo
from cripta.controlador.bench.reporte import Reporte
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada


def datos_de(estructura):
    resultado = []
    for dato in estructura:
        resultado.append(dato)
    return resultado


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


# 1. PilaAcotadaSimple (la alternativa) se comporta como la PilaAcotada
simple = PilaAcotadaSimple(3)
debe_fallar(ValueError, PilaAcotadaSimple, 0)
debe_fallar(ValueError, simple.apilar, None)
debe_fallar(IndexError, simple.desapilar)
debe_fallar(IndexError, simple.ver_tope)
assert simple.esta_vacia() and not simple.esta_llena()
assert simple.apilar("a") is None and simple.apilar("b") is None and simple.apilar("c") is None
assert simple.esta_llena() and datos_de(simple) == ["c", "b", "a"]
assert simple.apilar("d") == "a"                       # descarta el más antiguo
assert datos_de(simple) == ["d", "c", "b"] and len(simple) == 3
assert simple.ver_tope() == "d" and simple.desapilar() == "d"

# 2. Las dos bitácoras muestran los últimos N mensajes, con menos, igual o más de 20
for total in (0, 5, 20, 21, 500):
    for clave in ("cola_acotada", "cola_sin_tope"):
        bitacora = crear_bitacora(clave, 20)
        for numero in range(1, total + 1):
            bitacora.agregar(f"m{numero}")
        esperado_inicio = max(1, total - 19)
        completos = datos_de(bitacora.ultimos(20))
        assert completos == [f"m{numero}" for numero in range(esperado_inicio, total + 1)], clave
        ultimos_5 = datos_de(bitacora.ultimos(5))
        assert ultimos_5 == [f"m{numero}" for numero in range(max(1, total - 4), total + 1)]
assert len(BitacoraAcotada(20)) == 0 and len(BitacoraSinTope()) == 0
acotada = crear_bitacora("cola_acotada", 20)
sin_tope = crear_bitacora("cola_sin_tope", 20)
for _ in range(1000):
    acotada.agregar("x")
    sin_tope.agregar("x")
assert len(acotada) == 20 and len(sin_tope) == 1000

# 3. Claves desconocidas y nombres
for clave in ("pila_acotada_doble", "pila_acotada_simple"):
    assert "Pila" in nombre_pila(clave)
    assert crear_pila_acotada(clave, 5) is not None
for clave in ("cola_acotada", "cola_sin_tope"):
    assert "cola" in nombre_bitacora(clave).lower()
debe_fallar(ValueError, crear_pila_acotada, "otra", 5)
debe_fallar(ValueError, crear_bitacora, "otra", 5)
debe_fallar(ValueError, nombre_pila, "otra")
debe_fallar(ValueError, nombre_bitacora, "otra")
debe_fallar(ValueError, benchListaDoble.nombre_de, "otra")

# 4. Escenarios del inventario: qué objetos se sueltan y cómo queda la lista
assert operaciones_para(100) == 25 and operaciones_para(1000) == 100
assert operaciones_para(100000) == 100 and operaciones_para(10) == 2
esperados = (("inicio", list(range(0, 25))),
             ("medio", list(range(50, 75))),
             ("fin", list(range(99, 74, -1))))
for posicion, soltados_esperados in esperados:
    for clave in ("lista_doble", "lista_enlazada"):
        escenario = EscenarioSoltar(clave, posicion)
        escenario.preparar(100)
        soltados = escenario.ejecutar_y_registrar()
        assert datos_de(soltados) == soltados_esperados, (clave, posicion)
        restantes = datos_de(escenario.resto())
        assert len(restantes) == 75
        for numero in soltados_esperados:
            assert numero not in restantes
        if clave == "lista_doble":
            assert escenario.resto().es_consistente()
for clave in ("lista_doble", "lista_enlazada"):
    escenario = EscenarioEquipar(clave)
    escenario.preparar(100)
    escenario.ejecutar()
    final = datos_de(escenario.resto())
    # cada objeto equipado va al frente: el último equipado queda primero
    assert final == list(range(74, 49, -1)) + list(range(0, 50)) + list(range(75, 100)), clave
    if clave == "lista_doble":
        assert escenario.resto().es_consistente()
benchListaDoble.verificar_equivalencia()
benchHistorial.verificar_equivalencia()
benchBitacora.verificar_equivalencia()

# 5. Memoria: contar nodos es exacto, y tracemalloc queda apagado al terminar
assert benchBitacora.mostrados_para(100) == 2000
assert benchBitacora.mostrados_para(100000) == 20
nodos_a, bytes_a = benchBitacora.memoria("cola_acotada", 20000)
nodos_s, bytes_s = benchBitacora.memoria("cola_sin_tope", 20000)
assert nodos_a == 20 and nodos_s == 20000
assert bytes_a > 0 and bytes_s > 10 * bytes_a          # la memoria constante es mucho menor
assert not tracemalloc.is_tracing()

# 6. Cada medición (versión rápida) llena sus tablas
inicio = time.perf_counter()
reporte = benchListaDoble.ejecutar(Reporte(imprimir=False), rapido=True)
assert len(reporte.tablas) == 2
assert len(reporte.tablas.obtener(0)[2]) == 2 * 3 * 2      # 2 tamaños x 3 posiciones x 2 estructuras
assert len(reporte.tablas.obtener(1)[2]) == 2 * 2
for fila in reporte.tablas.obtener(0)[2]:
    if "decisión" in fila[2]:
        assert fila[4] == "1.0x"
reporte = benchHistorial.ejecutar(Reporte(imprimir=False), rapido=True)
assert len(reporte.tablas) == 1 and len(reporte.tablas.obtener(0)[2]) == 3 * 2
reporte = benchBitacora.ejecutar(Reporte(imprimir=False), rapido=True)
assert len(reporte.tablas) == 3
for posicion in range(3):
    assert len(reporte.tablas.obtener(posicion)[2]) == 3 * 2
for fila in reporte.tablas.obtener(2)[2]:
    if "decisión" in fila[1]:
        assert fila[2] == "20"                              # nodos de la ColaAcotada

# 7. benchTodo reúne todas las mediciones (agenda=3, listaDoble=2, historial=1,
# bitácora=3, cache=3, ordenamiento=7, guardado=3, etiquetas=1, rastro=2,
# precarga=1, datos=3, cazador=5 de 001-terreno-cazador: ciclo, cota, conteos,
# comparación y enlace)
todo = ejecutar_todo(Reporte(imprimir=False), rapido=True)
assert len(todo.tablas) == 3 + 2 + 1 + 3 + 3 + 7 + 3 + 1 + 2 + 1 + 3 + 5, len(todo.tablas)
assert time.perf_counter() - inicio < 120

print("Sección 4.4 OK")