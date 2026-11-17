"""T013 y T014 (004-linea-tiempo, US1): consultar el estado de un instante
pasado con «historia <t>» e «historia #k».

La referencia es el oráculo en vivo (spec corregida en 67c1a83): la huella
que la partida real tuvo en cada decisión y en cada instante de evento.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_linea_consulta
"""
import random

from cripta.modelo.nucleo.accion import Esperar, Mover, UsarPergamino
from cripta.vista.comando import Comando
from pruebas.apoyo_linea import (
    OraculoVivo, cripta_linea, estado_de, huella, huella_partida, partida_con_linea,
    secuencia_al_azar, viaje_al_azar)
from pruebas.apoyo_niebla import (
    ERRANTE, PERGAMINO, cerrar_fuentes, con_contenido, controlador_sobre, dar_objeto,
    pasillo_n)


def instante(partida, t):
    """La copia reconstruida del instante t (la línea de la partida real)."""
    return partida.linea.reconstruir_instante(t, partida)


def accion(partida, k):
    return partida.linea.reconstruir_accion(k, partida)


def partida_jugada(semilla=1, n=120, k=10, con_viajes=True):
    partida = partida_con_linea(cripta_linea(semilla), k=k, semilla=semilla)
    oraculo = OraculoVivo(partida)
    secuencia_al_azar(oraculo, random.Random(semilla), n, con_pergaminos=False,
                      con_viajes=con_viajes)
    return partida, oraculo


def controlador_con_linea(descripcion, semilla=1, vida_jugador=10 ** 9):
    controlador, vista, registro = controlador_sobre(descripcion, semilla=semilla,
                                                     vida_jugador=vida_jugador)
    return controlador, vista, registro


def ultimo_resumen(vista):
    return vista.estados[-1].historia


# ---------------------------------------------------------------------------
# Escenarios de US1
# ---------------------------------------------------------------------------

def caso_e1_instante_futuro_rechazado():
    """US1 escenario 1 (FR-003, FR-012; Apéndice B 1): t mayor que el reloj
    actual se rechaza con el reloj en el mensaje y nada cambia."""
    controlador, vista, registro = controlador_con_linea(cripta_linea(2))
    for _ in range(6):
        controlador.procesar(Comando("esperar"))
    partida = controlador.partida
    reloj = partida.reloj
    antes = (huella_partida(partida), len(registro.lineas), len(vista.errores))
    controlador.procesar(Comando("historia", (str(reloj + 1),)))
    assert len(vista.errores) == antes[2] + 1, "FR-003: debió rechazarse"
    assert str(reloj) in vista.errores[-1], f"FR-003: el mensaje no dice el reloj: {vista.errores[-1]}"
    assert (huella_partida(partida), len(registro.lineas)) == antes[:2], "FR-012: algo cambió"


def caso_e2_mismo_instante():
    """US1 escenario 2 (FR-001, FR-004; Apéndice B 3): en cada instante de
    evento (varios errantes se mueven en el mismo instante), el estado es el
    de después de todos ellos."""
    # Partida al azar con errantes y ratas: los enemigos de una misma sala y
    # velocidad actúan en el mismo instante, y los movimientos con costos
    # distintos dejan instantes de evento que no son de decisión.
    partida, oraculo = partida_jugada(semilla=4, n=150, k=5)
    assert len(oraculo.instantes) >= 10, len(oraculo.instantes)
    for t in sorted(oraculo.instantes):
        assert huella_partida(instante(partida, t)) == oraculo.huella_instante(t), (
            f"FR-004: el instante {t} no coincide")


def caso_e3_no_modifica_la_partida():
    """US1 escenario 3 (FR-011, FR-012; Apéndice B 4): consultar no consume
    tiempo, no escribe en partida.log, no cambia el estado y el siguiente
    pergamino revierte lo mismo que sin la consulta."""
    def jugar(consultar):
        controlador, vista, registro = controlador_con_linea(cripta_linea(5), semilla=3)
        dar_objeto(controlador.partida, PERGAMINO)
        azar = random.Random(8)
        for paso in range(30):
            direcciones = [s.direccion for s in controlador.partida.mundo.sala(
                controlador.partida.jugador.sala).salidas if s is not None and s.transitable()]
            controlador.procesar(Comando("mover", (azar.choice(direcciones),)))
            if consultar and paso % 3 == 0:
                reloj = controlador.partida.reloj
                controlador.procesar(Comando("historia", (str(reloj // 2),)))
                controlador.procesar(Comando("historia", ("#2",)))
                assert controlador.partida.reloj == reloj, "FR-012: la consulta consumió tiempo"
        controlador.procesar(Comando("pergamino"))
        return huella_partida(controlador.partida), [str(a) for a in registro.acciones()]

    sin, log_sin = jugar(False)
    con, log_con = jugar(True)
    assert log_con == log_sin, "FR-012: la consulta escribió en partida.log"
    assert con == sin, "FR-011: con consultas, el pergamino revirtió otra cosa"


def caso_e4_decisiones():
    """US1 escenario 4 (FR-001): en un instante de decisión, el estado justo
    antes de decidir."""
    partida, oraculo = partida_jugada(semilla=6, n=80)
    for k in oraculo.numeros_de_accion():
        t, valor = oraculo.decisiones[k]
        if t > partida.reloj:
            continue            # la decisión pendiente es posterior al reloj (FR-003): se pide con #k
        assert huella_partida(instante(partida, t)) == oraculo.huella_instante(t), (
            f"FR-001: decisión #{k} en el instante {t}")


def caso_e5_numero_de_accion():
    """US1 escenario 5 (FR-002, FR-003): #k con 1 ≤ k ≤ n + 1, y rechazos con
    k = 0, k > n + 1 y texto."""
    partida, oraculo = partida_jugada(semilla=7, n=60)
    n = partida.jugador.acciones
    for k in range(1, n + 2):
        assert huella_partida(accion(partida, k)) == oraculo.huella_accion(k), f"FR-002: #{k}"
    assert huella_partida(accion(partida, n + 1)) == huella_partida(partida), (
        "FR-002: #(n+1) debe ser el estado actual")
    controlador, vista, _ = controlador_con_linea(cripta_linea(7))
    for _ in range(3):
        controlador.procesar(Comando("esperar"))
    for malo in ("#0", "#5", "abc", "-3", "#", "1.5", ""):
        errores = len(vista.errores)
        controlador.procesar(Comando("historia", (malo,)))
        assert len(vista.errores) == errores + 1, f"FR-003: '{malo}' debió rechazarse"
    controlador.procesar(Comando("historia", ("#4",)))
    assert ultimo_resumen(vista) is not None, "FR-002: #(n+1) es válido"


def caso_e6_pasos_de_viaje():
    """US1 escenario 6 (FR-002): cada paso de «ir a» cuenta como una acción;
    las acciones rechazadas no cuentan."""
    partida = partida_con_linea(cripta_linea(9), k=4, semilla=9)
    oraculo = OraculoVivo(partida)
    secuencia_al_azar(oraculo, random.Random(9), 20, con_pergaminos=False, con_viajes=False)
    azar = random.Random(1)
    pasos = 0
    for _ in range(10):
        pasos += viaje_al_azar(oraculo, azar)
    assert pasos > 0, "la prueba necesita algún viaje"
    sala_actual = partida.mundo.sala(partida.jugador.sala)
    sin_salida = [d for d, s in zip(("N", "S", "E", "O"), sala_actual.salidas) if s is None]
    assert sin_salida, "la prueba necesita una dirección sin salida"
    rechazada = partida.aplicar_accion(Mover(sin_salida[0]))    # sin salida: rechazada
    assert not rechazada.aceptada
    assert partida.linea.acciones == partida.jugador.acciones, (
        "FR-002: la línea cuenta cada paso y no cuenta los rechazos")
    for k in oraculo.numeros_de_accion():
        assert huella_partida(accion(partida, k)) == oraculo.huella_accion(k), f"FR-002: #{k}"


def caso_e7_resumen_completo():
    """US1 escenario 7 (FR-005, FR-006): el resumen trae reloj, sala, vida y
    estadísticas, inventario, efectos, enemigos de la sala y el mapa conocido
    de ese instante."""
    controlador, vista, _ = controlador_con_linea(cripta_linea(10), semilla=2)
    for direccion in ("E", "E", "S", "O"):
        controlador.procesar(Comando("mover", (direccion,)))
    controlador.procesar(Comando("historia", ("#3",)))
    resumen = ultimo_resumen(vista)
    assert resumen is not None and resumen.pedido == "#3" and resumen.numero_accion == 3
    estado = resumen.estado
    for campo in (estado.jugador, estado.sala, estado.inventario, estado.efectos, estado.mapa):
        assert campo is not None, "FR-005: falta un campo del resumen"
    assert estado.mapa.cantidad_exploradas >= 1, "FR-006: el mapa conocido de ese instante"
    assert estado.jugador.acciones == 2, "FR-002: antes de la acción 3 hay 2 acciones"
    lineas = list(resumen.lineas)
    assert any("Mapa conocido" in linea for linea in lineas), lineas


def caso_e8_estado_inicial():
    """US1 escenario 8 (FR-001, FR-002): «historia 0» y «#1» dan el estado inicial."""
    partida, oraculo = partida_jugada(semilla=11, n=30)
    inicial = oraculo.huella_accion(1)
    assert huella_partida(accion(partida, 1)) == inicial
    assert huella_partida(instante(partida, 0)) == oraculo.huella_instante(0) == inicial


def caso_borde_entre_decisiones():
    """Caso borde (FR-001): un instante entre dos decisiones sin eventos en
    medio tiene el estado de la decisión siguiente."""
    partida, oraculo = partida_jugada(semilla=12, n=80)
    probados = 0
    numeros = oraculo.numeros_de_accion()
    for k in numeros[:-1]:
        d1 = oraculo.decisiones[k][0]
        d2 = oraculo.decisiones[k + 1][0]
        # Sin eventos en (d1, d2]: ni capturas de evento en medio ni eventos en
        # el mismo instante d2 antes de decidir (el reloj de la decisión
        # siguiente sigue en d1; la huella empieza por el reloj).
        if d2 - d1 < 2 or any(d1 < t <= d2 for t in oraculo.instantes) or \
                oraculo.huella_accion(k + 1)[0] > d1:
            continue
        t = d1 + 1
        assert huella_partida(instante(partida, t)) == oraculo.huella_accion(k + 1), (
            f"FR-001: instante {t} entre las decisiones {d1} y {d2}")
        probados += 1
    assert probados > 5, probados


# ---------------------------------------------------------------------------
# T014: SC-002 sin pergaminos y FR-026
# ---------------------------------------------------------------------------

def caso_sc002_sin_pergaminos():
    """SC-002 (sin pergaminos) y FR-026: 300 consultas con semilla sobre una
    partida de 500 acciones con viajes, iguales al oráculo e iguales con
    K = 1, 25 y 100."""
    resultados = {}
    for k in (1, 25, 100):
        partida = partida_con_linea(cripta_linea(13, lado=6), k=k, semilla=13)
        oraculo = OraculoVivo(partida)
        secuencia_al_azar(oraculo, random.Random(13), 500, con_pergaminos=False)
        azar = random.Random(99)
        instantes = [t for t in oraculo.instantes_conocidos() if t <= partida.reloj]
        numeros = oraculo.numeros_de_accion()
        obtenidas = []
        for _ in range(150):
            t = azar.choice(instantes)
            obtenido = huella_partida(instante(partida, t))
            assert obtenido == oraculo.huella_instante(t), f"SC-002 K={k}: instante {t}"
            obtenidas.append(obtenido)
            n = azar.choice(numeros)
            obtenido = huella_partida(accion(partida, n))
            assert obtenido == oraculo.huella_accion(n), f"SC-002 K={k}: #{n}"
            obtenidas.append(obtenido)
        resultados[k] = obtenidas
    assert resultados[1] == resultados[25] == resultados[100], "FR-026: depende de K"


CASOS = (caso_e1_instante_futuro_rechazado, caso_e2_mismo_instante,
         caso_e3_no_modifica_la_partida, caso_e4_decisiones, caso_e5_numero_de_accion,
         caso_e6_pasos_de_viaje, caso_e7_resumen_completo, caso_e8_estado_inicial,
         caso_borde_entre_decisiones, caso_sc002_sin_pergaminos)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}")
    finally:
        cerrar_fuentes()
    print(f"prueba_linea_consulta OK ({len(CASOS)} casos)")
