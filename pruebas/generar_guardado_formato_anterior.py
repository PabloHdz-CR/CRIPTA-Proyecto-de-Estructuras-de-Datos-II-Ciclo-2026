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


if __name__ == "__main__":
    main()
    sys.exit(0)
