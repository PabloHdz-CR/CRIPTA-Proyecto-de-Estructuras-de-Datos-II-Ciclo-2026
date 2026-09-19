import json
import os
import uuid

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
headers = {"X-Cripta-Client-Id": str(uuid.uuid4())}

os.makedirs("datos_offline", exist_ok=True)


def guardar(ruta, nombre_archivo):
    r = requests.get(BASE_URL + ruta, headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"Falló {ruta}: {r.status_code} {r.text}")
        return
    with open(f"datos_offline/{nombre_archivo}", "w", encoding="utf-8") as f:
        json.dump(r.json(), f, ensure_ascii=False, indent=2)
    print(f"Guardado {nombre_archivo}")


guardar("/criptas", "criptas.json")
guardar("/criptas/cripta-01", "cripta-01_general.json")
guardar("/criptas/cripta-01/salas?pagina=1", "cripta-01_salas_p1.json")
guardar("/criptas/cripta-01/contenido?salas=1,2,3", "cripta-01_contenido_1-3.json")