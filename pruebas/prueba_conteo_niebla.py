"""Costo de consultar y explorar el conocimiento (T044 de specs/002-niebla-guerra/tasks.md).

Cubre FR-032, FR-033 y SC-005 (US6 escenario 2) con conteos y no tiempos:
  - consultar el estado de una sala y el recuerdo de una cara no busca ni
    recorre nada: Mundo.sala y el iterador del registro de conocidas se
    reemplazan por versiones que fallan si se llaman;
  - una entrada con antorcha que revela 4 salas registra la misma cantidad de
    cambios en el Diario con mapas conocidos de 25, 100, 300 y 1200 salas, y
    deshacerla los revierte todos.
"""
from cripta.modelo.mundo.conocimiento import ConocimientoJugador, RegistroConocidas
from cripta.modelo.mundo.mundo import Mundo
from cripta.modelo.nucleo import mutador as m
from cripta.modelo.nucleo.accion import UsarPergamino

from pruebas.apoyo_niebla import (
    PERGAMINO, aplicar, cerrar_fuentes, conocer, dar_objeto, doble, encender_antorcha,
    huella_conocimiento, mover, partida_sobre, sala_n)

TAMANOS = (25, 100, 300, 1200)


def cripta(extras):
    """1 ─E─ 2, con la 2 rodeada de 3 (N), 4 (E) y 5 (S), más `extras` salas
    sueltas en cadena (ids desde 1000) que se marcan conocidas para agrandar
    el mapa conocido sin tocar la región de la entrada."""
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "N", 3)
    a24, b42 = doble(2, "E", 4)
    a25, b52 = doble(2, "S", 5)
    salas = [sala_n(1, a12), sala_n(2, b21, a23, a24, a25), sala_n(3, b32), sala_n(4, b42),
             sala_n(5, b52)]
    for i in range(extras):
        salidas = []
        if i + 1 < extras:
            salidas.append(doble(1000 + i, "E", 1001 + i)[0])
        if i > 0:
            salidas.append(doble(999 + i, "E", 1000 + i)[1])
        salas.append(sala_n(1000 + i, *salidas))
    return tuple(salas)


def _prohibido(*_):
    raise AssertionError("FR-032: la consulta buscó o recorrió una colección")


def caso_consultas_sin_recorrer():
    """FR-032, SC-005: estado y recuerdo no buscan salas ni recorren el registro."""
    for extras in (25, 1200):
        partida = partida_sobre(cripta(extras), diario=False)
        conocer(partida, *range(1000, 1000 + extras))
        salas = [s for s in partida.mundo]
        salidas = [x for s in salas for x in s.salidas if x is not None]
        sala_original = Mundo.sala
        iter_original = RegistroConocidas.__iter__
        Mundo.sala = _prohibido
        RegistroConocidas.__iter__ = _prohibido
        try:
            for s in salas:
                ConocimientoJugador.estado(s)
            for x in salidas:
                ConocimientoJugador.recuerdo(x)
        finally:
            Mundo.sala = sala_original
            RegistroConocidas.__iter__ = iter_original
        cerrar_fuentes()


def _registros_de_conocimiento(intervalo):
    return [r for r in intervalo if r[0] == m.CONOCIDA_AGREGAR
            or (r[0] == m.ATRIBUTO and r[2] in ("conocimiento", "recordada"))]


def caso_exploracion_proporcional_a_lo_revelado():
    """FR-033, SC-005: los registros de una entrada con antorcha no dependen del
    tamaño del mapa conocido, y deshacerla los revierte todos."""
    cantidades = []
    for extras in TAMANOS:
        partida = partida_sobre(cripta(extras))
        conocer(partida, *range(1000, 1000 + extras))
        dar_objeto(partida, PERGAMINO)
        encender_antorcha(partida)
        antes = huella_conocimiento(partida)
        mover(partida, "E")
        intervalo = list(partida.diario._intervalos.ver_tope())
        cantidades.append(len(_registros_de_conocimiento(intervalo)))
        aplicar(partida, UsarPergamino())
        assert huella_conocimiento(partida) == antes, f"FR-033: deshacer revierte todo ({extras})"
        cerrar_fuentes()
    assert len(set(cantidades)) == 1, (
        f"FR-033: los registros cambian con el tamaño del mapa: {dict(zip(TAMANOS, cantidades))}")
    assert cantidades[0] > 0


CASOS = (caso_consultas_sin_recorrer, caso_exploracion_proporcional_a_lo_revelado)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_conteo_niebla OK ({len(CASOS)} casos)")


main()
