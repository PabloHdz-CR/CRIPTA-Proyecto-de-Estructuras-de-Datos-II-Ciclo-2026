"""D17: toda falla de red llega como ErrorDeRed con la operación y la causa,
y los timeouts y conexiones rechazadas NO se reintentan (cuenta 1 solicitud).

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py pruebas/prueba_errores_red.py
"""
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.modelo.puertos.errores import ErrorDeRed


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    modo = "500"
    recibidas = 0

    def do_GET(self):
        Manejador.recibidas += 1
        if Manejador.modo == "500":
            self._responder(500, b'{"error": "fallo interno de prueba"}')
        elif Manejador.modo == "json_invalido":
            self._responder(200, b"esto no es json")
        elif Manejador.modo == "lento":
            time.sleep(1.0)
            self._responder(200, b'{"criptas": []}')

    def _responder(self, codigo, cuerpo):
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        try:
            self.wfile.write(cuerpo)
        except OSError:
            pass                                 # el cliente ya cortó (timeout)

    def log_message(self, formato, *argumentos):
        pass


def fallo(cliente):
    try:
        cliente.listar_criptas()
    except ErrorDeRed as error:
        return error
    raise AssertionError("debió lanzar ErrorDeRed")


class Servidor(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass                                     # el cliente cortó a propósito (timeout)


servidor = Servidor(("127.0.0.1", 0), Manejador)
threading.Thread(target=servidor.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{servidor.server_address[1]}"

try:
    # 1. HTTP 500: código, operación y el mensaje del servidor
    Manejador.modo, Manejador.recibidas = "500", 0
    contador = ContadorSolicitudes()
    error = fallo(ClienteHttp(url, contador, margen_espera=0))
    assert error.codigo_http == 500 and error.operacion == "listar criptas", error
    assert "fallo interno de prueba" in str(error) and "listar criptas" in str(error)
    assert contador.solicitudes_realizadas() == 1 == Manejador.recibidas   # sin reintento

    # 2. JSON inválido con 200: ErrorDeRed, no un ValueError de requests
    Manejador.modo, Manejador.recibidas = "json_invalido", 0
    error = fallo(ClienteHttp(url, ContadorSolicitudes(), margen_espera=0))
    assert error.operacion == "listar criptas" and "no es un JSON" in str(error), error

    # 3. Timeout: se informa y NO se reintenta (quizás el servidor sí la procesó)
    Manejador.modo, Manejador.recibidas = "lento", 0
    contador = ContadorSolicitudes()
    error = fallo(ClienteHttp(url, contador, timeout=0.2, margen_espera=0))
    assert "tiempo de espera agotado" in str(error), error
    assert contador.solicitudes_realizadas() == 1
    time.sleep(1.0)                                  # que el servidor termine la lenta
    assert Manejador.recibidas == 1

    # 4. Conexión rechazada: un puerto donde no escucha nadie
    libre = socket.socket()
    libre.bind(("127.0.0.1", 0))
    puerto_cerrado = libre.getsockname()[1]
    libre.close()
    contador = ContadorSolicitudes()
    error = fallo(ClienteHttp(f"http://127.0.0.1:{puerto_cerrado}", contador,
                              timeout=2, margen_espera=0))
    # En Windows, conectar a un puerto cerrado de localhost reintenta el SYN hasta
    # el timeout (ConnectTimeout); en Linux se rechaza al instante. Las dos son
    # ErrorDeRed con contexto y sin reintento.
    assert ("no se pudo conectar" in str(error) or "tiempo de espera agotado" in str(error))
    assert error.operacion == "listar criptas"
    assert contador.solicitudes_realizadas() == 1
finally:
    servidor.shutdown()
    servidor.server_close()

print("Sección errores de red (D17) OK")
