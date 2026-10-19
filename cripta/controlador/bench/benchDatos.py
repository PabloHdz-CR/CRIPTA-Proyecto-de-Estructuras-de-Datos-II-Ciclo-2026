"""Mediciones de la capa de datos (D3, D4, D5, D7, D15): traducir respuestas
del API a DTO, la Cola con referencia a la cola contra una sin ella, y
requests.Session contra requests.get suelto.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchDatos            (completo)
    python -m cripta.controlador.bench.benchDatos --rapido   (versión corta)

Las respuestas se arman como TEXTO JSON y se leen con json.loads, igual que
llegan de la red; se mide solo la traducción a DTO (el convertidor), que es
el código propio. Session se mide contra un servidor HTTP local, sin gastar
presupuesto del API real.
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

from ...adaptadores import convertidorJson as cj
from ...modelo.estructuras.cola import Cola
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .medidor import Medidor
from .reporte import Reporte

LATENCIA_RED_MS = 400          # lo que tarda una solicitud real (§4.2)
VECES = 200                    # conversiones por medición
SOLICITUDES_HTTP = 20


# ---------------------------------------------------------------------------
# 1. Traducción de respuestas (D3, D5, D7)
# ---------------------------------------------------------------------------

def _texto_esqueleto(n):
    salas = ",".join(
        f'{{"id": {i}, "nombre": "Sala {i}", "salidas": {{"N": {{"sala": {i + 1}}}, '
        f'"S": {{"sala": {i - 1}}}, "E": {{"sala": {i + 2}, "cerrada": true, '
        f'"llave": "itm_llave", "cierre_automatico": 300}}}}}}'
        for i in range(1, n + 1))
    return f'{{"pagina": 1, "total_paginas": 1, "salas": [{salas}]}}'


def _texto_contenido(n):
    salas = ",".join(
        f'{{"sala": {i}, "enemigos": [{{"instancia": "e{i}", "tipo": "ent_rata", "vida": 9}}], '
        f'"objetos": ["itm_daga", "itm_pocion"], '
        f'"trampas": [{{"instancia": "t{i}", "tipo": "trp_pinchos"}}]}}'
        for i in range(1, n + 1))
    return f'{{"contenido": [{salas}]}}'


def _texto_fichas(n):
    clases = (
        '{{"id": "ent_{i}", "nombre": "Rata {i}", "clase": "enemigo", "vida_max": 12, '
        '"ataque": 4, "defensa": 1, "velocidad": 120, "comportamiento": "errante", '
        '"suelta": ["itm_pocion"]}}',
        '{{"id": "arm_{i}", "nombre": "Daga {i}", "clase": "arma", "peso": 2, "valor": 15, '
        '"ataque_bonus": 3}}',
        '{{"id": "poc_{i}", "nombre": "Poción {i}", "clase": "pocion", "peso": 1, '
        '"valor": 10, "cura": 8}}',
        '{{"id": "trp_{i}", "nombre": "Pinchos {i}", "clase": "trampa", "daño": 5}}',
    )
    fichas = ",".join(clases[i % len(clases)].format(i=i) for i in range(n))
    return f'{{"entidades": [{fichas}]}}'


class EscenarioConversion:
    def __init__(self, crear_texto, convertir):
        self._crear_texto = crear_texto
        self._convertir = convertir
        self._datos = None

    def preparar(self, n):
        self._datos = json.loads(self._crear_texto(n))

    def ejecutar(self):
        convertir, datos = self._convertir, self._datos
        for _ in range(VECES):
            resultado = convertir(datos)
            for _elemento in (resultado.salas if hasattr(resultado, "salas") else resultado):
                pass                        # recorrer la colección, como lo hace el modelo


# ---------------------------------------------------------------------------
# 2. Cola con y sin referencia al último nodo (D4)
# ---------------------------------------------------------------------------

class _Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None


class ColaSinReferencia:
    """SOLO PARA MEDIR (alternativa descartada de D4): una cola enlazada que
    solo recuerda el primer nodo, así que encolar recorre hasta el final."""

    def __init__(self):
        self._primero = None

    def encolar(self, dato):
        nuevo = _Nodo(dato)
        if self._primero is None:
            self._primero = nuevo
            return
        actual = self._primero
        while actual.siguiente is not None:
            actual = actual.siguiente
        actual.siguiente = nuevo

    def desencolar(self):
        nodo = self._primero
        self._primero = nodo.siguiente
        return nodo.dato


class EscenarioCola:
    def __init__(self, crear):
        self._crear = crear
        self._n = 0

    def preparar(self, n):
        self._n = n

    def ejecutar(self):
        cola = self._crear()
        for numero in range(self._n):
            cola.encolar(numero)
        for _ in range(self._n):
            cola.desencolar()


def verificar_colas():
    for crear in (Cola, ColaSinReferencia):
        cola = crear()
        for numero in range(50):
            cola.encolar(numero)
        for esperado in range(50):
            if cola.desencolar() != esperado:
                raise RuntimeError(f"{crear.__name__} no respeta el orden FIFO")


# ---------------------------------------------------------------------------
# 3. requests.Session contra requests.get (D15)
# ---------------------------------------------------------------------------

class _Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"          # permite reutilizar la conexión

    def do_GET(self):
        cuerpo = b'{"criptas": []}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *argumentos):
        pass


def medir_http(repeticiones):
    """Mínimo de `repeticiones` corridas de SOLICITUDES_HTTP solicitudes, en
    ms por solicitud, con Session y con requests.get suelto."""
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), _Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    url = f"http://127.0.0.1:{servidor.server_address[1]}/criptas"
    try:
        mejor_sesion = None
        mejor_get = None
        for _ in range(repeticiones):
            with requests.Session() as sesion:
                inicio = time.perf_counter()
                for _ in range(SOLICITUDES_HTTP):
                    sesion.get(url, timeout=5).json()
                tiempo = time.perf_counter() - inicio
            mejor_sesion = tiempo if mejor_sesion is None else min(mejor_sesion, tiempo)
            inicio = time.perf_counter()
            for _ in range(SOLICITUDES_HTTP):
                requests.get(url, timeout=5).json()
            tiempo = time.perf_counter() - inicio
            mejor_get = tiempo if mejor_get is None else min(mejor_get, tiempo)
        return (mejor_sesion / SOLICITUDES_HTTP * 1000, mejor_get / SOLICITUDES_HTTP * 1000)
    finally:
        servidor.shutdown()
        servidor.server_close()


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    reporte.titulo("Capa de datos: traducción, cola y conexiones (D3, D4, D5, D7, D15)")

    # 1. Traducción
    casos = (
        ("esqueleto", _texto_esqueleto, cj.pagina_salas_desde_json,
         (1, 10, 50) if rapido else (1, 10, 50, 200)),
        ("contenido", _texto_contenido, cj.contenido_desde_json, (1, 10)),
        ("fichas", _texto_fichas, cj.fichas_desde_json, (1, 10)),
    )
    filas = ListaEnlazada()
    for nombre, crear_texto, convertir, tamanos in casos:
        for n in tamanos:
            escenario = EscenarioConversion(crear_texto, convertir)
            us = medidor.medir(escenario, n).minimo / VECES * 1e6
            filas.agregar_al_final((nombre, str(n), f"{us:.1f}",
                                    f"{us / (LATENCIA_RED_MS * 1000) * 100:.3f} %"))
    reporte.tabla("1. Traducir una respuesta JSON a DTO con ListaEnlazada (µs)",
                  ("respuesta", "elementos", "traducir µs",
                   f"vs una solicitud ({LATENCIA_RED_MS} ms)"), filas)

    # 2. Cola
    verificar_colas()
    filas = ListaEnlazada()
    for n in ((500, 2000) if rapido else (500, 2000, 5000)):
        con = medidor.medir(EscenarioCola(Cola), n).minimo / n * 1e6
        sin = medidor.medir(EscenarioCola(ColaSinReferencia), n).minimo / n * 1e6
        filas.agregar_al_final((str(n), f"{con:.2f}", f"{sin:.2f}", f"{sin / con:.0f}x"))
    reporte.tabla("2. Encolar y desencolar n elementos, por elemento (µs)",
                  ("n", "Cola (decisión)", "sin referencia al final", "sin / con"), filas)

    # 3. Session
    sesion, suelto = medir_http(2 if rapido else 5)
    filas = ListaEnlazada()
    filas.agregar_al_final(("requests.Session (decisión)", f"{sesion:.2f}", "1.0x"))
    filas.agregar_al_final(("requests.get suelto", f"{suelto:.2f}", f"{suelto / sesion:.1f}x"))
    reporte.tabla(f"3. {SOLICITUDES_HTTP} solicitudes seguidas a un servidor local, "
                  "por solicitud (ms)", ("cliente", "ms por solicitud", "vs decisión"), filas)
    reporte.nota("")
    reporte.nota("Traducir cuesta microsegundos y una solicitud cientos de milisegundos: "
                 "la estructura de las colecciones de los DTO no pesa (D3). La cola sin "
                 "referencia crece con n (O(n) por encolar). Session reutiliza la conexión; "
                 "contra el servidor real (HTTPS) cada conexión nueva "
                 "además negocia TLS, que este servidor local no mide.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
