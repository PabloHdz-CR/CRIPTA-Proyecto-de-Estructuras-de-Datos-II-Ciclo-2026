"""T010 (004-linea-tiempo, FR-012): el servicio de las copias de la línea de
tiempo no hace solicitudes ni gasta presupuesto.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_servicio_solo_lectura
"""
from cripta.modelo.datos.servicioSoloLectura import ServicioSoloLectura
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.nucleo.partida import Partida
from cripta.modelo.puertos.errores import ErrorCripta
from pruebas.apoyo_niebla import PERGAMINO, RATA, cerrar_fuentes, pasillo_n, servicio_niebla


class RegistroFalso:
    """Lo único que el servicio le pide a la línea: el contenido inicial que
    registró de una sala (o None)."""

    def __init__(self, id_sala, contenido) -> None:
        self._id = id_sala
        self._contenido = contenido

    def contenido_registrado(self, id_sala):
        return self._contenido if id_sala == self._id else None


def lista(*elementos) -> ListaEnlazada:
    resultado = ListaEnlazada()
    for elemento in elementos:
        resultado.agregar_al_final(elemento)
    return resultado


def preparar():
    servicio = servicio_niebla(pasillo_n(4))
    partida = Partida(servicio)
    partida.iniciar(1)                       # carga el contenido de la sala 1
    return servicio


def caso_contenido():
    """FR-012: el contenido sale de la memoria del servicio o del registro de
    la línea; si no está, error claro y ninguna solicitud."""
    servicio = preparar()
    antes = servicio.solicitudes_realizadas()
    contenido_1 = servicio.contenido_en_memoria(1)
    assert contenido_1 is not None
    registro = RegistroFalso(4, contenido_1)
    solo = ServicioSoloLectura(servicio, registro)
    assert solo.asegurar_contenido(1) is contenido_1
    assert solo.asegurar_contenido(4) is contenido_1, "debió salir del registro de la línea"
    try:
        solo.asegurar_contenido(3)
        raise AssertionError("FR-012: una sala sin contenido en memoria debió fallar")
    except ErrorCripta as error:
        assert "3" in str(error), str(error)
    solo.precargar(2)
    solo.precargar(3)
    assert servicio.solicitudes_realizadas() == antes, "FR-012: hubo solicitudes"


def caso_fichas():
    """FR-012: las fichas salen de memoria o disco, sin tocar la red ni la
    estadística de la caché; una ficha que no está da error claro."""
    servicio = preparar()
    servicio.resolver_fichas(lista(RATA, PERGAMINO))     # quedan en la caché real
    antes = servicio.solicitudes_realizadas()
    aciertos, fallos = servicio.aciertos_cache(), servicio.fallos_cache()
    solo = ServicioSoloLectura(servicio, None)
    fichas = solo.resolver_fichas(lista(PERGAMINO, RATA))
    assert [f.id for f in fichas] == [PERGAMINO, RATA]
    try:
        solo.resolver_fichas(lista("ficha_que_no_existe"))
        raise AssertionError("FR-012: una ficha ausente debió fallar")
    except ErrorCripta as error:
        assert "ficha_que_no_existe" in str(error), str(error)
    assert servicio.solicitudes_realizadas() == antes, "FR-012: hubo solicitudes"
    assert (servicio.aciertos_cache(), servicio.fallos_cache()) == (aciertos, fallos), (
        "FR-011: la consulta cambió la estadística de la caché")


CASOS = (caso_contenido, caso_fichas)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}")
    finally:
        cerrar_fuentes()
    print(f"prueba_servicio_solo_lectura OK ({len(CASOS)} casos)")
