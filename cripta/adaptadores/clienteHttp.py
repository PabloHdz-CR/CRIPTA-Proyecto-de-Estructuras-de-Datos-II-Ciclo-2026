import threading
import time
import uuid
from urllib.parse import quote

import requests

from ..modelo.puertos.errores import ErrorDeRed
from ..modelo.puertos.fuenteDatos import FuenteDatos, validar_lote
from . import convertidorJson

ENCABEZADO_CLIENTE = "X-Cripta-Client-Id"
TIMEOUT_POR_DEFECTO = 10            # segundos, como en el ejemplo del enunciado
REINTENTOS_429_POR_DEFECTO = 3      # reintentos DESPUÉS del primer intento
MARGEN_ESPERA_POR_DEFECTO = 1       # segundos extra sobre 'reintentar_en'
ESPERA_POR_DEFECTO_429 = 5          # si el 429 no dice cuánto esperar
ESPERA_MAXIMA_429 = 60              # más que esto no se espera: se lanza error


def _unir_con_comas(elementos):
    """Convierte 1, 2, 3 (ListaEnlazada) en el texto '1,2,3'."""
    texto = ""
    primero = True
    for elemento in elementos:
        if not primero:
            texto += ","
        texto += str(elemento)
        primero = False
    return texto


class ClienteHttp(FuenteDatos):
    def __init__(self, base_url, contador, timeout=TIMEOUT_POR_DEFECTO,max_reintentos_429=REINTENTOS_429_POR_DEFECTO,margen_espera=MARGEN_ESPERA_POR_DEFECTO):
        self._base_url = base_url.rstrip("/")
        self._contador = contador
        self._timeout = timeout
        self._max_reintentos = max_reintentos_429
        self._margen_espera = margen_espera
        self._id_cliente = str(uuid.uuid4())
        self._sesion = requests.Session()
        self._sesion.headers[ENCABEZADO_CLIENTE] = self._id_cliente
        self._cerrojo_http = threading.Lock()

    def id_cliente(self):
        return self._id_cliente

    def cerrar(self):
        self._sesion.close()

    def _pedir(self, operacion, ruta, parametros=None):

        with self._cerrojo_http:
            reintentos_hechos = 0
            while True:
                self._contador.registrar_intento(operacion)
                respuesta = self._enviar(operacion, ruta, parametros)

                if respuesta.status_code == 200:
                    return self._leer_json(operacion, respuesta)

                if respuesta.status_code == 429:
                    if reintentos_hechos >= self._max_reintentos:
                        raise ErrorDeRed(
                            operacion,
                            "el servicio sigue limitando la frecuencia después "
                            f"de {self._max_reintentos} reintentos",
                            429)
                    espera = self._espera_para_reintentar(operacion, respuesta)
                    time.sleep(espera)
                    reintentos_hechos += 1
                    continue

                raise ErrorDeRed(operacion, self._describir_error(respuesta),
                                 respuesta.status_code)

    def _enviar(self, operacion, ruta, parametros):
        url = self._base_url + ruta
        try:
            return self._sesion.get(url, params=parametros, timeout=self._timeout)
        except requests.exceptions.Timeout as error:
            raise ErrorDeRed(
                operacion, f"tiempo de espera agotado ({self._timeout} s)") from error
        except requests.exceptions.ConnectionError as error:
            raise ErrorDeRed(operacion, "no se pudo conectar con el servicio") from error
        except requests.exceptions.RequestException as error:
            raise ErrorDeRed(operacion, f"error de red: {error}") from error

    def _leer_json(self, operacion, respuesta):
        try:
            return respuesta.json()
        except ValueError as error:
            raise ErrorDeRed(
                operacion, "la respuesta no es un JSON válido", 200) from error

    def _espera_para_reintentar(self, operacion, respuesta):
        solicitada = ESPERA_POR_DEFECTO_429
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = None
        if isinstance(cuerpo, dict):
            valor = cuerpo.get("reintentar_en")
            es_numero = isinstance(valor, (int, float)) and not isinstance(valor, bool)
            if es_numero and valor >= 0:
                solicitada = valor
        if solicitada > ESPERA_MAXIMA_429:
            raise ErrorDeRed(
                operacion,
                f"el servicio pide esperar {solicitada} s, más de lo tolerable "
                f"({ESPERA_MAXIMA_429} s)",
                429)
        return solicitada + self._margen_espera

    def _describir_error(self, respuesta):
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = None
        if isinstance(cuerpo, dict):
            if "error" in cuerpo:
                return str(cuerpo["error"])
            if "detail" in cuerpo:
                return str(cuerpo["detail"])
        return respuesta.reason or "respuesta inesperada del servicio"

    def listar_criptas(self):
        datos = self._pedir("listar criptas", "/criptas")
        return convertidorJson.resumen_criptas_desde_json(datos)

    def datos_generales(self, id_cripta):
        operacion = f"obtener los datos generales de '{id_cripta}'"
        ruta = "/criptas/" + quote(str(id_cripta), safe="")
        datos = self._pedir(operacion, ruta)
        dto = convertidorJson.datos_cripta_desde_json(datos)
        # Aquí aprendemos el presupuesto de la cripta (no viene de otro lado).
        self._contador.establecer_presupuesto(dto.presupuesto_solicitudes)
        return dto

    def esqueleto(self, id_cripta, pagina):
        operacion = f"descargar la página {pagina} del esqueleto de '{id_cripta}'"
        ruta = "/criptas/" + quote(str(id_cripta), safe="") + "/salas"
        datos = self._pedir(operacion, ruta, {"pagina": pagina})
        return convertidorJson.pagina_salas_desde_json(datos)

    def contenido(self, id_cripta, ids_salas):
        operacion = "descargar el contenido de las salas"
        validar_lote(operacion, ids_salas)    # antes de gastar presupuesto
        ruta = "/criptas/" + quote(str(id_cripta), safe="") + "/contenido"
        datos = self._pedir(operacion, ruta, {"salas": _unir_con_comas(ids_salas)})
        return convertidorJson.contenido_desde_json(datos)

    def catalogo(self, ids):
        operacion = "descargar fichas del catálogo"
        validar_lote(operacion, ids)          # antes de gastar presupuesto
        datos = self._pedir(operacion, "/catalogo", {"ids": _unir_con_comas(ids)})
        return convertidorJson.fichas_desde_json(datos)

    def version_cripta(self, id_cripta):
        operacion = f"consultar la versión de '{id_cripta}'"
        ruta = "/criptas/" + quote(str(id_cripta), safe="") + "/version"
        datos = self._pedir(operacion, ruta)
        return convertidorJson.version_desde_json(datos, operacion)

    def version_catalogo(self):
        operacion = "consultar la versión del catálogo"
        datos = self._pedir(operacion, "/catalogo/version")
        return convertidorJson.version_desde_json(datos, operacion)

    def solicitudes_realizadas(self):
        return self._contador.solicitudes_realizadas()

    def presupuesto(self):
        return self._contador.presupuesto()

    def reiniciar_conteo(self):
        self._contador.reiniciar()