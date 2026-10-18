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
    #"prueba_reglas",
    #"prueba_1_3",               # DTO y convertidor de JSON
    #"prueba_1_4",               # puerto FuenteDatos
    #"prueba_1_5",               # ContadorSolicitudes
    #"prueba_falso_1_6",         # ClienteHttp contra un servidor simulado
    #"prueba_real_1_6",          # ClienteHttp real: necesita red, correrla aparte
    #"prueba_1_7",
    #"prueba_1_8",               # FuenteAsincrona
    #"prueba_falso_1_9",         # Todo junto
    #"prueba_real_1_9",          # todo junto real: necesita red, correrla aparte
    #"prueba_2_2",               # Heap Minimo
    #"prueba_2_3",
    #"prueba_4_1",               # ListaDoble
    #"prueba_4_2",               # Pila y PilaAcotada
    #"prueba_4_3",               # ColaAcotada
    #"prueba_4_4",               # mediciones de ListaDoble, PilaAcotada y ColaAcotada
    #"prueba_4_5",
    #"prueba_5_2",               # CacheFichas (LRU)
    #"prueba_5_3",               # AlmacenLocalDisco
    #"prueba_5_4",               # EsqueletoCripta y PlanificadorPrecarga
    #"prueba_5_5",               # ServicioDatos
    #"prueba_6_1",                # Ordenamiento
    #"prueba_6_2",                # Mediciones Ordenamiento
    #"prueba_6_3",
    #"prueba_6_4",
    #"prueba_6_5",
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