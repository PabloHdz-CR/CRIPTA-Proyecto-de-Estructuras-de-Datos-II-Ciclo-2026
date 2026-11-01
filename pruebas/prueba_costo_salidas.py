"""Costo de tránsito de las salidas (001-terreno-cazador, Historia 1).

Requisitos que ejerce: FR-001 (100 por omisión), FR-002 (mismo costo en los
dos sentidos), FR-004 (el costo de moverse es el de la salida, para todos
los actores), FR-005 (intervalo max(1, costo × 100 // velocidad)), FR-006
(las demás acciones no cambian), FR-007 (errante y rastreador eligen igual),
FR-008 (cambio de velocidad con la regla existente) y FR-028 (el actor ya
está en la sala de destino durante el intervalo).

Escenarios de aceptación: H1.E1 a H1.E6 (cada caso lleva su marca).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_costo_salidas
"""
from cripta.modelo.actores.comportamientos import Errante, Rastreador
from cripta.modelo.nucleo.accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar)
from cripta.modelo.nucleo.constantes import COSTO_ABRIR, COSTO_ESPERAR
from pruebas.apoyo_terreno import (
    activar_sala, buscar_enemigo, enemigo, ficha_enemigo, partida_minima, pasillo,
    salida)


def intervalo_tras(partida, accion) -> int:
    """Aplica la acción del jugador y devuelve cuánto después de su turno
    actual quedó programado el siguiente."""
    antes = partida.jugador.evento_accion.tiempo
    resultado = partida.aplicar_accion(accion)
    assert resultado.aceptada, f"{accion} fue rechazada: {resultado}"
    return partida.jugador.evento_accion.tiempo - antes


# ---------------------------------------------------------------------------
# H1.E1 a H1.E3: el intervalo de un movimiento del jugador (FR-001, FR-004, FR-005)
# ---------------------------------------------------------------------------

def caso_h1_e1_sin_costo_declarado():
    """H1.E1 (FR-001, FR-005): salida sin costo y velocidad 100 → +100."""
    partida = partida_minima(pasillo(3))
    assert intervalo_tras(partida, Mover("E")) == 100
    assert partida.mundo.sala(1).salida("E").costo == 100


def caso_h1_e2_costo_300():
    """H1.E2 (FR-004, FR-005): costo 300 y velocidad 100 → +300."""
    partida = partida_minima(pasillo(3, costo=300))
    assert intervalo_tras(partida, Mover("E")) == 300


def caso_h1_e3_costo_1_velocidad_1000():
    """H1.E3 (FR-005): costo 1 y velocidad 1000 → intervalo 1, nunca 0."""
    partida = partida_minima(pasillo(3, costo=1), velocidad_jugador=1000)
    assert intervalo_tras(partida, Mover("E")) == 1


def caso_intervalo_con_velocidades_distintas():
    """FR-005: max(1, costo × 100 // velocidad) con varias velocidades."""
    for costo, velocidad, esperado in ((250, 100, 250), (250, 150, 166),
                                       (50, 200, 25), (1, 150, 1), (300, 30, 1000)):
        partida = partida_minima(pasillo(3, costo=costo), velocidad_jugador=velocidad)
        assert intervalo_tras(partida, Mover("E")) == esperado, (costo, velocidad)


def caso_mismo_costo_en_ambos_sentidos():
    """FR-002: una puerta cruzada en los dos sentidos cuesta lo mismo, aunque
    solo una de sus caras declare el costo."""
    descripcion = ((1, (salida("E", 2, 250),)), (2, (salida("O", 1), salida("E", 3))),
                   (3, (salida("O", 2),)))
    partida = partida_minima(descripcion)
    assert intervalo_tras(partida, Mover("E")) == 250        # 1 → 2, declarado
    assert intervalo_tras(partida, Mover("O")) == 250        # 2 → 1, de la contraparte


# ---------------------------------------------------------------------------
# H1.E4: cambio de velocidad a mitad del tránsito (FR-008)
# ---------------------------------------------------------------------------

def caso_h1_e4_cambio_de_velocidad():
    """H1.E4 (FR-008): tras cruzar una salida de costo 400 con velocidad 100, la
    velocidad pasa a 200 a mitad del intervalo → el restante se reescala con la
    regla existente, restante × 100 // 200, mínimo 1."""
    partida = partida_minima(pasillo(3, costo=400))
    inicio = partida.jugador.evento_accion.tiempo
    assert intervalo_tras(partida, Mover("E")) == 400
    # Mitad del tránsito: el reloj avanza 100 sin que ocurra nada más (no hay
    # enemigos). Se asigna directo para aislar la regla de reescalado.
    partida.reloj = inicio + 100
    partida.cambiar_velocidad(partida.jugador, 200)
    assert partida.jugador.evento_accion.tiempo == inicio + 100 + 300 * 100 // 200
    # Mínimo 1: con muy poco restante y una velocidad enorme.
    partida.reloj = partida.jugador.evento_accion.tiempo - 1
    partida.cambiar_velocidad(partida.jugador, 10 ** 6)
    assert partida.jugador.evento_accion.tiempo == partida.reloj + 1


# ---------------------------------------------------------------------------
# H1.E5: errante y rastreador eligen igual; solo cambia la duración (FR-004, FR-007)
# ---------------------------------------------------------------------------

class Grabadora:
    """Envuelve un comportamiento y anota (reloj, acción) de cada decisión."""

    def __init__(self, original):
        self.original = original
        self.decisiones = []

    def decidir(self, enemigo, partida):
        accion = self.original.decidir(enemigo, partida)
        self.decisiones.append((partida.reloj, enemigo.sala, accion))
        return accion


FICHAS_H1_E5 = (ficha_enemigo("ent_errante", "errante"),
                ficha_enemigo("ent_rastreador", "rastreador"))


SALA_DEL_JUGADOR = 5


def _malla_cuatro(costo):
    """Cuatro salas en cuadrado (1-2 arriba, 3-4 abajo), todas con el mismo
    costo, y la sala 5 aislada para el jugador: así los enemigos nunca lo
    alcanzan y solo se mueven."""
    return ((1, (salida("S", 3, costo), salida("E", 2, costo))),
            (2, (salida("S", 4, costo), salida("O", 1, costo))),
            (3, (salida("N", 1, costo), salida("E", 4, costo))),
            (4, (salida("N", 2, costo), salida("O", 3, costo))),
            (SALA_DEL_JUGADOR, ()))


def _decisiones_del_errante(costo, cantidad):
    """Las primeras 'cantidad' direcciones que elige un errante que se mueve
    solo, más la partida para revisar después su agenda."""
    partida = partida_minima(_malla_cuatro(costo), sala_inicial=SALA_DEL_JUGADOR, semilla=7,
                             enemigos=(enemigo(4, "e-1", "ent_errante"),),
                             fichas=FICHAS_H1_E5)
    activar_sala(partida, 4)
    errante = buscar_enemigo(partida, "e-1")
    grabadora = Grabadora(errante.comportamiento)
    errante.comportamiento = grabadora
    while len(grabadora.decisiones) < cantidad:
        intervalo_tras(partida, Esperar())        # el jugador espera; el errante actúa
    return partida, errante, grabadora


def caso_h1_e5_errante_elige_igual():
    """H1.E5 (FR-007, FR-004): con costos o sin ellos, el errante elige
    exactamente las mismas salidas (un solo sorteo del Random propio por
    decisión) y solo cambia cuánto tarda cada movimiento."""
    _, _, sin_costos = _decisiones_del_errante(None, 12)
    partida, errante, con_costos = _decisiones_del_errante(300, 12)
    acciones_sin = [accion for _, _, accion in sin_costos.decisiones[:12]]
    acciones_con = [accion for _, _, accion in con_costos.decisiones[:12]]
    assert acciones_sin == acciones_con, (acciones_sin, acciones_con)
    assert all(isinstance(accion, Mover) for accion in acciones_con)
    # Duración: entre dos decisiones seguidas pasan 300 (costo 300, velocidad 100).
    tiempos = [reloj for reloj, _, _ in con_costos.decisiones]
    for anterior, siguiente in zip(tiempos, tiempos[1:]):
        assert siguiente - anterior == 300, tiempos
    tiempos_sin = [reloj for reloj, _, _ in sin_costos.decisiones]
    for anterior, siguiente in zip(tiempos_sin, tiempos_sin[1:]):
        assert siguiente - anterior == 100, tiempos_sin
    assert errante.evento_accion.tiempo - tiempos[-1] == 300


def caso_h1_e5_rastreador_elige_igual():
    """H1.E5 (FR-007): con el mismo rastro, el rastreador elige la misma salida
    con costos y sin ellos; el intervalo de su movimiento es el de la salida."""
    for costo in (None, 250):
        partida = partida_minima(_malla_cuatro(costo), sala_inicial=SALA_DEL_JUGADOR,
                                 enemigos=(enemigo(4, "r-1", "ent_rastreador"),),
                                 fichas=FICHAS_H1_E5)
        activar_sala(partida, 4)
        rastreador = buscar_enemigo(partida, "r-1")
        assert isinstance(rastreador.comportamiento, Rastreador)
        partida.mundo.sala(2).rastro = 5                 # más fresco que el de la 3
        partida.mundo.sala(3).rastro = 1
        accion = rastreador.comportamiento.decidir(rastreador, partida)
        assert accion == Mover("N"), (costo, accion)      # 4 → 2, el rastro más fresco
        assert partida.costo_de(rastreador, accion) == (100 if costo is None else costo)


# ---------------------------------------------------------------------------
# H1.E6: las demás acciones cuestan lo mismo que antes (FR-006)
# ---------------------------------------------------------------------------

def caso_h1_e6_otras_acciones():
    """H1.E6 (FR-006): atacar, esperar, abrir, recoger, soltar, usar y equipar
    cuestan su COSTO_BASE de siempre, aunque las salidas tengan costo."""
    # La sala 3 es la de salida (id mayor): moverse a la 2 no termina la partida.
    descripcion = ((1, (salida("E", 2, 300),)), (2, (salida("O", 1, 300),)), (3, ()))
    partida = partida_minima(descripcion)
    jugador = partida.jugador
    for accion in (Atacar("x"), Esperar(), AbrirPuerta("E"), Recoger(1), Soltar(1),
                   Usar(1), Equipar(1)):
        assert partida.costo_de(jugador, accion) == accion.costo_base, accion
    # Mover hacia una dirección sin salida: el costo base de siempre.
    assert partida.costo_de(jugador, Mover("N")) == Mover("N").costo_base
    assert partida.costo_de(jugador, AbrirPuerta("E")) == COSTO_ABRIR
    # De punta a punta: esperar sigue costando 100 y moverse, el costo de la salida.
    assert intervalo_tras(partida, Esperar()) == COSTO_ESPERAR
    assert intervalo_tras(partida, Mover("E")) == 300


# ---------------------------------------------------------------------------
# FR-028: durante el intervalo, el actor ya está en la sala de destino
# ---------------------------------------------------------------------------

def caso_fr028_en_destino_durante_el_intervalo():
    """FR-028: al cruzar una salida de costo 500, el jugador queda en la sala de
    destino desde el inicio del movimiento. Un guardián de esa sala, que se
    activa al entrar y actúa a los 100, lo ataca ahí aunque el intervalo del
    jugador todavía no terminó."""
    fichas = (ficha_enemigo("ent_guardian", "guardian", ataque=7),)
    partida = partida_minima(pasillo(3, costo=500), enemigos=(enemigo(2, "g-1", "ent_guardian"),),
                             fichas=fichas, vida_jugador=100)
    vida_antes = partida.jugador.vida
    inicio = partida.jugador.evento_accion.tiempo
    assert intervalo_tras(partida, Mover("E")) == 500
    assert partida.jugador.sala == 2
    assert partida.reloj < inicio + 500                # el intervalo no terminó
    assert partida.jugador.vida < vida_antes, "el guardián debía atacarlo en la sala 2"


CASOS = (
    caso_h1_e1_sin_costo_declarado,
    caso_h1_e2_costo_300,
    caso_h1_e3_costo_1_velocidad_1000,
    caso_intervalo_con_velocidades_distintas,
    caso_mismo_costo_en_ambos_sentidos,
    caso_h1_e4_cambio_de_velocidad,
    caso_h1_e5_errante_elige_igual,
    caso_h1_e5_rastreador_elige_igual,
    caso_h1_e6_otras_acciones,
    caso_fr028_en_destino_durante_el_intervalo,
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
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_costo_salidas OK ({len(CASOS)} casos)")


main()
