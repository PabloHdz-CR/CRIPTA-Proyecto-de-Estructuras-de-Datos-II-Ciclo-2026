"""Revisa que el código del programa (carpeta cripta) respete las reglas del
proyecto, leyendo el código como lo lee Python (módulo ast), no como texto:

  - sin lambda (todavía no se domina)
  - sin listas de Python: ni [ ... ], ni list(), ni comprensiones de lista, ni
    .append() .pop() .insert() .extend() .remove(). Donde haga falta una lista
    se usa nuestra ListaEnlazada.
  - sin diccionarios: ni { ... }, ni dict(), ni comprensiones de diccionario
    (§7 prohíbe dict como índice o tabla de búsqueda). Excepción: clienteHttp,
    que arma los parámetros de las solicitudes para la biblioteca requests.
  - sin sorted() ni .sort() (§4.9 los prohíbe en los ordenamientos evaluados)
  - sin bibliotecas que sustituyen a nuestras estructuras: heapq, bisect,
    queue y collections.deque (§7)

Como lee el código y no el texto, los comentarios y los textos explicativos no
producen falsas alarmas. Leer un diccionario que llega de response.json() (con
[ ] o .get) sí se permite: solo se prohíbe crearlos.
"""
import ast
from pathlib import Path

METODOS_DE_LISTA = ("append", "pop", "insert", "extend", "remove", "sort")
NOMBRES_PROHIBIDOS = (("list", "list()"), ("sorted", "sorted()"), ("dict", "dict()"))
ARCHIVOS_CON_DICT_PERMITIDO = ("clientehttp",)     # nombre en minúsculas y sin guiones bajos
MODULOS_PROHIBIDOS = ("heapq", "bisect", "queue")


def problema_en(nodo, dict_permitido):
    """Devuelve la descripción de lo prohibido que hay en este nodo, o None."""
    if isinstance(nodo, ast.Lambda):
        return "usa lambda"
    if isinstance(nodo, (ast.Dict, ast.DictComp)) and not dict_permitido:
        return "crea un diccionario { ... }"
    if isinstance(nodo, ast.List):
        return "usa una lista de Python [ ... ]"
    if isinstance(nodo, ast.ListComp):
        return "usa una comprensión de lista"
    if isinstance(nodo, ast.Call):
        funcion = nodo.func
        if isinstance(funcion, ast.Name):
            for nombre, descripcion in NOMBRES_PROHIBIDOS:
                if funcion.id == nombre and not (nombre == "dict" and dict_permitido):
                    return f"usa {descripcion}"
        if isinstance(funcion, ast.Attribute) and funcion.attr in METODOS_DE_LISTA:
            return f"usa .{funcion.attr}()"
    if isinstance(nodo, ast.Import):
        for alias in nodo.names:
            if alias.name.split(".")[0] in MODULOS_PROHIBIDOS:
                return f"importa {alias.name}"
    if isinstance(nodo, ast.ImportFrom):
        modulo = nodo.module or ""
        if modulo.split(".")[0] in MODULOS_PROHIBIDOS:
            return f"importa de {modulo}"
        if modulo == "collections":
            for alias in nodo.names:
                if alias.name == "deque":
                    return "importa collections.deque"
    return None


def revisar(nodo, ruta, encontradas, dict_permitido=False):
    """Recorre el árbol en el orden en que está escrito el código y anota cada
    uso prohibido en 'encontradas'."""
    descripcion = problema_en(nodo, dict_permitido)
    if descripcion is not None:
        encontradas.append(f"{ruta}:{nodo.lineno}: {descripcion}")
    for hijo in ast.iter_child_nodes(nodo):
        revisar(hijo, ruta, encontradas, dict_permitido)


def permite_dict(archivo):
    nombre = archivo.stem.lower().replace("_", "")
    return nombre in ARCHIVOS_CON_DICT_PERMITIDO


# Autoprueba del detector: (código, ¿debe encontrar algo prohibido?)
CASOS = (
    ("x = [1, 2]", True),
    ("x = list(y)", True),
    ("x = [a for a in y]", True),
    ("y.append(3)", True),
    ("y.pop()", True),
    ("f = lambda a: a", True),
    ("sorted(x)", True),
    ("x.sort()", True),
    ("import heapq", True),
    ("from bisect import insort", True),
    ("from collections import deque", True),
    ("def f(a=[]):\n    pass", True),
    ('"""un texto con [] lambda y .append(3)"""\nx = 1', False),
    ("# un comentario con [] lambda y list(x)\nx = 1", False),
    ("x = {'a': 1}", True),
    ("x = {k: v for k, v in y}", True),
    ("x = dict(a=1)", True),
    ("x = (1, 2)\nz = a[0]\nw = a[1:2]\nv = datos.get('c', ())", False),
    ("for a in ():\n    pass", False),
    ("from collections import namedtuple", False),
)
permitidos = []
revisar(ast.parse("x = {'a': 1}"), "caso", permitidos, True)
assert len(permitidos) == 0, "la excepción de clienteHttp no funciona"
for codigo, debe_encontrar in CASOS:
    detectadas = []
    revisar(ast.parse(codigo), "caso", detectadas)
    assert (len(detectadas) > 0) == debe_encontrar, (
        f"el detector falló con: {codigo!r} (encontró {detectadas})")

raiz = Path(__file__).resolve().parent.parent
encontradas = []           # esta lista es solo de la prueba, no del programa
revisados = 0
for archivo in raiz.joinpath("cripta").rglob("*.py"):
    revisados += 1
    ruta = archivo.relative_to(raiz).as_posix()
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=ruta)
    revisar(arbol, ruta, encontradas, permite_dict(archivo))

assert revisados > 0, "no se encontró la carpeta cripta"
if encontradas:
    print("Se encontraron usos de construcciones prohibidas:")
    for linea in encontradas:
        print(" ", linea)
    raise SystemExit(1)
print(f"Reglas del proyecto OK ({revisados} archivos revisados)")