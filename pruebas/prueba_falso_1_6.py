"""Servidor HTTP local que imita el API de Cripta con datos en memoria.

Sirve para probar el cliente sin internet y sin gastar solicitudes reales.
Solo es una herramienta de pruebas: no forma parte del programa.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ENCABEZADO_CLIENTE = "X-Cripta-Client-Id"

FICHAS = [
    {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 12,
     "ataque": 5, "defensa": 1, "velocidad": 150, "comportamiento": "rastreador",
     "suelta": ["itm_pocion"]},
    {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2, "valor": 15,
     "ataque_bonus": 3},
    {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 4,
     "rearme": 300},
    {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "peso": 1,
     "valor": 10, "cura": 8},
]


class _Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        falso = self.server.falso
        falso._anotar(self.path, self.headers.get(ENCABEZADO_CLIENTE))
        if falso.latencia:
            time.sleep(falso.latencia)
        if falso._toca_429():
            self._responder(429, {"error": "demasiadas solicitudes",
                                  "reintentar_en": 0})
            return
        codigo, cuerpo = falso._resolver(urlparse(self.path))
        self._responder(codigo, cuerpo)

    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, formato, *argumentos):
        pass  # silencia el registro del servidor de prueba


class ServidorFalso:
    """Una cripta lineal: cada sala i se conecta al norte con i+1 y al sur con i-1.

    - Las salas impares tienen una rata, las múltiplos de 3 una daga y las
      múltiplos de 5 una trampa de dardos.
    - contenido y catalogo devuelven los elementos en orden INVERSO al pedido,
      para comprobar que quien llama empareja por 'sala' o 'id', no por posición.
    - inyectar_429(n) hace que las próximas n solicitudes respondan 429.
    """

    def __init__(self, id_cripta="cripta-test", total_salas=25,
                 salas_por_pagina=10, presupuesto=12, latencia=0.0):
        self.id_cripta = id_cripta
        self.total_salas = total_salas
        self.salas_por_pagina = salas_por_pagina
        self.presupuesto = presupuesto
        self.latencia = latencia
        self._cerrojo = threading.Lock()
        self._recibidas = []           # (ruta con parámetros, id de cliente)
        self._pendientes_429 = 0
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Manejador)
        self._httpd.daemon_threads = True
        self._httpd.falso = self
        self.base_url = f"http://127.0.0.1:{self._httpd.server_address[1]}/v1"
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    # ------------------------------------------------------------------
    # Control desde las pruebas
    # ------------------------------------------------------------------

    def inyectar_429(self, cantidad):
        with self._cerrojo:
            self._pendientes_429 = cantidad

    def total_recibidas(self):
        with self._cerrojo:
            return len(self._recibidas)

    def rutas_recibidas(self):
        with self._cerrojo:
            rutas = []
            for ruta, _ in self._recibidas:
                rutas.append(ruta)
            return rutas

    def ids_de_cliente_vistos(self):
        with self._cerrojo:
            vistos = []
            for _, id_cliente in self._recibidas:
                if id_cliente not in vistos:
                    vistos.append(id_cliente)
            return vistos

    def cerrar(self):
        self._httpd.shutdown()
        self._httpd.server_close()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _anotar(self, ruta, id_cliente):
        with self._cerrojo:
            self._recibidas.append((ruta, id_cliente))

    def _toca_429(self):
        with self._cerrojo:
            if self._pendientes_429 > 0:
                self._pendientes_429 -= 1
                return True
            return False

    def _paginas(self):
        return (self.total_salas + self.salas_por_pagina - 1) // self.salas_por_pagina

    def _sala(self, numero):
        salidas = {}
        if numero < self.total_salas:
            salidas["N"] = {"sala": numero + 1}
        if numero > 1:
            salidas["S"] = {"sala": numero - 1}
        return {"id": numero, "nombre": f"Sala {numero}", "salidas": salidas}

    def _contenido(self, numero):
        enemigos = []
        if numero % 2 == 1:
            enemigos.append({"instancia": f"e-{numero}", "tipo": "ent_rata", "vida": 12})
        objetos = []
        if numero % 3 == 0:
            objetos.append("itm_daga")
        trampas = []
        if numero % 5 == 0:
            trampas.append({"instancia": f"t-{numero}", "tipo": "trp_dardos"})
        return {"sala": numero, "enemigos": enemigos, "objetos": objetos,
                "trampas": trampas}

    def _resolver(self, url):
        partes = url.path.strip("/").split("/")      # ["v1", "criptas", ...]
        consulta = parse_qs(url.query)
        if partes[0] != "v1":
            return 404, {"detail": "no encontrado"}
        partes = partes[1:]

        if partes == ["criptas"]:
            return 200, {"criptas": [{"id": self.id_cripta, "nombre": "Cripta de prueba",
                                      "salas": self.total_salas, "dificultad": 1}]}
        if partes == ["catalogo", "version"]:
            return 200, {"version": "cat-test-1"}
        if partes == ["catalogo"]:
            return self._catalogo(consulta)
        if len(partes) >= 2 and partes[0] == "criptas":
            if partes[1] != self.id_cripta:
                return 404, {"detail": "cripta no encontrada"}
            if len(partes) == 2:
                return 200, self._datos_generales()
            if partes[2:] == ["version"]:
                return 200, {"id": self.id_cripta, "version": "v-test-1"}
            if partes[2:] == ["salas"]:
                return self._pagina(consulta)
            if partes[2:] == ["contenido"]:
                return self._contenido_lote(consulta)
        return 404, {"detail": "no encontrado"}

    def _datos_generales(self):
        return {"id": self.id_cripta, "version": "v-test-1",
                "salas_total": self.total_salas, "paginas": self._paginas(),
                "salas_por_pagina": self.salas_por_pagina, "sala_inicial": 1,
                "sala_salida": self.total_salas, "llave_salida": "itm_llave",
                "presupuesto_solicitudes": self.presupuesto, "inventario_max": 10,
                "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}

    def _pagina(self, consulta):
        pagina = int(consulta.get("pagina", ["1"])[0])
        if pagina < 1 or pagina > self._paginas():
            return 404, {"detail": "página fuera de rango"}
        primera = (pagina - 1) * self.salas_por_pagina + 1
        ultima = min(pagina * self.salas_por_pagina, self.total_salas)
        salas = []
        for numero in range(primera, ultima + 1):
            salas.append(self._sala(numero))
        return 200, {"pagina": pagina, "total_paginas": self._paginas(), "salas": salas}

    def _contenido_lote(self, consulta):
        pedidas = consulta.get("salas", [""])[0].split(",")
        if len(pedidas) > 10:
            return 422, {"detail": "máximo 10 salas por solicitud"}
        respuesta = []
        for texto in reversed(pedidas):               # orden inverso a propósito
            numero = int(texto)
            if numero < 1 or numero > self.total_salas:
                return 404, {"detail": f"sala {numero} no existe"}
            respuesta.append(self._contenido(numero))
        return 200, {"contenido": respuesta}

    def _catalogo(self, consulta):
        pedidos = consulta.get("ids", [""])[0].split(",")
        if len(pedidos) > 10:
            return 422, {"detail": "máximo 10 ids por solicitud"}
        respuesta = []
        for id_ficha in reversed(pedidos):            # orden inverso a propósito
            encontrada = None
            for ficha in FICHAS:
                if ficha["id"] == id_ficha:
                    encontrada = ficha
            if encontrada is None:
                return 404, {"detail": f"ficha {id_ficha} no existe"}
            respuesta.append(encontrada)
        return 200, {"entidades": respuesta}