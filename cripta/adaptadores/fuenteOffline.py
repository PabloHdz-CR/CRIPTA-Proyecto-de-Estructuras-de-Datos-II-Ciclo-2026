"""Adaptador de disco: implementa FuenteDatos leyendo un paquete de
respuestas previamente descargado (§3: modo --offline).

El contrato es EXACTAMENTE el mismo que ClienteHttp (FuenteDatos): el
modelo no sabe si los datos vinieron de HTTP o de archivos. Lo único que
cambia es de dónde sale el JSON de cada respuesta; la conversión a DTO usa
las MISMAS funciones de convertidorJson.py que usa ClienteHttp, así que el
formato de cada archivo es idéntico al de la respuesta real del API.

Organización en disco (un archivo por ENTIDAD, no por combinación de lote):
    <carpeta>/
        criptas.json                        {"criptas": [...]}
        criptas/<id_cripta>/
            general.json                    datos generales de la cripta
            version.json                    {"version": "..."}
            esqueleto/pagina_<n>.json       {"pagina", "total_paginas", "salas"}
            llaves.json                     {"llaves": [...]} (003-resolubilidad)
            contenido/<id_sala>.json        UNA sala: {"sala", "enemigos", ...}
        catalogo/
            version.json                    {"version": "..."}
            <id_ficha>.json                 UNA ficha

DECISIÓN: un archivo por sala y por ficha (y no un archivo por combinación
de ids pedida), igual que AlmacenLocalDisco con las fichas: el modelo puede
pedir contenido() o catalogo() con cualquier combinación de ids dentro del
lote, en cualquier orden, y esta forma la resuelve sin tener que adivinar de
antemano qué combinaciones se pedirán. Pedir 10 archivos chicos de disco no
tiene el costo de 10 solicitudes de red: no hace falta agrupar por lotes
aquí, agrupar solo importaba para ahorrar solicitudes HTTP (§4.2).
"""
import json
from pathlib import Path

from ..modelo.puertos.errores import ErrorDeRed
from ..modelo.puertos.fuenteDatos import FuenteDatos, validar_lote
from . import convertidorJson


def _nombre_seguro(id_texto) -> str:
    """Igual que en AlmacenLocalDisco: ids de catálogo pueden traer cualquier
    carácter; se reemplaza lo que no sea seguro en un nombre de archivo."""
    seguro = ""
    for caracter in str(id_texto):
        if caracter.isalnum() or caracter in "-_.":
            seguro += caracter
        else:
            seguro += "_"
    return seguro + ".json"


class FuenteOffline(FuenteDatos):
    """Lee desde una carpeta local el mismo contenido que ClienteHttp pediría
    por red. Nunca cuenta solicitudes ni tiene presupuesto (son conceptos de
    red): solicitudes_realizadas() siempre da 0, presupuesto() siempre da
    None, reiniciar_conteo() no hace nada (igual que documenta el puerto)."""

    def __init__(self, carpeta):
        self._carpeta = Path(carpeta)

    # ------------------------------------------------------------------
    # Lectura de disco (un único lugar: aquí se arma el dict que espera
    # convertidorJson, igual que clienteHttp con response.json())
    # ------------------------------------------------------------------

    def _leer(self, operacion, ruta_relativa):
        ruta = self._carpeta / ruta_relativa
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except FileNotFoundError as error:
            raise ErrorDeRed(
                operacion, f"no se encontró el archivo offline '{ruta_relativa}'") from error
        except (json.JSONDecodeError, OSError) as error:
            raise ErrorDeRed(
                operacion, f"el archivo offline '{ruta_relativa}' está dañado") from error

    # ------------------------------------------------------------------
    # Contrato FuenteDatos
    # ------------------------------------------------------------------

    def listar_criptas(self):
        datos = self._leer("listar criptas", "criptas.json")
        return convertidorJson.resumen_criptas_desde_json(datos)

    def datos_generales(self, id_cripta):
        operacion = f"obtener los datos generales de '{id_cripta}'"
        datos = self._leer(operacion, f"criptas/{id_cripta}/general.json")
        return convertidorJson.datos_cripta_desde_json(datos)

    def esqueleto(self, id_cripta, pagina):
        operacion = f"leer la página {pagina} del esqueleto de '{id_cripta}'"
        datos = self._leer(
            operacion, f"criptas/{id_cripta}/esqueleto/pagina_{pagina}.json")
        return convertidorJson.pagina_salas_desde_json(datos)

    def contenido(self, id_cripta, ids_salas):
        operacion = "leer el contenido de las salas"
        validar_lote(operacion, ids_salas)
        salas_json = []
        for id_sala in ids_salas:
            salas_json.append(self._leer(
                operacion, f"criptas/{id_cripta}/contenido/{id_sala}.json"))
        return convertidorJson.contenido_desde_json({"contenido": salas_json})

    def catalogo(self, ids):
        operacion = "leer fichas del catálogo"
        validar_lote(operacion, ids)
        fichas_json = []
        for id_ficha in ids:
            fichas_json.append(self._leer(
                operacion, "catalogo/" + _nombre_seguro(id_ficha)))
        return convertidorJson.fichas_desde_json({"entidades": fichas_json})

    def llaves(self, id_cripta):
        """La ubicación de llaves del paquete (FR-029). Si falta el archivo,
        ErrorDeRed como cualquier otro archivo: nunca se supone que la cripta
        no tiene llaves."""
        operacion = f"leer la ubicación de llaves de '{id_cripta}'"
        datos = self._leer(operacion, f"criptas/{id_cripta}/llaves.json")
        return convertidorJson.llaves_desde_json(datos)

    def version_cripta(self, id_cripta):
        operacion = f"leer la versión de '{id_cripta}'"
        datos = self._leer(operacion, f"criptas/{id_cripta}/version.json")
        return convertidorJson.version_desde_json(datos, operacion)

    def version_catalogo(self):
        operacion = "leer la versión del catálogo"
        datos = self._leer(operacion, "catalogo/version.json")
        return convertidorJson.version_desde_json(datos, operacion)

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass