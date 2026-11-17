"""Genera el fixture pruebas/datos/terreno_cazador/guardado_formato_anterior.bin
(T003 de specs/001-terreno-cazador/tasks.md, FR-022).

Es una partida guardada con el formato de archivo ANTERIOR a 001-terreno-cazador
(FORMATO_VERSION = 1, sin costo por salida). La usa prueba_persistencia_cazador
(T047(b)) para comprobar que un archivo del formato anterior se reporta
incompatible (VersionIncompatible) y no se migra en silencio (principio V).

No es una prueba y no va en ejecutar_pruebas.py: se corrió una vez, con el
código anterior a la feature, y el .bin quedó confirmado en git. Volver a
correrlo después de cambiar el formato produciría un archivo del formato NUEVO,
así que se niega a hacerlo.

Uso, desde la raíz del proyecto y con .venv activado:
    py -m pruebas.generar_guardado_formato_anterior

La cripta se elige en ejecución (la de menos salas en datos_offline/), así que
ningún id de cripta aparece aquí (principio IV). La semilla es fija para que el
archivo sea reproducible.

Modo de la versión 2 (T002 de specs/002-niebla-guerra/tasks.md, FR-013):
    py -m pruebas.generar_guardado_formato_anterior --formato-2

genera pruebas/datos/niebla/guardado_formato_2.bin, una partida guardada con
el formato de 001-terreno-cazador (FORMATO_VERSION = 2, sin el conocimiento
del jugador) después de dos movimientos. La usa prueba_persistencia_niebla
para comprobar que un archivo de la versión 2 se reporta incompatible con la
versión 3. Tiene su propia comprobación de versión y no toca el camino de la
versión 1: cada modo se niega a correr si el formato vigente no es el suyo.

Modo de la versión 3 (T002 de specs/004-linea-tiempo/tasks.md, FR-010):
    py -m pruebas.generar_guardado_formato_anterior --formato-3

genera pruebas/datos/linea/guardado_formato_3.bin, una partida guardada con
el formato de 002-niebla-guerra (FORMATO_VERSION = 3, sin la línea de tiempo)
después de dos movimientos. La usa prueba_persistencia_linea para comprobar
que un archivo de la versión 3 se reporta incompatible con la versión 4.
Tiene su propia comprobación de versión; los modos 1 y 2 no cambian.
"""
import sys
import tempfile
from pathlib import Path

from cripta.adaptadores import partidaBinaria
from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.nucleo.partida import Partida

FORMATO_ANTERIOR = 1
SEMILLA = 20261101

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_OFFLINE = RAIZ / "datos_offline"
DESTINO = RAIZ / "pruebas" / "datos" / "terreno_cazador" / "guardado_formato_anterior.bin"

FORMATO_2 = 2
SEMILLA_FORMATO_2 = 20261115
DESTINO_FORMATO_2 = RAIZ / "pruebas" / "datos" / "niebla" / "guardado_formato_2.bin"
MOVIMIENTOS_FORMATO_2 = 2

FORMATO_3 = 3
SEMILLA_FORMATO_3 = 20261117
DESTINO_FORMATO_3 = RAIZ / "pruebas" / "datos" / "linea" / "guardado_formato_3.bin"


def cripta_mas_chica(fuente):
    """Id de la cripta con menos salas; en un empate, la primera listada."""
    elegida = None
    for resumen in fuente.listar_criptas():
        if elegida is None or resumen.salas < elegida.salas:
            elegida = resumen
    if elegida is None:
        raise SystemExit(f"No hay criptas en {CARPETA_OFFLINE}")
    return elegida


def main():
    if partidaBinaria.FORMATO_VERSION != FORMATO_ANTERIOR:
        raise SystemExit(
            f"El formato vigente es {partidaBinaria.FORMATO_VERSION}, no "
            f"{FORMATO_ANTERIOR}: este script solo sirve con el código anterior a "
            "001-terreno-cazador. El fixture confirmado en git no se regenera.")

    sincrona = FuenteOffline(CARPETA_OFFLINE)
    cache_fichas = Path(tempfile.mkdtemp(prefix="fixture_formato_anterior_"))
    servicio = ServicioDatos(sincrona, FuenteAsincrona(sincrona), CacheFichas(25),
                             AlmacenLocalDisco(cache_fichas))
    resumen = cripta_mas_chica(sincrona)
    servicio.iniciar_cripta(resumen.id)
    partida = Partida(servicio)
    partida.iniciar(SEMILLA)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    PartidaBinaria.guardar(partida, DESTINO)

    with open(DESTINO, "rb") as archivo:
        encabezado = archivo.read(8)
    assert encabezado[:4] == partidaBinaria.MAGIC, "el archivo no empieza con MAGIC"
    assert int.from_bytes(encabezado[4:8], "little") == FORMATO_ANTERIOR, (
        "el archivo no quedó con la versión de formato anterior")
    print(f"Fixture generado: {DESTINO.relative_to(RAIZ).as_posix()} "
          f"({DESTINO.stat().st_size} bytes, {resumen.salas} salas, "
          f"formato {FORMATO_ANTERIOR}, semilla {SEMILLA})")


def _primer_movimiento(partida):
    """Primera dirección (N, S, E, O) con salida abierta desde la sala del
    jugador, o None. Determinista: no usa azar."""
    from cripta.modelo.puertos.dto import DIRECCIONES
    sala = partida.mundo.sala(partida.jugador.sala)
    for direccion in DIRECCIONES:
        salida = sala.salida(direccion)
        if salida is not None and salida.transitable():
            return direccion
    return None


def main_formato_2():
    """Modo propio de la versión 2 (002-niebla-guerra, T002): su propia
    comprobación de versión; el camino de la versión 1 no cambia."""
    from cripta.modelo.nucleo.accion import Mover
    if partidaBinaria.FORMATO_VERSION != FORMATO_2:
        raise SystemExit(
            f"El formato vigente es {partidaBinaria.FORMATO_VERSION}, no "
            f"{FORMATO_2}: el modo --formato-2 solo sirve con el código anterior a "
            "002-niebla-guerra. El fixture confirmado en git no se regenera.")

    sincrona = FuenteOffline(CARPETA_OFFLINE)
    cache_fichas = Path(tempfile.mkdtemp(prefix="fixture_formato_2_"))
    servicio = ServicioDatos(sincrona, FuenteAsincrona(sincrona), CacheFichas(25),
                             AlmacenLocalDisco(cache_fichas))
    resumen = cripta_mas_chica(sincrona)
    servicio.iniciar_cripta(resumen.id)
    partida = Partida(servicio)
    partida.iniciar(SEMILLA_FORMATO_2)
    movimientos = 0
    for _ in range(MOVIMIENTOS_FORMATO_2):
        direccion = _primer_movimiento(partida)
        if direccion is None or partida.terminada():
            break
        if partida.aplicar_accion(Mover(direccion)).aceptada:
            movimientos += 1

    DESTINO_FORMATO_2.parent.mkdir(parents=True, exist_ok=True)
    PartidaBinaria.guardar(partida, DESTINO_FORMATO_2)

    with open(DESTINO_FORMATO_2, "rb") as archivo:
        encabezado = archivo.read(8)
    assert encabezado[:4] == partidaBinaria.MAGIC, "el archivo no empieza con MAGIC"
    assert int.from_bytes(encabezado[4:8], "little") == FORMATO_2, (
        "el archivo no quedó con la versión de formato 2")
    print(f"Fixture generado: {DESTINO_FORMATO_2.relative_to(RAIZ).as_posix()} "
          f"({DESTINO_FORMATO_2.stat().st_size} bytes, {resumen.salas} salas, "
          f"formato {FORMATO_2}, {movimientos} movimientos, semilla {SEMILLA_FORMATO_2})")


def main_formato_3():
    """Modo propio de la versión 3 (004-linea-tiempo, T002): su propia
    comprobación de versión; los caminos de las versiones 1 y 2 no cambian."""
    from cripta.modelo.nucleo.accion import Mover
    if partidaBinaria.FORMATO_VERSION != FORMATO_3:
        raise SystemExit(
            f"El formato vigente es {partidaBinaria.FORMATO_VERSION}, no "
            f"{FORMATO_3}: el modo --formato-3 solo sirve con el código anterior a "
            "004-linea-tiempo. El fixture confirmado en git no se regenera.")

    sincrona = FuenteOffline(CARPETA_OFFLINE)
    cache_fichas = Path(tempfile.mkdtemp(prefix="fixture_formato_3_"))
    servicio = ServicioDatos(sincrona, FuenteAsincrona(sincrona), CacheFichas(25),
                             AlmacenLocalDisco(cache_fichas))
    resumen = cripta_mas_chica(sincrona)
    servicio.iniciar_cripta(resumen.id)
    partida = Partida(servicio)
    partida.iniciar(SEMILLA_FORMATO_3)
    movimientos = 0
    for _ in range(MOVIMIENTOS_FORMATO_2):
        direccion = _primer_movimiento(partida)
        if direccion is None or partida.terminada():
            break
        if partida.aplicar_accion(Mover(direccion)).aceptada:
            movimientos += 1

    DESTINO_FORMATO_3.parent.mkdir(parents=True, exist_ok=True)
    PartidaBinaria.guardar(partida, DESTINO_FORMATO_3)

    with open(DESTINO_FORMATO_3, "rb") as archivo:
        encabezado = archivo.read(8)
    assert encabezado[:4] == partidaBinaria.MAGIC, "el archivo no empieza con MAGIC"
    assert int.from_bytes(encabezado[4:8], "little") == FORMATO_3, (
        "el archivo no quedó con la versión de formato 3")
    print(f"Fixture generado: {DESTINO_FORMATO_3.relative_to(RAIZ).as_posix()} "
          f"({DESTINO_FORMATO_3.stat().st_size} bytes, {resumen.salas} salas, "
          f"formato {FORMATO_3}, {movimientos} movimientos, semilla {SEMILLA_FORMATO_3})")


if __name__ == "__main__":
    if "--formato-3" in sys.argv[1:]:
        main_formato_3()
    elif "--formato-2" in sys.argv[1:]:
        main_formato_2()
    else:
        main()
    sys.exit(0)
