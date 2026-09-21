import random
import time

from cripta.modelo.estructuras.heapMinimo import HeapMinimo


class EventoDePrueba:
    """Define SOLO <, igual que el Evento real: el montículo no puede exigir más."""

    def __init__(self, tiempo, secuencia):
        self.tiempo = tiempo
        self.secuencia = secuencia

    def __lt__(self, otro):
        if self.tiempo != otro.tiempo:
            return self.tiempo < otro.tiempo
        return self.secuencia < otro.secuencia


def ordenar_a_mano(valores):
    """Ordenamiento por inserción, solo como referencia independiente."""
    resultado = []
    for valor in valores:
        posicion = len(resultado)
        while posicion > 0 and valor < resultado[posicion - 1]:
            posicion -= 1
        resultado.insert(posicion, valor)
    return resultado


def sacar_todo(monticulo):
    salida = []
    while not monticulo.esta_vacio():
        salida.append(monticulo.extraer_minimo())
    return salida


# 1. Montículo vacío
m = HeapMinimo()
assert m.esta_vacio() and len(m) == 0 and m.es_consistente()
for operacion in (m.extraer_minimo, m.ver_minimo):
    try:
        operacion()
        assert False, "debió lanzar IndexError"
    except IndexError:
        pass

# 2. Un solo elemento
m.insertar(7)
assert len(m) == 1 and m.ver_minimo() == 7 and m.es_consistente()
assert m.extraer_minimo() == 7
assert m.esta_vacio() and m.es_consistente()

# 3. Órdenes de inserción distintos, con repetidos: sale siempre ordenado
azar = random.Random(42)
casos = [
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],                   # ya ordenado
    [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],                   # al revés
    [5, 5, 5, 5, 5],                                   # todos iguales
    [3, 1, 3, 1, 2, 2, 3, 1],                          # con repetidos
]
aleatorio = []
for _ in range(500):
    aleatorio.append(azar.randint(0, 100))
casos.append(aleatorio)
for caso in casos:
    m = HeapMinimo()
    for valor in caso:
        m.insertar(valor)
        assert m.es_consistente()
    assert len(m) == len(caso)
    assert sacar_todo(m) == ordenar_a_mano(caso)
    assert m.es_consistente()

# 4. Mezcla de inserciones y extracciones contra un modelo simple
azar = random.Random(7)
m = HeapMinimo()
modelo = []
for _ in range(1500):
    if not modelo or azar.random() < 0.6:
        valor = azar.randint(0, 50)
        m.insertar(valor)
        modelo.append(valor)
    else:
        esperado = min(modelo)
        modelo.remove(esperado)
        assert m.extraer_minimo() == esperado
    assert len(m) == len(modelo) and m.es_consistente()
    if modelo:
        assert m.ver_minimo() == min(modelo)

# 5. Desempate determinista por secuencia, sin importar el orden de inserción
eventos = []
for numero in range(200):
    eventos.append((azar.randint(0, 4), numero))       # muchos tiempos repetidos
esperado = ordenar_a_mano(eventos)
for orden in range(3):
    if orden == 1:
        eventos.reverse()
    elif orden == 2:
        azar.shuffle(eventos)
    m = HeapMinimo()
    for tiempo, secuencia in eventos:
        m.insertar(EventoDePrueba(tiempo, secuencia))
    saco = []
    for evento in sacar_todo(m):
        saco.append((evento.tiempo, evento.secuencia))
    assert saco == esperado

# 6. Recorrido, tamaño y vaciar
m = HeapMinimo()
for valor in (9, 4, 7, 1, 8, 3):
    m.insertar(valor)
vistos = []
for valor in m:
    vistos.append(valor)
assert len(vistos) == 6 and ordenar_a_mano(vistos) == [1, 3, 4, 7, 8, 9]
m.vaciar()
assert m.esta_vacio() and m.es_consistente() and len(m) == 0
m.insertar(2)                                          # sigue funcionando
assert m.extraer_minimo() == 2

# 7. Carga como la de la agenda: 300 eventos pendientes y 20 000 ciclos
#    "sacar el próximo evento, ejecutarlo y programar otro más adelante"
azar = random.Random(2026)
m = HeapMinimo()
secuencia = 0
for _ in range(300):
    secuencia += 1
    m.insertar(EventoDePrueba(azar.randint(0, 1000), secuencia))
ultimo_tiempo = 0
inicio = time.perf_counter()
for _ in range(20000):
    evento = m.extraer_minimo()
    assert evento.tiempo >= ultimo_tiempo              # el reloj nunca retrocede
    ultimo_tiempo = evento.tiempo
    secuencia += 1
    m.insertar(EventoDePrueba(evento.tiempo + azar.randint(1, 500), secuencia))
duracion = time.perf_counter() - inicio
assert len(m) == 300 and m.es_consistente()
print(f"20 000 ciclos con 300 eventos: {duracion * 1000:.0f} ms")

# 8. Una estructura de 5000 elementos
m = HeapMinimo()
valores = []
for _ in range(5000):
    valores.append(azar.randint(0, 100000))
for valor in valores:
    m.insertar(valor)
assert m.es_consistente()
anterior = -1
for _ in range(5000):
    actual = m.extraer_minimo()
    assert actual >= anterior
    anterior = actual
assert m.esta_vacio()

print("Sección 2.2 OK")