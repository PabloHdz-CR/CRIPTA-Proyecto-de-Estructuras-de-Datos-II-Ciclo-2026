"""«ir a» en partida.log y --replay (T025 de specs/002-niebla-guerra/tasks.md).

Cubre FR-026, FR-027 (US3 escenario 10, US5 escenario 5) y SC-007.
"""
import random
import tempfile
from pathlib import Path

from cripta.adaptadores.registroArchivo import RegistroArchivo
from cripta.modelo.mundo.conocimiento import EXPLORADA
from cripta.modelo.nucleo.accion import Mover
from cripta.modelo.puertos.registroAcciones import EncabezadoPartida
from cripta.vista.comando import Comando

from pruebas.apoyo_niebla import (
    CAZADOR_MANSO, cerrar_fuentes, con_contenido, conocer, controlador_sobre,
    huella_conocimiento, malla_n, partida_sobre, pasillo_n)

PARTIDAS_SC007 = 20


def registro_temporal():
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_replay_ir_a_"))
    return RegistroArchivo(carpeta / "partida.log"), carpeta / "partida.log"


def caso_us3_e10_comentario_y_movimientos():
    """US3 escenario 10 (FR-026): `# IR_A <id>` y luego un MOVER por paso; una
    orden rechazada no escribe nada."""
    registro, ruta = registro_temporal()
    controlador, _, _ = controlador_sobre(pasillo_n(4), registro=registro)
    conocer(controlador.partida, 2, 3, 4)
    controlador.procesar(Comando("ir_a", (999,)))          # rechazada
    controlador.procesar(Comando("ir_a", (4,)))
    while controlador.viaje is not None:
        controlador.procesar(None)
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert lineas[1:] == ["# IR_A 4", "MOVER E", "MOVER E", "MOVER E"], (
        f"FR-026: {lineas[1:]}")


def caso_fr027_leer_salta_comentarios():
    """FR-027: leer() salta las líneas `#`; un log sin comentarios se lee igual."""
    registro, ruta = registro_temporal()
    registro.iniciar(EncabezadoPartida("c", "v", "cat", 1))
    registro.registrar_comentario("IR_A 7")
    registro.registrar_accion(Mover("E"))
    registro.registrar_comentario("cualquier cosa")
    registro.registrar_accion(Mover("S"))
    _, acciones = registro.leer()
    assert [a.direccion for a in acciones] == ["E", "S"], "FR-027: los comentarios no son acciones"

    sin, _ = registro_temporal()
    sin.iniciar(EncabezadoPartida("c", "v", "cat", 1))
    sin.registrar_accion(Mover("E"))
    sin.registrar_accion(Mover("S"))
    assert [a.direccion for a in sin.leer()[1]] == ["E", "S"], "FR-027: log sin comentarios"


def _reproducir(descripcion, semilla, acciones):
    """El camino de --replay sin Vista: partida nueva con la misma semilla y
    las acciones del log, una por una."""
    partida = partida_sobre(descripcion, semilla=semilla)
    for accion in acciones:
        assert partida.aplicar_accion(accion).aceptada, f"replay rechazó {accion!r}"
    return partida


def caso_sc007_veinte_partidas():
    """SC-007 (FR-027): 20 partidas con viajes reproducidas terminan igual,
    con el mismo conocimiento."""
    azar = random.Random(20261115)
    for numero in range(PARTIDAS_SC007):
        descripcion = con_contenido(malla_n(4), 16, enemigos=(("m1", CAZADOR_MANSO),))
        semilla = 1000 + numero
        registro, _ = registro_temporal()
        controlador, _, _ = controlador_sobre(descripcion, semilla=semilla, registro=registro)
        partida = controlador.partida
        for _ in range(4):
            for _ in range(3):
                sala = partida.mundo.sala(partida.jugador.sala)
                direcciones = [d for d, s in zip("NSEO", sala.salidas) if s is not None]
                controlador.procesar(Comando("mover", (azar.choice(direcciones),)))
            exploradas = [s.id for s in partida.mundo
                          if s.conocimiento == EXPLORADA and s.id != partida.jugador.sala]
            if exploradas and not partida.terminada():
                controlador.procesar(Comando("ir_a", (azar.choice(exploradas),)))
                while controlador.viaje is not None:
                    controlador.procesar(None)
        _, acciones = registro.leer()
        copia = _reproducir(descripcion, semilla, acciones)
        assert (copia.reloj, copia.jugador.sala, copia.jugador.vida, copia.fin) == (
            partida.reloj, partida.jugador.sala, partida.jugador.vida, partida.fin), (
            f"SC-007: partida {numero} no se reproduce igual")
        assert huella_conocimiento(copia) == huella_conocimiento(partida), (
            f"SC-007: partida {numero}: otro conocimiento al final")
        cerrar_fuentes()


CASOS = (caso_us3_e10_comentario_y_movimientos, caso_fr027_leer_salta_comentarios,
         caso_sc007_veinte_partidas)


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
    print(f"prueba_replay_ir_a OK ({len(CASOS)} casos)")


main()
