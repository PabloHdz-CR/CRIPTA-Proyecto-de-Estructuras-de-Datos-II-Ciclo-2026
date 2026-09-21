import random

from cripta.modelo.estructuras.pila import Pila
from cripta.modelo.estructuras.pilaAcotada import PilaAcotada


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


# ---------------------------------------------------------------- Pila
pila = Pila()
assert pila.esta_vacia() and len(pila) == 0 and datos_de(pila) == []
debe_fallar(IndexError, pila.desapilar)
debe_fallar(IndexError, pila.ver_tope)
for numero in (1, 2, 3):
    pila.apilar(numero)
assert len(pila) == 3 and pila.ver_tope() == 3
assert datos_de(pila) == [3, 2, 1]                  # del tope al fondo
assert pila.desapilar() == 3 and pila.desapilar() == 2      # último en entrar, primero en salir
pila.apilar(9)
assert pila.ver_tope() == 9 and datos_de(pila) == [9, 1]
assert pila.desapilar() == 9 and pila.desapilar() == 1
assert pila.esta_vacia()
debe_fallar(IndexError, pila.desapilar)
pila.apilar(None)                                    # la Pila simple sí admite None
assert pila.desapilar() is None
for numero in range(5):
    pila.apilar(numero)
pila.vaciar()
assert pila.esta_vacia() and datos_de(pila) == []
pila.apilar(1)                                       # funciona tras vaciarla
assert pila.ver_tope() == 1

# Deshacer los cambios de una acción en orden inverso (uso real en el Diario)
cambios = Pila()
hechos = ("vida del jugador -4", "vida de la rata -7", "trampa desarmada")
for cambio in hechos:
    cambios.apilar(cambio)
deshechos = []
while not cambios.esta_vacia():
    deshechos.append(cambios.desapilar())
assert deshechos == ["trampa desarmada", "vida de la rata -7", "vida del jugador -4"]

# ---------------------------------------------------------------- PilaAcotada
debe_fallar(ValueError, PilaAcotada, 0)
debe_fallar(ValueError, PilaAcotada, -3)
acotada = PilaAcotada(3)
assert acotada.capacidad == 3
assert acotada.esta_vacia() and not acotada.esta_llena() and len(acotada) == 0
debe_fallar(IndexError, acotada.desapilar)
debe_fallar(IndexError, acotada.ver_tope)
debe_fallar(ValueError, acotada.apilar, None)        # None no se admite

assert acotada.apilar("a") is None                   # sin descarte
assert acotada.apilar("b") is None
assert acotada.apilar("c") is None
assert acotada.esta_llena() and len(acotada) == 3
assert datos_de(acotada) == ["c", "b", "a"]          # tope primero
assert acotada.apilar("d") == "a"                    # se descarta el MÁS ANTIGUO
assert acotada.apilar("e") == "b"
assert datos_de(acotada) == ["e", "d", "c"] and len(acotada) == 3
assert acotada.ver_tope() == "e"
assert acotada.desapilar() == "e" and not acotada.esta_llena()
assert acotada.apilar("f") is None                   # hay lugar: no descarta
assert datos_de(acotada) == ["f", "d", "c"]
assert acotada.desapilar() == "f" and acotada.desapilar() == "d"
assert acotada.desapilar() == "c" and acotada.esta_vacia()
debe_fallar(IndexError, acotada.desapilar)
acotada.apilar("x")
acotada.vaciar()
assert acotada.esta_vacia() and acotada.apilar("y") is None and acotada.ver_tope() == "y"
assert acotada._elementos.es_consistente()

# Capacidad 1: cada apilada descarta la anterior
una = PilaAcotada(1)
assert una.apilar(1) is None and una.esta_llena()
assert una.apilar(2) == 1 and datos_de(una) == [2]
assert una.desapilar() == 2 and una.esta_vacia()

# El historial del retroceso (§2.11 y §4.6): 8 acciones, solo quedan las 5 últimas
historial = PilaAcotada(5)
descartadas = []
for numero in range(1, 9):
    accion = Pila()                                  # los cambios de esa acción
    accion.apilar(f"cambio A de la acción {numero}")
    accion.apilar(f"cambio B de la acción {numero}")
    viejo = historial.apilar(accion)
    if viejo is not None:
        descartadas.append(viejo.ver_tope())
assert len(historial) == 5
assert descartadas == ["cambio B de la acción 1", "cambio B de la acción 2",
                       "cambio B de la acción 3"]
deshechas = []
while not historial.esta_vacia():
    accion = historial.desapilar()
    cambios_de_la_accion = []
    while not accion.esta_vacia():
        cambios_de_la_accion.append(accion.desapilar())
    deshechas.append(cambios_de_la_accion)
assert len(deshechas) == 5
assert deshechas[0] == ["cambio B de la acción 8", "cambio A de la acción 8"]   # la última primero
assert deshechas[4] == ["cambio B de la acción 4", "cambio A de la acción 4"]   # la más antigua que quedó

# Prueba aleatoria contra un modelo con lista de Python (capacidad 5, 3 000 operaciones)
azar = random.Random(42)
acotada = PilaAcotada(5)
modelo = []                                          # el tope al final
for numero in range(3000):
    if not modelo or azar.random() < 0.65:
        esperado = None
        if len(modelo) == 5:
            esperado = modelo.pop(0)                 # el más antiguo
        modelo.append(numero)
        assert acotada.apilar(numero) == esperado
    else:
        assert acotada.desapilar() == modelo.pop()
    assert len(acotada) == len(modelo) and len(modelo) <= 5
    assert datos_de(acotada) == modelo[::-1]
    assert acotada.esta_llena() == (len(modelo) == 5)
    if modelo:
        assert acotada.ver_tope() == modelo[-1]
assert acotada._elementos.es_consistente()

print("Sección 4.2 OK")