"""US2: memoria de puertas (T019 de specs/002-niebla-guerra/tasks.md).

Cubre FR-005, FR-006, FR-007 (escenarios 1 a 3 de US2), el caso borde de
caras con estados distintos (FR-021), FR-014 para la sala actual y la regla
de plan.md ("Riesgos"): `cerrada` solo se escribe en Partida.cambiar_puerta
y en el constructor de Salida (el Diario y la carga no la nombran).

Cripta de la prueba:
        4                 (4 ─S-> 1 de un solo sentido)
        ↓
  5 ─O─ 1 ═E═ 2 ─E─ 3     (1 ═ 2: cerrada con llave y cierre automático 400)
La cara 1->5 está abierta y la 5->1 cerrada (caras distintas).
"""
import ast
from pathlib import Path

from cripta.modelo.mundo.conocimiento import ABIERTA, CERRADA, NO_OBSERVADA
from cripta.modelo.nucleo.accion import AbrirPuerta, Esperar
from cripta.vista.estadoVista import SALIDA_ABIERTA

from pruebas.apoyo_niebla import (
    LLAVE, aplicar, cerrar_fuentes, controlador_sobre, dar_objeto, doble, mover,
    partida_sobre, sala, sala_n, sn)

RAIZ = Path(__file__).resolve().parent.parent
CIERRE = 400


def cripta():
    a12, b21 = doble(1, "E", 2, cerrada=True, llave=LLAVE, cierre=CIERRE)
    a23, b32 = doble(2, "E", 3)
    return (sala_n(1, a12, sn("O", 5)),
            sala_n(2, b21, a23),
            sala_n(3, b32),
            sala_n(4, sn("S", 1)),
            sala_n(5, sn("E", 1, cerrada=True)))


def cara(partida, id_sala, direccion):
    return sala(partida, id_sala).salida(direccion)


def esperar_cierre(partida, salida, maximo=20):
    for _ in range(maximo):
        if salida.cerrada:
            return
        aplicar(partida, Esperar())
    raise AssertionError("la puerta no se cerró sola")


def abrir_1_2():
    partida = partida_sobre(cripta())
    dar_objeto(partida, LLAVE)
    aplicar(partida, AbrirPuerta("E"))
    return partida


def caso_us2_e1_cambio_con_jugador_presente():
    """US2 escenario 1 (FR-005, FR-006): abrir con llave y el cierre automático
    con el jugador en la sala se observan en el acto."""
    partida = partida_sobre(cripta())
    assert cara(partida, 1, "E").recordada == CERRADA, "FR-005: observada al iniciar"
    assert cara(partida, 2, "O").recordada == CERRADA, "FR-005: también la cara 2->1"
    dar_objeto(partida, LLAVE)
    aplicar(partida, AbrirPuerta("E"))
    assert cara(partida, 1, "E").recordada == ABIERTA, "FR-005: abrir con llave se observa"
    assert cara(partida, 2, "O").recordada == CERRADA, "FR-006: la otra cara sigue cerrada"
    esperar_cierre(partida, cara(partida, 1, "E"))
    assert cara(partida, 1, "E").recordada == CERRADA, "FR-005: el cierre se observa"


def caso_us2_e2_cierre_con_jugador_lejos():
    """US2 escenario 2 (FR-006): cerrada sin que el jugador la vea, sigue recordada abierta."""
    partida = abrir_1_2()
    mover(partida, "E", "E")                 # a la 3: lejos de 1 y de 2
    salida = cara(partida, 1, "E")
    esperar_cierre(partida, salida)
    assert salida.cerrada, "la puerta está cerrada en realidad"
    assert salida.recordada == ABIERTA, "FR-006: el mapa la recuerda abierta"


def caso_us2_e3_vuelve_a_verla():
    """US2 escenario 3 (FR-005, FR-006): al entrar a una de sus salas, el recuerdo se actualiza."""
    partida = abrir_1_2()
    mover(partida, "E", "E")
    esperar_cierre(partida, cara(partida, 1, "E"))
    mover(partida, "O")                      # a la 2: una de las dos salas de la puerta
    assert cara(partida, 1, "E").recordada == CERRADA, "FR-005: observada desde la 2"
    assert cara(partida, 2, "O").recordada == CERRADA


def caso_un_sentido_y_no_observada():
    """FR-005: estando en 1 se observa la cara de un solo sentido 4->1 (entrante).
    FR-007: las caras que no tocan una sala donde estuvo el jugador no se observaron."""
    partida = partida_sobre(cripta())
    assert cara(partida, 4, "S").recordada == ABIERTA, "FR-005: entrante de un solo sentido"
    assert cara(partida, 2, "E").recordada == NO_OBSERVADA, "FR-007: 2->3 sin observar"
    assert cara(partida, 3, "O").recordada == NO_OBSERVADA, "FR-007: 3->2 sin observar"


def caso_caras_distintas():
    """Caso borde (FR-005, FR-021): cada cara guarda su propio recuerdo."""
    partida = partida_sobre(cripta())
    assert cara(partida, 1, "O").recordada == ABIERTA, "1->5 abierta"
    assert cara(partida, 5, "E").recordada == CERRADA, "5->1 cerrada"


def caso_sala_actual_desde_el_recuerdo():
    """FR-014: la sala actual se dibuja desde el recuerdo, no desde `cerrada`."""
    controlador, vista, _ = controlador_sobre(cripta())
    salida = controlador.partida.mundo.sala(1).salida("O")
    salida.cerrada = True                    # a propósito, sin cambiar_puerta
    controlador._mostrar_estado_actual()
    visible = vista.ultimo_estado.sala.salidas[3]
    assert visible.estado == SALIDA_ABIERTA, (
        f"FR-014: la vista sigue al recuerdo (abierta), no al real: {visible.estado}")


def _escrituras_de_cerrada():
    """(archivo, función) de cada escritura de `cerrada` en cripta/."""
    encontradas = []
    for ruta in sorted((RAIZ / "cripta").rglob("*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for funcion in ast.walk(arbol):
            if not isinstance(funcion, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for nodo in ast.walk(funcion):
                if isinstance(nodo, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
                    for objetivo in objetivos:
                        if isinstance(objetivo, ast.Attribute) and objetivo.attr == "cerrada":
                            encontradas.append((ruta.name, funcion.name))
                if (isinstance(nodo, ast.Call) and len(nodo.args) >= 2
                        and isinstance(nodo.args[1], ast.Constant) and nodo.args[1].value == "cerrada"):
                    encontradas.append((ruta.name, funcion.name))
    return encontradas


def caso_cerrada_solo_en_cambiar_puerta():
    """plan.md "Riesgos" (FR-005): ningún camino del juego cambia una puerta sin observarla."""
    permitidas = {("salida.py", "__init__"), ("salida.py", "cerrada"),
                  ("partida.py", "cambiar_puerta")}
    otras = [e for e in _escrituras_de_cerrada() if e not in permitidas]
    assert not otras, f"FR-005: `cerrada` se escribe fuera de cambiar_puerta: {otras}"


CASOS = (caso_us2_e1_cambio_con_jugador_presente, caso_us2_e2_cierre_con_jugador_lejos,
         caso_us2_e3_vuelve_a_verla, caso_un_sentido_y_no_observada, caso_caras_distintas,
         caso_sala_actual_desde_el_recuerdo, caso_cerrada_solo_en_cambiar_puerta)


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
    print(f"prueba_niebla_puertas OK ({len(CASOS)} casos)")


main()
