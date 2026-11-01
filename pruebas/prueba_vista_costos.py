"""Costos de las salidas y cazadores en los DTOs de la Vista
(001-terreno-cazador, Historia 3).

Requisitos que ejerce: FR-023 (la vista muestra el costo de cada salida de
la sala actual, 100 si no se declaró) y FR-024 (la vista distingue a los
cazadores de los demás enemigos). Se comprueba en los DTOs que arma el
Controlador (ConstructorEstadoVista): la Vista solo recibe esos DTOs
(principio III, contracts/vista.md).

Escenarios de aceptación: H3.E1 y H3.E2 (cada caso lleva su marca).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_vista_costos
"""
from cripta.controlador.constructorEstadoVista import ConstructorEstadoVista
from cripta.controlador.mapaEtiquetas import MapaEtiquetas
from cripta.vista.estadoVista import (
    ActorVisible, SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE, SALIDA_SIN_SALIDA,
    SalidaVisible)
from pruebas.apoyo_terreno import (
    a_lista, cerrar_fuentes, enemigo, ficha_enemigo, partida_minima, salida)

# Sala 1: N sin costo declarado (100), S costo 250 (cerrada), E costo 1, sin O.
DESCRIPCION = (
    (1, (salida("N", 2), salida("S", 3, 250, cerrada=True), salida("E", 4, 1))),
    (2, (salida("S", 1),)),
    (3, (salida("N", 1, 250),)),
    (4, (salida("O", 1, 1),)),
    (5, ()),                                   # sala de salida, aislada
)
FICHAS = (ficha_enemigo("ent_cazador", "cazador", rango=300),
          ficha_enemigo("ent_errante", "errante"))


def estado_de_la_sala_1():
    partida = partida_minima(DESCRIPCION, sala_inicial=1, fichas=FICHAS,
                             enemigos=(enemigo(1, "c-1", "ent_cazador"),
                                       enemigo(1, "e-1", "ent_errante")))
    return ConstructorEstadoVista(MapaEtiquetas()).construir(partida)


def caso_h3_e1_costos_de_las_salidas():
    """H3.E1 (FR-023): una sala con salidas de costo 100 (no declarado), 250 y 1
    → SalidaVisible.costo vale 100, 250 y 1, abierta o cerrada, y None donde
    no hay salida."""
    salidas = estado_de_la_sala_1().sala.salidas
    resumen = [(s.direccion, s.estado, s.costo) for s in salidas]
    assert resumen == [("N", SALIDA_ABIERTA, 100), ("S", SALIDA_CERRADA_CON_LLAVE, 250),
                       ("E", SALIDA_ABIERTA, 1), ("O", SALIDA_SIN_SALIDA, None)], resumen


def caso_h3_e2_cazador_distinguible():
    """H3.E2 (FR-024): un cazador y un errante en la sala → es_cazador vale True
    para el cazador y False para el errante."""
    enemigos = a_lista(estado_de_la_sala_1().sala.enemigos)
    assert len(enemigos) == 2, enemigos
    por_tipo = {actor.es_cazador: actor for actor in enemigos}
    assert set(por_tipo) == {True, False}, enemigos


def caso_dtos_sin_campos_nuevos():
    """Compatibilidad (contracts/vista.md): un DTO construido sin los campos
    nuevos sigue siendo válido, con sus valores por omisión."""
    assert SalidaVisible(direccion="N", estado=SALIDA_SIN_SALIDA).costo is None
    assert SalidaVisible("E", SALIDA_ABIERTA).costo is None
    assert ActorVisible(etiqueta="Rata #1", vida=3, vida_max=5).es_cazador is False
    assert ActorVisible("Rata #1", 3, 5).es_cazador is False


CASOS = (
    caso_h3_e1_costos_de_las_salidas,
    caso_h3_e2_cazador_distinguible,
    caso_dtos_sin_campos_nuevos,
)


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
    print(f"prueba_vista_costos OK ({len(CASOS)} casos)")


main()
