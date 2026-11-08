"""Ejecuta todas las pruebas del proyecto, una por una, y resume el resultado.

Uso (desde la carpeta que contiene 'cripta' y 'pruebas'):
    python -m pruebas.ejecutar_pruebas

Cada prueba corre en su propio proceso, así una no contamina a las demás.
Al agregar una prueba nueva, escribe su nombre en la lista PRUEBAS.
"""
import subprocess
import sys
import time
from pathlib import Path

PRUEBAS = (
    "prueba_reglas",
    "prueba_1_3",               # DTO y convertidor de JSON
    "prueba_1_4",               # puerto FuenteDatos
    "prueba_1_5",               # ContadorSolicitudes
    # prueba_falso_1_6 no va en la lista: no es una prueba, sino el módulo que
    # define ServidorFalso (sin asserts). Lo ejercita prueba_falso_1_9.
    #"prueba_falso_1_6",
    #"prueba_real_1_6",          # ClienteHttp real: necesita red, correrla aparte
    "prueba_1_7",
    "prueba_1_8",               # FuenteAsincrona
    "prueba_falso_1_9",         # Todo junto
    "prueba_errores_red",       # D17: HTTP 500, JSON inválido, timeout, sin conexión
    #"prueba_real_1_9",          # todo junto real: necesita red, correrla aparte
    "prueba_2_2",               # Heap Minimo
    "prueba_2_3",
    "prueba_4_1",               # ListaDoble
    "prueba_4_2",               # Pila y PilaAcotada
    "prueba_4_3",               # ColaAcotada
    "prueba_4_4",               # mediciones de ListaDoble, PilaAcotada y ColaAcotada
    "prueba_4_5",
    "prueba_cursor_inventario",  # Tab / Shift+Tab: da la vuelta y sigue la vista
    "prueba_5_2",               # CacheFichas (LRU)
    "prueba_5_3",               # AlmacenLocalDisco
    "prueba_5_4",               # EsqueletoCripta y PlanificadorPrecarga
    "prueba_5_5",               # ServicioDatos
    "prueba_6_1",                # Ordenamiento
    "prueba_6_2",                # Mediciones Ordenamiento
    "prueba_6_3",
    "prueba_6_4",
    "prueba_6_5",
    "prueba_vista_1",
    "prueba_vista_2",
    "prueba_vista_3",
    "prueba_vista_4",
    "prueba_vista_5",
    "prueba_vista_6",
    "prueba_vista_7",
    "prueba_vista_8",
    "prueba_vista_9",
    "prueba_vista_10",           # teclas nuevas: nombre, replay, fin, benchmark
    "prueba_controlador",        # Controlador de punta a punta (offline)
    "prueba_replay_menu",        # replay en la ventana, nombre y benchmark (offline)
    # 001-terreno-cazador (specs/001-terreno-cazador/tasks.md, T053)
    "prueba_costo_salidas",      # FR-001, FR-002, FR-004 a FR-008, FR-028 (H1.E1 a H1.E6)
    "prueba_datos_costo",        # FR-001, FR-003, FR-009, FR-019, FR-020, FR-027 (H1.E7, H1.E8)
    "prueba_fuentes_costos",     # FR-019, FR-020, FR-021: en línea y sin conexión, igual
    "prueba_cazador",            # FR-010 a FR-016 y casos borde (H2.E1 a H2.E9)
    "prueba_cazador_equivalencia",  # FR-017, FR-018, FR-022, SC-002: 1000 situaciones vs. oráculo
    "prueba_conteo_cazador",     # FR-026, SC-004: salas examinadas (H4.E2)
    "prueba_rendimiento_cazador",  # FR-025, SC-003: ciclo < 20 ms (H4.E1)
    "prueba_persistencia_cazador",  # FR-022, FR-027, SC-005: guardar, cargar y --replay
    "prueba_vista_costos",       # FR-023, FR-024 (H3.E1, H3.E2)
    # 003-resolubilidad (specs/003-resolubilidad/tasks.md)
    "prueba_sin_datos_concretos",  # FR-036: ids y versiones de criptas ausentes de cripta/ (T005)
    "prueba_resolubilidad_reglas",   # FR-001 a FR-010, FR-016, FR-017, FR-030 (H1.E2 a E5, E9, E10, E12)
    "prueba_resolubilidad_reporte",  # FR-011 a FR-016, SC-004 (H1.E1, E6, E7, E8, E11)
    "prueba_resolubilidad_oraculo",  # 200 criptas al azar contra el oráculo (R13)
    "prueba_datos_llaves",           # FR-025 a FR-031, SC-007 (H4.E1 a H4.E6)

)

TIEMPO_MAXIMO = 120  # segundos por prueba


def main():
    raiz = Path(__file__).resolve().parent.parent
    fallidas = []
    for nombre in PRUEBAS:
        inicio = time.perf_counter()
        try:
            resultado = subprocess.run(
                [sys.executable, "-m", "pruebas." + nombre],
                cwd=raiz, capture_output=True, text=True, timeout=TIEMPO_MAXIMO)
            salio_bien = resultado.returncode == 0
            salida = resultado.stdout + resultado.stderr
        except subprocess.TimeoutExpired:
            salio_bien = False
            salida = f"Se excedió el tiempo máximo de {TIEMPO_MAXIMO} s"
        duracion = time.perf_counter() - inicio
        estado = "OK   " if salio_bien else "FALLÓ"
        print(f"[{estado}] {nombre:<26} {duracion:5.1f} s")
        if not salio_bien:
            fallidas.append(nombre)
            print(salida)
    print()
    if fallidas:
        print("Fallaron:", ", ".join(fallidas))
        sys.exit(1)
    print(f"Todas las pruebas pasaron ({len(PRUEBAS)}).")


main()