"""El trabajo de los cazadores no crece con el tamaño de la cripta
(001-terreno-cazador, Historia 4).

Requisitos que ejerce: FR-026 y SC-004, con conteos deterministas de salas
examinadas, sin medir tiempo:
  (a) cada decisión examina solo las salidas de la sala del cazador y sus
      destinos;
  (b) cada cálculo del mapa examina como máximo las salas a costo <= R de la
      sala del jugador más sus vecinas inmediatas, donde R es el mayor rango
      entre los cazadores activos en el momento del cálculo (FR-026(b)
      enmendado por la política de cota P3);
  (c) los dos conteos son idénticos en una cripta base y en otra 10 veces más
      grande con la misma región alcanzable.

Escenario de aceptación: H4.E2 (la marca va en el caso).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_conteo_cazador
"""
from cripta.modelo.mundo.mapaDistancias import MapaDistancias
from pruebas.apoyo_terreno import (
    activar_sala, buscar_enemigo, cerrar_fuentes, enemigo, ficha_enemigo, id_malla, malla,
    partida_minima)

COSTO = 100
RANGOS = (100, 200, 300)        # R = 300: el mayor de los que consultan
LADO_BASE = 9                   # 81 salas; la región a costo <= 400 cabe entera
LADO_GRANDE = 29                # 841 salas: más de 10 veces la base


class MapaQueCuenta(MapaDistancias):
    """MapaDistancias que anota qué salas consulta cada decisión (FR-026(a))."""

    def __init__(self, mundo, mayor_rango_activo):
        super().__init__(mundo, mayor_rango_activo)
        self.consultadas = []

    def distancia(self, sala):
        self.consultadas.append(sala.id)
        return super().distancia(sala)


def relativas(lado, ids):
    """Ids de la malla de 'lado' → posiciones (fila, columna) relativas al centro."""
    centro = lado // 2
    return sorted(((i - 1) // lado - centro, (i - 1) % lado - centro) for i in ids)


def region_esperada(lado, centro, rango):
    """Salas a costo <= rango del centro (Manhattan × COSTO) más sus vecinas
    inmediatas, calculadas aparte del mapa (cota de FR-026(b))."""
    dentro = set()
    for fila in range(lado):
        for columna in range(lado):
            if (abs(fila - centro) + abs(columna - centro)) * COSTO <= rango:
                dentro.add((fila, columna))
    vecinas = set()
    for fila, columna in dentro:
        for df, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f, c = fila + df, columna + dc
            if 0 <= f < lado and 0 <= c < lado and (f, c) not in dentro:
                vecinas.add((f, c))
    return len(dentro) + len(vecinas)


def medir(lado):
    """Partida en una malla de 'lado' × 'lado' con el jugador al centro y tres
    cazadores de rangos 100, 200 y 300 a dos pasos. Devuelve los conteos."""
    centro = lado // 2
    jugador = id_malla(lado, centro, centro)
    sala_cazadores = id_malla(lado, centro - 1, centro + 1)      # a costo 200
    fichas = tuple(ficha_enemigo(f"ent_c{r}", "cazador", rango=r) for r in RANGOS)
    enemigos = tuple(enemigo(sala_cazadores, f"c-{r}", f"ent_c{r}") for r in RANGOS)
    descripcion = malla(lado, costo=COSTO) + ((lado * lado + 1, ()),)
    partida = partida_minima(descripcion, sala_inicial=jugador, enemigos=enemigos, fichas=fichas)
    activar_sala(partida, sala_cazadores)
    # El mismo algoritmo y la misma política que el juego, conectado al R_activos
    # de la partida; solo agrega la cuenta de las salas consultadas.
    mapa = MapaQueCuenta(partida.mundo, partida.mayor_rango_activo)
    partida._mapa_distancias = mapa
    por_decision = []
    for r in RANGOS:
        cazador = buscar_enemigo(partida, f"c-{r}")
        mapa.consultadas = []
        cazador.comportamiento.decidir(cazador, partida)
        destinos = sorted(s.sala_destino.id for s in partida.mundo.sala(cazador.sala).salidas
                          if s is not None and not s.cerrada)
        assert set(mapa.consultadas) <= set(destinos), (mapa.consultadas, destinos)
        por_decision.append(relativas(lado, mapa.consultadas))
    # Tres decisiones de rangos crecientes: la cota sube 100 → 200 → 300 (P3
    # duplica, con tope R_activos = 300) y nunca pasa de R_activos.
    assert partida.mayor_rango_activo() == max(RANGOS)
    assert mapa.cota == max(RANGOS), mapa.cota
    return {
        "por_decision": por_decision,
        "ultimo_calculo": mapa.examinadas_ultimo_calculo,
        "calculos": mapa.calculos,
        "cota_fr026b": region_esperada(lado, centro, max(RANGOS)),
    }


def caso_h4_e2_conteos_iguales():
    """H4.E2 (FR-026, SC-004): en una cripta base y en otra 10 veces más grande
    con la misma región alcanzable, las salas que examina cada decisión (solo
    los destinos de las salidas del cazador) y las que examina el cálculo del
    mapa (a costo <= R del jugador, más sus vecinas) son idénticas, y respetan
    la cota de FR-026(b)."""
    assert LADO_GRANDE * LADO_GRANDE >= 10 * LADO_BASE * LADO_BASE
    base = medir(LADO_BASE)
    grande = medir(LADO_GRANDE)
    # (a) Cada decisión consulta como mucho las 4 vecinas de su sala.
    for consultadas in base["por_decision"]:
        assert 1 <= len(consultadas) <= 4, consultadas
    # (b) El último cálculo (R = 300) no pasa de la región más sus vecinas.
    assert base["ultimo_calculo"] <= base["cota_fr026b"], base
    assert base["cota_fr026b"] == 25 + 16          # 25 a costo <= 300 y 16 vecinas a 400
    # (c) Idénticos en las dos criptas.
    assert base == grande, (base, grande)


def caso_conteo_no_depende_del_tamano_con_cota_chica():
    """FR-026(b): con un solo cazador de rango 100, el cálculo examina la sala
    del jugador, sus 4 vecinas (a costo 100) y las 8 a costo 200 que las
    rodean: 13 salas, en la base y en la grande."""
    for lado in (LADO_BASE, LADO_GRANDE):
        centro = lado // 2
        partida = partida_minima(malla(lado, costo=COSTO) + ((lado * lado + 1, ()),),
                                 sala_inicial=id_malla(lado, centro, centro))
        mapa = MapaDistancias(partida.mundo)
        mapa.asegurar(partida.jugador.sala, 100)
        assert mapa.examinadas_ultimo_calculo == 1 + 4 + 8, (lado, mapa.examinadas_ultimo_calculo)


def caso_cota_con_tope_r_activos():
    """FR-026(b) enmendado (política P3): al recalcular, la cota se duplica
    pero nunca pasa del mayor rango entre los cazadores ACTIVOS; si el de
    mayor rango muere, el tope baja."""
    lado = LADO_BASE
    centro = lado // 2
    jugador = id_malla(lado, centro, centro)
    fichas = (ficha_enemigo("ent_corto", "cazador", rango=100),
              ficha_enemigo("ent_largo", "cazador", rango=250))
    partida = partida_minima(malla(lado, costo=COSTO) + ((lado * lado + 1, ()),),
                             sala_inicial=jugador, fichas=fichas,
                             enemigos=(enemigo(jugador + 1, "c-corto", "ent_corto"),
                                       enemigo(jugador + 1, "c-largo", "ent_largo")))
    assert partida.mayor_rango_activo() == 0                  # todavía dormidos
    activar_sala(partida, jugador + 1)
    assert partida.mayor_rango_activo() == 250
    mapa = partida.mapa_distancias
    mapa.asegurar(jugador, 100)
    assert mapa.cota == 100
    partida.mundo.sala(1).salida("E").cerrada = True          # cambia la versión
    mapa.asegurar(jugador, 100)
    assert mapa.cota == 100                                   # el estado cambió: no duplica
    mapa.asegurar(jugador, 200)                               # mismo estado: duplica a 200
    assert mapa.cota == 200, mapa.cota
    mapa.asegurar(jugador, 220)                               # duplicaría a 400: tope 250
    assert mapa.cota == 250, mapa.cota
    largo = buscar_enemigo(partida, "c-largo")
    largo.vivo = False
    assert partida.mayor_rango_activo() == 100
    partida.mundo.sala(1).salida("E").cerrada = False
    mapa.asegurar(jugador, 100)
    assert mapa.cota == 100


CASOS = (caso_h4_e2_conteos_iguales, caso_conteo_no_depende_del_tamano_con_cota_chica,
         caso_cota_con_tope_r_activos)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:                  # se reportan todos los casos
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_conteo_cazador OK ({len(CASOS)} casos)")


main()
