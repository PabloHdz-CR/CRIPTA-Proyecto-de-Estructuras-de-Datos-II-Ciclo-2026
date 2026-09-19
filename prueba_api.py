import uuid
import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
headers = {"X-Cripta-Client-Id": str(uuid.uuid4())}

for ruta in ["/criptas", "/criptas/cripta-01", "/criptas/cripta-01/salas?pagina=1"]:
    r = requests.get(BASE_URL + ruta, headers=headers, timeout=10)
    print(ruta, r.status_code)
    print(r.json())
    print()