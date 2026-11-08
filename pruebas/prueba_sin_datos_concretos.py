"""FR-036 (003-resolubilidad) y principio IV de la constitución: ningún dato
de una cripta concreta aparece en el código del programa.

Junta:
  - los ids de cripta de `datos_offline/` y de cada paquete de `pruebas/datos/`
    (`criptas.json`);
  - las versiones de cripta de `datos_offline/` (`criptas/<id>/version.json`),
    que son las de criptas publicadas. Las versiones de los paquetes de prueba
    son sintéticas ("v1") y el bench también las usa como dato sintético, así
    que no se buscan.

y busca cada uno en las constantes de texto de `cripta/`, leyendo el código
con `ast`: los comentarios no son constantes y los docstrings se descartan,
así que un ejemplo en la documentación no da una falsa alarma.

Limitación declarada (tasks.md T005): las cantidades (salas, llaves,
presupuesto) son números que no se distinguen de forma confiable de otras
constantes; esa parte se revisa a mano (T054).

Uso: py -m pruebas.prueba_sin_datos_concretos
"""
import ast
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CODIGO = RAIZ / "cripta"
PUBLICADAS = RAIZ / "datos_offline"
PAQUETES_DE_PRUEBA = RAIZ / "pruebas" / "datos"


def _ids_de(paquete):
    archivo = paquete / "criptas.json"
    if not archivo.exists():
        return []
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return [cripta["id"] for cripta in datos["criptas"]]


def _versiones_de(paquete):
    versiones = []
    for archivo in paquete.glob("criptas/*/version.json"):
        version = json.loads(archivo.read_text(encoding="utf-8")).get("version")
        if isinstance(version, str) and version:
            versiones.append(version)
    return versiones


def datos_buscados():
    """(texto, de dónde viene) por cada id o versión que no debe aparecer."""
    buscados = []
    for id_cripta in _ids_de(PUBLICADAS):
        buscados.append((id_cripta, "id de datos_offline/"))
    for version in _versiones_de(PUBLICADAS):
        buscados.append((version, "versión de datos_offline/"))
    for paquete in sorted(PAQUETES_DE_PRUEBA.iterdir()):
        if paquete.is_dir():
            for id_cripta in _ids_de(paquete):
                buscados.append((id_cripta, f"id de pruebas/datos/{paquete.name}/"))
    return buscados


def _docstrings(arbol):
    """Los nodos Constant que son docstrings (módulo, clase o función)."""
    nodos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                    and isinstance(cuerpo[0].value, ast.Constant)
                    and isinstance(cuerpo[0].value.value, str)):
                nodos.add(id(cuerpo[0].value))
    return nodos


def constantes_de_texto(ruta):
    """(línea, texto) de cada constante de texto del archivo, sin docstrings."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    excluidos = _docstrings(arbol)
    resultado = []
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
                and id(nodo) not in excluidos):
            resultado.append((nodo.lineno, nodo.value))
    return resultado


def hallazgos(carpeta=CODIGO, buscados=None):
    if buscados is None:
        buscados = datos_buscados()
    encontrados = []
    for ruta in sorted(carpeta.rglob("*.py")):
        for linea, texto in constantes_de_texto(ruta):
            for buscado, origen in buscados:
                if buscado in texto:
                    encontrados.append(
                        f"{ruta.relative_to(RAIZ)}:{linea}: '{buscado}' ({origen})")
    return encontrados


def main():
    buscados = datos_buscados()
    # Sin nada que buscar, la prueba no probaría nada: se exige al menos un
    # paquete con criptas.
    assert buscados, "No se encontró ningún paquete con criptas.json para revisar"
    encontrados = hallazgos(buscados=buscados)
    if encontrados:
        print("FR-036: el código tiene datos de criptas concretas:")
        for texto in encontrados:
            print("  " + texto)
        sys.exit(1)
    print(f"FR-036: ninguno de los {len(buscados)} ids y versiones de criptas aparece en cripta/.")


if __name__ == "__main__":
    main()
