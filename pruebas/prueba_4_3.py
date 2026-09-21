import random

from cripta.modelo.estructuras.colaAcotada import ColaAcotada


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


debe_fallar(ValueError, ColaAcotada, 0)
debe_fallar(ValueError, ColaAcotada, -1)
cola = ColaAcotada(3)
assert cola.capacidad == 3
assert cola.esta_vacia() and not cola.esta_llena() and len(cola) == 0
assert datos_de(cola) == []
debe_fallar(IndexError, cola.desencolar)
debe_fallar(IndexError, cola.ver_frente)
debe_fallar(ValueError, cola.encolar, None)

# Sin llenar: se comporta como una cola normal
assert cola.encolar("a") is None and cola.encolar("b") is None
assert cola.ver_frente() == "a" and len(cola) == 2 and not cola.esta_llena()
assert cola.desencolar() == "a"
assert cola.encolar("c") is None and cola.encolar("d") is None
assert cola.esta_llena() and datos_de(cola) == ["b", "c", "d"]

# Llena: descarta el MÁS ANTIGUO y lo devuelve
assert cola.encolar("e") == "b"
assert cola.encolar("f") == "c"
assert datos_de(cola) == ["d", "e", "f"] and len(cola) == 3
assert cola.ver_frente() == "d"
assert cola.desencolar() == "d" and not cola.esta_llena()
assert cola.encolar("g") is None                     # hay lugar: no descarta
assert datos_de(cola) == ["e", "f", "g"]
cola.vaciar()
assert cola.esta_vacia() and datos_de(cola) == []
assert cola.encolar("h") is None and cola.ver_frente() == "h"    # sigue funcionando

# Capacidad 1: cada mensaje reemplaza al anterior
una = ColaAcotada(1)
assert una.encolar(1) is None and una.esta_llena()
assert una.encolar(2) == 1 and datos_de(una) == [2]

# La bitácora en pantalla (§4.8): 500 mensajes, solo se conservan los últimos 20
bitacora = ColaAcotada(20)
descartados = 0
for numero in range(1, 501):
    if bitacora.encolar(f"mensaje {numero}") is not None:
        descartados += 1
    assert len(bitacora) <= 20                       # la memoria nunca crece
assert len(bitacora) == 20 and descartados == 480
mensajes = datos_de(bitacora)
assert mensajes[0] == "mensaje 481" and mensajes[19] == "mensaje 500"
assert mensajes == [f"mensaje {numero}" for numero in range(481, 501)]   # en orden, sin huecos

# Prueba aleatoria contra un modelo con lista de Python (capacidad 7, 3 000 operaciones)
azar = random.Random(7)
cola = ColaAcotada(7)
modelo = []                                          # el más antiguo al frente
for numero in range(3000):
    if not modelo or azar.random() < 0.7:
        esperado = None
        if len(modelo) == 7:
            esperado = modelo.pop(0)
        modelo.append(numero)
        assert cola.encolar(numero) == esperado
    else:
        assert cola.desencolar() == modelo.pop(0)
    assert len(cola) == len(modelo) and len(modelo) <= 7
    assert datos_de(cola) == modelo
    assert cola.esta_llena() == (len(modelo) == 7)
    if modelo:
        assert cola.ver_frente() == modelo[0]

print("Sección 4.3 OK")