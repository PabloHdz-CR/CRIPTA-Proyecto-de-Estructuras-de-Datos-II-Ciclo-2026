"""Comprueba que cada archivo esté en su versión más reciente y que existan
todas las pruebas.

Uso (desde la carpeta que contiene 'cripta' y 'pruebas'):
    python -m pruebas.verificar_versiones

Para cada archivo busca textos que SOLO tiene la versión nueva (y textos que
SOLO tenía la vieja). Si no ve lo esperado, te dice cuál archivo reemplazar.
"""
from pathlib import Path

# (archivo, textos que DEBE contener, textos que NO debe contener)
REVISIONES = (
    ("cripta/modelo/estructuras/listaEnlazada.py",
     ("def establecer", "def eliminar_en", "def eliminar_ultimo"),
     ("textos = []",)),
    ("cripta/controlador/bench/alternativasAgenda.py",
     ("class MonticuloSobreLista", "class AgendaListaOrdenada"),
     ("MonticuloArreglo", "Binaria")),
    ("cripta/controlador/bench/benchAgenda.py",
     ("def elegir_al_azar", "def listas_iguales"),
     ("azar.sample(",)),
    ("cripta/controlador/bench/reporte.py",
     ("import ListaEnlazada",),
     ("self.tablas = []",)),
    ("cripta/controlador/bench/medidor.py",
     ("minimo = None",),
     ("tiempos = []",)),
    ("cripta/adaptadores/convertidorJson.py",
     ('.get("enemigos", ())',),
     ('.get("enemigos", [])',)),
    ("cripta/modelo/estructuras/listaDoble.py",
     ("class ListaDoble", "def mover_al_inicio"),
     ()),
    ("cripta/modelo/estructuras/pilaAcotada.py",
     ("class PilaAcotada",),
     ()),
    ("cripta/modelo/estructuras/colaAcotada.py",
     ("class ColaAcotada",),
     ()),
    ("cripta/controlador/bench/alternativasEstructuras.py",
     ("class PilaAcotadaSimple", "class BitacoraSinTope"),
     ()),
    ("cripta/controlador/bench/benchListaDoble.py",
     ("class EscenarioSoltar",),
     ("tiempos_por_posicion",)),
    ("cripta/controlador/bench/benchHistorial.py",
     ("class EscenarioApilarLlena",),
     ()),
    ("cripta/controlador/bench/benchBitacora.py",
     ("def memoria",),
     ()),
    ("cripta/controlador/bench/benchTodo.py",
     ("def ejecutar_todo",),
     ()),
    ("pruebas/prueba_reglas.py",
     ("import ast", "ast.Dict"),
     ()),
    ("pruebas/prueba_2_3.py",
     ("elegir_al_azar", "MonticuloSobreLista"),
     ("MonticuloArreglo",)),
)

# Archivos de prueba que el ejecutor espera encontrar en la carpeta pruebas
PRUEBAS_ESPERADAS = (
    "prueba_1_2", "prueba_1_3", "prueba_1_4", "prueba_1_5", "prueba_1_6",
    "prueba_1_8", "prueba_1_9_integracion", "prueba_2_2", "prueba_2_3",
    "prueba_4_1", "prueba_4_2", "prueba_4_3", "prueba_4_4", "prueba_reglas",
)


def revisar_archivo(raiz, ruta, debe, no_debe):
    """Devuelve una lista de problemas (vacía si el archivo está al día)."""
    archivo = raiz.joinpath(ruta)
    if not archivo.exists():
        return ["NO EXISTE (¿se llama distinto o está en otra carpeta?)"]
    texto = archivo.read_text(encoding="utf-8")
    problemas = []
    for buscado in debe:
        if buscado not in texto:
            problemas.append(f"le falta '{buscado}'")
    for buscado in no_debe:
        if buscado in texto:
            problemas.append(f"todavía tiene '{buscado}' (versión vieja)")
    return problemas


def main():
    raiz = Path(__file__).resolve().parent.parent
    hay_problemas = False

    print("=== Versión de cada archivo ===")
    for ruta, debe, no_debe in REVISIONES:
        problemas = revisar_archivo(raiz, ruta, debe, no_debe)
        if problemas:
            hay_problemas = True
            print(f"[REEMPLAZAR] {ruta}")
            for problema in problemas:
                print(f"             - {problema}")
        else:
            print(f"[OK        ] {ruta}")

    print()
    print("=== Archivos de prueba ===")
    for nombre in PRUEBAS_ESPERADAS:
        ruta = f"pruebas/{nombre}.py"
        if raiz.joinpath(ruta).exists():
            print(f"[OK        ] {ruta}")
        else:
            hay_problemas = True
            print(f"[FALTA     ] {ruta}")

    print()
    if hay_problemas:
        print("Arregla lo marcado y vuelve a correr este script.")
    else:
        print("Todo está en su última versión: ya puedes correr  python -m pruebas.ejecutar_pruebas")


main()