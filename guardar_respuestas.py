"""Descarga del API el paquete de respuestas para --offline (§3.4), con la
organización en disco que espera FuenteOffline (un archivo por entidad):

    datos_offline/
        criptas.json
        criptas/<id>/general.json, version.json
        criptas/<id>/esqueleto/pagina_<n>.json
        criptas/<id>/contenido/<id_sala>.json
        catalogo/version.json, catalogo/<id_ficha>.json

Uso (desde la raíz del proyecto):
    python guardar_respuestas.py                 # todas las criptas publicadas
    python guardar_respuestas.py cripta-01 ...   # solo esas

Herramienta de desarrollo, fuera de cripta/: habla directo con requests y
json. Pide contenido y catálogo en lotes de 10 (§3.3) y respeta HTTP 429.
"""
import json
import sys
import time
import uuid
from pathlib import Path

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
CARPETA = Path("datos_offline")
LOTE = 10
TIMEOUT = 15
REINTENTOS_429 = 5
CABECERAS = {"X-Cripta-Client-Id": str(uuid.uuid4())}   # uno por ejecución
solicitudes = 0


def pedir(ruta):
    global solicitudes
    for _ in range(REINTENTOS_429 + 1):
        solicitudes += 1
        respuesta = requests.get(BASE_URL + ruta, headers=CABECERAS, timeout=TIMEOUT)
        if respuesta.status_code == 200:
            return respuesta.json()
        if respuesta.status_code == 429:
            espera = respuesta.json().get("reintentar_en", 5)
            print(f"  429 en {ruta}: espero {espera} s")
            time.sleep(espera)
            continue
        raise SystemExit(f"Falló GET {ruta}: HTTP {respuesta.status_code} {respuesta.text}")
    raise SystemExit(f"Falló GET {ruta}: demasiados 429 seguidos")


def escribir(relativa, datos):
    ruta = CARPETA / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def nombre_seguro(texto):
    """Misma convención que FuenteOffline/_nombre_seguro."""
    return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(texto)) + ".json"


def lotes(elementos):
    for inicio in range(0, len(elementos), LOTE):
        yield elementos[inicio:inicio + LOTE]


def descargar_cripta(id_cripta, ids_fichas):
    print(f"Cripta {id_cripta}")
    general = pedir(f"/criptas/{id_cripta}")
    escribir(f"criptas/{id_cripta}/general.json", general)
    escribir(f"criptas/{id_cripta}/version.json", pedir(f"/criptas/{id_cripta}/version"))

    ids_salas = []
    for pagina in range(1, general["paginas"] + 1):
        datos = pedir(f"/criptas/{id_cripta}/salas?pagina={pagina}")
        escribir(f"criptas/{id_cripta}/esqueleto/pagina_{pagina}.json", datos)
        ids_salas.extend(sala["id"] for sala in datos["salas"])

    for lote in lotes(ids_salas):
        datos = pedir(f"/criptas/{id_cripta}/contenido?salas=" + ",".join(map(str, lote)))
        for sala in datos["contenido"]:
            escribir(f"criptas/{id_cripta}/contenido/{sala['sala']}.json", sala)
            for enemigo in sala.get("enemigos", ()):
                ids_fichas.add(enemigo["tipo"])
            for trampa in sala.get("trampas", ()):
                ids_fichas.add(trampa["tipo"])
            ids_fichas.update(sala.get("objetos", ()))
    ids_fichas.add(general["llave_salida"])


def descargar_catalogo(ids_fichas):
    escribir("catalogo/version.json", pedir("/catalogo/version"))
    # Las fichas pueden referir a otras (lo que suelta un enemigo, la llave de
    # una puerta): se repite hasta que no aparezcan ids nuevos.
    pendientes = sorted(ids_fichas)
    descargadas = set()
    while pendientes:
        nuevos = set()
        for lote in lotes(pendientes):
            datos = pedir("/catalogo?ids=" + ",".join(lote))
            for ficha in datos["entidades"]:
                escribir("catalogo/" + nombre_seguro(ficha["id"]), ficha)
                descargadas.add(ficha["id"])
                nuevos.update(ficha.get("suelta", ()))
        pendientes = sorted(nuevos - descargadas)
    print(f"Catálogo: {len(descargadas)} fichas")


def main():
    criptas = pedir("/criptas")
    escribir("criptas.json", criptas)
    pedidas = sys.argv[1:] or [c["id"] for c in criptas["criptas"]]
    ids_fichas = set()
    for id_cripta in pedidas:
        descargar_cripta(id_cripta, ids_fichas)
    descargar_catalogo(ids_fichas)
    print(f"Listo: {solicitudes} solicitudes, paquete en {CARPETA}/")


if __name__ == "__main__":
    main()
