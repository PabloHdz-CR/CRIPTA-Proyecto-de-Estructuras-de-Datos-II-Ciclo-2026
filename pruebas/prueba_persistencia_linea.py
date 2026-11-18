"""T025 (004-linea-tiempo, US4): guardar y cargar conserva la línea de tiempo
(formato 4).

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_persistencia_linea
"""
import random
import tempfile
from pathlib import Path

from cripta.adaptadores import partidaBinaria
from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.modelo.nucleo.accion import UsarPergamino
from cripta.modelo.nucleo.diario import Diario
from cripta.modelo.puertos.errores import VersionIncompatible
from pruebas.apoyo_linea import (
    OraculoVivo, accion_al_azar, cripta_linea, huella_partida, partida_con_linea,
    secuencia_al_azar)
from pruebas.apoyo_niebla import PERGAMINO, cerrar_fuentes, dar_objeto, pasillo_n

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE_3 = RAIZ / "pruebas" / "datos" / "linea" / "guardado_formato_3.bin"


def ruta_temporal() -> Path:
    return Path(tempfile.mkdtemp(prefix="persistencia_linea_")) / "partida.bin"


def guardar_y_cargar(partida):
    ruta = ruta_temporal()
    PartidaBinaria.guardar(partida, ruta)
    cargada = PartidaBinaria.cargar(ruta, partida.servicio)
    cargada.conectar_diario(Diario())
    return cargada


def todas_las_consultas(partida) -> list:
    """Las huellas de toda consulta: #1 a #(n+1) y cada 25 de tiempo hasta el reloj."""
    linea = partida.linea
    huellas = [huella_partida(linea.reconstruir_accion(k, partida))
               for k in range(1, linea.acciones + 2)]
    huellas += [huella_partida(linea.reconstruir_instante(t, partida))
                for t in range(0, partida.reloj + 1, 25)]
    return huellas


def partida_jugada(semilla, n=80, k=6):
    partida = partida_con_linea(cripta_linea(semilla), k=k, semilla=semilla)
    for _ in range(3):
        dar_objeto(partida, PERGAMINO)
    oraculo = OraculoVivo(partida)
    secuencia_al_azar(oraculo, random.Random(semilla), n)
    return partida, oraculo


def caso_e1_mismas_consultas():
    """US4 escenario 1 (FR-009): con pergaminos y viajes, guardar y cargar da
    el mismo resumen en todos los instantes y números de acción."""
    partida, _ = partida_jugada(71)
    antes = todas_las_consultas(partida)
    cargada = guardar_y_cargar(partida)
    assert cargada.linea is not None, "FR-009: la carga no trajo la línea"
    assert cargada.linea.acciones == partida.linea.acciones
    assert todas_las_consultas(cargada) == antes, "FR-009: una consulta cambió al cargar"


def caso_e2_formato_anterior():
    """US4 escenario 2 (FR-010; Apéndice B 6): un archivo de la versión 3 se
    reporta incompatible con las dos versiones y no se carga."""
    partida = partida_con_linea(pasillo_n(3), k=5)
    try:
        PartidaBinaria.cargar(FIXTURE_3, partida.servicio)
        raise AssertionError("FR-010: el formato 3 debió rechazarse")
    except VersionIncompatible as error:
        assert error.esperada == partidaBinaria.FORMATO_VERSION == 4 and error.encontrada == 3
        assert "se esperaba 4 y se encontró 3" in str(error), str(error)


def caso_e3_historia_continua():
    """US4 escenario 3 (FR-009): después de cargar se sigue jugando; las
    consultas de antes y de después de la carga dan lo mismo que sin cargar."""
    original, _ = partida_jugada(72, n=40)
    cargada = guardar_y_cargar(original)
    azar_a, azar_b = random.Random(5), random.Random(5)
    for _ in range(30):
        original.aplicar_accion(accion_al_azar(original, azar_a, con_pergaminos=False))
        cargada.aplicar_accion(accion_al_azar(cargada, azar_b, con_pergaminos=False))
    assert todas_las_consultas(cargada) == todas_las_consultas(original), (
        "FR-009: la historia no es continua en el punto de la carga")


def caso_borde_pergamino_tras_cargar():
    """Caso borde (análisis G4): el historial del pergamino no se guarda
    (primera parte); justo después de cargar el pergamino no tiene nada que
    revertir y las consultas de antes de la carga siguen iguales."""
    partida, _ = partida_jugada(73, n=30)
    antes = todas_las_consultas(partida)
    cargada = guardar_y_cargar(partida)
    resultado = cargada.aplicar_accion(UsarPergamino())
    assert not resultado.aceptada, "sin historial del pergamino después de cargar"
    assert todas_las_consultas(cargada) == antes


def caso_cargar_sala_no_lee_la_linea():
    """Análisis F1: cargar_sala lee solo el encabezado, el índice y su sala: la
    cantidad de bytes no depende del tamaño de la línea."""
    leidos = []
    abrir_original = open

    class ArchivoContado:
        def __init__(self, archivo):
            self._archivo = archivo

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self._archivo.close()

        def seek(self, posicion):
            return self._archivo.seek(posicion)

        def read(self, cantidad=-1):
            datos = self._archivo.read(cantidad)
            leidos.append(len(datos))
            return datos

    def bytes_de_cargar_sala(partida):
        ruta = ruta_temporal()
        PartidaBinaria.guardar(partida, ruta)
        leidos.clear()
        partidaBinaria.open = lambda r, modo="r": ArchivoContado(abrir_original(r, modo))
        try:
            PartidaBinaria.cargar_sala(ruta, partida.mundo.sala_inicial, partida.servicio)
        finally:
            del partidaBinaria.open
        return sum(leidos), ruta.stat().st_size

    corta = partida_con_linea(cripta_linea(74), k=1, semilla=74)
    larga = partida_con_linea(cripta_linea(74), k=1, semilla=74)
    secuencia_al_azar(OraculoVivo(larga), random.Random(1), 200, con_pergaminos=False,
                      con_viajes=False)
    bytes_corta, tamano_corta = bytes_de_cargar_sala(corta)
    bytes_larga, tamano_larga = bytes_de_cargar_sala(larga)
    assert tamano_larga > tamano_corta * 20, (tamano_corta, tamano_larga)
    assert bytes_larga <= bytes_corta + 2048, (
        f"F1: cargar_sala leyó {bytes_larga} bytes con la línea larga y {bytes_corta} sin ella")


def caso_sc005_mil_secuencias():
    """SC-005: 1000 secuencias con semilla con un guardar y cargar en un punto
    elegido con la semilla: ninguna consulta cambia respecto de no cargar."""
    descripcion = cripta_linea(75, lado=4)
    for semilla in range(1000):
        azar_a, azar_b = random.Random(semilla), random.Random(semilla)
        sin = partida_con_linea(descripcion, k=3, semilla=semilla % 5 + 1)
        con = partida_con_linea(descripcion, k=3, semilla=semilla % 5 + 1)
        punto = semilla % 8
        for paso in range(8):
            if paso == punto:
                con = guardar_y_cargar(con)
            sin.aplicar_accion(accion_al_azar(sin, azar_a, con_pergaminos=False))
            con.aplicar_accion(accion_al_azar(con, azar_b, con_pergaminos=False))
        assert huella_partida(con) == huella_partida(sin), f"SC-005 semilla {semilla}"
        k = semilla % (sin.linea.acciones + 1) + 1
        assert huella_partida(con.linea.reconstruir_accion(k, con)) == \
            huella_partida(sin.linea.reconstruir_accion(k, sin)), f"SC-005 semilla {semilla} #{k}"
        t = semilla * 37 % (sin.reloj + 1)
        assert huella_partida(con.linea.reconstruir_instante(t, con)) == \
            huella_partida(sin.linea.reconstruir_instante(t, sin)), f"SC-005 semilla {semilla} t={t}"


CASOS = (caso_e1_mismas_consultas, caso_e2_formato_anterior, caso_e3_historia_continua,
         caso_borde_pergamino_tras_cargar, caso_cargar_sala_no_lee_la_linea,
         caso_sc005_mil_secuencias)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}", flush=True)
    finally:
        cerrar_fuentes()
    print(f"prueba_persistencia_linea OK ({len(CASOS)} casos)")
