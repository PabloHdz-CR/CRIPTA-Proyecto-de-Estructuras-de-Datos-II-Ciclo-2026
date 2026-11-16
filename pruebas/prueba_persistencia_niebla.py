"""US5: guardar y cargar el conocimiento (T039 de specs/002-niebla-guerra/tasks.md).

Cubre FR-012 y FR-013 (escenarios 3 y 4 de US5) y la segunda mitad de SC-003:
en las mismas 1000 secuencias de T038, guardar y cargar en un punto elegido
con la semilla devuelve el mismo conocimiento.
"""
import random
import tempfile
from pathlib import Path

from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.modelo.mundo.conocimiento import ABIERTA
from cripta.modelo.nucleo.accion import AbrirPuerta, Esperar
from cripta.modelo.puertos.errores import ErrorCripta, VersionIncompatible
from cripta.vista.comando import Comando

from pruebas.apoyo_niebla import (
    LLAVE, aplicar, aplicar_paso, cerrar_fuentes, controlador_sobre, dar_objeto, doble,
    encender_antorcha, huella_conocimiento, ids_conocidas, mover, partida_sobre, sala,
    sala_n, secuencias_sc003, servicio_niebla)

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE = RAIZ / "pruebas" / "datos" / "niebla" / "guardado_formato_2.bin"
SECUENCIAS = 1000
SEMILLA = 20261115


def guardar_y_cargar(partida, descripcion):
    ruta = Path(tempfile.mkdtemp(prefix="prueba_persistencia_niebla_")) / "partida.bin"
    PartidaBinaria.guardar(partida, ruta)
    return PartidaBinaria.cargar(ruta, servicio_niebla(descripcion)), ruta


def caso_us5_e3_guardar_y_cargar():
    """US5 escenario 3 (FR-012): exploradas, avistadas y un recuerdo
    desactualizado vuelven idénticos al cargar, también con cargar_sala."""
    a12, b21 = doble(1, "E", 2)
    a23, b32 = doble(2, "E", 3, cerrada=True, llave=LLAVE, cierre=200)
    descripcion = (sala_n(1, a12), sala_n(2, b21, a23), sala_n(3, b32))
    partida = partida_sobre(descripcion)
    dar_objeto(partida, LLAVE)
    mover(partida, "E")
    aplicar(partida, AbrirPuerta("E"))
    mover(partida, "O")
    puerta = sala(partida, 2).salida("E")
    while not puerta.cerrada:
        aplicar(partida, Esperar())
    assert puerta.recordada == ABIERTA, "recuerdo desactualizado antes de guardar"
    cargada, ruta = guardar_y_cargar(partida, descripcion)
    assert huella_conocimiento(cargada) == huella_conocimiento(partida), "FR-012: idéntico"
    assert sorted(ids_conocidas(cargada)) == sorted(ids_conocidas(partida)), "FR-012: registro"
    assert cargada.mundo.sala(2).salida("E").recordada == ABIERTA, "FR-012: recuerdo viejo"
    sola = PartidaBinaria.cargar_sala(ruta, 2, servicio_niebla(descripcion))
    assert sola.conocimiento == sala(partida, 2).conocimiento, "FR-012: cargar_sala"
    assert [s.recordada for s in sola.salidas if s is not None] == [
        s.recordada for s in sala(partida, 2).salidas if s is not None], "FR-012: cargar_sala"


def caso_sc003_guardar_en_mil_secuencias():
    """SC-003 (FR-012): en las mismas 1000 secuencias de T038, guardar y
    cargar en un punto elegido con la semilla devuelve el mismo conocimiento."""
    for numero, (descripcion, semilla, antorcha, acciones, fraccion) in enumerate(
            secuencias_sc003(SEMILLA, SECUENCIAS)):
        partida = partida_sobre(descripcion, semilla=semilla)
        dar_objeto(partida, LLAVE)
        if antorcha:
            encender_antorcha(partida)
        punto = int(fraccion * (len(acciones) + 1))
        azar = random.Random(semilla)
        for tipo in acciones[:punto]:
            aplicar_paso(partida, tipo, azar)
        cargada, _ = guardar_y_cargar(partida, descripcion)
        assert huella_conocimiento(cargada) == huella_conocimiento(partida), (
            f"SC-003: secuencia {numero}, punto {punto}")
        cerrar_fuentes()


def caso_us5_e4_formato_anterior():
    """US5 escenario 4 (FR-013; clarificación 4): el guardado de la versión 2
    se reporta incompatible, con las dos versiones, y no se carga."""
    try:
        PartidaBinaria.cargar(FIXTURE, servicio_niebla((sala_n(1),)))
    except VersionIncompatible as error:
        assert error.esperada == 3 and error.encontrada == 2, error
        assert "se esperaba 3 y se encontró 2" in str(error), str(error)
    else:
        raise AssertionError("FR-013: el formato 2 debía reportarse incompatible")


def caso_us5_e4_el_controlador_lo_muestra():
    """FR-013: el Controlador muestra el rechazo con mostrar_error."""
    controlador, vista, _ = controlador_sobre((sala_n(1),))

    class GestorViejo:
        def existe_guardado(self, id_cripta):
            return True

        def cargar(self, id_cripta, servicio, registro):
            return PartidaBinaria.cargar(FIXTURE, servicio)

    controlador._gestor_guardado = GestorViejo()
    controlador.procesar(Comando("cargar"))
    assert "se esperaba 3 y se encontró 2" in (vista.ultimo_error or ""), vista.ultimo_error


def caso_valores_fuera_de_rango():
    """FR-012: un conocimiento o un recuerdo fuera de rango es un archivo corrupto."""
    for campo in ("conocimiento", "recordada"):
        descripcion = (sala_n(1, doble(1, "E", 2)[0]), sala_n(2, doble(1, "E", 2)[1]))
        partida = partida_sobre(descripcion)
        if campo == "conocimiento":
            sala(partida, 2).conocimiento = 7
        else:
            sala(partida, 1).salida("E").recordada = 9
        try:
            guardar_y_cargar(partida, descripcion)
        except ErrorCripta as error:
            assert campo in str(error), str(error)
        else:
            raise AssertionError(f"FR-012: {campo} fuera de rango debía rechazarse")
        cerrar_fuentes()


CASOS = (caso_us5_e3_guardar_y_cargar, caso_sc003_guardar_en_mil_secuencias,
         caso_us5_e4_formato_anterior, caso_us5_e4_el_controlador_lo_muestra,
         caso_valores_fuera_de_rango)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_persistencia_niebla OK ({len(CASOS)} casos)")


main()
