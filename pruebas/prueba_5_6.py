import random

from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.inventario import Inventario
from cripta.modelo.puertos.dto import (FichaAntidotoDTO, FichaArmaDTO,
                                       FichaArmaduraDTO,
                                       FichaPergaminoRetrocesoDTO, FichaPocionDTO)


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


def datos_de(lista_enlazada):
    r = []
    for d in lista_enlazada:
        r.append(d.ficha.id)
    return r


def cache_con(*fichas):
    cache = CacheFichas(50)
    for ficha in fichas:
        cache.insertar(ficha.id, ficha)
    return cache, fichas


DAGA = FichaArmaDTO(id="itm_daga", nombre="Daga", peso=2, valor=15, ataque_bonus=3)
ESPADA = FichaArmaDTO(id="itm_espada", nombre="Espada", peso=5, valor=40, ataque_bonus=8)
ESCUDO = FichaArmaduraDTO(id="itm_escudo", nombre="Escudo", peso=6, valor=20, defensa_bonus=4)
CASCO = FichaArmaduraDTO(id="itm_casco", nombre="Casco", peso=1, valor=10, defensa_bonus=2)
POCION = FichaPocionDTO(id="itm_pocion", nombre="Poción", peso=1, valor=10, cura=8)
PERGAMINO = FichaPergaminoRetrocesoDTO(id="itm_pergamino", nombre="Pergamino", peso=0, valor=50)
ANTIDOTO = FichaAntidotoDTO(id="itm_antidoto", nombre="Antídoto", peso=1, valor=5)


# 1. Vacío
cache, _ = cache_con(DAGA)
inv = Inventario(5, cache)
assert inv.capacidad == 5 and len(inv) == 0 and inv.esta_vacio() and not inv.esta_lleno()
assert inv.actual() is None and inv.siguiente() is None and inv.anterior() is None
debe_fallar(IndexError, inv.soltar_actual)
debe_fallar(IndexError, inv.usar_actual)
debe_fallar(IndexError, inv.equipar_actual)
assert inv.arma_equipada() is None and inv.armadura_equipada() is None
assert inv.cantidad_pergaminos() == 0

# 2. Recoger exige que la ficha ya esté en caché (precondición documentada)
cache_vacia = CacheFichas(5)
inv_vacio_cache = Inventario(5, cache_vacia)
debe_fallar(ValueError, inv_vacio_cache.recoger, DAGA)

# 3. Recoger: el cursor queda en el primero, y fija la ficha en caché
cache, _ = cache_con(DAGA, POCION, ESCUDO)
inv = Inventario(5, cache)
daga = inv.recoger(DAGA)
assert inv.actual() is daga and len(inv) == 1
assert cache.esta_en_uso("itm_daga")
pocion = inv.recoger(POCION)
assert inv.actual() is daga            # agregar al final no mueve el cursor
assert [o.ficha.id for o in inv] == ["itm_daga", "itm_pocion"]
escudo = inv.recoger(ESCUDO)
assert [o.ficha.id for o in inv] == ["itm_daga", "itm_pocion", "itm_escudo"]

# 4. Lleno: recoger devuelve None sin romper nada
cache_chica, _ = cache_con(DAGA, POCION, CASCO)
inv_chico = Inventario(2, cache_chica)
inv_chico.recoger(DAGA)
inv_chico.recoger(POCION)
assert inv_chico.esta_lleno()
assert inv_chico.recoger(CASCO) is None
assert len(inv_chico) == 2
assert not cache_chica.esta_en_uso("itm_casco")        # nunca se fijó: no se recogió

# 5. Navegación en ambos sentidos
cache, _ = cache_con(DAGA, POCION, ESCUDO)
inv = Inventario(5, cache)
inv.recoger(DAGA)
inv.recoger(POCION)
inv.recoger(ESCUDO)
assert inv.actual().ficha.id == "itm_daga"
assert inv.siguiente().ficha.id == "itm_pocion"
assert inv.siguiente().ficha.id == "itm_escudo"
assert inv.siguiente().ficha.id == "itm_escudo"        # ya en el último: no se pasa
assert inv.anterior().ficha.id == "itm_pocion"
assert inv.anterior().ficha.id == "itm_daga"
assert inv.anterior().ficha.id == "itm_daga"            # ya en el primero: no se pasa

# 6. Soltar en el medio, sin que importe la posición: el inventario queda bien
cache, _ = cache_con(DAGA, POCION, ESCUDO)
inv = Inventario(5, cache)
inv.recoger(DAGA)
inv.recoger(POCION)
inv.recoger(ESCUDO)
inv.siguiente()                           # ahora mira la poción (la del medio)
assert inv.actual().ficha.id == "itm_pocion"
soltado = inv.soltar_actual()
assert soltado.ficha.id == "itm_pocion"
assert [o.ficha.id for o in inv] == ["itm_daga", "itm_escudo"]
assert not cache.esta_en_uso("itm_pocion")               # se soltó la fijación
assert inv.actual().ficha.id == "itm_escudo"              # el cursor pasó al vecino

# 7. Soltar el único objeto deja el inventario vacío otra vez
cache, _ = cache_con(DAGA)
inv = Inventario(5, cache)
inv.recoger(DAGA)
inv.soltar_actual()
assert inv.esta_vacio() and inv.actual() is None
assert not cache.esta_en_uso("itm_daga")

# 8. usar_actual: libera la referencia igual que soltar
cache, _ = cache_con(POCION)
inv = Inventario(5, cache)
inv.recoger(POCION)
usado = inv.usar_actual()
assert usado.ficha.id == "itm_pocion" and inv.esta_vacio()
assert not cache.esta_en_uso("itm_pocion")

# 9. Equipar: mueve al frente, aplica solo a arma/armadura, y SUSTITUYE sin eliminar
cache, _ = cache_con(DAGA, ESPADA, ESCUDO, CASCO, POCION)
inv = Inventario(6, cache)
inv.recoger(DAGA)
inv.recoger(ESPADA)
inv.recoger(ESCUDO)
inv.recoger(POCION)
inv.siguiente()                           # mira la espada
inv.equipar_actual()
assert inv.arma_equipada().ficha.id == "itm_espada"
assert [o.ficha.id for o in inv] == ["itm_espada", "itm_daga", "itm_escudo", "itm_pocion"]

# equipar movió la espada al frente; el cursor quedó sobre ella (posición 0).
# Avanzar una vez lleva a la daga, que sigue en su posición original (1).
inv.siguiente()
assert inv.actual().ficha.id == "itm_daga"
inv.equipar_actual()
assert inv.arma_equipada().ficha.id == "itm_daga"         # la daga reemplaza a la espada
assert [o.ficha.id for o in inv] == ["itm_daga", "itm_espada", "itm_escudo", "itm_pocion"]
# la espada SIGUE en el inventario, solo que ya no está marcada como equipada
assert any(o.ficha.id == "itm_espada" for o in inv)

inv.siguiente(); inv.siguiente()          # mira el escudo
assert inv.actual().ficha.id == "itm_escudo"
inv.equipar_actual()
assert inv.armadura_equipada().ficha.id == "itm_escudo"

# No se puede equipar una poción
inv.siguiente()
while inv.actual().ficha.id != "itm_pocion":
    inv.siguiente()
debe_fallar(ValueError, inv.equipar_actual)

# 10. Soltar el objeto equipado limpia la referencia de equipo
cache, _ = cache_con(DAGA, POCION)
inv = Inventario(5, cache)
inv.recoger(DAGA)
inv.recoger(POCION)
inv.equipar_actual()                      # equipa la daga (es 'actual' tras recoger)
assert inv.arma_equipada() is not None
while inv.actual().ficha.id != "itm_daga":
    inv.siguiente()
inv.soltar_actual()
assert inv.arma_equipada() is None        # ya no hay arma equipada: se limpió sola
assert [o.ficha.id for o in inv] == ["itm_pocion"]

# 11. Pergaminos
cache, _ = cache_con(DAGA, PERGAMINO, ANTIDOTO, PERGAMINO)
inv = Inventario(10, cache)
inv.recoger(DAGA)
inv.recoger(PERGAMINO)
inv.recoger(ANTIDOTO)
inv.recoger(PERGAMINO)
assert inv.cantidad_pergaminos() == 2

# 12. Vista ordenada por peso, valor y nombre, SIN alterar el orden real
cache, _ = cache_con(ESPADA, DAGA, CASCO, ESCUDO)
inv = Inventario(10, cache)
inv.recoger(ESPADA)     # peso 5, valor 40, "Espada"
inv.recoger(DAGA)       # peso 2, valor 15, "Daga"
inv.recoger(CASCO)      # peso 1, valor 10, "Casco"
inv.recoger(ESCUDO)     # peso 6, valor 20, "Escudo"
orden_real_antes = [o.ficha.id for o in inv]

por_peso = inv.vista_ordenada("peso")
assert [o.ficha.id for o in por_peso] == ["itm_casco", "itm_daga", "itm_espada", "itm_escudo"]

por_valor = inv.vista_ordenada("valor")
assert [o.ficha.id for o in por_valor] == ["itm_casco", "itm_daga", "itm_escudo", "itm_espada"]

por_nombre = inv.vista_ordenada("nombre")
assert [o.ficha.id for o in por_nombre] == ["itm_casco", "itm_daga", "itm_escudo", "itm_espada"]

assert [o.ficha.id for o in inv] == orden_real_antes      # el orden real NO cambió
debe_fallar(ValueError, inv.vista_ordenada, "color")

# Vista ordenada sobre inventario vacío o de 1 elemento
cache_vacio, _ = cache_con(DAGA)
vacio = Inventario(5, cache_vacio)
assert len(vacio.vista_ordenada("peso")) == 0
vacio.recoger(DAGA)
assert [o.ficha.id for o in vacio.vista_ordenada("peso")] == ["itm_daga"]

# 13. Prueba aleatoria: el inventario nunca excede su capacidad, y las
#     fijaciones de caché coinciden exactamente con lo que hay dentro
azar = random.Random(7)
CATALOGO = (DAGA, ESPADA, ESCUDO, CASCO, POCION, PERGAMINO, ANTIDOTO)
cache = CacheFichas(50)
for ficha in CATALOGO:
    cache.insertar(ficha.id, ficha)
inv = Inventario(6, cache)
modelo = []     # ids de instancia vivos, en orden real, para contrastar tamaño
for _ in range(2000):
    accion = azar.randint(0, 3)
    if accion <= 1:
        ficha = azar.choice(CATALOGO)
        objeto = inv.recoger(ficha)
        if objeto is not None:
            modelo.append(objeto.id_instancia)
        else:
            assert inv.esta_lleno()
    elif accion == 2 and not inv.esta_vacio():
        if azar.random() < 0.5:
            inv.siguiente()
        else:
            inv.anterior()
    elif accion == 3 and not inv.esta_vacio():
        removido = inv.soltar_actual()
        modelo.remove(removido.id_instancia)
    assert len(inv) == len(modelo) and len(inv) <= 6
    assert (inv.actual() is None) == inv.esta_vacio()

print("Sección 5.6 OK")