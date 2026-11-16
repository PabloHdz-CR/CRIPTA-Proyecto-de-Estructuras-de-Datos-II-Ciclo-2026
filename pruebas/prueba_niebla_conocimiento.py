"""US1: estados de sala para el jugador (T011 de specs/002-niebla-guerra/tasks.md).

Cubre FR-001, FR-002, FR-003, FR-004 y FR-016 (escenarios 1 a 3 de US1) y el
invariante del registro de conocidas (data-model.md).

Cripta de la prueba:
      1 ──E── 2 ──E── 4 ──E── 5
      │
      S
      │
      3
"""
from cripta.modelo.mundo.conocimiento import AVISTADA, DESCONOCIDA, EXPLORADA
from cripta.modelo.nucleo import mutador as m

from pruebas.apoyo_niebla import (
    cerrar_fuentes, doble, huella_conocimiento, ids_conocidas, mover, partida_sobre,
    sala, sala_n)


def cripta():
    a12, b21 = doble(1, "E", 2)
    a13, b31 = doble(1, "S", 3)
    a24, b42 = doble(2, "E", 4)
    a45, b54 = doble(4, "E", 5)
    return (sala_n(1, a12, a13), sala_n(2, b21, a24), sala_n(3, b31),
            sala_n(4, b42, a45), sala_n(5, b54))


def estados(partida):
    return {s.id: s.conocimiento for s in partida.mundo}


def registros_de_conocimiento(partida):
    """Registros del último intervalo del Diario que tocan el conocimiento."""
    intervalo = partida.diario._intervalos.ver_tope()
    return [r for r in intervalo
            if r[0] == m.CONOCIDA_AGREGAR or (r[0] == m.ATRIBUTO and r[2] == "conocimiento")]


def caso_us1_e1_instante_0():
    """US1 escenario 1 (FR-001, FR-002, FR-003, FR-016): la inicial explorada, sus
    destinos avistados, el resto desconocido; el registro tiene esas salas."""
    partida = partida_sobre(cripta())
    assert estados(partida) == {1: EXPLORADA, 2: AVISTADA, 3: AVISTADA, 4: DESCONOCIDA,
                                5: DESCONOCIDA}, f"FR-001/FR-003: {estados(partida)}"
    assert sorted(ids_conocidas(partida)) == [1, 2, 3], "FR-016: registro de conocidas"
    assert not partida.diario.hay_cambios(), "FR-003: el instante 0 no es un cambio reversible"


def caso_us1_e2_entrar_a_avistada():
    """US1 escenario 2 (FR-001, FR-004): entrar a una avistada la explora y
    aviva sus destinos desconocidos."""
    partida = partida_sobre(cripta())
    mover(partida, "E")
    assert estados(partida) == {1: EXPLORADA, 2: EXPLORADA, 3: AVISTADA, 4: AVISTADA,
                                5: DESCONOCIDA}, f"FR-004: {estados(partida)}"
    assert sorted(ids_conocidas(partida)) == [1, 2, 3, 4], "FR-016"


def caso_us1_e3_volver_a_explorada():
    """US1 escenario 3 (FR-004): volver a una explorada no cambia ninguna sala
    ni agrega registros de conocimiento al Diario."""
    partida = partida_sobre(cripta())
    mover(partida, "E")
    antes = huella_conocimiento(partida)
    conocidas = ids_conocidas(partida)
    mover(partida, "O")
    assert huella_conocimiento(partida)[0] == antes[0], "FR-004: ninguna sala cambia"
    assert ids_conocidas(partida) == conocidas, "FR-004: el registro no cambia"
    assert registros_de_conocimiento(partida) == [], "FR-004: sin registros de conocimiento"


def caso_invariante_sin_repetidas():
    """data-model.md: dos salas unidas en los dos sentidos no se agregan dos veces."""
    partida = partida_sobre(cripta())
    mover(partida, "E", "O", "E", "E", "O", "O")
    ids = ids_conocidas(partida)
    assert len(ids) == len(set(ids)), f"sala repetida en el registro: {ids}"
    for s in partida.mundo:
        assert (s.conocimiento != DESCONOCIDA) == (s.id in ids), (
            f"invariante: sala {s.id} con conocimiento {s.conocimiento} y registro {ids}")
    assert sala(partida, 5).conocimiento == AVISTADA


CASOS = (caso_us1_e1_instante_0, caso_us1_e2_entrar_a_avistada,
         caso_us1_e3_volver_a_explorada, caso_invariante_sin_repetidas)


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
    print(f"prueba_niebla_conocimiento OK ({len(CASOS)} casos)")


main()
