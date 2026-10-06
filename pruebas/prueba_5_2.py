import random

from cripta.modelo.datos.cacheFichas import CacheFichas


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


def orden_interno(cache):
    """Ids del frente (más reciente) al fondo (más antiguo), para verificar el
    orden LRU directamente, sin pasar por obtener() (que lo alteraría)."""
    ids = []
    nodo = cache._entradas.primero()
    while nodo is not None:
        ids.append(nodo.dato.id_ficha)
        nodo = cache._entradas.siguiente_de(nodo)
    return ids


# 1. Vacía
debe_fallar(ValueError, CacheFichas, 0)
cache = CacheFichas(3)
assert cache.capacidad == 3 and len(cache) == 0
assert cache.obtener("x") is None
assert cache.fallos == 1 and cache.aciertos == 0
assert not cache.contiene("x")

# 2. Insertar, obtener, estadísticas
assert cache.insertar("a", "ficha-a") is None
assert cache.insertar("b", "ficha-b") is None
assert len(cache) == 2 and orden_interno(cache) == ["b", "a"]     # b es lo más reciente
assert cache.obtener("a") == "ficha-a"
assert cache.aciertos == 1 and cache.fallos == 1
assert orden_interno(cache) == ["a", "b"]          # 'a' se usó: pasa al frente
assert cache.contiene("b") and not cache.contiene("z")

# 3. El ejemplo del enunciado: A, B, C, A, D (capacidad 3) -> se desaloja B
cache = CacheFichas(3)
cache.insertar("A", 1)
cache.insertar("B", 2)
cache.insertar("C", 3)
assert orden_interno(cache) == ["C", "B", "A"]
assert cache.obtener("A") == 1
assert orden_interno(cache) == ["A", "C", "B"]     # A se usó: al frente
desalojado = cache.insertar("D", 4)
assert desalojado == "B"                            # el menos usado recientemente
assert orden_interno(cache) == ["D", "A", "C"]
assert len(cache) == 3 and not cache.contiene("B")

# 4. Reemplazar un id existente no cuenta como desalojo ni crece la caché
cache = CacheFichas(2)
cache.insertar("x", "v1")
cache.insertar("y", "v2")
assert cache.insertar("x", "v1-nueva") is None
assert len(cache) == 2 and cache.obtener("x") == "v1-nueva"

# 5. Las fichas en uso no se desalojan
cache = CacheFichas(3)
cache.insertar("a", 1)
cache.insertar("b", 2)
cache.insertar("c", 3)
cache.fijar("a")                                    # 'a' es la más antigua, pero está en uso
assert cache.esta_en_uso("a") and not cache.esta_en_uso("b")
desalojado = cache.insertar("d", 4)
assert desalojado == "b"                            # se saltó a 'a' por estar en uso
assert cache.contiene("a") and not cache.contiene("b")

# 6. Varias referencias a la misma ficha (dos ratas con la misma ficha)
cache = CacheFichas(2)
cache.insertar("rata", "ficha-rata")
cache.fijar("rata")
cache.fijar("rata")                                 # dos instancias la usan
cache.soltar_referencia("rata")                      # muere una rata
assert cache.esta_en_uso("rata")                     # sigue en uso: queda una
cache.soltar_referencia("rata")                      # muere la otra
assert not cache.esta_en_uso("rata")                 # ya se puede desalojar

# 7. Errores: fijar o soltar algo que no está, o soltar de más
cache = CacheFichas(2)
debe_fallar(ValueError, cache.fijar, "no_existe")
debe_fallar(ValueError, cache.soltar_referencia, "no_existe")
cache.insertar("a", 1)
debe_fallar(ValueError, cache.soltar_referencia, "a")     # nunca se fijó

# 8. Si TODAS están en uso, la caché crece por encima del tope (no se pierde nada)
cache = CacheFichas(2)
cache.insertar("a", 1)
cache.insertar("b", 2)
cache.fijar("a")
cache.fijar("b")
desalojado = cache.insertar("c", 3)
assert desalojado is None
assert len(cache) == 3                               # excede la capacidad, a propósito
assert cache.contiene("a") and cache.contiene("b") and cache.contiene("c")

# 9. Prueba aleatoria: nunca se desaloja algo en uso, y el tamaño no baja de lo esperado
azar = random.Random(2026)
cache = CacheFichas(5)
en_memoria = {}      # solo para el modelo de la prueba (no es parte del programa)
fijados = set()
contador = 0
for _ in range(3000):
    accion = azar.randint(0, 4)
    if accion <= 2:
        contador += 1
        id_nuevo = f"id{contador}"
        desalojado = cache.insertar(id_nuevo, contador)
        en_memoria[id_nuevo] = contador
        if desalojado is not None:
            assert desalojado not in fijados           # NUNCA se desaloja algo fijado
            del en_memoria[desalojado]
    elif accion == 3 and en_memoria:
        id_azar = azar.choice(list(en_memoria.keys()))
        cache.fijar(id_azar)
        fijados.add(id_azar)
    elif accion == 4 and fijados:
        id_azar = azar.choice(list(fijados))
        cache.soltar_referencia(id_azar)
        fijados.discard(id_azar)
    assert len(cache) == len(en_memoria)
    for id_fijado in fijados:
        assert cache.esta_en_uso(id_fijado)

# 10. ver(): como obtener(), pero sin tocar estadísticas ni reordenar
cache = CacheFichas(3)
cache.insertar("a", 1)
cache.insertar("b", 2)
assert cache.ver("a") == 1
assert cache.aciertos == 0 and cache.fallos == 0      # ver() no cuenta nada
assert orden_interno(cache) == ["b", "a"]              # tampoco reordena
assert cache.ver("no_existe") is None
assert cache.aciertos == 0 and cache.fallos == 0

print("Sección 5.2 (extra: ver) OK")