"""Reglas de la verificación de resolubilidad (003-resolubilidad, T011).

FR-001 a FR-010, FR-016, FR-017, FR-030. Escenarios H1.E2, H1.E3, H1.E4,
H1.E5, H1.E9, H1.E10, H1.E12 y casos borde (marcados "# borde:").

Verifica descripciones en memoria (apoyo_resolubilidad): sin vista, red ni
partida.

Uso: py -m pruebas.prueba_resolubilidad_reglas
"""
from cripta.modelo.puertos.errores import DatosInvalidos
from cripta.modelo.resolubilidad.resultadoResolubilidad import (
    NO_RESOLUBLE, RESOLUBLE, SIN_PUERTA_DE_SALIDA)

from pruebas.apoyo_resolubilidad import (
    Cripta, FuenteLlaves, a_tuplas, abierta, cerrada, verificar)

S = "itm_res_salida"
A, B = "itm_res_a", "itm_res_b"


def orden(resultado):
    return [(l.id, l.ubicacion.sala, l.ubicacion.enemigo) for l in resultado.orden]


def cadena():
    """A abre la zona de B, B la de llave_salida, y su puerta da a la salida."""
    return Cripta([
        (1, [cerrada("E", 2, A)]),
        (2, [abierta("O", 1), cerrada("E", 3, B)]),
        (3, [abierta("O", 2), cerrada("E", 4, S)]),
        (4, [abierta("O", 3)]),
    ], sala_salida=4, llave_salida=S, ubicaciones=[(A, 1), (B, 2), (S, 3)])


def prueba_h1_e4_cadena():
    # H1.E4 (FR-007, FR-008): cadena A, B, llave_salida.
    resultado = verificar(cadena())
    assert resultado.veredicto == RESOLUBLE, resultado
    assert orden(resultado) == [(A, 1, None), (B, 2, None), (S, 3, None)], orden(resultado)


def prueba_h1_e2_errante():
    # H1.E2 (FR-004, FR-017; Apéndice B): la llave que suelta un errante se
    # obtiene en la sala donde ese enemigo inicia.
    cripta = Cripta([
        (1, [abierta("E", 2)]),
        (2, [abierta("O", 1), cerrada("E", 3, S)]),
        (3, [abierta("O", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2, "e-201")])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    assert orden(resultado) == [(S, 2, "e-201")]


def prueba_h1_e3_determinista_y_menor():
    # H1.E3 (FR-009, FR-010; Apéndice B): varios órdenes válidos; siempre el
    # mismo, y en cada posición la llave disponible de menor id.
    azul, bronce, salida = "itm_llave_azul", "itm_llave_bronce", "itm_llave_salida"
    cripta = Cripta([
        (1, [cerrada("E", 2, azul)]),
        (2, [abierta("O", 1), cerrada("E", 3, salida)]),
        (3, [abierta("O", 2)]),
    ], sala_salida=3, llave_salida=salida,
        ubicaciones=[(bronce, 1), (azul, 1), (salida, 2)])
    primero = verificar(cripta)
    assert primero.veredicto == RESOLUBLE
    assert [l.id for l in primero.orden] == [azul, bronce, salida]
    assert a_tuplas(verificar(cripta)) == a_tuplas(primero)
    # FR-010: el orden de llegada de salas, salidas y entradas no importa.
    for semilla in range(10):
        assert a_tuplas(verificar(cripta, semilla_desorden=semilla)) == a_tuplas(primero), semilla


def prueba_h1_e5_llave_que_no_hace_falta():
    # H1.E5 (FR-007, FR-008, FR-016): una llave que no hace falta para ganar
    # también va en el orden, una sola vez, aunque tenga dos ubicaciones.
    base = cadena()
    extra = "itm_res_z"
    cripta = Cripta(base.salas, base.sala_salida, base.llave_salida,
                    base.ubicaciones + [(extra, 2), (extra, 1)])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    ids = [l.id for l in resultado.orden]
    assert ids.count(extra) == 1, ids
    # z está disponible desde el principio (sala 1), pero en cada paso hay
    # otra de id menor: primero A, después B y después llave_salida.
    assert ids == [A, B, S, extra], ids


def prueba_borde_llave_salida_no_va_al_final():
    # borde: FR-008, llave_salida no se fuerza a la última posición. Es
    # alcanzable desde el comienzo y abre la zona de otra llave de id menor.
    otra = "itm_aaa"
    cripta = Cripta([
        (1, [cerrada("N", 2, S), cerrada("E", 3, S)]),
        (2, [abierta("S", 1)]),
        (3, [abierta("O", 1)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 1), (otra, 2)])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    assert [l.id for l in resultado.orden] == [S, otra]


def prueba_h1_e9_cierre_automatico():
    # H1.E9 (FR-005): una puerta con cierre automático en el único camino no
    # bloquea si su llave se obtiene antes.
    cripta = Cripta([
        (1, [cerrada("E", 2, A, cierre_automatico=300)]),
        (2, [abierta("O", 1), cerrada("E", 3, S, cierre_automatico=300)]),
        (3, [abierta("O", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(A, 1), (S, 2)])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    assert [l.id for l in resultado.orden] == [A, S]


def prueba_h1_e10_caras_distintas():
    # H1.E10 (FR-006): cada cara se evalúa en el sentido en que se recorre:
    # de 1 a 2 está abierta; de 2 a 1, cerrada con una llave que no existe.
    vuelta = "itm_res_vuelta"
    ida = Cripta([
        (1, [abierta("E", 2)]),
        (2, [cerrada("O", 1, vuelta), cerrada("N", 3, S)]),
        (3, [abierta("S", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2)])
    assert verificar(ida).veredicto == RESOLUBLE
    # La misma puerta desde el otro lado: empezando en 2 no se llega a 1.
    vuelta_cripta = Cripta([
        (1, [abierta("E", 2)]),
        (2, [cerrada("O", 1, vuelta), cerrada("N", 3, S)]),
        (3, [abierta("S", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 1)], sala_inicial=2)
    resultado = verificar(vuelta_cripta)
    assert resultado.veredicto == NO_RESOLUBLE
    # Frontera en orden canónico: sala de origen y luego N, S, E, O.
    assert a_tuplas(resultado)[5] == ((2, "N", 3, S), (2, "O", 1, vuelta)), a_tuplas(resultado)


def prueba_h1_e12_dos_caminos():
    # H1.E12 (FR-001): sala_salida se alcanza por un camino abierto (que se
    # recorre primero) y por una salida que requiere llave_salida: resoluble.
    cripta = Cripta([
        (1, [abierta("N", 2), abierta("E", 3)]),
        (2, [abierta("S", 1)]),
        (3, [abierta("O", 1), cerrada("N", 2, S)]),
    ], sala_salida=2, llave_salida=S, ubicaciones=[(S, 1)])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE, a_tuplas(resultado)
    # Sin la salida cerrada, solo el camino abierto: no resoluble (b).
    sin_puerta = Cripta([
        (1, [abierta("N", 2), abierta("E", 3)]),
        (2, [abierta("S", 1)]),
        (3, [abierta("O", 1)]),
    ], sala_salida=2, llave_salida=S, ubicaciones=[(S, 1)])
    resultado = verificar(sin_puerta)
    assert resultado.veredicto == NO_RESOLUBLE
    assert resultado.motivo == SIN_PUERTA_DE_SALIDA
    assert resultado.sala_salida_solo_sin_puerta


def prueba_borde_llave_abre_varias_puertas():
    # borde: FR-002, FR-003. Una llave abre varias puertas y no se consume.
    cripta = Cripta([
        (1, [cerrada("N", 3, A), cerrada("E", 2, A)]),
        (2, [abierta("O", 1), cerrada("E", 4, S)]),
        (3, [abierta("S", 1)]),
        (4, [abierta("O", 2)]),
    ], sala_salida=4, llave_salida=S, ubicaciones=[(A, 1), (S, 3)])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    assert [l.id for l in resultado.orden] == [A, S]


def prueba_borde_llave_en_sala_inicial():
    # borde: FR-007. Una llave en la sala inicial está disponible al empezar.
    resultado = verificar(cadena())
    primera = resultado.orden.ver_primero()
    assert (primera.id, primera.ubicacion.sala) == (A, 1)


def prueba_borde_varias_ubicaciones():
    # borde: FR-016. Con una ubicación alcanzable basta; se muestra esa.
    cripta = Cripta([
        (1, [cerrada("E", 2, S)]),
        (2, [abierta("O", 1)]),
        (9, [abierta("N", 2)]),
    ], sala_salida=2, llave_salida=S, ubicaciones=[(S, 9), (S, 1, "e-1")])
    resultado = verificar(cripta)
    assert resultado.veredicto == RESOLUBLE
    assert orden(resultado) == [(S, 1, "e-1")]


def prueba_borde_salida_abierta_con_llave():
    # borde: FR-002, R3. Una salida abierta que declara llave no la requiere:
    # no cuenta como "salida que requiere llave_salida".
    cripta = Cripta([
        (1, [("E", 2, False, S, None)]),
        (2, [abierta("O", 1)]),
    ], sala_salida=2, llave_salida=S, ubicaciones=[(S, 1)])
    resultado = verificar(cripta)
    assert resultado.veredicto == NO_RESOLUBLE
    assert resultado.motivo == SIN_PUERTA_DE_SALIDA and resultado.sala_salida_solo_sin_puerta


def prueba_borde_no_pide_contenido_ni_catalogo():
    # borde: FR-017. La verificación usa solo esqueleto, datos generales y
    # ubicaciones: con un servicio sobre una fuente que falla si se le pide
    # contenido o catálogo, verificar con lo que entrega iniciar_cripta no
    # pide nada más.
    # borde: trampas (FR-005, FR-017). Aunque el contenido de la cripta
    # tuviera trampas en el único camino, la verificación nunca lo lee: el
    # veredicto es el mismo y no se pidió contenido.
    from cripta.modelo.resolubilidad.verificadorResolubilidad import verificar_resolubilidad
    from pruebas.apoyo_terreno import cerrar_fuentes, servicio_sobre

    fuente = FuenteLlaves(cadena())
    servicio = servicio_sobre(fuente)
    try:
        datos = servicio.iniciar_cripta(fuente.datos_generales(None).id)
        salas = [entrada.sala for entrada in servicio.esqueleto()]
        resultado = verificar_resolubilidad(datos, salas, fuente.llaves(datos.id))
        assert resultado.veredicto == RESOLUBLE
        assert fuente.llamadas_contenido == 0 and fuente.llamadas_catalogo == 0
    finally:
        cerrar_fuentes()


def prueba_borde_datos_invalidos_en_el_grafo():
    # borde: FR-030. Una ubicación en una sala que no existe, o una salida
    # hacia una sala que no existe, es un error de datos que nombra la entrada.
    con_ubicacion_mala = Cripta([(1, [abierta("E", 2)]), (2, [])], sala_salida=2,
                                llave_salida=S, ubicaciones=[(S, 1), (A, 77)])
    try:
        verificar(con_ubicacion_mala)
    except DatosInvalidos as error:
        assert "77" in str(error) and A in str(error), str(error)
    else:
        raise AssertionError("una ubicación en una sala inexistente debía fallar")

    con_destino_malo = Cripta([(1, [abierta("E", 88)])], sala_salida=1,
                              llave_salida=S, ubicaciones=[(S, 1)])
    try:
        verificar(con_destino_malo)
    except DatosInvalidos as error:
        assert "88" in str(error) and "1" in str(error), str(error)
    else:
        raise AssertionError("una salida hacia una sala inexistente debía fallar")


def main():
    pruebas = [valor for nombre, valor in sorted(globals().items())
               if nombre.startswith("prueba_") and callable(valor)]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print(f"prueba_resolubilidad_reglas: {len(pruebas)} casos OK")


if __name__ == "__main__":
    main()
