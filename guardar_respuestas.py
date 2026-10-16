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
import uuid
from pathlib import Path

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


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

def guardar(ruta, nombre_archivo):
    r = requests.get(BASE_URL + ruta, headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"Falló {ruta}: {r.status_code} {r.text}")
        return
    with open(f"datos_offline/{nombre_archivo}", "w", encoding="utf-8") as f:
        json.dump(r.json(), f, ensure_ascii=False, indent=2)
    print(f"Guardado {nombre_archivo}")

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

guardar("/criptas", "criptas.json")
guardar("/criptas/cripta-01", "cripta-01_general.json")
guardar("/criptas/cripta-01/salas?pagina=1", "cripta-01_salas_p1.json")
guardar("/criptas/cripta-01/contenido?salas=1,2,3", "cripta-01_contenido_1-3.json")