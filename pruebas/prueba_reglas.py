"""Revisa que el código del programa (carpeta cripta) respete las reglas del
proyecto, leyendo el código como lo lee Python (módulo ast), no como texto:

  - sin lambda (todavía no se domina)
  - sin listas de Python: ni [ ... ], ni list(), ni comprensiones de lista, ni
    .append() .pop() .insert() .extend() .remove(). Donde haga falta una lista
    se usa nuestra ListaEnlazada. Excepción: clienteHttp, almacenLocalDisco y
    fuenteOffline, que arman/leen estructuras planas para hablar con
    requests/json (empaquetar para la red o el disco, no sustituir una
    estructura propia del programa).
  - sin diccionarios: ni { ... }, ni dict(), ni comprensiones de diccionario
    (§7 prohíbe dict como índice o tabla de búsqueda). Misma excepción que
    arriba, por la misma razón.
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
# Archivos (nombre en minúsculas, sin guiones bajos) donde armar/leer un dict o
# una lista de Python es interactuar con requests/json, no sustituir una
# estructura propia del programa.
ARCHIVOS_CON_EXCEPCION = ("clientehttp", "almacenlocaldisco", "fuenteoffline",
                          "puntajesarchivo", "benchguardado")
MODULOS_PROHIBIDOS = ("heapq", "bisect", "queue")


def problema_en(nodo, excepcion):
    """Devuelve la descripción de lo prohibido que hay en este nodo, o None."""
    if isinstance(nodo, ast.Lambda):
        return "usa lambda"
    if isinstance(nodo, (ast.Dict, ast.DictComp)) and not excepcion:
        return "crea un diccionario { ... }"
    if isinstance(nodo, ast.List) and not excepcion:
        return "usa una lista de Python [ ... ]"
    if isinstance(nodo, ast.ListComp) and not excepcion:
        return "usa una comprensión de lista"
    if isinstance(nodo, ast.Call):
        funcion = nodo.func
        if isinstance(funcion, ast.Name):
            for nombre, descripcion in NOMBRES_PROHIBIDOS:
                # DECISIÓN: 'list'/'dict' se exceptúan igual que los literales
                # [...]/{...} en los archivos de ARCHIVOS_CON_EXCEPCION (misma
                # razón: convertir a algo que json.dumps() entienda, como en
                # benchGuardado.py con el estado del random). 'sorted' NUNCA
                # se exceptúa: ninguna interoperación de disco/red lo necesita,
                # y §4.9 lo prohíbe siempre en los ordenamientos evaluados.
                si_se_exceptua = nombre in ("dict", "list") and excepcion
                if funcion.id == nombre and not si_se_exceptua:
                    return f"usa {descripcion}"
        if (isinstance(funcion, ast.Attribute) and funcion.attr in METODOS_DE_LISTA
                and not excepcion):
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


def revisar(nodo, ruta, encontradas, excepcion=False):
    """Recorre el árbol en el orden en que está escrito el código y anota cada
    uso prohibido en 'encontradas'."""
    descripcion = problema_en(nodo, excepcion)
    if descripcion is not None:
        encontradas.append(f"{ruta}:{nodo.lineno}: {descripcion}")
    for hijo in ast.iter_child_nodes(nodo):
        revisar(hijo, ruta, encontradas, excepcion)


def tiene_excepcion(archivo):
    nombre = archivo.stem.lower().replace("_", "")
    return nombre in ARCHIVOS_CON_EXCEPCION


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
revisar(ast.parse(
    "x = {'a': 1}\ny = [1, 2]\ny.append(3)\nz = list(w)\nv = dict(a=1)"),
    "caso", permitidos, True)
assert len(permitidos) == 0, "la excepción de archivos permitidos no funciona"
exceptuados_pero_prohibidos = []
revisar(ast.parse("x = sorted(y)"), "caso", exceptuados_pero_prohibidos, True)
assert len(exceptuados_pero_prohibidos) == 1, "sorted() no debería exceptuarse nunca"
for codigo, debe_encontrar in CASOS:
    detectadas = []
    revisar(ast.parse(codigo), "caso", detectadas)
    assert (len(detectadas) > 0) == debe_encontrar, (
        f"el detector falló con: {codigo!r} (encontró {detectadas})")

raiz = Path(__file__).resolve().parent.parent   # la raíz del proyecto (pruebas/ es hija suya, igual que cripta/)
encontradas = []           # esta lista es solo de la prueba, no del programa
revisados = 0
for archivo in raiz.joinpath("cripta").rglob("*.py"):
    revisados += 1
    ruta = archivo.relative_to(raiz).as_posix()
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=ruta)
    revisar(arbol, ruta, encontradas, tiene_excepcion(archivo))

assert revisados > 0, "no se encontró la carpeta cripta"
if encontradas:
    print("Se encontraron usos de construcciones prohibidas:")
    for linea in encontradas:
        print(" ", linea)
    raise SystemExit(1)
print(f"Reglas del proyecto OK ({revisados} archivos revisados)")