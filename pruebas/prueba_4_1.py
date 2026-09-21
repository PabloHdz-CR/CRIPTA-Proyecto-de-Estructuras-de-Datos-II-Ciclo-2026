import random

from cripta.modelo.estructuras.listaDoble import ListaDoble


def como_lista(lista_doble):
    """Los datos hacia adelante, en una lista de Python (solo para comparar)."""
    resultado = []
    for dato in lista_doble:
        resultado.append(dato)
    return resultado


def como_lista_al_reves(lista_doble):
    resultado = []
    for dato in lista_doble.recorrer_al_reves():
        resultado.append(dato)
    return resultado


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


# 1. Lista vacía
lista = ListaDoble()
assert lista.esta_vacia() and len(lista) == 0 and lista.es_consistente()
assert lista.primero() is None and lista.ultimo() is None
for operacion in (lista.ver_primero, lista.ver_ultimo, lista.eliminar_primero,
                  lista.eliminar_ultimo):
    debe_fallar(IndexError, operacion)
debe_fallar(IndexError, lista.obtener, 0)
assert como_lista(lista) == [] and como_lista_al_reves(lista) == []
assert lista.buscar(1) is None and not lista.contiene(1)
assert repr(lista) == "ListaDoble([])"

# 2. Agregar en ambos extremos, y recorrer en los dos sentidos
n3 = lista.agregar_al_final(3)
n2 = lista.agregar_al_inicio(2)
n1 = lista.agregar_al_inicio(1)
n4 = lista.agregar_al_final(4)
assert como_lista(lista) == [1, 2, 3, 4]
assert como_lista_al_reves(lista) == [4, 3, 2, 1]
assert len(lista) == 4 and lista.es_consistente()
assert (n1.dato, n2.dato, n3.dato, n4.dato) == (1, 2, 3, 4)
assert lista.ver_primero() == 1 and lista.ver_ultimo() == 4
assert repr(lista) == "ListaDoble([1, 2, 3, 4])"
for indice in range(4):
    assert lista.obtener(indice) == indice + 1
debe_fallar(IndexError, lista.obtener, 4)
debe_fallar(IndexError, lista.obtener, -1)
assert lista.buscar(3) is n3 and lista.contiene(4) and not lista.contiene(9)

# 3. Navegación por nodos, en ambos sentidos
assert lista.primero() is n1 and lista.ultimo() is n4
assert lista.siguiente_de(n1) is n2 and lista.siguiente_de(n3) is n4
assert lista.siguiente_de(n4) is None
assert lista.anterior_de(n4) is n3 and lista.anterior_de(n2) is n1
assert lista.anterior_de(n1) is None
recorrido = []
nodo = lista.primero()
while nodo is not None:
    recorrido.append(nodo.dato)
    nodo = lista.siguiente_de(nodo)
assert recorrido == [1, 2, 3, 4]

# 4. Insertar antes y después de un nodo (extremos y medio)
n25 = lista.insertar_despues_de(n2, 2.5)        # medio
n05 = lista.insertar_antes_de(n1, 0.5)          # antes de la cabeza
n45 = lista.insertar_despues_de(n4, 4.5)        # después de la cola
n15 = lista.insertar_antes_de(n2, 1.5)          # medio
assert como_lista(lista) == [0.5, 1, 1.5, 2, 2.5, 3, 4, 4.5]
assert como_lista_al_reves(lista) == [4.5, 4, 3, 2.5, 2, 1.5, 1, 0.5]
assert lista.primero() is n05 and lista.ultimo() is n45
assert len(lista) == 8 and lista.es_consistente()

# 5. Eliminar por nodo: cabeza, cola, medio; devuelve el dato y el nodo queda inválido
assert lista.eliminar_nodo(n05) == 0.5          # cabeza
assert lista.eliminar_nodo(n45) == 4.5          # cola
assert lista.eliminar_nodo(n25) == 2.5          # medio
assert como_lista(lista) == [1, 1.5, 2, 3, 4] and lista.es_consistente()
for viejo in (n05, n45, n25):
    debe_fallar(ValueError, lista.eliminar_nodo, viejo)
    debe_fallar(ValueError, lista.siguiente_de, viejo)
    debe_fallar(ValueError, lista.anterior_de, viejo)
    debe_fallar(ValueError, lista.mover_al_inicio, viejo)
    debe_fallar(ValueError, lista.insertar_antes_de, viejo, 0)
    debe_fallar(ValueError, lista.insertar_despues_de, viejo, 0)
assert lista.eliminar_primero() == 1 and lista.eliminar_ultimo() == 4
assert como_lista(lista) == [1.5, 2, 3] and lista.es_consistente()

# 6. Un nodo de otra lista no sirve, y un objeto cualquiera tampoco
otra = ListaDoble()
ajeno = otra.agregar_al_final("x")
for operacion in (lista.eliminar_nodo, lista.siguiente_de, lista.anterior_de,
                  lista.mover_al_inicio):
    debe_fallar(ValueError, operacion, ajeno)
debe_fallar(ValueError, lista.insertar_antes_de, ajeno, 0)
debe_fallar(ValueError, lista.eliminar_nodo, None)
debe_fallar(ValueError, lista.eliminar_nodo, "no soy un nodo")
assert como_lista(otra) == ["x"] and otra.es_consistente()     # la ajena no se tocó

# 7. mover_al_inicio: el MISMO nodo sigue siendo válido
lista = ListaDoble()
nodos = []
for numero in range(1, 6):
    nodos.append(lista.agregar_al_final(numero))           # 1 2 3 4 5
lista.mover_al_inicio(nodos[2])                            # medio -> 3 1 2 4 5
assert como_lista(lista) == [3, 1, 2, 4, 5] and lista.es_consistente()
lista.mover_al_inicio(nodos[4])                            # cola  -> 5 3 1 2 4
assert como_lista(lista) == [5, 3, 1, 2, 4] and lista.es_consistente()
assert lista.ultimo() is nodos[3]
lista.mover_al_inicio(nodos[4])                            # ya es la cabeza: nada cambia
assert como_lista(lista) == [5, 3, 1, 2, 4] and lista.es_consistente()
assert nodos[2].dato == 3 and lista.siguiente_de(nodos[2]) is nodos[0]   # sigue válido
assert como_lista_al_reves(lista) == [4, 2, 1, 3, 5]
solo = ListaDoble()
unico = solo.agregar_al_inicio("a")
solo.mover_al_inicio(unico)                                # lista de un solo nodo
assert como_lista(solo) == ["a"] and solo.es_consistente()

# 8. Lista de un solo elemento: todos los extremos coinciden
solo = ListaDoble()
uno = solo.agregar_al_inicio(7)
assert solo.primero() is uno and solo.ultimo() is uno
assert solo.siguiente_de(uno) is None and solo.anterior_de(uno) is None
assert solo.eliminar_nodo(uno) == 7
assert solo.esta_vacia() and solo.primero() is None and solo.ultimo() is None
assert solo.es_consistente()
solo.agregar_al_final(8)                                   # sigue funcionando
assert como_lista(solo) == [8] and solo.es_consistente()

# 9. vaciar invalida todas las posiciones anteriores
lista = ListaDoble()
viejos = []
for numero in range(5):
    viejos.append(lista.agregar_al_final(numero))
lista.vaciar()
assert lista.esta_vacia() and lista.es_consistente()
for viejo in viejos:
    debe_fallar(ValueError, lista.eliminar_nodo, viejo)
lista.agregar_al_final(1)                                  # se puede volver a usar
assert como_lista(lista) == [1] and lista.es_consistente()
debe_fallar(ValueError, lista.eliminar_nodo, viejos[0])    # sigue inválido

# 10. Escenario del inventario (§4.5): 6 objetos, el jugador mira el tercero
inventario = ListaDoble()
objetos = ("daga", "poción", "llave", "antorcha", "escudo", "pergamino")
posiciones = []
for objeto in objetos:
    posiciones.append(inventario.agregar_al_final(objeto))
actual = posiciones[2]                                     # viendo la llave
actual = inventario.siguiente_de(actual)                   # avanza: antorcha
actual = inventario.anterior_de(actual)                    # retrocede: llave
assert actual.dato == "llave"
siguiente = inventario.siguiente_de(actual)
assert inventario.eliminar_nodo(actual) == "llave"         # la suelta: O(1)
actual = siguiente                                         # el cursor queda en la antorcha
assert como_lista(inventario) == ["daga", "poción", "antorcha", "escudo", "pergamino"]
inventario.mover_al_inicio(actual)                         # equipar la antorcha: va al frente
assert como_lista(inventario) == ["antorcha", "daga", "poción", "escudo", "pergamino"]
assert actual.dato == "antorcha" and inventario.es_consistente()
assert inventario.buscar("escudo").dato == "escudo"

# 11. Prueba aleatoria contra un modelo con lista de Python (3 000 operaciones)
azar = random.Random(2026)
lista = ListaDoble()
modelo = []                # datos en orden
nodos_vivos = []           # (nodo, dato) en el mismo orden que el modelo
contador = 0
for _ in range(3000):
    accion = azar.randint(0, 6)
    if accion == 0 or not modelo:
        contador += 1
        nodo = lista.agregar_al_inicio(contador)
        modelo.insert(0, contador)
        nodos_vivos.insert(0, nodo)
    elif accion == 1:
        contador += 1
        nodo = lista.agregar_al_final(contador)
        modelo.append(contador)
        nodos_vivos.append(nodo)
    elif accion == 2:
        posicion = azar.randrange(len(modelo))
        contador += 1
        nuevo = lista.insertar_despues_de(nodos_vivos[posicion], contador)
        modelo.insert(posicion + 1, contador)
        nodos_vivos.insert(posicion + 1, nuevo)
    elif accion == 3:
        posicion = azar.randrange(len(modelo))
        contador += 1
        nuevo = lista.insertar_antes_de(nodos_vivos[posicion], contador)
        modelo.insert(posicion, contador)
        nodos_vivos.insert(posicion, nuevo)
    elif accion == 4:
        posicion = azar.randrange(len(modelo))
        assert lista.eliminar_nodo(nodos_vivos[posicion]) == modelo[posicion]
        del modelo[posicion]
        del nodos_vivos[posicion]
    elif accion == 5:
        posicion = azar.randrange(len(modelo))
        lista.mover_al_inicio(nodos_vivos[posicion])
        modelo.insert(0, modelo.pop(posicion))
        nodos_vivos.insert(0, nodos_vivos.pop(posicion))
    else:
        if azar.random() < 0.5:
            assert lista.eliminar_primero() == modelo.pop(0)
            nodos_vivos.pop(0)
        else:
            assert lista.eliminar_ultimo() == modelo.pop()
            nodos_vivos.pop()
    assert como_lista(lista) == modelo
    assert como_lista_al_reves(lista) == modelo[::-1]
    assert len(lista) == len(modelo) and lista.es_consistente()
    if modelo:
        indice = azar.randrange(len(modelo))
        assert lista.obtener(indice) == modelo[indice]
        assert lista.primero() is nodos_vivos[0] and lista.ultimo() is nodos_vivos[-1]

print("Sección 4.1 OK")