"""El cazador (001-terreno-cazador, Historia 2).

Requisitos que ejerce: FR-010 (comparte sala con el jugador vivo: ataca y no
se mueve), FR-011 (d = costo mínimo por salidas abiertas en el sentido del
recorrido), FR-012 (sin ruta o d > rango: espera con costo 100), FR-013
(d ≤ rango: un paso por una ruta de costo d, con el costo de esa salida),
FR-014 (desempate por la vecina de menor id y, a la misma vecina, la primera
en el orden N, S, E, O), FR-015 (no depende del contenido descargado) y
FR-016 (no abre puertas). También los casos borde de spec.md con la marca
BORDE, y la regla de activación de Assumptions (primer costo 100).

Escenarios de aceptación: H2.E1 a H2.E9 (cada caso lleva su marca). Cada
decisión se compara además con el oráculo independiente (pruebas/oraculo_rutas).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_cazador
"""
from cripta.modelo.actores.comportamientos import Cazador
from cripta.modelo.nucleo.accion import Atacar, Esperar, Mover
from cripta.modelo.nucleo.constantes import COSTO_PRIMERA_ACCION_ENEMIGO, calcular_intervalo
from pruebas import oraculo_rutas
from pruebas.apoyo_terreno import (
    activar_sala, buscar_enemigo, cerrar_fuentes, duplicadas_misma_vecina, enemigo,
    ficha_enemigo, partida_minima, pasillo, ruta_corta_cara, salida)

FICHA_CAZADOR = "ent_cazador"


def situacion(descripcion, sala_cazador, sala_jugador, rango, cazadores=1, otras_fichas=(),
              otros_enemigos=()):
    """Partida con el jugador en sala_jugador y 'cazadores' cazadores activos de
    ese rango en sala_cazador. Devuelve (partida, lista de cazadores)."""
    # La sala de salida es la de id mayor: se agrega una aislada para que
    # ninguna situación termine la partida por llegar a ella.
    ultima = max(id_sala for id_sala, _ in descripcion) + 1
    descripcion = tuple(descripcion) + ((ultima, ()),)
    fichas = (ficha_enemigo(FICHA_CAZADOR, "cazador", rango=rango),) + tuple(otras_fichas)
    enemigos = tuple(enemigo(sala_cazador, f"c-{i}", FICHA_CAZADOR)
                     for i in range(1, cazadores + 1)) + tuple(otros_enemigos)
    partida = partida_minima(descripcion, sala_inicial=sala_jugador, enemigos=enemigos,
                             fichas=fichas)
    activar_sala(partida, sala_cazador)
    lista = [buscar_enemigo(partida, f"c-{i}") for i in range(1, cazadores + 1)]
    for cazador in lista:
        assert isinstance(cazador.comportamiento, Cazador), cazador.comportamiento
        assert cazador.comportamiento.rango == rango
    return partida, lista


def decision(partida, cazador):
    """(acción, costo) del cazador; antes comprueba que coincide con el oráculo."""
    accion = cazador.comportamiento.decidir(cazador, partida)
    costo = partida.costo_de(cazador, accion)
    esperada = oraculo_rutas.decidir_en_partida(partida, cazador, cazador.comportamiento.rango)
    assert (accion, costo) == esperada, f"cazador {(accion, costo)} ≠ oráculo {esperada}"
    return accion, costo


ESPERAR = (Esperar(), 100)


# ---------------------------------------------------------------------------
# Escenarios de aceptación de la Historia 2
# ---------------------------------------------------------------------------

def caso_h2_e1_comparte_sala():
    """H2.E1 (FR-010): en la misma sala que el jugador vivo, ataca y no se mueve."""
    partida, (cazador,) = situacion(pasillo(3), 2, 2, rango=1000)
    accion, costo = decision(partida, cazador)
    assert accion == Atacar(partida.jugador.id_instancia) and costo == 100
    partida.ejecutar_accion_enemigo(cazador, accion)
    assert cazador.sala == 2


def caso_h2_e2_sin_ruta():
    """H2.E2 (FR-012): sin ninguna ruta de salidas abiertas → espera, costo 100.
    Aquí la única salida hacia el jugador es de un solo sentido, al revés."""
    descripcion = ((1, ()), (2, (salida("O", 1),)))
    partida, (cazador,) = situacion(descripcion, 1, 2, rango=10 ** 6)
    assert decision(partida, cazador) == ESPERAR


def caso_h2_e3_d_mayor_que_rango():
    """H2.E3 (FR-012): rango 500 y la ruta más barata cuesta 600 → espera, 100."""
    partida, (cazador,) = situacion(pasillo(7), 1, 7, rango=500)
    assert decision(partida, cazador) == ESPERAR


def caso_h2_e4_d_igual_a_rango():
    """H2.E4 (FR-013): rango 500 y la ruta cuesta exactamente 500 → se mueve."""
    partida, (cazador,) = situacion(pasillo(6), 1, 6, rango=500)
    assert decision(partida, cazador) == (Mover("E"), 100)


def caso_h2_e5_mas_salas_pero_mas_barata():
    """H2.E5 (FR-011, FR-013): una ruta de 1 salida que cuesta 500 contra una de
    3 salidas que suma 300 → sigue la de 3, y el costo de su acción es el de
    la primera salida de esa ruta (100)."""
    partida, (cazador,) = situacion(ruta_corta_cara(), 1, 2, rango=300)
    assert decision(partida, cazador) == (Mover("N"), 100)


def caso_h2_e6_empate_menor_id():
    """H2.E6 (FR-014): v1 = 3 (por el E) y v2 = 4 (por el N) dan el mismo d →
    va a la de menor id, aunque el N se recorra primero."""
    descripcion = ((1, (salida("N", 4, 100), salida("E", 3, 100))),
                   (3, (salida("N", 5, 100),)), (4, (salida("E", 5, 100),)), (5, ()))
    partida, (cazador,) = situacion(descripcion, 1, 5, rango=1000)
    assert decision(partida, cazador) == (Mover("E"), 100)


def _dos_rutas():
    """1 → 2 → 3 cuesta 200 (por el E); 1 → 4 → 5 → 3 cuesta 300 (por el N)."""
    return ((1, (salida("N", 4, 100), salida("E", 2, 100))),
            (2, (salida("E", 3, 100), salida("O", 1, 100))),
            (3, (salida("O", 2, 100), salida("S", 5, 100))),
            (4, (salida("S", 1, 100), salida("E", 5, 100))),
            (5, (salida("O", 4, 100), salida("N", 3, 100))))


def caso_h2_e7_puerta_que_se_cierra():
    """H2.E7 (FR-017): entre dos turnos se cierra una puerta de la ruta → decide
    como desde cero: se desvía si le alcanza el rango, o espera si no."""
    for rango, despues in ((300, (Mover("N"), 100)), (250, ESPERAR)):
        partida, (cazador,) = situacion(_dos_rutas(), 1, 3, rango=rango)
        assert decision(partida, cazador) == (Mover("E"), 100)
        puerta = partida.mundo.sala(2).salida("E")
        partida.mutador.asignar(puerta, "cerrada", True)      # 2 → 3 se cierra
        assert decision(partida, cazador) == despues, rango
        partida.mutador.asignar(puerta, "cerrada", False)     # y se vuelve a abrir
        assert decision(partida, cazador) == (Mover("E"), 100)


def caso_h2_e8_salas_sin_descargar():
    """H2.E8 (FR-015): la decisión es la misma si las salas de la ruta no tienen
    el contenido descargado que si lo tienen."""
    partida, (cazador,) = situacion(pasillo(6), 1, 6, rango=500)
    sin_cargar = [sala.id for sala in partida.mundo if not sala.contenido_cargado]
    assert len(sin_cargar) >= 3, sin_cargar
    antes = decision(partida, cazador)
    for id_sala in sin_cargar:
        activar_sala(partida, id_sala)
    assert all(sala.contenido_cargado for sala in partida.mundo)
    assert decision(partida, cazador) == antes == (Mover("E"), 100)


def caso_h2_e9_no_abre_puertas():
    """H2.E9 (FR-016): la única ruta tiene una puerta cerrada → no la abre:
    espera, y la puerta sigue cerrada después de su turno."""
    descripcion = ((1, (salida("E", 2, 100, cerrada=True),)), (2, (salida("O", 1, 100),)))
    partida, (cazador,) = situacion(descripcion, 1, 2, rango=10 ** 6)
    accion, costo = decision(partida, cazador)
    assert (accion, costo) == ESPERAR
    partida.ejecutar_accion_enemigo(cazador, accion)
    assert partida.mundo.sala(1).salida("E").cerrada and cazador.sala == 1


# ---------------------------------------------------------------------------
# Más reglas (FR-011 a FR-014)
# ---------------------------------------------------------------------------

def caso_rango_cero():
    """FR-012, FR-010: con rango 0 solo ataca (misma sala) o espera."""
    partida, (cazador,) = situacion(pasillo(3), 1, 2, rango=0)
    assert decision(partida, cazador) == ESPERAR
    partida, (cazador,) = situacion(pasillo(3), 2, 2, rango=0)
    assert decision(partida, cazador)[0] == Atacar(partida.jugador.id_instancia)


def caso_misma_vecina_por_dos_salidas():
    """FR-014: dos salidas abiertas de su sala llevan a la misma vecina con el
    mismo costo → usa la primera en el orden N, S, E, O."""
    partida, (cazador,) = situacion(duplicadas_misma_vecina(), 1, 2, rango=1000)
    assert decision(partida, cazador) == (Mover("N"), 50)
    partida.mutador.asignar(partida.mundo.sala(1).salida("N"), "cerrada", True)
    assert decision(partida, cazador) == (Mover("E"), 50)      # ya solo queda la del E


def caso_costos_y_sentido_del_recorrido():
    """FR-011: solo cuentan las salidas abiertas en el sentido del recorrido.
    1 —E→ 2 está abierta pero 2 —O→ 1 cerrada: el cazador en 1 sí llega a 2,
    y el de 2 no llega a 1."""
    descripcion = ((1, (salida("E", 2, 250),)), (2, (salida("O", 1, 250, cerrada=True),)))
    partida, (cazador,) = situacion(descripcion, 1, 2, rango=250)
    assert decision(partida, cazador) == (Mover("E"), 250)
    partida, (cazador,) = situacion(descripcion, 2, 1, rango=10 ** 6)
    assert decision(partida, cazador) == ESPERAR


def caso_el_jugador_cambia_de_sala():
    """FR-011, FR-017: el mapa se calcula hacia la sala ACTUAL del jugador."""
    partida, (cazador,) = situacion(pasillo(5), 3, 5, rango=1000)
    assert decision(partida, cazador) == (Mover("E"), 100)
    partida.jugador.sala = 1
    assert decision(partida, cazador) == (Mover("O"), 100)


# ---------------------------------------------------------------------------
# Casos borde de spec.md (BORDE)
# ---------------------------------------------------------------------------

def caso_borde_jugador_muerto():
    """BORDE jugador muerto (FR-010): en la misma sala que un jugador muerto, el
    cazador no lo ataca."""
    partida, (cazador,) = situacion(pasillo(3), 2, 2, rango=1000)
    partida.jugador.vivo = False
    accion, _ = decision(partida, cazador)
    assert not isinstance(accion, Atacar), accion


def caso_borde_varios_cazadores_en_la_misma_sala():
    """BORDE varios cazadores en la misma sala con el mismo objetivo (FR-014,
    FR-018): cada uno decide por su cuenta y, si sus rangos lo permiten, todos
    toman la misma decisión; uno de rango corto espera."""
    partida, cazadores = situacion(ruta_corta_cara(), 1, 2, rango=300, cazadores=3)
    decisiones = [decision(partida, c) for c in cazadores]
    assert decisiones == [(Mover("N"), 100)] * 3, decisiones
    corto = ficha_enemigo("ent_corto", "cazador", rango=299)
    partida, cazadores = situacion(ruta_corta_cara(), 1, 2, rango=300, cazadores=2,
                                   otras_fichas=(corto,),
                                   otros_enemigos=(enemigo(1, "c-9", "ent_corto"),))
    activar_sala(partida, 1)
    otro = buscar_enemigo(partida, "c-9")
    assert [decision(partida, c) for c in cazadores] == [(Mover("N"), 100)] * 2
    assert decision(partida, otro) == ESPERAR


def caso_borde_primer_costo_al_aparecer():
    """BORDE primera acción al aparecer (Assumptions: regla de activación): el
    cazador está dormido hasta que el jugador entra a su sala, y su primera
    acción se programa con costo base 100, igual que la de un errante."""
    otras = (ficha_enemigo("ent_errante", "errante", velocidad=150),)
    descripcion = pasillo(3)
    ultima = 4
    partida = partida_minima(descripcion + ((ultima, ()),), sala_inicial=1,
                             enemigos=(enemigo(2, "c-1", FICHA_CAZADOR),
                                       enemigo(2, "e-1", "ent_errante")),
                             fichas=(ficha_enemigo(FICHA_CAZADOR, "cazador", velocidad=150,
                                                   rango=500),) + otras)
    activar_sala(partida, 2)
    cazador = buscar_enemigo(partida, "c-1")
    errante = buscar_enemigo(partida, "e-1")
    esperado = calcular_intervalo(COSTO_PRIMERA_ACCION_ENEMIGO, 150)
    assert COSTO_PRIMERA_ACCION_ENEMIGO == 100
    assert cazador.evento_accion.tiempo - partida.reloj == esperado
    assert errante.evento_accion.tiempo - partida.reloj == esperado


def caso_borde_dormido_no_actua():
    """BORDE regla de activación (Assumptions): un cazador cuya sala el jugador
    no visitó está dormido y no tiene turno en la agenda."""
    partida = partida_minima(pasillo(3) + ((4, ()),), sala_inicial=1,
                             enemigos=(enemigo(3, "c-1", FICHA_CAZADOR),),
                             fichas=(ficha_enemigo(FICHA_CAZADOR, "cazador", rango=1000),))
    for _ in range(5):
        partida.aplicar_accion(Esperar())
    assert partida.jugador.sala == 1
    assert not partida.mundo.sala(3).contenido_cargado, "nadie entró a la sala 3"
    assert all(sala.activos.esta_vacia() for sala in partida.mundo), "no hay enemigos activos"


def caso_turno_completo_por_la_agenda():
    """FR-013, FR-004: por la agenda, el cazador avanza un paso por la salida que
    eligió y su siguiente turno queda a costo × 100 // velocidad."""
    descripcion = ((1, (salida("E", 2, 250),)), (2, (salida("O", 1, 250), salida("E", 3, 250))),
                   (3, (salida("O", 2, 250),)))
    partida, (cazador,) = situacion(descripcion, 3, 1, rango=1000)
    turno = cazador.evento_accion.tiempo
    while cazador.sala == 3:
        partida.aplicar_accion(Esperar())
    assert cazador.sala == 2
    assert cazador.evento_accion.tiempo - turno == 250


CASOS = (
    caso_h2_e1_comparte_sala,
    caso_h2_e2_sin_ruta,
    caso_h2_e3_d_mayor_que_rango,
    caso_h2_e4_d_igual_a_rango,
    caso_h2_e5_mas_salas_pero_mas_barata,
    caso_h2_e6_empate_menor_id,
    caso_h2_e7_puerta_que_se_cierra,
    caso_h2_e8_salas_sin_descargar,
    caso_h2_e9_no_abre_puertas,
    caso_rango_cero,
    caso_misma_vecina_por_dos_salidas,
    caso_costos_y_sentido_del_recorrido,
    caso_el_jugador_cambia_de_sala,
    caso_borde_jugador_muerto,
    caso_borde_varios_cazadores_en_la_misma_sala,
    caso_borde_primer_costo_al_aparecer,
    caso_borde_dormido_no_actua,
    caso_turno_completo_por_la_agenda,
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
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_cazador OK ({len(CASOS)} casos)")


main()
