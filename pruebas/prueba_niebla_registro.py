"""Fundamentos de la niebla (T006 de specs/002-niebla-guerra/tasks.md).

Cubre FR-011 (el conocimiento se revierte con el Diario, sin copias), FR-016
(salas conocidas ordenadas por id numérico) y FR-033 (agregar y quitar del
registro de conocidas en O(1), sin depender del tamaño del mapa).
"""
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.mundo import conocimiento as c
from cripta.modelo.mundo.sala import Sala
from cripta.modelo.mundo.salida import Salida
from cripta.modelo.nucleo.diario import Diario
from cripta.modelo.nucleo.mutador import Mutador
from cripta.modelo.puertos.errores import ErrorCripta


def _sala(id_sala):
    return Sala(id_sala, f"Sala {id_sala}", (None, None, None, None))


def caso_valores_iniciales():
    """FR-001, FR-007: una sala nueva es desconocida y una salida nueva, no observada."""
    assert c.DESCONOCIDA == 0 and c.AVISTADA == 1 and c.EXPLORADA == 2
    assert c.NO_OBSERVADA == 0 and c.ABIERTA == 1 and c.CERRADA == 2
    assert _sala(1).conocimiento == c.DESCONOCIDA, "FR-001: sala nueva desconocida"
    assert Salida("N", 2).recordada == c.NO_OBSERVADA, "FR-007: salida nueva no observada"


def caso_agregar_y_quitar():
    """FR-033: agregar al final y quitar la última; quitar otra sala es un error."""
    registro = c.RegistroConocidas()
    a, b = _sala(5), _sala(3)
    registro.agregar(a)
    registro.agregar(b)
    assert [s.id for s in registro] == [5, 3], "FR-033: orden de descubrimiento"
    assert len(registro) == 2
    try:
        registro.quitar_ultima(a)
    except ErrorCripta:
        pass
    else:
        raise AssertionError("FR-033: quitar_ultima con otra sala debía fallar")
    registro.quitar_ultima(b)
    assert [s.id for s in registro] == [5], "FR-033: quitar_ultima quita la última"


def caso_ordenadas_por_id():
    """FR-016: ids 10, 9, 2, 100 → 2, 9, 10, 100 (como números), sin tocar el registro."""
    registro = c.RegistroConocidas()
    for i in (10, 9, 2, 100):
        registro.agregar(_sala(i))
    ordenadas = registro.ordenadas_por_id()
    assert isinstance(ordenadas, ListaEnlazada), "FR-016: estructura propia"
    assert [s.id for s in ordenadas] == [2, 9, 10, 100], "FR-016: orden numérico por id"
    assert [s.id for s in registro] == [10, 9, 2, 100], "FR-016: el registro no cambia"


def caso_diario_revierte():
    """FR-011: alta en el registro y cambio de conocimiento se revierten con el Diario."""
    mutador = Mutador()
    diario = Diario()
    mutador.diario = diario
    registro = c.RegistroConocidas()
    sala = _sala(7)
    diario.abrir_intervalo(None)
    mutador.conocida_agregar(registro, sala)
    mutador.asignar(sala, "conocimiento", c.AVISTADA)
    diario.cerrar_intervalo()
    assert len(registro) == 1 and sala.conocimiento == c.AVISTADA
    assert diario.deshacer(None), "FR-011: había algo que deshacer"
    assert len(registro) == 0, "FR-011: el registro vuelve a vacío"
    assert sala.conocimiento == c.DESCONOCIDA, "FR-011: la sala vuelve a desconocida"


CASOS = (caso_valores_iniciales, caso_agregar_y_quitar, caso_ordenadas_por_id,
         caso_diario_revierte)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_niebla_registro OK ({len(CASOS)} casos)")


main()
