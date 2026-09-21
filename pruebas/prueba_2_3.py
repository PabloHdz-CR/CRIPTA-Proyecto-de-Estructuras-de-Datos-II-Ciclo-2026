import gc
import io
import random
import time
from contextlib import redirect_stdout

from cripta.controlador.bench.alternativasAgenda import (
    CLAVES_AGENDA, EventoBench, EventoContado, MonticuloSobreLista, crear_agenda)
from cripta.controlador.bench.benchAgenda import (
    EscenarioCancelacion, EscenarioCiclos, comparaciones_por_ciclo, ejecutar,
    elegir_al_azar, listas_iguales, verificar_mismo_orden)
from cripta.controlador.bench.medidor import Medidor
from cripta.controlador.bench.reporte import Reporte
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada


def sacar_todo(agenda):
    """Vacía la agenda. Con tope: una agenda con errores podría no vaciarse nunca."""
    salida = []
    for _ in range(1000):
        evento = agenda.siguiente()
        if evento is None:
            return salida
        salida.append((evento.tiempo, evento.secuencia))
    raise AssertionError("la agenda no se vació: entregó más de 1000 eventos")


# 0. Métodos nuevos de ListaEnlazada: establecer, eliminar_en y eliminar_ultimo
lista = ListaEnlazada()
for numero in range(5):
    lista.agregar_al_final(numero)                   # 0 1 2 3 4
lista.establecer(2, 20)
assert lista.obtener(2) == 20
assert lista.eliminar_en(2) == 20 and len(lista) == 4      # en el medio
assert lista.eliminar_en(0) == 0 and lista.ver_primero() == 1   # la cabeza
assert lista.eliminar_ultimo() == 4 and len(lista) == 2    # la cola
lista.agregar_al_final(9)                                  # la cola quedó bien enlazada
assert lista.obtener(2) == 9 and len(lista) == 3
assert lista.eliminar_en(2) == 9                           # eliminar la última con eliminar_en
lista.agregar_al_final(7)
assert lista.obtener(len(lista) - 1) == 7
for operacion in (0, 1, 2):
    try:
        if operacion == 0:
            lista.establecer(5, 1)
        elif operacion == 1:
            lista.eliminar_en(-1)
        else:
            ListaEnlazada().eliminar_ultimo()
        assert False, "debió lanzar IndexError"
    except IndexError:
        pass
lista.vaciar()
assert lista.esta_vacia()
lista.agregar_al_final(1)                                  # funciona tras vaciarla
assert lista.eliminar_ultimo() == 1 and lista.esta_vacia()
lista.agregar_al_final(3)
assert lista.ver_primero() == 3 and len(lista) == 1
assert repr(lista) == "ListaEnlazada([3])"
assert repr(ListaEnlazada()) == "ListaEnlazada([])"
mixta = ListaEnlazada()
mixta.agregar_todos((1, "a", (2, 3)))
assert repr(mixta) == "ListaEnlazada([1, 'a', (2, 3)])"

# 1. EventoContado cuenta cada comparación y se puede reiniciar
a = EventoContado(5, 1)
b = EventoContado(5, 2)
EventoContado.comparaciones = 0
assert (a < b) is True and (b < a) is False
assert EventoContado.comparaciones == 2
EventoContado.comparaciones = 0
assert EventoContado.comparaciones == 0
assert (EventoBench(1, 9) < EventoBench(2, 1)) is True   # gana el tiempo
assert (EventoBench(2, 1) < EventoBench(2, 2)) is True   # empate: gana la secuencia

# 2. MonticuloSobreLista (la alternativa) también ordena bien
azar = random.Random(11)
m = MonticuloSobreLista()
try:
    m.extraer_minimo()
    assert False, "debió lanzar IndexError"
except IndexError:
    pass
valores = []
for _ in range(400):
    valores.append(azar.randint(0, 60))
for valor in valores:
    m.insertar(valor)
assert len(m) == 400 and not m.esta_vacio()
anterior = -1
for _ in range(400):
    actual = m.extraer_minimo()
    assert actual >= anterior
    anterior = actual
assert m.esta_vacio()

# 3. Cada agenda respeta el orden y salta los cancelados
todas = CLAVES_AGENDA + ("reconstruida",)
for clave in todas:
    agenda = crear_agenda(clave)
    eventos = []
    for secuencia in range(1, 41):
        evento = EventoBench(azar.randint(0, 9), secuencia)   # muchos empates de tiempo
        eventos.append(evento)
        agenda.programar(evento)
    cancelados = []
    for posicion in range(0, 40, 3):
        agenda.cancelar(eventos[posicion])
        cancelados.append(posicion)
    esperado = []
    for posicion in range(40):
        if posicion not in cancelados:      # sin mirar la bandera: no todas la usan
            esperado.append((eventos[posicion].tiempo, eventos[posicion].secuencia))
    # referencia sin ninguna estructura: ordenar a mano por inserción
    ordenado = []
    for par in esperado:
        posicion = len(ordenado)
        while posicion > 0 and par < ordenado[posicion - 1]:
            posicion -= 1
        ordenado.insert(posicion, par)
    assert sacar_todo(agenda) == ordenado, clave
    assert agenda.siguiente() is None, clave                 # vacía: devuelve None
    assert len(ordenado) == 40 - len(cancelados)

# 4. Los cancelados que salen sin ejecutarse se cuentan (agendas perezosas)
for clave in ("monticulo_enlazado", "monticulo_sobre_lista", "lista_ordenada"):
    agenda = crear_agenda(clave)
    eventos = []
    for secuencia in range(1, 21):
        eventos.append(EventoBench(secuencia, secuencia))
        agenda.programar(eventos[secuencia - 1])
    for posicion in range(5):
        agenda.cancelar(eventos[posicion])
    sacar_todo(agenda)
    assert agenda.descartados == 5, clave

# 5. Todas las agendas sacan los eventos en el mismo orden
verificar_mismo_orden(False)
verificar_mismo_orden(True)

# 6. Escenarios: tamaño, orden temporal y descartados = cancelados
escenario = EscenarioCiclos("monticulo_enlazado", 150)
escenario.preparar(200)
orden = escenario.ejecutar_y_registrar()
assert len(orden) == 150
for posicion in range(1, len(orden)):
    assert orden.obtener(posicion)[0] >= orden.obtener(posicion - 1)[0]  # el reloj no retrocede
cancelacion = EscenarioCancelacion("monticulo_enlazado", 0.5)
cancelacion.preparar(100)
assert cancelacion.cancelados() == 50
vivos = cancelacion.ejecutar_y_registrar()
assert len(vivos) == 50
assert cancelacion._agenda.descartados == 50

# 6b. listas_iguales y elegir_al_azar (sin listas de Python)
uno = ListaEnlazada()
uno.agregar_todos((1, 2, 3))
dos = ListaEnlazada()
dos.agregar_todos((1, 2, 3))
assert listas_iguales(uno, dos) and listas_iguales(ListaEnlazada(), ListaEnlazada())
dos.agregar_al_final(4)
assert not listas_iguales(uno, dos)                       # distinto largo
tres = ListaEnlazada()
tres.agregar_todos((1, 2, 9))
assert not listas_iguales(uno, tres)                      # mismo largo, otro dato
base = ListaEnlazada()
for numero in range(1, 101):
    base.agregar_al_final(numero)
for cantidad in (0, 1, 37, 100):
    elegidos = elegir_al_azar(base, cantidad, random.Random(5))
    assert len(elegidos) == cantidad                       # EXACTAMENTE la cantidad pedida
    anterior = 0
    for numero in elegidos:
        assert numero > anterior and 1 <= numero <= 100    # sin repetidos y en orden
        anterior = numero
assert listas_iguales(elegir_al_azar(base, 37, random.Random(5)),
                      elegir_al_azar(base, 37, random.Random(5)))       # reproducible
assert not listas_iguales(elegir_al_azar(base, 37, random.Random(5)),
                          elegir_al_azar(base, 37, random.Random(6)))   # otra semilla
# Justicia: elegir 1 de 10, 2000 veces: cada elemento debe salir unas 200 veces
diez = ListaEnlazada()
for numero in range(10):
    diez.agregar_al_final(numero)
veces = ListaEnlazada()
for _ in range(10):
    veces.agregar_al_final(0)
azar_justicia = random.Random(99)
for _ in range(2000):
    for numero in elegir_al_azar(diez, 1, azar_justicia):
        veces.establecer(numero, veces.obtener(numero) + 1)
for numero in range(10):
    assert 130 <= veces.obtener(numero) <= 270, veces

# 7. Conteos de comparaciones (deterministas, no dependen de la velocidad)
enlazado = comparaciones_por_ciclo("monticulo_enlazado", 1000, 100)
sobre_lista = comparaciones_por_ciclo("monticulo_sobre_lista", 1000, 100)
lineal = comparaciones_por_ciclo("busqueda_lineal", 1000, 100)
ordenada = comparaciones_por_ciclo("lista_ordenada", 1000, 100)
assert enlazado == sobre_lista            # mismo algoritmo: mismas comparaciones
assert lineal == 999                      # n - 1 comparaciones por ciclo
assert lineal > 10 * enlazado             # el montículo escala mucho mejor
assert ordenada > 5 * enlazado            # insertar en una lista ordenada compara mucho más
assert comparaciones_por_ciclo("busqueda_lineal", 100, 100) == 99


# 8. Medidor: repeticiones, orden de los tiempos y recolector de basura
class Falso:
    def __init__(self, fallar=False):
        self.preparados = []
        self.ejecutados = 0
        self.fallar = fallar

    def preparar(self, n):
        self.preparados.append(n)

    def ejecutar(self):
        self.ejecutados += 1
        time.sleep(0.002)
        if self.fallar:
            raise RuntimeError("falla dentro de la medición")


falso = Falso()
medicion = Medidor(4).medir(falso, 77)
assert falso.preparados == [77, 77, 77, 77] and falso.ejecutados == 4
assert medicion.repeticiones == 4
assert 0.002 <= medicion.minimo <= medicion.promedio <= medicion.maximo
try:
    Medidor(0)
    assert False, "debió lanzar ValueError"
except ValueError:
    pass
try:
    Medidor(2).medir(Falso(fallar=True), 1)
    assert False, "debió propagar el error"
except RuntimeError:
    pass
assert gc.isenabled()                    # el recolector se reactiva aunque falle

# 9. Reporte: columnas alineadas y tablas guardadas
filas_de_prueba = ListaEnlazada()
filas_de_prueba.agregar_todos((("1", "x", "22"), ("333", "yy", "4")))
reporte = Reporte(imprimir=False)
reporte.tabla("prueba", ("a", "nombre largo", "c"), filas_de_prueba)
assert len(reporte.tablas) == 1 and len(reporte.tablas.obtener(0)[2]) == 2
captura = io.StringIO()
with redirect_stdout(captura):
    Reporte().tabla("titulo", ("a", "nombre largo", "c"), filas_de_prueba)
lineas = captura.getvalue().strip().split("\n")
tabla = lineas[1:]                       # sin la línea del título
assert len(tabla) == 4
for linea in tabla:
    assert len(linea) == len(tabla[0])

# 10. El benchmark completo (versión rápida) corre y llena las tres tablas
inicio = time.perf_counter()
reporte = ejecutar(Reporte(imprimir=False), rapido=True)
assert time.perf_counter() - inicio < 60
assert len(reporte.tablas) == 3
assert len(reporte.tablas.obtener(0)[2]) == 2 * 4        # 2 tamaños x 4 estructuras
assert len(reporte.tablas.obtener(1)[2]) == 2 * 4
assert len(reporte.tablas.obtener(2)[2]) == 3 * 2        # 3 fracciones x 2 estrategias
for fila in reporte.tablas.obtener(0)[2]:
    if "decisión" in fila[1]:
        assert fila[4] == "1.0x"                 # contra sí misma
assert "mismo orden" in reporte.notas.obtener(0)

print("Sección 2.3 OK")