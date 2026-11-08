"""--verificar ID (003-resolubilidad, T042).

FR-022 a FR-024, SC-006, contracts/linea-de-comandos.md. Escenarios H3.E1 a
H3.E3:
  - H3.E1: el reporte sale por la terminal; no se crean partidas/,
    guardados/ ni puntajes.jsonl, y la Vista (arcade) no se importa;
  - H3.E2: códigos 0 (resoluble), 1 (no resoluble) y 2 (no se pudo
    verificar, o falta el ID); --forzar no los cambia;
  - H3.E3: el texto sin conexión es idéntico al obtenido en línea (contra
    ServidorFalso) para la misma versión de la cripta.

Uso: py -m pruebas.prueba_verificar
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "pruebas" / "datos" / "resolubilidad"
MAIN = RAIZ / "main.py"


def correr(*argumentos):
    """main.py en un subproceso con un directorio de trabajo temporal."""
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_verificar_"))
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    resultado = subprocess.run([sys.executable, str(MAIN)] + list(argumentos), cwd=carpeta,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=entorno, timeout=120)
    return resultado, carpeta


def h3_e1_y_e2_por_terminal():
    offline = f"--offline={PAQUETE}"
    casos = (("res-cadena", 0, "Cripta res-cadena (versión v1): RESOLUBLE"),
             ("res-autociclo", 1, "Cripta res-autociclo (versión v1): NO RESOLUBLE"),
             ("res-sin-llaves", 2, "Cripta res-sin-llaves: NO SE PUDO VERIFICAR"))
    for id_cripta, codigo, primera in casos:
        for extra in ((), ("--forzar",)):
            resultado, carpeta = correr("--verificar", id_cripta, offline, *extra)
            salida = resultado.stdout + resultado.stderr
            assert resultado.returncode == codigo, (id_cripta, extra, resultado.returncode, salida)
            assert primera in resultado.stdout, (id_cripta, salida)
            # H3.E1, FR-023: ni partida, ni log, ni puntaje.
            for nombre in ("partidas", "guardados", "puntajes.jsonl"):
                assert not (carpeta / nombre).exists(), (id_cripta, nombre)
    # El orden de llaves sale completo en la terminal.
    resultado, _ = correr("--verificar", "res-cadena", offline)
    for linea in ("  1. itm_res_a: sala 1", "  2. itm_res_b: sala 2",
                  "  3. itm_res_salida: sala 3"):
        assert linea in resultado.stdout, resultado.stdout
    # Sin ID: código 2 y el mensaje de uso.
    resultado, _ = correr("--verificar")
    assert resultado.returncode == 2, resultado.returncode
    assert "uso" in (resultado.stdout + resultado.stderr).lower()


def h3_e1_sin_vista_en_el_mismo_proceso():
    # FR-023, principio III: --verificar no importa la Vista.
    from cripta.controlador.fabricaAplicacion import FabricaAplicacion
    anterior = os.getcwd()
    os.chdir(tempfile.mkdtemp(prefix="prueba_verificar_proceso_"))
    try:
        try:
            FabricaAplicacion(("--verificar", "res-ciclo-dos", f"--offline={PAQUETE}")).ejecutar()
        except SystemExit as salida:
            codigo = salida.code
        else:
            raise AssertionError("--verificar debía terminar con sys.exit")
    finally:
        os.chdir(anterior)
    assert codigo == 1, codigo
    assert "arcade" not in sys.modules, "--verificar importó la Vista"


def paquete_desde_servidor(servidor):
    """Un paquete sin conexión con exactamente lo que responde ServidorFalso
    (datos generales, versión, páginas del esqueleto y llaves)."""
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_verificar_espejo_"))
    id_cripta = servidor.id_cripta

    def escribir(relativa, ruta_api):
        codigo, cuerpo = servidor._resolver(urlparse(ruta_api))
        assert codigo == 200, (ruta_api, codigo)
        destino = carpeta / relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(cuerpo), encoding="utf-8")
        return cuerpo

    escribir("criptas.json", "/v1/criptas")
    general = escribir(f"criptas/{id_cripta}/general.json", f"/v1/criptas/{id_cripta}")
    escribir(f"criptas/{id_cripta}/version.json", f"/v1/criptas/{id_cripta}/version")
    for pagina in range(1, general["paginas"] + 1):
        escribir(f"criptas/{id_cripta}/esqueleto/pagina_{pagina}.json",
                 f"/v1/criptas/{id_cripta}/salas?pagina={pagina}")
    escribir(f"criptas/{id_cripta}/llaves.json", f"/v1/criptas/{id_cripta}/llaves")
    escribir("catalogo/version.json", "/v1/catalogo/version")
    return carpeta


def lineas_de_modo(fuente, id_cripta):
    from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
    from cripta.controlador.bench.reporte import Reporte
    from cripta.controlador.modoVerificar import ModoVerificar
    from cripta.controlador.reporteFinal import ReporteFinal
    from cripta.modelo.datos.cacheFichas import CacheFichas
    from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
    from cripta.modelo.datos.servicioDatos import ServicioDatos
    asincrona = FuenteAsincrona(fuente)
    try:
        servicio = ServicioDatos(fuente, asincrona, CacheFichas(25), AlmacenLocalDisco(
            Path(tempfile.mkdtemp(prefix="prueba_verificar_fichas_"))))
        modo = ModoVerificar(servicio, Reporte(imprimir=False),
                             ReporteFinal(Reporte(imprimir=False)))
        codigo = modo.ejecutar(id_cripta)
        return codigo, list(modo.lineas)
    finally:
        asincrona.cerrar()


def h3_e3_en_linea_igual_que_sin_conexion():
    # H3.E3 (FR-022, FR-029): mismo texto con --offline y en línea.
    from cripta.adaptadores.clienteHttp import ClienteHttp
    from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
    from cripta.adaptadores.fuenteOffline import FuenteOffline
    from pruebas.prueba_falso_1_6 import ServidorFalso
    # La cripta lineal de ServidorFalso: la llave de salida en la sala 3; la
    # sala 25 (salida) no tiene puerta que la requiera: NO_RESOLUBLE (b).
    servidor = ServidorFalso(presupuesto=40, llaves=[{"id": "itm_llave", "sala": 3}])
    cliente = ClienteHttp(servidor.base_url, ContadorSolicitudes(), margen_espera=0)
    try:
        en_linea = lineas_de_modo(cliente, servidor.id_cripta)
        sin_conexion = lineas_de_modo(FuenteOffline(paquete_desde_servidor(servidor)),
                                      servidor.id_cripta)
    finally:
        cliente.cerrar()
        servidor.cerrar()
    assert en_linea == sin_conexion, (en_linea, sin_conexion)
    codigo, lineas = en_linea
    assert codigo == 1, codigo
    assert lineas[0] == "Cripta cripta-test (versión v-test-1): NO RESOLUBLE", lineas


def main():
    h3_e1_y_e2_por_terminal()
    print("  ok  H3.E1 y H3.E2 por terminal")
    h3_e3_en_linea_igual_que_sin_conexion()
    print("  ok  H3.E3 en línea igual que sin conexión")
    h3_e1_sin_vista_en_el_mismo_proceso()
    print("  ok  H3.E1 sin Vista en el mismo proceso")
    print("prueba_verificar OK")


if __name__ == "__main__":
    main()
