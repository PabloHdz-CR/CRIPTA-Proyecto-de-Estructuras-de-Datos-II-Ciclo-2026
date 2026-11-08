"""Oráculo de la resolubilidad (003-resolubilidad, research.md R13, T010).

Implementa las definiciones de spec.md AL PIE DE LA LETRA, sin optimizar y
sin usar ninguna clase ni el formateador del programa. Recibe una Cripta de
apoyo_resolubilidad y devuelve un resultado en tuplas de Python, con la misma
forma que apoyo_resolubilidad.a_tuplas:

    (veredicto, motivo, sala_salida_solo_sin_puerta, orden, no_obtenibles,
     frontera, ciclos)

  - orden (solo si RESOLUBLE): en cada paso se recorre DESDE CERO con las
    llaves ya ordenadas y se elige la disponible de menor id (FR-007, FR-009);
    la ubicación mostrada es la primera, por (sala, enemigo), ya alcanzada.
  - veredicto y motivo: FR-001 y FR-011.
  - no_obtenibles (siempre) y frontera (siempre): FR-011 a FR-013, FR-016.
  - ciclos (solo si NO_RESOLUBLE): una búsqueda por cada puerta bloqueada da
    la relación de FR-014; los grupos salen de la clausura transitiva y cada
    ciclo, de la regla de FR-015.

Vive en pruebas/: puede usar dict, set y list.
"""
from __future__ import annotations

from collections import deque

from cripta.modelo.puertos.dto import DIRECCIONES

RESOLUBLE = "RESOLUBLE"
NO_RESOLUBLE = "NO_RESOLUBLE"
LLAVE_SALIDA_NO_OBTENIBLE = "LLAVE_SALIDA_NO_OBTENIBLE"
SIN_PUERTA_DE_SALIDA = "SIN_PUERTA_DE_SALIDA"


def _clave_ubicacion(ubicacion):
    sala, enemigo = ubicacion
    return (sala, enemigo is not None, enemigo or "")


def oraculo(cripta):
    caras = []          # (origen, direccion, destino, cerrada, llave)
    for id_sala, salidas in cripta.salas:
        for direccion, destino, es_cerrada, llave, _cierre in salidas:
            caras.append((id_sala, direccion, destino, es_cerrada, llave))
    caras.sort(key=lambda c: (c[0], DIRECCIONES.index(c[1])))

    def transitable(cara, obtenidas):
        _, _, _, es_cerrada, llave = cara
        return (not es_cerrada) or (llave is not None and llave in obtenidas)

    def alcanzables(desde, obtenidas):
        vistas = set(desde)
        cola = deque(desde)
        while cola:
            sala = cola.popleft()
            for cara in caras:
                if cara[0] == sala and transitable(cara, obtenidas) and cara[2] not in vistas:
                    vistas.add(cara[2])
                    cola.append(cara[2])
        return vistas

    ubicaciones = {}
    for id_llave, sala, enemigo in cripta.ubicaciones:
        ubicaciones.setdefault(id_llave, []).append((sala, enemigo))
    for id_llave in ubicaciones:
        ubicaciones[id_llave].sort(key=_clave_ubicacion)
    todas = set(ubicaciones) | {cripta.llave_salida}
    todas |= {c[4] for c in caras if c[3] and c[4] is not None}

    # Orden: FR-007 y FR-009, recorriendo desde cero en cada paso.
    obtenidas = set()
    orden = []
    while True:
        region = alcanzables([cripta.sala_inicial], obtenidas)
        disponibles = [l for l in todas if l not in obtenidas
                       and any(s in region for s, _ in ubicaciones.get(l, ()))]
        if not disponibles:
            break
        elegida = min(disponibles)
        sala, enemigo = min((u for u in ubicaciones[elegida] if u[0] in region),
                            key=_clave_ubicacion)
        orden.append((elegida, sala, enemigo))
        obtenidas.add(elegida)
    region = alcanzables([cripta.sala_inicial], obtenidas)

    # Veredicto: FR-001.
    entra = any(c[0] in region and c[3] and c[4] == cripta.llave_salida
                and c[2] == cripta.sala_salida for c in caras)
    resoluble = cripta.llave_salida in obtenidas and entra

    no_obtenibles = tuple(
        (l, tuple(ubicaciones.get(l, ()))) for l in sorted(todas - obtenidas))
    frontera = tuple((c[0], c[1], c[2], c[4]) for c in caras
                     if c[0] in region and c[3] and c[2] not in region)

    if resoluble:
        return (RESOLUBLE, None, False, tuple(orden), no_obtenibles, frontera, ())

    if cripta.llave_salida not in obtenidas:
        motivo, solo_sin_puerta = LLAVE_SALIDA_NO_OBTENIBLE, False
    else:
        motivo = SIN_PUERTA_DE_SALIDA
        solo_sin_puerta = cripta.sala_salida in region

    # FR-014: K depende de Y si una salida cerrada que requiere Y conduce a
    # la ubicación de K sin atravesar otra salida intransitable. Una búsqueda
    # por cada puerta bloqueada.
    no_obt = todas - obtenidas
    dependencias = {}            # K -> {Y: [puertas]}
    for cara in caras:
        if not (cara[3] and cara[4] is not None and cara[4] in no_obt):
            continue
        llegadas = alcanzables([cara[2]], obtenidas)
        for k in no_obt:
            if any(s in llegadas for s, _ in ubicaciones.get(k, ())):
                dependencias.setdefault(k, {}).setdefault(cara[4], []).append(cara)

    # Clausura transitiva: alcanza[K] = llaves de las que K depende por cadena.
    alcanza = {k: set(dependencias.get(k, {})) for k in no_obt}
    cambio = True
    while cambio:
        cambio = False
        for k in no_obt:
            nuevas = set()
            for y in alcanza[k]:
                nuevas |= alcanza[y]
            if not nuevas <= alcanza[k]:
                alcanza[k] |= nuevas
                cambio = True

    grupos = []
    asignadas = set()
    for k in sorted(no_obt):
        if k in asignadas or k not in alcanza[k]:
            continue
        grupo = {y for y in no_obt if y in alcanza[k] and k in alcanza[y]} | {k}
        asignadas |= grupo
        grupos.append(grupo)
    grupos.sort(key=min)

    ciclos = []
    for grupo in grupos:
        actual = min(grupo)
        visitadas = []
        pasos = []
        while actual not in visitadas:
            visitadas.append(actual)
            siguiente = min(y for y in dependencias[actual] if y in grupo)
            puerta = min(dependencias[actual][siguiente],
                         key=lambda c: (c[0], DIRECCIONES.index(c[1])))
            pasos.append((actual, puerta[0], puerta[1], puerta[2], siguiente))
            actual = siguiente
        inicio = visitadas.index(actual)
        ciclos.append(tuple(pasos[inicio:]))

    return (NO_RESOLUBLE, motivo, solo_sin_puerta, (), no_obtenibles, frontera, tuple(ciclos))
