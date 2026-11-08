"""Texto exacto del reporte de resolubilidad (003-resolubilidad, T012).

FR-011 a FR-016, SC-004, contracts/reporte.md. Escenarios H1.E1 (Apéndice
B), H1.E6, H1.E7, H1.E8, H1.E11 y casos borde (marcados "# borde:").

Compara el texto completo, carácter por carácter, y repite cada caso con las
entradas desordenadas (FR-010, SC-004).

Uso: py -m pruebas.prueba_resolubilidad_reporte
"""
from cripta.controlador.textoResolubilidad import lineas_reporte
from cripta.modelo.resolubilidad.resultadoResolubilidad import no_verificada

from pruebas.apoyo_resolubilidad import Cripta, abierta, cerrada, texto, verificar

S = "itm_res_salida"
X = "itm_res_x"
KA, KB = "itm_res_ka", "itm_res_kb"
ENCABEZADO_NO = "Cripta res-sintetica (versión v1): NO RESOLUBLE"
MOTIVO_A = f"Motivo: la llave de salida {S} no se puede obtener."


def comparar(cripta, esperado):
    """El texto del reporte es el esperado, también con las entradas
    desordenadas (FR-010, SC-004)."""
    obtenido = texto(verificar(cripta))
    assert obtenido == esperado, f"\n--- obtenido ---\n{obtenido}\n--- esperado ---\n{esperado}"
    for semilla in range(5):
        desordenado = texto(verificar(cripta, semilla_desorden=semilla))
        assert desordenado == esperado, f"semilla {semilla}:\n{desordenado}"


def prueba_h1_e1_ciclo_de_una_llave():
    # H1.E1 (FR-012 a FR-014; Apéndice B): llave_salida detrás de la única
    # puerta que ella abre.
    cripta = Cripta([
        (1, [cerrada("E", 2, S)]),
        (2, [abierta("O", 1), cerrada("E", 3, S)]),
        (3, [abierta("O", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (1):",
        f"  - {S}: sala 2",
        "Frontera bloqueada (1):",
        f"  - sala 1 E -> sala 2: requiere {S}",
        "Ciclos (1):",
        f"  1. {S}, encerrada por sala 1 E -> sala 2 (requiere {S}) -> {S}",
    ]))


def prueba_h1_e6_llave_sin_ubicacion():
    # H1.E6 (FR-011 a FR-013): la puerta de la frontera pide una llave que no
    # aparece en la ubicación de llaves.
    cripta = Cripta([
        (1, [cerrada("E", 2, X)]),
        (2, [abierta("O", 1), cerrada("E", 3, S)]),
        (3, []),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (2):",
        f"  - {S}: sala 2",
        f"  - {X}: sin ubicación",
        "Frontera bloqueada (1):",
        f"  - sala 1 E -> sala 2: requiere {X}",
        "Ciclos: ninguno.",
    ]))


def prueba_h1_e7_enemigo_inalcanzable():
    # H1.E7 (FR-004, FR-011, FR-013): la llave la suelta un enemigo que
    # inicia en una región inalcanzable.
    cripta = Cripta([
        (1, [cerrada("E", 2, X)]),
        (2, [abierta("O", 1), cerrada("E", 3, S)]),
        (3, []),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2, "e-7")])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (2):",
        f"  - {S}: sala 2 (suelta e-7)",
        f"  - {X}: sin ubicación",
        "Frontera bloqueada (1):",
        f"  - sala 1 E -> sala 2: requiere {X}",
        "Ciclos: ninguno.",
    ]))


def ciclo_de_dos():
    return Cripta([
        (1, [cerrada("N", 2, KB), cerrada("S", 3, KA)]),
        (2, [abierta("S", 1), cerrada("N", 4, S)]),
        (3, [abierta("N", 1)]),
        (4, [abierta("S", 2)]),
    ], sala_salida=4, llave_salida=S, ubicaciones=[(KA, 2), (S, 2), (KB, 3)])


def prueba_h1_e8_ciclo_de_dos_llaves():
    # H1.E8 (FR-014, FR-015): cada llave detrás de la puerta que abre la otra.
    # llave_salida también depende de las dos y queda en el mismo grupo; el
    # ciclo empieza en la de menor id y sigue la dependencia de menor id.
    comparar(ciclo_de_dos(), "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (3):",
        f"  - {KA}: sala 2",
        f"  - {KB}: sala 3",
        f"  - {S}: sala 2",
        "Frontera bloqueada (2):",
        f"  - sala 1 N -> sala 2: requiere {KB}",
        f"  - sala 1 S -> sala 3: requiere {KA}",
        "Ciclos (1):",
        f"  1. {KA}, encerrada por sala 1 N -> sala 2 (requiere {KB}) -> "
        f"{KB}, encerrada por sala 1 S -> sala 3 (requiere {KA}) -> {KA}",
    ]))


def prueba_h1_e11_sin_ciclo():
    # H1.E11 (FR-011, FR-012, FR-014): no resoluble por una puerta cerrada sin
    # llave; el reporte dice que no hay ciclo.
    cripta = Cripta([
        (1, [cerrada("E", 2)]),
        (2, [abierta("O", 1), cerrada("E", 3, S)]),
        (3, []),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (1):",
        f"  - {S}: sala 2",
        "Frontera bloqueada (1):",
        "  - sala 1 E -> sala 2: sin llave",
        "Ciclos: ninguno.",
    ]))


def prueba_borde_varios_grupos():
    # borde: varios ciclos de dependencia (FR-015): un ciclo por grupo, los
    # grupos por su menor id.
    kc, kd = "itm_res_kc", "itm_res_kd"
    cripta = Cripta([
        (1, [cerrada("N", 2, KB), cerrada("S", 3, KA), cerrada("E", 4, kd), cerrada("O", 5, kc)]),
        (2, [abierta("S", 1), cerrada("N", 6, S)]),
        (3, [abierta("N", 1)]),
        (4, [abierta("O", 1)]),
        (5, [abierta("E", 1)]),
        (6, []),
    ], sala_salida=6, llave_salida=S,
        ubicaciones=[(KA, 2), (KB, 3), (kc, 4), (kd, 5), (S, 2)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (5):",
        f"  - {KA}: sala 2",
        f"  - {KB}: sala 3",
        f"  - {kc}: sala 4",
        f"  - {kd}: sala 5",
        f"  - {S}: sala 2",
        "Frontera bloqueada (4):",
        f"  - sala 1 N -> sala 2: requiere {KB}",
        f"  - sala 1 S -> sala 3: requiere {KA}",
        f"  - sala 1 E -> sala 4: requiere {kd}",
        f"  - sala 1 O -> sala 5: requiere {kc}",
        "Ciclos (2):",
        f"  1. {KA}, encerrada por sala 1 N -> sala 2 (requiere {KB}) -> "
        f"{KB}, encerrada por sala 1 S -> sala 3 (requiere {KA}) -> {KA}",
        f"  2. {kc}, encerrada por sala 1 E -> sala 4 (requiere {kd}) -> "
        f"{kd}, encerrada por sala 1 O -> sala 5 (requiere {kc}) -> {kc}",
    ]))


def prueba_borde_varios_ciclos_en_un_grupo():
    # borde: el ejemplo de la spec (FR-015): k_a depende de k_b y de k_c, y
    # k_b y k_c de k_a. Se muestra solo k_a -> k_b -> k_a.
    k_a, k_b, k_c, k_s = "k_a", "k_b", "k_c", "k_salida"
    cripta = Cripta([
        (1, [cerrada("N", 2, k_b), cerrada("S", 3, k_a), cerrada("E", 2, k_c), cerrada("O", 4, k_a)]),
        (2, [abierta("S", 1)]),
        (3, [abierta("N", 1)]),
        (4, [abierta("E", 1)]),
        (5, []),
    ], sala_salida=5, llave_salida=k_s, ubicaciones=[(k_a, 2), (k_b, 3), (k_c, 4)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        f"Motivo: la llave de salida {k_s} no se puede obtener.",
        "Llaves no obtenibles (4):",
        f"  - {k_a}: sala 2",
        f"  - {k_b}: sala 3",
        f"  - {k_c}: sala 4",
        f"  - {k_s}: sin ubicación",
        "Frontera bloqueada (4):",
        f"  - sala 1 N -> sala 2: requiere {k_b}",
        f"  - sala 1 S -> sala 3: requiere {k_a}",
        f"  - sala 1 E -> sala 2: requiere {k_c}",
        f"  - sala 1 O -> sala 4: requiere {k_a}",
        "Ciclos (1):",
        f"  1. {k_a}, encerrada por sala 1 N -> sala 2 (requiere {k_b}) -> "
        f"{k_b}, encerrada por sala 1 S -> sala 3 (requiere {k_a}) -> {k_a}",
    ]))


def prueba_borde_puerta_mostrada():
    # borde: FR-015, la puerta de cada paso es la de menor sala de origen y,
    # a igual sala, la primera en N, S, E, O. Dos puertas de la sala 1 que
    # requieren KB llevan a la ubicación de KA: se muestra la N, no la E. Y
    # una puerta de la sala 3 que también requiere KA lleva a la de KB.
    cripta = Cripta([
        (1, [cerrada("E", 2, KB), cerrada("N", 2, KB), cerrada("S", 3, KA)]),
        (2, [abierta("S", 1)]),
        (3, [abierta("N", 1), cerrada("E", 4, KA)]),
        (4, [abierta("O", 3)]),
    ], sala_salida=4, llave_salida=S, ubicaciones=[(KA, 2), (KB, 3)])
    lineas = texto(verificar(cripta)).split("\n")
    ciclo = lineas[-1]
    assert ciclo == (f"  1. {KA}, encerrada por sala 1 N -> sala 2 (requiere {KB}) -> "
                     f"{KB}, encerrada por sala 1 S -> sala 3 (requiere {KA}) -> {KA}"), ciclo


def prueba_borde_destino_alcanzable_no_es_frontera():
    # borde: FR-012. Una puerta cerrada cuyo destino se alcanza por otro
    # camino no es frontera.
    cripta = Cripta([
        (1, [abierta("E", 2), cerrada("N", 2, X)]),
        (2, [abierta("O", 1)]),
        (3, []),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 2)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        f"Motivo: ninguna salida que requiere {S} da acceso a la sala de salida 3 "
        "desde la región alcanzable.",
        "Llaves no obtenibles (1):",
        f"  - {X}: sin ubicación",
        "Frontera bloqueada (0):",
        "Ciclos: ninguno.",
    ]))


def prueba_borde_ubicacion_vacia():
    # borde: la ubicación de llaves está vacía.
    cripta = Cripta([(1, [cerrada("E", 2, S)]), (2, [])], sala_salida=2,
                    llave_salida=S, ubicaciones=[])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        MOTIVO_A,
        "Llaves no obtenibles (1):",
        f"  - {S}: sin ubicación",
        "Frontera bloqueada (1):",
        f"  - sala 1 E -> sala 2: requiere {S}",
        "Ciclos: ninguno.",
    ]))


def prueba_borde_motivo_b_solo_sin_puerta():
    # borde: sala_salida solo se alcanza sin la salida que requiere
    # llave_salida (FR-001, FR-011 (b) con su línea extra). Las secciones
    # vacías se escriben con conteo 0.
    cripta = Cripta([(1, [abierta("E", 2)]), (2, [abierta("O", 1)])], sala_salida=2,
                    llave_salida=S, ubicaciones=[(S, 1)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        f"Motivo: ninguna salida que requiere {S} da acceso a la sala de salida 2 "
        "desde la región alcanzable.",
        "  La sala de salida 2 solo se alcanza por caminos sin esa salida.",
        "Llaves no obtenibles (0):",
        "Frontera bloqueada (0):",
        "Ciclos: ninguno.",
    ]))


def prueba_borde_motivo_b_sin_linea():
    # borde: llave_salida obtenible, pero ninguna salida que la requiere lleva
    # a sala_salida desde la región alcanzable, y sala_salida no se alcanza.
    cripta = Cripta([
        (1, [cerrada("E", 2, S)]),
        (2, [abierta("O", 1)]),
        (3, [abierta("O", 2)]),
    ], sala_salida=3, llave_salida=S, ubicaciones=[(S, 1)])
    comparar(cripta, "\n".join([
        ENCABEZADO_NO,
        f"Motivo: ninguna salida que requiere {S} da acceso a la sala de salida 3 "
        "desde la región alcanzable.",
        "Llaves no obtenibles (0):",
        "Frontera bloqueada (0):",
        "Ciclos: ninguno.",
    ]))


def prueba_resoluble():
    # contracts/reporte.md, RESOLUBLE: encabezado y orden con ubicaciones.
    cripta = Cripta([
        (1, [cerrada("E", 2, S)]),
        (2, [abierta("O", 1)]),
        (3, [abierta("N", 1)]),
    ], sala_salida=2, llave_salida=S, ubicaciones=[(S, 1, "e-12"), (S, 3)])
    comparar(cripta, "\n".join([
        "Cripta res-sintetica (versión v1): RESOLUBLE",
        "Orden de obtención de llaves (1):",
        f"  1. {S}: sala 1 (suelta e-12)",
    ]))


def prueba_no_verificada():
    # contracts/reporte.md, NO_VERIFICADA (FR-031).
    resultado = no_verificada("res-x", None, S, 3, "no se encontró el archivo offline")
    assert "\n".join(lineas_reporte(resultado)) == (
        "Cripta res-x: NO SE PUDO VERIFICAR\n"
        "Motivo: no se encontró el archivo offline")


def main():
    pruebas = [valor for nombre, valor in sorted(globals().items())
               if nombre.startswith("prueba_") and callable(valor)]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print(f"prueba_resolubilidad_reporte: {len(pruebas)} casos OK")


if __name__ == "__main__":
    main()
