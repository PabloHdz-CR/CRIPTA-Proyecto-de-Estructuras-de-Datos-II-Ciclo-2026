"""Consulta de la ubicación de llaves (003-resolubilidad, T021).

FR-025 a FR-031, SC-007, contracts/datos-llaves.md. Escenarios H4.E1 a
H4.E6 y los casos de NO_VERIFICADA.

Usa ServidorFalso (HTTP local, sin internet ni presupuesto real) y
FuenteOffline sobre carpetas temporales.

Uso: py -m pruebas.prueba_datos_llaves
"""
import json
import tempfile
from pathlib import Path

from cripta.adaptadores import convertidorJson
from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.puertos.dto import UbicacionLlaveDTO
from cripta.modelo.puertos.errores import DatosInvalidos
from cripta.modelo.resolubilidad.resultadoResolubilidad import NO_VERIFICADA
from cripta.modelo.resolubilidad.verificacion import verificar_cripta

from pruebas.apoyo_resolubilidad import Cripta, FuenteLlaves, abierta
from pruebas.prueba_falso_1_6 import ServidorFalso

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "pruebas" / "datos" / "resolubilidad"
LLAVES = [{"id": "itm_llave", "sala": 3}, {"id": "itm_x", "sala": 5, "enemigo": "e-5"},
          {"id": "itm_llave", "sala": 1}]


def carpeta_temporal(prefijo):
    return Path(tempfile.mkdtemp(prefix=prefijo))


class Montaje:
    """ServidorFalso + ClienteHttp + ServicioDatos, con el almacén en una
    carpeta temporal (o la que se pase, para probar la caché en disco)."""

    def __init__(self, presupuesto=40, llaves=None, cuerpo_llaves=None, carpeta=None):
        self.servidor = ServidorFalso(presupuesto=presupuesto, llaves=llaves or LLAVES,
                                      cuerpo_llaves=cuerpo_llaves)
        self.contador = ContadorSolicitudes()
        self.cliente = ClienteHttp(self.servidor.base_url, self.contador, margen_espera=0)
        self.asincrona = FuenteAsincrona(self.cliente)
        self.carpeta = carpeta or carpeta_temporal("prueba_datos_llaves_")
        self.servicio = ServicioDatos(self.cliente, self.asincrona, CacheFichas(25),
                                      AlmacenLocalDisco(self.carpeta))

    def rutas_llaves(self):
        return [r for r in self.servidor.rutas_recibidas() if r.endswith("/llaves")]

    def cerrar(self):
        self.asincrona.cerrar()
        self.cliente.cerrar()
        self.servidor.cerrar()


def como_tuplas(ubicaciones):
    return [(u.id, u.sala, u.enemigo) for u in ubicaciones]


def prueba_h4_e1_cuenta_en_el_presupuesto():
    # H4.E1 (FR-025, FR-026): una consulta, que cuenta como una solicitud; un
    # 429 reintentado cuenta dos.
    montaje = Montaje()
    try:
        montaje.cliente.datos_generales(montaje.servidor.id_cripta)
        antes = montaje.cliente.solicitudes_realizadas()
        ubicaciones = montaje.cliente.llaves(montaje.servidor.id_cripta)
        assert montaje.cliente.solicitudes_realizadas() == antes + 1
        assert como_tuplas(ubicaciones) == [("itm_llave", 3, None), ("itm_x", 5, "e-5"),
                                            ("itm_llave", 1, None)]
        montaje.servidor.inyectar_429(1)
        montaje.cliente.llaves(montaje.servidor.id_cripta)
        assert montaje.cliente.solicitudes_realizadas() == antes + 3
    finally:
        montaje.cerrar()


def prueba_h4_e2_cache_misma_version():
    # H4.E2 (FR-027, SC-007): con la misma versión no se vuelve a pedir, ni en
    # memoria ni desde el disco en una sesión nueva.
    montaje = Montaje()
    try:
        montaje.servicio.iniciar_cripta(montaje.servidor.id_cripta)
        primera = montaje.servicio.ubicacion_llaves()
        segunda = montaje.servicio.ubicacion_llaves()
        assert como_tuplas(primera) == como_tuplas(segunda)
        assert len(montaje.rutas_llaves()) == 1
        carpeta = montaje.carpeta
    finally:
        montaje.cerrar()
    otro = Montaje(carpeta=carpeta)
    try:
        otro.servicio.iniciar_cripta(otro.servidor.id_cripta)
        assert como_tuplas(otro.servicio.ubicacion_llaves()) == como_tuplas(primera)
        assert otro.rutas_llaves() == [], otro.rutas_llaves()
    finally:
        otro.cerrar()


def prueba_h4_e3_otra_version_se_pide():
    # H4.E3 (FR-027, FR-028): lo guardado con otra versión (por ejemplo, de la
    # primera parte) se invalida por la validación de versión y se pide de
    # nuevo; el archivo queda con la versión actual.
    carpeta = carpeta_temporal("prueba_datos_llaves_version_")
    AlmacenLocalDisco(carpeta).guardar_llaves("cripta-test", "v-vieja", convertidorJson.llaves_desde_json(
        {"llaves": [{"id": "itm_vieja", "sala": 2}]}))
    montaje = Montaje(carpeta=carpeta)
    try:
        montaje.servicio.iniciar_cripta(montaje.servidor.id_cripta)
        ubicaciones = montaje.servicio.ubicacion_llaves()
        assert len(montaje.rutas_llaves()) == 1
        assert "itm_vieja" not in [u.id for u in ubicaciones]
        guardado = AlmacenLocalDisco(carpeta).cargar_llaves("cripta-test", "v-test-1")
        assert guardado is not None and como_tuplas(guardado) == como_tuplas(ubicaciones)
        assert AlmacenLocalDisco(carpeta).cargar_llaves("cripta-test", "v-vieja") is None
    finally:
        montaje.cerrar()


def prueba_h4_e4_en_linea_igual_que_sin_conexion():
    # H4.E4 (FR-029): la fuente en línea y la sin conexión, sobre el mismo
    # JSON de la misma versión, entregan las mismas ubicaciones.
    carpeta = carpeta_temporal("prueba_datos_llaves_offline_")
    archivo = carpeta / "criptas" / "cripta-test" / "llaves.json"
    archivo.parent.mkdir(parents=True)
    archivo.write_text(json.dumps({"llaves": LLAVES}), encoding="utf-8")
    montaje = Montaje()
    try:
        en_linea = montaje.cliente.llaves("cripta-test")
    finally:
        montaje.cerrar()
    sin_conexion = FuenteOffline(carpeta).llaves("cripta-test")
    assert como_tuplas(en_linea) == como_tuplas(sin_conexion)
    assert list(en_linea)[1] == UbicacionLlaveDTO(id="itm_x", sala=5, enemigo="e-5")


def prueba_h4_e5_respuestas_mal_formadas():
    # H4.E5 (FR-030): cada caso de contracts/datos-llaves.md es un error de
    # datos explícito que nombra la entrada; nunca se descarta en silencio.
    casos = [
        ({"otra": []}, "llaves"),
        ({"llaves": {"id": "x"}}, "llaves"),
        ({"llaves": ["texto"]}, "entrada 0"),
        ({"llaves": [{"sala": 1}]}, "entrada 0"),
        ({"llaves": [{"id": "", "sala": 1}]}, "entrada 0"),
        ({"llaves": [{"id": 7, "sala": 1}]}, "entrada 0"),
        ({"llaves": [{"id": "a", "sala": 1}, {"id": "b"}]}, "entrada 1"),
        ({"llaves": [{"id": "a", "sala": True}]}, "entrada 0"),
        ({"llaves": [{"id": "a", "sala": "3"}]}, "entrada 0"),
        ({"llaves": [{"id": "a", "sala": 1, "enemigo": 5}]}, "entrada 0"),
    ]
    for datos, nombra in casos:
        try:
            convertidorJson.llaves_desde_json(datos)
        except DatosInvalidos as error:
            assert nombra in str(error), (datos, str(error))
        else:
            raise AssertionError(f"debía fallar: {datos}")
    # Campos extra se ignoran; ids repetidos son varias ubicaciones (FR-016);
    # enemigo null es "en el suelo".
    validas = convertidorJson.llaves_desde_json({"llaves": [
        {"id": "a", "sala": 1, "extra": 9}, {"id": "a", "sala": 2, "enemigo": None}]})
    assert como_tuplas(validas) == [("a", 1, None), ("a", 2, None)]
    # Una sala inexistente en el esqueleto: verificar_cripta da NO_VERIFICADA
    # y su error nombra la entrada y la sala (FR-030, FR-031).
    cripta = Cripta([(1, [abierta("E", 2)]), (2, [abierta("O", 1)])], sala_salida=2,
                    llave_salida="itm_s", ubicaciones=[("itm_s", 99)])
    resultado = verificar_cripta(servicio_memoria(FuenteLlaves(cripta)))
    assert resultado.veredicto == NO_VERIFICADA
    assert "99" in resultado.error and "itm_s" in resultado.error, resultado.error


def prueba_h4_e6_presupuesto_insuficiente():
    # H4.E6 (FR-026, FR-031): iniciar la cripta gasta 5 solicitudes (datos,
    # versión del catálogo y 3 páginas); con presupuesto 5 la consulta de
    # llaves no se hace, no se supera el presupuesto y el resultado es
    # NO_VERIFICADA.
    montaje = Montaje(presupuesto=5)
    try:
        montaje.servicio.iniciar_cripta(montaje.servidor.id_cripta)
        assert montaje.cliente.solicitudes_realizadas() == 5
        resultado = verificar_cripta(montaje.servicio)
        assert resultado.veredicto == NO_VERIFICADA, resultado
        assert montaje.cliente.solicitudes_realizadas() <= 5
        assert montaje.servidor.total_recibidas() <= 5
    finally:
        montaje.cerrar()


def servicio_memoria(fuente):
    from pruebas.apoyo_terreno import servicio_sobre
    servicio = servicio_sobre(fuente)
    servicio.iniciar_cripta(fuente.datos_generales(None).id)
    return servicio


def prueba_no_verificada_sin_archivo_offline():
    # FR-029, FR-031: sin llaves.json en el paquete sin conexión, NO_VERIFICADA;
    # nunca se supone que la cripta no tiene llaves.
    fuente = FuenteOffline(PAQUETE)
    servicio = ServicioDatos(fuente, FuenteAsincrona(fuente), CacheFichas(25),
                             AlmacenLocalDisco(carpeta_temporal("prueba_datos_llaves_sin_")))
    servicio.iniciar_cripta("res-sin-llaves")
    resultado = verificar_cripta(servicio)
    assert resultado.veredicto == NO_VERIFICADA
    assert "llaves.json" in resultado.error, resultado.error


def prueba_no_verificada_error_de_red_y_datos():
    # FR-031: un error de red o una respuesta inválida dan NO_VERIFICADA.
    cripta = Cripta([(1, [abierta("E", 2)]), (2, [])], sala_salida=2, llave_salida="itm_s")
    assert verificar_cripta(servicio_memoria(FuenteLlaves(cripta, sin_llaves=True))).veredicto \
        == NO_VERIFICADA
    montaje = Montaje(cuerpo_llaves={"llaves": [{"id": "x"}]})
    try:
        montaje.servicio.iniciar_cripta(montaje.servidor.id_cripta)
        resultado = verificar_cripta(montaje.servicio)
        assert resultado.veredicto == NO_VERIFICADA and "entrada 0" in resultado.error
    finally:
        montaje.cerrar()


def prueba_cache_danada_se_ignora():
    # FR-027: un archivo de caché dañado se trata como no encontrado.
    carpeta = carpeta_temporal("prueba_datos_llaves_danado_")
    (carpeta / "llaves").mkdir(parents=True, exist_ok=True)
    (carpeta / "llaves" / "cripta-test.json").write_text("{no es json", encoding="utf-8")
    assert AlmacenLocalDisco(carpeta).cargar_llaves("cripta-test", "v-test-1") is None
    montaje = Montaje(carpeta=carpeta)
    try:
        montaje.servicio.iniciar_cripta(montaje.servidor.id_cripta)
        montaje.servicio.ubicacion_llaves()
        assert len(montaje.rutas_llaves()) == 1
    finally:
        montaje.cerrar()


def main():
    from pruebas.apoyo_terreno import cerrar_fuentes
    pruebas = [valor for nombre, valor in sorted(globals().items())
               if nombre.startswith("prueba_") and callable(valor)]
    try:
        for prueba in pruebas:
            prueba()
            print(f"  ok  {prueba.__name__}")
    finally:
        cerrar_fuentes()
    print(f"prueba_datos_llaves: {len(pruebas)} casos OK")


if __name__ == "__main__":
    main()
