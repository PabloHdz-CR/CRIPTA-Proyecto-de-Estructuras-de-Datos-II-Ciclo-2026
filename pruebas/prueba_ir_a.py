"""US3: viajar con «ir a» (T023 de specs/002-niebla-guerra/tasks.md).

Cubre FR-005, FR-018 a FR-025, FR-028 y FR-030: los escenarios obligatorios
1 a 3 del Apéndice B, los escenarios 4 a 9 y 11 de US3, sus casos borde y la
parte del Controlador (mensaje de detención, interrumpir, qué comandos
detienen el viaje y el None que el menú le entrega a la partida).

Las salas se dejan "ya conocidas" con apoyo_niebla.conocer() cuando el
escenario parte de un mapa conocido; eso es preparación de la prueba, no una
acción del juego.
"""
from cripta.modelo.mundo.conocimiento import ABIERTA, CERRADA
from cripta.modelo.nucleo.accion import AbrirPuerta, Esperar, Mover
from cripta.vista.comando import Comando

from pruebas.apoyo_niebla import (
    CAZADOR, CAZADOR_MANSO, LLAVE, PINCHOS, RATA, aplicar, cerrar_fuentes, con_contenido,
    conocer, controlador_sobre, dar_objeto, doble, huella_conocimiento, pasillo_n, sala_n,
    viajar)

NO_EXPLORADA = "Esa sala no está explorada."
YA_ESTAS = "Ya estás en esa sala."
SIN_RUTA = "No hay ruta conocida hasta esa sala."
LLEGADA = "Viaje detenido: llegada."
ENEMIGOS = "Viaje detenido: enemigos en la sala."
DANO = "Viaje detenido: daño recibido."
SIN_RUTA_DETENIDO = "Viaje detenido: sin ruta conocida."
FIN = "Viaje detenido: partida terminada."
INTERRUMPIDO = "Viaje detenido: interrumpido."


def movimientos(registro):
    return [a.direccion for a in registro.acciones() if isinstance(a, Mover)]


def esperar_cierre(controlador, salida, maximo=30):
    for _ in range(maximo):
        if salida.cerrada:
            return
        controlador.procesar(Comando("esperar"))
    raise AssertionError("la puerta no se cerró sola")


# ---------------------------------------------------------------------------
# Apéndice B 1
# ---------------------------------------------------------------------------

def caso_apendice_b1_destino_no_explorado():
    """Apéndice B 1 / US3 escenario 1 (FR-018): avistada, desconocida o
    inexistente → mismo rechazo, sin moverse, sin tiempo y sin líneas en el log."""
    controlador, vista, registro = controlador_sobre(pasillo_n(4))
    partida = controlador.partida
    reloj = partida.reloj
    for destino in (2, 4, 999):              # avistada, desconocida, inexistente
        controlador.procesar(Comando("ir_a", (destino,)))
        assert vista.ultimo_error == NO_EXPLORADA, (
            f"FR-018: destino {destino}: {vista.ultimo_error!r}")
        assert controlador.viaje is None, "FR-018: no hay viaje"
    assert partida.jugador.sala == 1 and partida.reloj == reloj, "FR-018: sin moverse ni tiempo"
    assert registro.lineas == [], "FR-018: sin líneas en el log"


# ---------------------------------------------------------------------------
# Apéndice B 2
# ---------------------------------------------------------------------------

def _cripta_b2(con_alternativa):
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "E", 3, cerrada=True, llave=LLAVE, cierre=400)
    s1 = [a12]
    s3 = [b32]
    salas = []
    if con_alternativa:
        a14, b41 = doble(1, "S", 4)
        a45, b54 = doble(4, "E", 5)
        a53, b35 = doble(5, "N", 3)
        s1.append(a14)
        s3.append(b35)
        salas += [sala_n(4, b41, a45), sala_n(5, b54, a53)]
    return tuple([sala_n(1, *s1), sala_n(2, b21, a23), sala_n(3, *s3)] + salas)


def _preparar_b2(con_alternativa):
    controlador, vista, registro = controlador_sobre(_cripta_b2(con_alternativa))
    partida = controlador.partida
    dar_objeto(partida, LLAVE)
    conocer(partida, 3)
    if con_alternativa:
        conocer(partida, 4, 5)
    for comando in (Comando("mover", ("E",)), Comando("abrir", ("E",)),
                    Comando("mover", ("O",))):
        controlador.procesar(comando)
    puerta = partida.mundo.sala(2).salida("E")
    assert partida.jugador.sala == 1 and puerta.recordada == ABIERTA
    esperar_cierre(controlador, puerta)
    assert puerta.cerrada and puerta.recordada == ABIERTA, "la puerta se cerró sin verla"
    return controlador, vista, registro, puerta


def caso_apendice_b2_sin_otra_ruta():
    """Apéndice B 2 / US3 escenario 2 (FR-005, FR-021, FR-024, FR-025): al llegar
    a la 2 ve la puerta cerrada; sin otra ruta, se detiene sin gastar más tiempo."""
    controlador, vista, registro, puerta = _preparar_b2(False)
    partida = controlador.partida
    controlador.procesar(Comando("ir_a", (3,)))
    assert partida.jugador.sala == 2, "primer paso a la 2"
    assert puerta.recordada == CERRADA, "FR-005: observada al llegar a la 2"
    reloj = partida.reloj
    while controlador.viaje is not None:
        controlador.procesar(None)
    assert partida.reloj == reloj, "FR-024 (d): detenerse no consume tiempo"
    assert vista.mensajes[-1] == SIN_RUTA_DETENIDO, vista.mensajes[-1]


def caso_apendice_b2_con_otra_ruta():
    """Apéndice B 2 / US3 escenario 2 (FR-021, FR-024): con otra ruta conocida,
    el viaje sigue por ella y llega."""
    controlador, vista, registro, puerta = _preparar_b2(True)
    mensajes = viajar(controlador, 3)
    assert mensajes == [LLEGADA], mensajes
    assert controlador.partida.jugador.sala == 3
    assert movimientos(registro)[-5:] == ["E", "O", "S", "E", "N"], movimientos(registro)


# ---------------------------------------------------------------------------
# Apéndice B 3
# ---------------------------------------------------------------------------

def caso_apendice_b3_enemigos_dormidos():
    """Apéndice B 3 / US3 escenario 3 (FR-024, FR-025): entrar a una sala con
    enemigos dormidos los activa (P1 §2.4) y detiene el viaje."""
    descripcion = con_contenido(pasillo_n(4), 3, enemigos=(("r1", RATA),))
    controlador, vista, _ = controlador_sobre(descripcion)
    partida = controlador.partida
    conocer(partida, 2, 3, 4)
    assert viajar(controlador, 4) == [ENEMIGOS]
    sala3 = partida.mundo.sala(3)
    assert partida.jugador.sala == 3, "se detuvo en la 3"
    assert len(sala3.activos) == 1 and sala3.dormidos.esta_vacia(), "P1 §2.4: activados"


def caso_entrar_con_enemigos_activos():
    """FR-024 (b): entrar a una sala con enemigos activos también detiene."""
    descripcion = con_contenido(pasillo_n(4), 2, enemigos=(("r1", RATA),))
    controlador, _, _ = controlador_sobre(descripcion)
    partida = controlador.partida
    conocer(partida, 2, 3, 4)
    partida.mutador.pausar()
    partida._asegurar_contenido(2)
    partida.mundo.sala(2).activar_enemigos(partida)
    partida.mutador.reanudar()
    assert viajar(controlador, 4) == [ENEMIGOS]
    assert partida.jugador.sala == 2


# ---------------------------------------------------------------------------
# Escenarios 4 y 11, 5, 6 y 7
# ---------------------------------------------------------------------------

def _cripta_empate():
    a1e, b9 = doble(1, "E", 9, costo=50)
    a1n, b10 = doble(1, "N", 10, costo=50)
    a9, c20 = doble(9, "N", 20, costo=50)
    a10, d20 = doble(10, "E", 20, costo=50)
    return (sala_n(1, a1e, a1n), sala_n(9, b9, a9), sala_n(10, b10, a10),
            sala_n(20, c20, d20))


def caso_us3_e4_y_e11_empate_por_menor_id():
    """US3 escenarios 4 y 11 (FR-020, FR-030), mismo armado: primeros pasos
    posibles hacia 9 (E) y 10 (N), igual costo: va a la 9 (como número) y la
    elección se repite."""
    elecciones = []
    for _ in range(2):
        controlador, _, registro = controlador_sobre(_cripta_empate())
        conocer(controlador.partida, 9, 10, 20)
        assert viajar(controlador, 20) == [LLEGADA]
        elecciones.append(movimientos(registro))
        cerrar_fuentes()
    assert elecciones[0][0] == "E", f"FR-020: primer paso a la 9: {elecciones[0]}"
    assert elecciones[0] == elecciones[1], "FR-030: la misma elección en cada ejecución"


def caso_us3_e5_sin_costo_vale_100():
    """US3 escenario 5 (FR-019): 1→3 sin costo (100) frente a 1→2→3 de 30 + 30."""
    a13, b31 = doble(1, "E", 3)
    a12, b21 = doble(1, "S", 2, costo=30)
    a23, b32 = doble(2, "E", 3, costo=30)
    descripcion = (sala_n(1, a13, a12), sala_n(2, b21, a23), sala_n(3, b31, b32))
    controlador, _, registro = controlador_sobre(descripcion)
    conocer(controlador.partida, 2, 3)
    assert viajar(controlador, 3) == [LLEGADA]
    assert movimientos(registro) == ["S", "E"], f"FR-019: {movimientos(registro)}"


def caso_us3_e6_no_abre_puertas():
    """US3 escenario 6 (FR-018, FR-022): la única ruta tiene una puerta recordada
    cerrada y el jugador tiene la llave: rechazo, sin abrir y sin tiempo."""
    a12, b21 = doble(1, "E", 2, cerrada=True, llave=LLAVE)
    descripcion = (sala_n(1, a12), sala_n(2, b21))
    controlador, vista, registro = controlador_sobre(descripcion)
    partida = controlador.partida
    dar_objeto(partida, LLAVE)
    conocer(partida, 2)
    reloj = partida.reloj
    controlador.procesar(Comando("ir_a", (2,)))
    assert vista.ultimo_error == SIN_RUTA, vista.ultimo_error
    assert partida.mundo.sala(1).salida("E").cerrada, "FR-022: no abrió la puerta"
    assert partida.reloj == reloj and registro.lineas == []


def caso_us3_e7_igual_que_a_mano():
    """US3 escenario 7 (FR-023): mismo tiempo, mismas acciones y mismo
    conocimiento que los mismos movimientos hechos a mano."""
    descripcion = con_contenido(pasillo_n(5), 5, enemigos=(("m1", CAZADOR_MANSO),))
    viaje, _, registro = controlador_sobre(descripcion, semilla=7)
    conocer(viaje.partida, 2, 3, 4)
    viajar(viaje, 4)
    a_mano, _, _ = controlador_sobre(descripcion, semilla=7)
    conocer(a_mano.partida, 2, 3, 4)
    for direccion in movimientos(registro):
        a_mano.procesar(Comando("mover", (direccion,)))
    p1, p2 = viaje.partida, a_mano.partida
    assert (p1.reloj, p1.jugador.acciones, p1.jugador.sala) == (
        p2.reloj, p2.jugador.acciones, p2.jugador.sala), "FR-023: igual que a mano"
    assert huella_conocimiento(p1) == huella_conocimiento(p2), "FR-023: mismo conocimiento"


# ---------------------------------------------------------------------------
# Escenarios 8 y 9
# ---------------------------------------------------------------------------

def caso_us3_e8_trampa():
    """US3 escenario 8 (FR-024, FR-025): una trampa en el camino detiene por daño."""
    descripcion = con_contenido(pasillo_n(4), 2, trampas=(("t1", PINCHOS),))
    controlador, _, _ = controlador_sobre(descripcion)
    conocer(controlador.partida, 2, 3, 4)
    assert viajar(controlador, 4) == [DANO]
    assert controlador.partida.jugador.sala == 2


def caso_us3_e8_veneno():
    """US3 escenario 8 (FR-024; clarificación 2): el veneno también detiene."""
    controlador, _, registro = controlador_sobre(pasillo_n(8))
    partida = controlador.partida
    conocer(partida, *range(2, 9))
    partida.mutador.pausar()                 # preparación, no una acción
    partida.envenenar(partida.jugador)
    partida.mutador.reanudar()
    assert viajar(controlador, 8) == [DANO]
    assert partida.jugador.sala < 8, "FR-024: se detuvo antes de llegar"


def caso_us3_e8_ataque():
    """US3 escenario 8 (FR-024): un cazador que alcanza al jugador y lo ataca detiene."""
    descripcion = con_contenido(pasillo_n(8), 1, enemigos=(("c1", CAZADOR),))
    controlador, _, _ = controlador_sobre(descripcion)
    partida = controlador.partida
    conocer(partida, *range(2, 9))
    assert viajar(controlador, 8) == [DANO]
    assert partida.jugador.sala < 8


def caso_us3_e9_llegada():
    """US3 escenario 9 (FR-024, FR-025): llegada, con el comentario y un MOVER por paso."""
    controlador, _, registro = controlador_sobre(pasillo_n(4))
    conocer(controlador.partida, 2, 3, 4)
    assert viajar(controlador, 4) == [LLEGADA]
    assert registro.comentarios() == ["IR_A 4"], "FR-026: comentario de la orden"
    assert movimientos(registro) == ["E", "E", "E"], "FR-026: un MOVER por paso"


# ---------------------------------------------------------------------------
# Casos borde
# ---------------------------------------------------------------------------

def caso_borde_sala_actual():
    """FR-018: «ir a» a la sala actual se rechaza sin tiempo."""
    controlador, vista, registro = controlador_sobre(pasillo_n(3))
    controlador.procesar(Comando("ir_a", (1,)))
    assert vista.ultimo_error == YA_ESTAS and registro.lineas == []


def caso_borde_errante_sin_dano():
    """FR-024 (clarificación 3): un enemigo que llega a la sala sin hacer daño
    no detiene el viaje."""
    descripcion = con_contenido(pasillo_n(8), 1, enemigos=(("m1", CAZADOR_MANSO),))
    controlador, _, _ = controlador_sobre(descripcion)
    conocer(controlador.partida, *range(2, 9))
    assert viajar(controlador, 8) == [LLEGADA]


def caso_borde_victoria():
    """FR-024 (e): entrar a la sala de salida termina la partida y el viaje."""
    controlador, _, _ = controlador_sobre(pasillo_n(4), sala_salida=3)
    conocer(controlador.partida, 2, 3, 4)
    assert viajar(controlador, 4) == [FIN]
    assert controlador.partida.fin == "victoria"


def caso_borde_muerte():
    """FR-024 (e): morir en el viaje lo termina con la partida."""
    descripcion = con_contenido(pasillo_n(4), 2, trampas=(("t1", PINCHOS),))
    controlador, _, _ = controlador_sobre(descripcion, vida_jugador=3)
    conocer(controlador.partida, 2, 3, 4)
    assert viajar(controlador, 4) == [FIN]
    assert controlador.partida.fin == "derrota"


def caso_borde_desde_sala_con_enemigos():
    """Supuesto "Enemigos y viaje": se puede ordenar «ir a» desde una sala con enemigos."""
    descripcion = con_contenido(pasillo_n(3), 1, enemigos=(("r1", RATA),))
    controlador, _, _ = controlador_sobre(descripcion, vida_jugador=1000)
    conocer(controlador.partida, 2, 3)
    mensajes = viajar(controlador, 3)
    assert mensajes in ([LLEGADA], [DANO]), mensajes
    assert controlador.partida.jugador.sala != 1, "la orden se aceptó y dio al menos un paso"


# ---------------------------------------------------------------------------
# Controlador (escritas antes de T031)
# ---------------------------------------------------------------------------

def caso_controlador_mensaje_y_viaje_visible():
    """FR-025: el viaje en curso se ve y al terminar el mensaje dice el motivo."""
    controlador, vista, _ = controlador_sobre(pasillo_n(4))
    conocer(controlador.partida, 2, 3, 4)
    controlador.procesar(Comando("ir_a", (4,)))
    assert vista.ultimo_estado.viaje is not None, "FR-025: viaje visible"
    assert vista.ultimo_estado.viaje.destino_id == 4
    while controlador.viaje is not None:
        controlador.procesar(None)
    assert vista.mensajes[-1] == LLEGADA and vista.ultimo_estado.viaje is None


def caso_controlador_interrumpir():
    """FR-028: interrumpir detiene el viaje."""
    controlador, vista, registro = controlador_sobre(pasillo_n(5))
    conocer(controlador.partida, 2, 3, 4, 5)
    controlador.procesar(Comando("ir_a", (5,)))
    controlador.procesar(Comando("interrumpir"))
    assert controlador.viaje is None and vista.mensajes[-1] == INTERRUMPIDO
    pasos = len(movimientos(registro))
    controlador.procesar(None)
    assert len(movimientos(registro)) == pasos == 1, "FR-028: no se da ningún paso más"


def caso_controlador_comando_de_partida_detiene():
    """FR-028 (research R6): una acción detiene el viaje y después se procesa."""
    controlador, vista, registro = controlador_sobre(pasillo_n(5))
    conocer(controlador.partida, 2, 3, 4, 5)
    controlador.procesar(Comando("ir_a", (5,)))
    controlador.procesar(Comando("esperar"))
    assert controlador.viaje is None and INTERRUMPIDO in vista.mensajes
    assert isinstance(registro.acciones()[-1], Esperar), "la acción se procesó"


def caso_controlador_presentacion_no_detiene():
    """FR-028 (research R6): M, Tab y O no detienen el viaje."""
    controlador, _, _ = controlador_sobre(pasillo_n(5))
    conocer(controlador.partida, 2, 3, 4, 5)
    controlador.procesar(Comando("ir_a", (5,)))
    for comando in (Comando("alternar_mapa"), Comando("alternar_mapa"),
                    Comando("inventario_siguiente"), Comando("ordenar_inventario", ("peso",))):
        controlador.procesar(comando)
        assert controlador.viaje is not None, f"FR-028: {comando.verbo} detuvo el viaje"
    while controlador.viaje is not None:
        controlador.procesar(None)
    assert controlador.partida.jugador.sala == 5


def caso_controlador_menu_entrega_none():
    """FR-023: el menú le pasa los None a la partida con un viaje en curso."""
    from cripta.controlador.controladorMenu import ControladorMenu
    controlador, vista, _ = controlador_sobre(pasillo_n(4))
    conocer(controlador.partida, 2, 3, 4)
    menu = ControladorMenu.__new__(ControladorMenu)
    menu._replay = None
    menu._juego = controlador
    menu._pendiente = None
    controlador.procesar(Comando("ir_a", (4,)))
    salas = [controlador.partida.jugador.sala]
    for _ in range(5):
        menu.procesar(None)
        salas.append(controlador.partida.jugador.sala)
    assert salas[:4] == [2, 3, 4, 4], f"FR-023: un paso por vuelta: {salas}"


CASOS = (caso_apendice_b1_destino_no_explorado, caso_apendice_b2_sin_otra_ruta,
         caso_apendice_b2_con_otra_ruta, caso_apendice_b3_enemigos_dormidos,
         caso_entrar_con_enemigos_activos, caso_us3_e4_y_e11_empate_por_menor_id,
         caso_us3_e5_sin_costo_vale_100, caso_us3_e6_no_abre_puertas,
         caso_us3_e7_igual_que_a_mano, caso_us3_e8_trampa, caso_us3_e8_veneno,
         caso_us3_e8_ataque, caso_us3_e9_llegada, caso_borde_sala_actual,
         caso_borde_errante_sin_dano, caso_borde_victoria, caso_borde_muerte,
         caso_borde_desde_sala_con_enemigos, caso_controlador_mensaje_y_viaje_visible,
         caso_controlador_interrumpir, caso_controlador_comando_de_partida_detiene,
         caso_controlador_presentacion_no_detiene, caso_controlador_menu_entrega_none)


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
    print(f"prueba_ir_a OK ({len(CASOS)} casos)")


main()
