import time
import uuid

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class FuenteRed:
    def __init__(self):
        self.client_id = str(uuid.uuid4())
        self.solicitudes = 0

    def _get(self, ruta, operacion):
        while True:
            self.solicitudes += 1
            try:
                r = requests.get(
                    BASE_URL + ruta,
                    headers={"X-Cripta-Client-Id": self.client_id},
                    timeout=10,
                )
            except requests.RequestException as e:
                raise RuntimeError(f"Error de red en '{operacion}': {e}")

            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                espera = r.json().get("reintentar_en", 1)
                time.sleep(espera)
                continue
            raise RuntimeError(f"'{operacion}' falló con código {r.status_code}")

    def listar_criptas(self):
        return self._get("/criptas", "listar criptas")

    def datos_cripta(self, id_cripta):
        return self._get(f"/criptas/{id_cripta}", "datos de la cripta")