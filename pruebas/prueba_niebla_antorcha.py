"""US4: la antorcha explora las salas vecinas (T036 de specs/002-niebla-guerra/tasks.md).

Cubre FR-004, FR-007, FR-008, FR-009 y FR-021: el escenario obligatorio 4 del
Apéndice B, los escenarios 1 a 4 de US4 y sus casos borde.

Cripta de la prueba:
              6
              │
              3   (rata dormida y trampa de pinchos)
              │N
   1 ──E── 2 ═E═ 4   (2 ═ 4: puerta cerrada en las dos caras)
              │S
              5
"""
from cripta.modelo.mundo.conocimiento import (
    ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, NO_OBSERVADA)
from cripta.vista.comando import Comando

from pruebas.apoyo_niebla import (
    ANTORCHA_CORTA, PINCHOS, RATA, cerrar_fuentes, con_contenido, conocer,
    controlador_sobre, doble, encender_antorcha, mover, partida_sobre, sala, sala_n, viajar)


def cripta():
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "N", 3)
    a24, b42 = doble(2, "E", 4, cerrada=True)
    a25, b52 = doble(2, "S", 5)
    a36, b63 = doble(3, "N", 6)
    salas = (sala_n(1, a12), sala_n(2, b21, a23, a24, a25), sala_n(3, b32, a36),
             sala_n(4, b42), sala_n(5, b52), sala_n(6, b63))
    return con_contenido(salas, 3, enemigos=(("r1", RATA),), trampas=(("t1", PINCHOS),))


def estados(partida):
    return {s.id: s.conocimiento for s in partida.mundo}


def caso_apendice_b4_explora_vecinas_sin_activar():
    """Apéndice B 4 / US4 escenario 1 (FR-008, FR-009): con la antorcha, entrar
    a la 2 explora 3, 4 y 5 (por salidas abiertas y cerradas), sin activar a la
    rata ni disparar la trampa, y sin mostrar su contenido."""
    controlador, vista, _ = controlador_sobre(cripta())
    partida = controlador.partida
    encender_antorcha(partida)
    controlador.procesar(Comando("mover", ("E",)))
    e = estados(partida)
    assert (e[2], e[3], e[4], e[5]) == (EXPLORADA,) * 4, f"FR-008: {e}"
    s3 = sala(partida, 3)
    for trampa in s3.trampas:
        assert trampa.armada, "FR-009: la trampa de la 3 no se disparó"
    assert s3.activos.esta_vacia(), "FR-009: la rata de la 3 no se activó"
    controlador.procesar(Comando("alternar_mapa"))
    texto = repr(vista.ultimo_estado)
    assert "Rata" not in texto and "Pinchos" not in texto, "FR-009: sin contenido de las vecinas"


def caso_us4_e2_destinos_de_vecinas_avistados():
    """US4 escenario 2 (FR-004, FR-008): los destinos desconocidos de las vecinas
    quedan avistados."""
    partida = partida_sobre(cripta())
    encender_antorcha(partida)
    mover(partida, "E")
    assert sala(partida, 6).conocimiento == AVISTADA, "FR-008: la 6 queda avistada"


def caso_us4_e3_sin_antorcha():
    """US4 escenario 3 (FR-004, FR-008): sin antorcha solo se explora la sala."""
    partida = partida_sobre(cripta())
    mover(partida, "E")
    e = estados(partida)
    assert e[2] == EXPLORADA and (e[3], e[4], e[5]) == (AVISTADA,) * 3, f"FR-004: {e}"
    assert e[6] == DESCONOCIDA


def caso_us4_e4_caras_no_observadas():
    """US4 escenario 4 (FR-007, FR-009, FR-021; clarificación 1): las caras de la
    3 que no tocan la sala del jugador quedan sin observar y «ir a» no las usa."""
    controlador, vista, _ = controlador_sobre(cripta())
    partida = controlador.partida
    encender_antorcha(partida)
    controlador.procesar(Comando("mover", ("E",)))
    assert sala(partida, 3).salida("S").recordada == ABIERTA, "FR-009: la cara 3->2 sí"
    assert sala(partida, 3).salida("N").recordada == NO_OBSERVADA, "FR-007: la cara 3->6 no"
    assert sala(partida, 4).salida("O").recordada == CERRADA, "la cara 4->2 se ve desde la 2"
    conocer(partida, 6)                     # la 6 explorada, pero 3->6 sigue sin observar
    controlador.procesar(Comando("ir_a", (6,)))
    assert vista.ultimo_error == "No hay ruta conocida hasta esa sala.", (
        f"FR-021: «ir a» no usa caras no observadas: {vista.ultimo_error}")


def caso_borde_encender_dentro_de_una_sala():
    """FR-008: encender la antorcha no explora nada hasta la próxima entrada."""
    partida = partida_sobre(cripta())
    mover(partida, "E")
    antes = estados(partida)
    encender_antorcha(partida)
    assert estados(partida) == antes, "FR-008: encender no explora"
    mover(partida, "S")                     # a la 5: ahora sí, sus vecinas (la 2)
    assert estados(partida)[5] == EXPLORADA


def caso_borde_se_apaga_durante_el_viaje():
    """FR-008: si la antorcha se apaga en medio de un viaje, las entradas
    siguientes exploran solo la sala."""
    salas = []
    for i in range(1, 9):
        salidas = []
        if i < 8:
            salidas.append(doble(i, "E", i + 1)[0])
        if i > 1:
            salidas.append(doble(i - 1, "E", i)[1])
        lado, vuelta = doble(i, "S", 100 + i)
        salidas.append(lado)
        salas.append(sala_n(i, *salidas))
        salas.append(sala_n(100 + i, vuelta))
    controlador, _, _ = controlador_sobre(tuple(salas))
    partida = controlador.partida
    conocer(partida, *range(2, 9))
    encender_antorcha(partida, ANTORCHA_CORTA)
    assert partida.jugador.antorcha_encendida
    assert viajar(controlador, 8) == ["Viaje detenido: llegada."]
    assert not partida.jugador.antorcha_encendida, "la antorcha corta se apagó en el viaje"
    assert sala(partida, 102).conocimiento == EXPLORADA, "FR-008: con antorcha, la vecina de 2"
    assert sala(partida, 108).conocimiento == AVISTADA, "FR-008: sin antorcha, solo la sala"


CASOS = (caso_apendice_b4_explora_vecinas_sin_activar, caso_us4_e2_destinos_de_vecinas_avistados,
         caso_us4_e3_sin_antorcha, caso_us4_e4_caras_no_observadas,
         caso_borde_encender_dentro_de_una_sala, caso_borde_se_apaga_durante_el_viaje)


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
    print(f"prueba_niebla_antorcha OK ({len(CASOS)} casos)")


main()
