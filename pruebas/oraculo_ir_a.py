"""Oráculo independiente del primer paso de «ir a» (T004 de
specs/002-niebla-guerra/tasks.md; FR-019, FR-020, FR-021; base de SC-006).

Bellman-Ford HACIA ADELANTE desde la sala del jugador, sin heap, sin sellos y
sin caché, sobre el subgrafo conocido: una cara u → v se puede usar si u y v
están exploradas y la cara está recordada abierta. Nunca lee el estado real
de las puertas (`cerrada`). El costo de una salida es `salida.costo` (100 si
no se declaró, FR-019; lo resuelve la propia Salida).

Desempate (FR-020): la etiqueta de cada sala es (costo total, id de la vecina
del primer paso, índice de la dirección del primer paso en N, S, E, O), y se
queda la menor en orden lexicográfico. Los ids se comparan como números.

Es otro algoritmo y otra forma de recorrer que BuscadorRuta (Dijkstra con
heap y parada temprana), así que no comparte sus errores. Vive en pruebas/:
puede usar estructuras de Python.

Autoprueba: py -m pruebas.oraculo_ir_a
"""
from __future__ import annotations

DIRECCIONES = ("N", "S", "E", "O")
EXPLORADA = 2
ABIERTA = 1
INFINITO = None


def _caras_usables(sala):
    """(índice de dirección, salida, vecina) de las caras recorribles desde sala."""
    for indice, salida in enumerate(sala.salidas):
        if salida is None or salida.recordada != ABIERTA:
            continue
        vecina = salida.sala_destino
        if vecina is None or vecina.conocimiento != EXPLORADA:
            continue
        yield indice, salida, vecina


def primer_paso(salas, origen, destino):
    """Dirección del primer paso de la ruta de «ir a» de origen a destino, o
    None si no hay ruta conocida (o si origen es destino). `salas` es un
    iterable con todas las salas del mundo."""
    if origen is destino or origen.conocimiento != EXPLORADA or destino.conocimiento != EXPLORADA:
        return None
    todas = [s for s in salas if s.conocimiento == EXPLORADA]
    etiqueta = {id(s): INFINITO for s in todas}
    etiqueta[id(origen)] = (0, -1, -1)
    for _ in range(len(todas)):
        cambio = False
        for u in todas:
            eu = etiqueta[id(u)]
            if eu is INFINITO:
                continue
            for indice, salida, v in _caras_usables(u):
                if u is origen:
                    candidata = (eu[0] + salida.costo, v.id, indice)
                else:
                    candidata = (eu[0] + salida.costo, eu[1], eu[2])
                ev = etiqueta.get(id(v), INFINITO)
                if v is origen:
                    continue
                if ev is INFINITO or candidata < ev:
                    etiqueta[id(v)] = candidata
                    cambio = True
        if not cambio:
            break
    final = etiqueta.get(id(destino), INFINITO)
    if final is INFINITO:
        return None
    return DIRECCIONES[final[2]]


# ---------------------------------------------------------------------------
# Autoprueba con objetos falsos (no usa el modelo)
# ---------------------------------------------------------------------------

class _Sala:
    def __init__(self, id_sala, conocimiento=EXPLORADA):
        self.id = id_sala
        self.conocimiento = conocimiento
        self.salidas = (None, None, None, None)


class _Salida:
    def __init__(self, destino, costo=100, recordada=ABIERTA):
        self.sala_destino = destino
        self.costo = costo
        self.recordada = recordada


def _unir(a, direccion, b, costo=100, recordada=ABIERTA):
    salidas = list(a.salidas)
    salidas[DIRECCIONES.index(direccion)] = _Salida(b, costo, recordada)
    a.salidas = tuple(salidas)


def _autoprueba():
    # Vecinas 9 y 10 con rutas de igual costo hacia 20: el primer paso va a la 9.
    s1, s9, s10, s20 = _Sala(1), _Sala(9), _Sala(10), _Sala(20)
    _unir(s1, "N", s10, 50)
    _unir(s1, "E", s9, 50)
    _unir(s10, "E", s20, 50)
    _unir(s9, "N", s20, 50)
    assert primer_paso((s1, s9, s10, s20), s1, s20) == "E", "9 antes que 10 (FR-020)"

    # Una cara "no observada" no se usa aunque sea la más barata (FR-021).
    a, b, c = _Sala(1), _Sala(2), _Sala(3)
    _unir(a, "E", c, 10, recordada=0)
    _unir(a, "N", b, 100)
    _unir(b, "E", c, 100)
    assert primer_paso((a, b, c), a, c) == "N", "no usa caras no observadas"

    # Una cara recordada cerrada tampoco, y una vecina avistada no es transitable.
    _unir(a, "N", b, 100, recordada=2)
    assert primer_paso((a, b, c), a, c) is None, "sin ruta conocida"
    b.conocimiento = 1
    _unir(a, "N", b, 100)
    assert primer_paso((a, b, c), a, c) is None, "no atraviesa avistadas"

    # Dos salidas hacia la misma vecina con el mismo costo: N antes que E.
    x, y = _Sala(1), _Sala(2)
    _unir(x, "E", y, 30)
    _unir(x, "N", y, 30)
    assert primer_paso((x, y), x, y) == "N", "N, S, E, O hacia la misma vecina"

    # Sin costo declarado vale 100 (lo resuelve la Salida): 30 + 30 < 100.
    p, q, r = _Sala(1), _Sala(2), _Sala(3)
    _unir(p, "E", r, 100)
    _unir(p, "S", q, 30)
    _unir(q, "E", r, 30)
    assert primer_paso((p, q, r), p, r) == "S", "costo mínimo (FR-019)"
    print("oraculo_ir_a OK")


if __name__ == "__main__":
    _autoprueba()
