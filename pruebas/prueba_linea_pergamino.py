"""T018 y T019 (004-linea-tiempo, US2): la línea de tiempo respeta el
pergamino de retroceso.

Referencia: el oráculo en vivo (spec corregida en 67c1a83), que al usar un
pergamino quita lo revertido y vuelve a capturar el estado actual.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_linea_pergamino
"""
import random

from cripta.modelo.nucleo.accion import Esperar, Mover, Recoger, Soltar, UsarPergamino
from cripta.modelo.nucleo.lineaTiempo import ConsultaInvalida
from pruebas.apoyo_linea import (
    OraculoVivo, accion_al_azar, cripta_linea, huella_partida, partida_con_linea,
    secuencia_al_azar, viaje_al_azar)
from pruebas.apoyo_niebla import (
    PERGAMINO, cerrar_fuentes, con_contenido, dar_objeto, pasillo_n)


def instante(partida, t):
    return partida.linea.reconstruir_instante(t, partida)


def accion(partida, k):
    return partida.linea.reconstruir_accion(k, partida)


def comparar_todo(partida, oraculo, contexto=""):
    """Toda consulta posible (instantes ≤ reloj y números de acción) igual al
    oráculo en vivo."""
    for t in oraculo.instantes_conocidos():
        if t <= partida.reloj:
            assert huella_partida(instante(partida, t)) == oraculo.huella_instante(t), (
                f"{contexto}: instante {t}")
    for k in oraculo.numeros_de_accion():
        assert huella_partida(accion(partida, k)) == oraculo.huella_accion(k), (
            f"{contexto}: #{k}")


def cantidad_pergaminos(partida_o_copia) -> int:
    return partida_o_copia.jugador.inventario.cantidad_pergaminos()


def con_pergaminos(descripcion, cantidad, k=4, semilla=1):
    partida = partida_con_linea(descripcion, k=k, semilla=semilla)
    for _ in range(cantidad):
        dar_objeto(partida, PERGAMINO)
    return partida, OraculoVivo(partida)


def caso_e1_revertido_no_existe():
    """US2 escenario 1 (FR-007; Apéndice B 2): después del pergamino ninguna
    consulta muestra efectos de lo revertido."""
    partida, oraculo = con_pergaminos(cripta_linea(21), 3)
    secuencia_al_azar(oraculo, random.Random(21), 12, con_pergaminos=False, con_viajes=False)
    oraculo.aplicar(UsarPergamino())
    oraculo.aplicar(UsarPergamino())
    secuencia_al_azar(oraculo, random.Random(22), 18, con_pergaminos=False, con_viajes=False)
    comparar_todo(partida, oraculo, "FR-007")


def caso_e2_numeracion():
    """US2 escenario 2 (FR-002, FR-007): revertir y hacer otras acciones: la
    numeración #k sigue la historia que quedó, sin huecos."""
    partida, oraculo = con_pergaminos(pasillo_n(6), 2, k=3)
    for direccion in ("E", "E", "E"):
        oraculo.aplicar(Mover(direccion))
    oraculo.aplicar(UsarPergamino())            # revierte el tercer movimiento
    assert partida.linea.acciones == partida.jugador.acciones == 2
    oraculo.aplicar(Esperar())
    oraculo.aplicar(Esperar())
    assert partida.linea.acciones == 4
    for k in range(1, 6):
        assert huella_partida(accion(partida, k)) == oraculo.huella_accion(k), f"FR-002: #{k}"


def caso_e3_pergamino_gastado():
    """US2 escenario 3 (FR-008): el pergamino gastado figura en los instantes
    anteriores al reloj al que volvió y no desde ese instante."""
    partida, oraculo = con_pergaminos(pasillo_n(6), 2, k=3)
    for direccion in ("E", "E"):
        oraculo.aplicar(Mover(direccion))
    decision_revertida = partida.jugador.evento_accion.tiempo
    oraculo.aplicar(Mover("E"))
    oraculo.aplicar(UsarPergamino())
    assert partida.jugador.evento_accion.tiempo == decision_revertida
    oraculo.aplicar(Esperar())                    # ahora el instante R' ya pasó
    antes = accion(partida, 2)
    assert cantidad_pergaminos(antes) == 2, "FR-008: antes de R' figura el pergamino gastado"
    en_r = instante(partida, decision_revertida)
    assert cantidad_pergaminos(en_r) == 1, "FR-008: desde R' ya no figura"
    comparar_todo(partida, oraculo, "FR-008")


def caso_e4_posterior_a_r_rechazado():
    """US2 escenario 4 (FR-003, FR-007): después del pergamino, un instante
    mayor que el reloj actual (aunque antes se hubiera alcanzado) se rechaza."""
    partida, oraculo = con_pergaminos(pasillo_n(6), 1, k=3)
    for direccion in ("E", "E", "E"):
        oraculo.aplicar(Mover(direccion))
    reloj_antes = partida.reloj
    oraculo.aplicar(UsarPergamino())
    assert partida.reloj < reloj_antes
    try:
        instante(partida, reloj_antes)
        raise AssertionError("FR-003: debió rechazarse")
    except ConsultaInvalida:
        pass


def caso_e5_recogido_en_tramo_revertido():
    """US2 escenario 5 (FR-008, regla D50): un pergamino recogido en el tramo
    revertido no figura antes de R' y sí desde R'."""
    descripcion = con_contenido(pasillo_n(5), 2, objetos=[PERGAMINO])
    partida, oraculo = con_pergaminos(descripcion, 1, k=3)
    oraculo.aplicar(Mover("E"))                   # entra a la sala 2 (con un pergamino en el suelo)
    piso = partida.mundo.sala(2).suelo.ver_primero()
    decision = partida.jugador.evento_accion.tiempo
    oraculo.aplicar(Recoger(piso.id_instancia))
    oraculo.aplicar(UsarPergamino())             # revierte la recogida; D50 lo deja en el inventario
    assert partida.jugador.inventario.buscar(piso.id_instancia) is not None, "regla D50"
    oraculo.aplicar(Esperar())
    antes = accion(partida, 1)
    assert antes.jugador.inventario.buscar(piso.id_instancia) is None, (
        "FR-008: antes de R' no figura el pergamino recogido en el tramo revertido")
    desde = instante(partida, decision)
    assert desde.jugador.inventario.buscar(piso.id_instancia) is not None, (
        "FR-008: desde R' figura")
    assert desde.mundo.sala(2).buscar_objeto(piso.id_instancia) is None, "no vuelve al suelo"
    comparar_todo(partida, oraculo, "D50")


def caso_borde_soltado_y_viaje():
    """Casos borde (FR-007, FR-008): un pergamino soltado en el tramo revertido
    queda en el suelo (D50), y un pergamino que revierte un paso de «ir a»."""
    partida, oraculo = con_pergaminos(pasillo_n(6), 3, k=2)
    oraculo.aplicar(Mover("E"))
    soltado = partida.jugador.inventario.primer_pergamino()
    oraculo.aplicar(Soltar(soltado.id_instancia))
    oraculo.aplicar(UsarPergamino())             # revierte soltar: D50 lo deja en el suelo
    assert partida.mundo.sala(2).buscar_objeto(soltado.id_instancia) is not None, "regla D50"
    oraculo.aplicar(Mover("E"))
    oraculo.aplicar(Mover("E"))
    oraculo.aplicar(Mover("O"))
    pasos = viaje_al_azar(oraculo, random.Random(3))
    if pasos:
        oraculo.aplicar(UsarPergamino())         # revierte el último paso del viaje
    oraculo.aplicar(Esperar())
    comparar_todo(partida, oraculo, "borde")


def caso_sc002_con_pergaminos():
    """SC-002: 1000 consultas con semilla sobre partidas de al menos 500
    acciones con pergaminos y viajes, todas iguales al oráculo en vivo."""
    consultas = 0
    for semilla in (31, 32):
        partida, oraculo = con_pergaminos(cripta_linea(semilla, lado=6), 4, k=25, semilla=semilla)
        secuencia_al_azar(oraculo, random.Random(semilla), 500)
        assert partida.jugador.acciones >= 500
        instantes = [t for t in oraculo.instantes_conocidos() if t <= partida.reloj]
        numeros = oraculo.numeros_de_accion()
        azar = random.Random(semilla * 7)
        for _ in range(250):
            t = azar.choice(instantes)
            assert huella_partida(instante(partida, t)) == oraculo.huella_instante(t), (
                f"SC-002 semilla {semilla}: instante {t}")
            k = azar.choice(numeros)
            assert huella_partida(accion(partida, k)) == oraculo.huella_accion(k), (
                f"SC-002 semilla {semilla}: #{k}")
            consultas += 2
    assert consultas == 1000


def caso_recorte_constante():
    """FR-023: recortar la línea al usar el pergamino toca un número constante
    de entradas, con 100 y con 1000 acciones."""
    tocadas = []
    for n in (100, 1000):
        partida = partida_con_linea(pasillo_n(4), k=25, semilla=2)
        dar_objeto(partida, PERGAMINO)
        for _ in range(n):
            partida.aplicar_accion(Esperar())
        partida.aplicar_accion(UsarPergamino())
        tocadas.append(partida.linea.ultimo_recorte)
    assert tocadas[0] == tocadas[1] and tocadas[0] <= 3, f"FR-023: recorte {tocadas}"


def caso_sc004_consultas_no_cambian_nada():
    """SC-004 (FR-011): 1000 secuencias con semilla, con y sin consultas
    intercaladas: mismo reloj, mismo estado, mismas acciones (log) y el
    siguiente pergamino revierte lo mismo."""
    descripcion = cripta_linea(41, lado=4)
    for semilla in range(1000):
        azar_a, azar_b, azar_c = random.Random(semilla), random.Random(semilla), random.Random(semilla + 1)
        con = partida_con_linea(descripcion, k=3, semilla=semilla % 7 + 1)
        sin = partida_con_linea(descripcion, k=3, semilla=semilla % 7 + 1)
        dar_objeto(con, PERGAMINO)
        dar_objeto(sin, PERGAMINO)
        log_con, log_sin = [], []
        for _ in range(8):
            accion_con = accion_al_azar(con, azar_a, con_pergaminos=False)
            accion_sin = accion_al_azar(sin, azar_b, con_pergaminos=False)
            if con.aplicar_accion(accion_con).aceptada:
                log_con.append(str(accion_con))
            if sin.aplicar_accion(accion_sin).aceptada:
                log_sin.append(str(accion_sin))
            if con.reloj > 0:
                instante(con, azar_c.randint(0, con.reloj))
                accion(con, azar_c.randint(1, con.linea.acciones + 1))
        con.aplicar_accion(UsarPergamino())
        sin.aplicar_accion(UsarPergamino())
        assert log_con == log_sin, f"SC-004 semilla {semilla}: el log cambió"
        assert con.reloj == sin.reloj, f"SC-004 semilla {semilla}: el reloj cambió"
        assert huella_partida(con) == huella_partida(sin), f"SC-004 semilla {semilla}"


CASOS = (caso_e1_revertido_no_existe, caso_e2_numeracion, caso_e3_pergamino_gastado,
         caso_e4_posterior_a_r_rechazado, caso_e5_recogido_en_tramo_revertido,
         caso_borde_soltado_y_viaje, caso_sc002_con_pergaminos, caso_recorte_constante,
         caso_sc004_consultas_no_cambian_nada)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}", flush=True)
    finally:
        cerrar_fuentes()
    print(f"prueba_linea_pergamino OK ({len(CASOS)} casos)")
