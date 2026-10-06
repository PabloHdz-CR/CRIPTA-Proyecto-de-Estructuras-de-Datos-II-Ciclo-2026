import random

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.ordenamiento import (ClaveOrden, UMBRAL_TAMANO, casi_ordenada,
                                        insercion, inversiones_adyacentes, mezcla,
                                        ordenar, seleccionar_algoritmo)


def le(*elementos):
    l = ListaEnlazada()
    l.agregar_todos(elementos)
    return l


def datos_de(lista_enlazada):
    r = []
    for d in lista_enlazada:
        r.append(d)
    return r


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


# ---------------------------------------------------------------- correctitud
for algoritmo in (insercion, mezcla, ordenar):
    assert datos_de(algoritmo(le())) == []
    assert datos_de(algoritmo(le(1))) == [1]
    assert datos_de(algoritmo(le(3, 1, 2))) == [1, 2, 3]
    assert datos_de(algoritmo(le(5, 4, 3, 2, 1))) == [1, 2, 3, 4, 5]       # al revés
    assert datos_de(algoritmo(le(1, 1, 1))) == [1, 1, 1]                   # todos iguales
    assert datos_de(algoritmo(le(2, 1, 2, 1, 3, 1))) == [1, 1, 1, 2, 2, 3]  # repetidos

# Ninguna de las dos funciones muta la lista original
original = le(3, 1, 2)
resultado = insercion(original)
assert datos_de(original) == [3, 1, 2] and datos_de(resultado) == [1, 2, 3]
original2 = le(3, 1, 2)
mezcla(original2)
assert datos_de(original2) == [3, 1, 2]

# Contra random + sorted() de Python (SOLO en la prueba: §7 prohíbe sorted() en el programa)
azar = random.Random(2026)
for _ in range(60):
    tamano = azar.randint(0, 200)
    valores = []
    for _ in range(tamano):
        valores.append(azar.randint(-50, 50))
    lista = le(*valores)
    esperado = sorted(valores)
    assert datos_de(insercion(lista)) == esperado
    assert datos_de(mezcla(lista)) == esperado
    assert datos_de(ordenar(lista)) == esperado

# ---------------------------------------------------------------- estabilidad
# Pares (clave, etiqueta): al ordenar por clave, los empates deben conservar
# el orden relativo original (eso es "estable").
pares = le(
    ClaveOrden(2, "a"), ClaveOrden(1, "b"), ClaveOrden(2, "c"),
    ClaveOrden(1, "d"), ClaveOrden(2, "e"), ClaveOrden(1, "f"))
for algoritmo in (insercion, mezcla):
    resultado = algoritmo(pares)
    etiquetas = []
    for item in resultado:
        etiquetas.append(item.valor)
    # Todos los de clave 1 deben salir en su orden original (b, d, f),
    # y luego todos los de clave 2 en el suyo (a, c, e)
    assert etiquetas == ["b", "d", "f", "a", "c", "e"], (algoritmo.__name__, etiquetas)

# ---------------------------------------------------------------- ClaveOrden
cosas = le(ClaveOrden("daga", 2), ClaveOrden("casco", 1), ClaveOrden("espada", 5))
resultado = ordenar(cosas)
assert [c.clave for c in resultado] == ["casco", "daga", "espada"]
assert [c.valor for c in resultado] == [1, 2, 5]

# ---------------------------------------------------------------- inversiones_adyacentes
assert inversiones_adyacentes(le()) == 0
assert inversiones_adyacentes(le(1)) == 0
assert inversiones_adyacentes(le(1, 2, 3, 4, 5)) == 0            # ya ordenada
assert inversiones_adyacentes(le(5, 4, 3, 2, 1)) == 4             # al revés: todas
assert inversiones_adyacentes(le(1, 2, 1, 2, 1)) == 2             # dos bajadas

# ---------------------------------------------------------------- casi_ordenada
assert casi_ordenada(le())
assert casi_ordenada(le(1))
ordenada_grande = le(*range(100))
assert casi_ordenada(ordenada_grande)
desordenada_grande = le(*range(99, -1, -1))
assert not casi_ordenada(desordenada_grande)
# Una lista grande con solo una inversión (99% ordenada)
casi = list(range(100))
casi[50], casi[51] = casi[51], casi[50]
assert casi_ordenada(le(*casi))

# ---------------------------------------------------------------- seleccionar_algoritmo
pequena = le(*range(10))
assert len(pequena) <= UMBRAL_TAMANO
assert seleccionar_algoritmo(pequena) == "insercion"

grande_desordenada = le(*range(199, -1, -1))     # 200 elementos, al revés
assert len(grande_desordenada) > UMBRAL_TAMANO and not casi_ordenada(grande_desordenada)
assert seleccionar_algoritmo(grande_desordenada) == "mezcla"

grande_casi_ordenada = le(*list(range(200)))
assert len(grande_casi_ordenada) > UMBRAL_TAMANO
assert seleccionar_algoritmo(grande_casi_ordenada) == "insercion"

# ordenar() de verdad despacha al algoritmo correcto (consistencia cruzada)
for caso in (pequena, grande_desordenada, grande_casi_ordenada):
    assert datos_de(ordenar(caso)) == datos_de(insercion(caso)) == datos_de(mezcla(caso))

print("Sección 6.1 OK")