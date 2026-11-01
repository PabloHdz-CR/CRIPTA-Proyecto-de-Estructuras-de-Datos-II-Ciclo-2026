"""Fuente en línea y sin conexión entregan los mismos costos (001-terreno-cazador).

Requisitos que ejerce: FR-019 (el esqueleto acepta el campo costo opcional) y
FR-021 (las fuentes en línea y sin conexión entregan los mismos costos para
la misma versión de cripta).

La fuente en línea es ClienteHttp contra ServidorFalso (de
pruebas/prueba_falso_1_6.py, como en prueba_falso_1_9), con una subclase que
sirve las páginas de esqueleto del paquete pruebas/datos/terreno_cazador. La
fuente sin conexión es FuenteOffline sobre ese mismo paquete. Las dos pasan
por el mismo convertidor, y deben dar el mismo SalidaDTO.costo en cada salida
y el mismo costo efectivo después de Mundo.enlazar().

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_fuentes_costos
"""
import json

from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.modelo.mundo.mundo import Mundo
from pruebas.apoyo_terreno import CARPETA_TERRENO
from pruebas.prueba_falso_1_6 import ServidorFalso

ID = "terreno-a"


def leer_paquete(relativa):
    return json.loads((CARPETA_TERRENO / relativa).read_text(encoding="utf-8"))


class ServidorTerreno(ServidorFalso):
    """ServidorFalso que sirve las páginas de esqueleto y los datos generales
    de una cripta del paquete de prueba, tal cual están en disco."""

    def __init__(self, id_cripta):
        general = leer_paquete(f"criptas/{id_cripta}/general.json")
        super().__init__(id_cripta=id_cripta, total_salas=general["salas_total"],
                         salas_por_pagina=general["salas_por_pagina"], presupuesto=100)
        self._general = general

    def _datos_generales(self):
        return self._general

    def _pagina(self, consulta):
        pagina = int(consulta.get("pagina", ["1"])[0])
        ruta = CARPETA_TERRENO / f"criptas/{self.id_cripta}/esqueleto/pagina_{pagina}.json"
        if not ruta.exists():
            return 404, {"detail": "página fuera de rango"}
        return 200, json.loads(ruta.read_text(encoding="utf-8"))


def costos_declarados(fuente, datos):
    """{(sala, dirección): SalidaDTO.costo} de todas las páginas del esqueleto."""
    resultado = {}
    for pagina in range(1, datos.paginas + 1):
        for sala in fuente.esqueleto(ID, pagina).salas:
            for salida in sala.salidas:
                resultado[(sala.id, salida.direccion)] = salida.costo
    return resultado


def costos_efectivos(fuente, datos):
    """{(sala, dirección): Salida.costo} después de Mundo.enlazar()."""
    mundo = Mundo(datos)
    for pagina in range(1, datos.paginas + 1):
        mundo.agregar_esqueleto(fuente.esqueleto(ID, pagina).salas)
    mundo.enlazar()
    resultado = {}
    for sala in mundo:
        for salida in sala.salidas:
            if salida is not None:
                resultado[(sala.id, salida.direccion)] = salida.costo
    return resultado


# Lo que declara terreno-a (T004) y lo que vale después del enlace.
DECLARADOS = {
    (1, "N"): None, (1, "E"): 300,
    (2, "S"): None, (2, "N"): 1, (2, "E"): 250,
    (3, "O"): 300, (3, "N"): 50,
    (4, "S"): None, (4, "E"): None,
    (5, "O"): 250, (5, "S"): 50, (5, "N"): None,
    (6, "S"): None, (6, "E"): None,
    (7, "O"): None,
}
EFECTIVOS = {
    (1, "N"): 100, (1, "E"): 300,
    (2, "S"): 100, (2, "N"): 1, (2, "E"): 250,
    (3, "O"): 300, (3, "N"): 50,
    (4, "S"): 1,                    # de la contraparte 2 —N→ 4 (una sola cara declara)
    (4, "E"): 100,                  # un solo sentido, sin costo
    (5, "O"): 250, (5, "S"): 50, (5, "N"): 100,
    (6, "S"): 100, (6, "E"): 100,
    (7, "O"): 100,
}


def main():
    servidor = ServidorTerreno(ID)
    try:
        cliente = ClienteHttp(servidor.base_url, ContadorSolicitudes(), margen_espera=0)
        offline = FuenteOffline(CARPETA_TERRENO)
        datos_linea = cliente.datos_generales(ID)
        datos_offline = offline.datos_generales(ID)
        assert datos_linea == datos_offline

        # FR-021, FR-019: el mismo SalidaDTO.costo en cada salida, y el esperado.
        declarados_linea = costos_declarados(cliente, datos_linea)
        declarados_offline = costos_declarados(offline, datos_offline)
        assert declarados_linea == declarados_offline, (declarados_linea, declarados_offline)
        assert declarados_offline == DECLARADOS, declarados_offline

        # FR-021: el mismo costo efectivo después del enlace, y el esperado.
        efectivos_linea = costos_efectivos(cliente, datos_linea)
        efectivos_offline = costos_efectivos(offline, datos_offline)
        assert efectivos_linea == efectivos_offline, (efectivos_linea, efectivos_offline)
        assert efectivos_offline == EFECTIVOS, efectivos_offline
    finally:
        servidor.cerrar()
    print("prueba_fuentes_costos OK")


main()
