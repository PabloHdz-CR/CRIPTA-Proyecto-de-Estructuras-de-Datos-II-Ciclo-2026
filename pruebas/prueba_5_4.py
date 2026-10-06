from cripta.modelo.datos.esqueletoCripta import EsqueletoCripta
from cripta.modelo.datos.planificadorPrecarga import PlanificadorPrecarga
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.dto import PaginaSalasDTO, SalaDTO, SalidaDTO


def salidas(*pares):
    """pares: (direccion, id_destino, cerrada=False)."""
    lista = ListaEnlazada()
    for par in pares:
        direccion, destino = par[0], par[1]
        cerrada = par[2] if len(par) > 2 else False
        lista.agregar_al_final(SalidaDTO(direccion=direccion, sala=destino, cerrada=cerrada))
    return lista


def pagina_de(salas_dict_like, total_paginas=1, pagina=1):
    """salas_dict_like: lista de SalaDTO ya armadas."""
    lista = ListaEnlazada()
    lista.agregar_todos(salas_dict_like)
    return PaginaSalasDTO(pagina=pagina, total_paginas=total_paginas, salas=lista)


def ids_de(lista_enlazada):
    resultado = []
    for dato in lista_enlazada:
        resultado.append(dato)
    return resultado


# --- Cripta de prueba: un pasillo lineal 1-2-3-4-5, con una puerta cerrada
#     entre 3 y 4, y una bifurcación en 2 hacia 6 ---
#     1 - 2 - 3 | 4 - 5
#         |
#         6
salas_prueba = (
    SalaDTO(id=1, nombre="S1", salidas=salidas(("N", 2))),
    SalaDTO(id=2, nombre="S2", salidas=salidas(("S", 1), ("N", 3), ("E", 6))),
    SalaDTO(id=3, nombre="S3", salidas=salidas(("S", 2), ("N", 4, True))),   # cerrada
    SalaDTO(id=4, nombre="S4", salidas=salidas(("S", 3, True), ("N", 5))),
    SalaDTO(id=5, nombre="S5", salidas=salidas(("S", 4))),
    SalaDTO(id=6, nombre="S6", salidas=salidas(("O", 2))),
)


def esqueleto_de_prueba():
    e = EsqueletoCripta()
    e.agregar_pagina(pagina_de(salas_prueba))
    return e


# 1. EsqueletoCripta: buscar, vecinas abiertas, no duplicar
e = esqueleto_de_prueba()
assert len(e) == 6
assert e.buscar(1).sala.nombre == "S1"
assert e.buscar(99) is None
assert ids_de(e.vecinas_abiertas(2)) == [3, 1, 6]        # orden N,S,E,O: N(3), S(1), E(6)
assert ids_de(e.vecinas_abiertas(3)) == [2]              # la salida a 4 está cerrada: no cuenta
assert ids_de(e.vecinas_abiertas(99)) == []               # sala inexistente: lista vacía
e.agregar_pagina(pagina_de([salas_prueba[0]]))             # repetir una página no duplica
assert len(e) == 6
assert e.paginas_completas(1) and not e.paginas_completas(0)

# 2. Varias páginas se acumulan
e2 = EsqueletoCripta()
e2.agregar_pagina(pagina_de(salas_prueba[:3], total_paginas=2, pagina=1))
assert len(e2) == 3 and not e2.paginas_completas(1)
e2.agregar_pagina(pagina_de(salas_prueba[3:], total_paginas=2, pagina=2))
assert len(e2) == 6 and e2.paginas_completas(2)

# 3. PlanificadorPrecarga: BFS determinista desde la sala 1, lote completo
e = esqueleto_de_prueba()
p = PlanificadorPrecarga()
lote = p.siguiente_lote(e, 1, limite=10)
# BFS desde 1: visita 2 primero (único vecino). Desde 2, en orden N,S,E,O: 3 (N), 1 ya visto (S), 6 (E).
# Desde 3: solo 2, ya visto (4 está detrás de puerta cerrada). Desde 6: solo 2, ya visto.
assert ids_de(lote) == [2, 3, 6]
for id_sala in (2, 3, 6):
    assert e.buscar(id_sala).solicitada

# 4. Una segunda llamada inmediata no repite lo ya solicitado
lote2 = p.siguiente_lote(e, 1, limite=10)
assert ids_de(lote2) == []                                 # nada nuevo que ofrecer

# 5. El límite de lote se respeta
e = esqueleto_de_prueba()
p = PlanificadorPrecarga()
lote_chico = p.siguiente_lote(e, 1, limite=2)
assert len(lote_chico) == 2
assert ids_de(lote_chico) == [2, 3]                        # 2 (único vecino de 1), luego 3 (N desde 2)

# 6. Una cripta más grande (lineal de 30 salas) respeta el tope de 10 por lote
e = EsqueletoCripta()
grandes = []
for numero in range(1, 31):
    pares = []
    if numero > 1:
        pares.append(("S", numero - 1))
    if numero < 30:
        pares.append(("N", numero + 1))
    grandes.append(SalaDTO(id=numero, nombre=f"S{numero}", salidas=salidas(*pares)))
e.agregar_pagina(pagina_de(grandes))
p = PlanificadorPrecarga()
lote = p.siguiente_lote(e, 1, limite=10)
assert ids_de(lote) == list(range(2, 12))                  # las 10 más cercanas, en orden

# 7. Sala aislada (sin salidas) no revienta: lote vacío
aislada = EsqueletoCripta()
aislada.agregar_pagina(pagina_de([SalaDTO(id=1, nombre="sola", salidas=ListaEnlazada())]))
p = PlanificadorPrecarga()
assert ids_de(p.siguiente_lote(aislada, 1)) == []

# 8. Determinismo: el mismo esqueleto, en cualquier estado, da siempre el mismo lote
for _ in range(5):
    e = esqueleto_de_prueba()
    lote = p.siguiente_lote(e, 1, limite=10)
    assert ids_de(lote) == [2, 3, 6]

print("Sección 5.4 OK")