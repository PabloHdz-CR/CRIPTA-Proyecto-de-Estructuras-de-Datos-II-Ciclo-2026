"""US5: el pergamino revierte el conocimiento (T038 de specs/002-niebla-guerra/tasks.md).

Cubre FR-010, FR-011, FR-024, FR-029 y FR-034: los escenarios obligatorios 5 y
6 del Apéndice B (escenarios 1 y 2 de US5), sus casos borde y SC-003 (1000
secuencias aplicadas y revertidas).
"""
import random

from cripta.modelo.mundo.conocimiento import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA
from cripta.modelo.nucleo import mutador as m
from cripta.modelo.nucleo.accion import AbrirPuerta, Esperar, UsarPergamino
from cripta.vista.comando import Comando

from pruebas.apoyo_niebla import (
    LLAVE, PERGAMINO, aplicar, aplicar_paso, cerrar_fuentes, conocer, controlador_sobre,
    dar_objeto, doble, encender_antorcha, huella_conocimiento, ids_conocidas, mover,
    partida_sobre, pasillo_n, sala, sala_n, secuencias_sc003)

SECUENCIAS = 1000
SEMILLA = 20261115


def cripta_antorcha():
    """1 ─E─ 2, y la 2 con vecinas 3 (N), 4 (E) y 5 (S); la 3 sigue a la 6."""
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "N", 3)
    a24, b42 = doble(2, "E", 4)
    a25, b52 = doble(2, "S", 5)
    a36, b63 = doble(3, "N", 6)
    return (sala_n(1, a12), sala_n(2, b21, a23, a24, a25), sala_n(3, b32, a36),
            sala_n(4, b42), sala_n(5, b52), sala_n(6, b63))


def dar_pergaminos(partida, cantidad):
    for _ in range(cantidad):
        dar_objeto(partida, PERGAMINO)


def caso_apendice_b5_pergamino_sobre_entrada_con_antorcha():
    """Apéndice B 5 / US5 escenario 1 (FR-010, FR-011): el pergamino devuelve
    la sala y las vecinas exploradas por la antorcha, y los recuerdos de
    puertas, a su estado anterior."""
    partida = partida_sobre(cripta_antorcha())
    dar_pergaminos(partida, 1)
    encender_antorcha(partida)
    huella = huella_conocimiento(partida)
    conocidas = ids_conocidas(partida)
    mover(partida, "E")
    assert huella_conocimiento(partida) != huella, "la entrada con antorcha cambió el mapa"
    aplicar(partida, UsarPergamino())
    assert huella_conocimiento(partida) == huella, "FR-011: el conocimiento vuelve al anterior"
    assert ids_conocidas(partida) == conocidas, "FR-011: el registro de conocidas también"


def caso_apendice_b6_pergamino_durante_el_viaje():
    """Apéndice B 6 / US5 escenario 2 (FR-011, FR-024, FR-029): con el viaje en
    curso, el pergamino lo detiene al terminar el paso, revierte solo ese paso
    y el viaje no sigue."""
    controlador, vista, registro = controlador_sobre(pasillo_n(6))
    partida = controlador.partida
    conocer(partida, 2, 3, 4, 5, 6)
    dar_pergaminos(partida, 1)
    controlador.procesar(Comando("ir_a", (6,)))          # paso 1: a la 2
    reloj_tras_1 = partida.reloj
    huella_tras_1 = huella_conocimiento(partida)
    controlador.procesar(None)                            # paso 2: a la 3
    assert partida.jugador.sala == 3
    controlador.procesar(Comando("pergamino"))
    assert controlador.viaje is None, "FR-029: el viaje se detiene"
    assert "Viaje detenido: pergamino de retroceso." in vista.mensajes, (
        f"FR-025: motivo del pergamino: {vista.mensajes[-3:]}")
    assert partida.jugador.sala == 2 and partida.reloj == reloj_tras_1, (
        "FR-029: se revierte solo el último paso")
    assert huella_conocimiento(partida) == huella_tras_1, "FR-011: y su conocimiento"
    for _ in range(3):
        controlador.procesar(None)
    assert partida.jugador.sala == 2, "FR-029: el viaje no continúa"


def caso_borde_revertir_primera_entrada():
    """FR-010, FR-011: revertir la primera entrada a una sala la devuelve a
    avistada y sus destinos nuevos a desconocidos."""
    partida = partida_sobre(pasillo_n(4))
    dar_pergaminos(partida, 1)
    mover(partida, "E")
    assert sala(partida, 3).conocimiento == AVISTADA
    aplicar(partida, UsarPergamino())
    assert sala(partida, 2).conocimiento == AVISTADA, "FR-011: vuelve a avistada"
    assert sala(partida, 3).conocimiento == DESCONOCIDA, "FR-011: su destino vuelve a desconocido"


def caso_borde_revertir_entrada_a_explorada():
    """FR-011: revertir un movimiento a una sala ya explorada restaura solo los
    recuerdos de puertas observados en ese paso."""
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "E", 3, cerrada=True, llave=LLAVE, cierre=400)
    partida = partida_sobre((sala_n(1, a12), sala_n(2, b21, a23), sala_n(3, b32)))
    dar_objeto(partida, LLAVE)
    dar_pergaminos(partida, 1)
    mover(partida, "E")
    aplicar(partida, AbrirPuerta("E"))
    mover(partida, "O")
    puerta = sala(partida, 2).salida("E")
    while not puerta.cerrada:
        aplicar(partida, Esperar())
    assert puerta.recordada == ABIERTA
    estados = [s.conocimiento for s in partida.mundo]
    mover(partida, "E")
    assert puerta.recordada == CERRADA, "la entrada observó la puerta cerrada"
    aplicar(partida, UsarPergamino())
    assert puerta.recordada == ABIERTA, "FR-011: el recuerdo vuelve al anterior"
    assert [s.conocimiento for s in partida.mundo] == estados, "FR-011: las salas no cambian"


def caso_borde_varios_pergaminos():
    """FR-029: cada pergamino revierte un paso individual más."""
    controlador, _, _ = controlador_sobre(pasillo_n(6))
    partida = controlador.partida
    conocer(partida, 2, 3, 4, 5, 6)
    dar_pergaminos(partida, 3)
    controlador.procesar(Comando("ir_a", (5,)))
    while controlador.viaje is not None:
        controlador.procesar(None)
    salas = [partida.jugador.sala]
    for _ in range(3):
        controlador.procesar(Comando("pergamino"))
        salas.append(partida.jugador.sala)
    assert salas == [5, 4, 3, 2], f"FR-029: un paso por pergamino: {salas}"


def caso_fr034_todo_cambio_queda_registrado():
    """FR-034: cada cambio de conocimiento de una acción está en el Diario."""
    partida = partida_sobre(cripta_antorcha())
    encender_antorcha(partida)
    antes = huella_conocimiento(partida)
    conocidas_antes = ids_conocidas(partida)
    mover(partida, "E")
    despues = huella_conocimiento(partida)
    salas_cambiadas = {a[0] for a, b in zip(antes[0], despues[0]) if a != b}
    caras_cambiadas = {(a[0], a[1]) for a, b in zip(antes[1], despues[1]) if a != b}
    intervalo = list(partida.diario._intervalos.ver_tope())
    salas_registradas = {r[1].id for r in intervalo
                         if r[0] == m.ATRIBUTO and r[2] == "conocimiento"}
    caras_registradas = set()
    for r in intervalo:
        if r[0] == m.ATRIBUTO and r[2] == "recordada":
            for s in partida.mundo:
                for indice, salida in enumerate(s.salidas):
                    if salida is r[1]:
                        caras_registradas.add((s.id, "NSEO"[indice]))
    # La Pila del intervalo se recorre del tope al fondo: al revés del orden de los cambios.
    agregadas = [r[4].id for r in reversed(intervalo) if r[0] == m.CONOCIDA_AGREGAR]
    assert salas_registradas == salas_cambiadas, "FR-034: salas"
    assert caras_registradas == caras_cambiadas, "FR-034: caras"
    assert agregadas == ids_conocidas(partida)[len(conocidas_antes):], "FR-034: registro"


def caso_fr010_solo_lo_observado():
    """FR-010: un cierre automático con el jugador lejos no cambia el
    conocimiento, y revertirlo tampoco."""
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "E", 3, cerrada=True, llave=LLAVE, cierre=200)
    partida = partida_sobre((sala_n(1, a12), sala_n(2, b21, a23), sala_n(3, b32)))
    dar_objeto(partida, LLAVE)
    dar_pergaminos(partida, 1)
    mover(partida, "E")
    aplicar(partida, AbrirPuerta("E"))
    mover(partida, "O")
    puerta = sala(partida, 2).salida("E")
    while True:
        huella = huella_conocimiento(partida)
        aplicar(partida, Esperar())
        if puerta.cerrada:
            break
    assert huella_conocimiento(partida) == huella, "FR-010: el cierre no visto no cambia nada"
    intervalo = list(partida.diario._intervalos.ver_tope())
    assert not [r for r in intervalo if r[0] == m.CONOCIDA_AGREGAR
                or (r[0] == m.ATRIBUTO and r[2] in ("conocimiento", "recordada"))], (
        "FR-010: sin registros de conocimiento")
    aplicar(partida, UsarPergamino())
    assert huella_conocimiento(partida) == huella, "FR-010: revertirlo tampoco lo cambia"


def caso_sc003_mil_secuencias():
    """SC-003 (FR-011): 1000 secuencias de 1 a 5 acciones aplicadas y revertidas
    con pergaminos devuelven el conocimiento inicial."""
    for numero, (descripcion, semilla, antorcha, acciones, _) in enumerate(
            secuencias_sc003(SEMILLA, SECUENCIAS)):
        partida = partida_sobre(descripcion, semilla=semilla)
        dar_objeto(partida, LLAVE)
        dar_pergaminos(partida, 5)
        if antorcha:
            encender_antorcha(partida)
        huella = huella_conocimiento(partida)
        conocidas = ids_conocidas(partida)
        azar = random.Random(semilla)
        aplicadas = sum(1 for tipo in acciones if aplicar_paso(partida, tipo, azar))
        for _ in range(aplicadas):
            aplicar(partida, UsarPergamino())
        assert huella_conocimiento(partida) == huella, f"SC-003: secuencia {numero}"
        assert ids_conocidas(partida) == conocidas, f"SC-003: registro, secuencia {numero}"
        cerrar_fuentes()


CASOS = (caso_apendice_b5_pergamino_sobre_entrada_con_antorcha,
         caso_apendice_b6_pergamino_durante_el_viaje, caso_borde_revertir_primera_entrada,
         caso_borde_revertir_entrada_a_explorada, caso_borde_varios_pergaminos,
         caso_fr034_todo_cambio_queda_registrado, caso_fr010_solo_lo_observado,
         caso_sc003_mil_secuencias)


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
    print(f"prueba_niebla_retroceso OK ({len(CASOS)} casos)")


main()
