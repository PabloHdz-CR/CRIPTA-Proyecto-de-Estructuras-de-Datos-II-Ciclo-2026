"""Guardar, cargar y reproducir partidas con costos y cazadores
(001-terreno-cazador, persistencia transversal).

Requisitos que ejerce: FR-022 (partidas guardadas y registro permiten
reanudar y reproducir con resultado idéntico; los archivos del formato
anterior se reportan incompatibles), FR-027 (caras con costos distintos:
también --replay lo reporta y sale con código 1) y SC-005 (--replay da la
misma secuencia y el mismo estado final).

  (a) Guardar y cargar terreno-a en el formato nuevo: los costos se
      conservan, enlazar() corre al cargar y el cazador decide igual antes
      de guardar y después de cargar; las dos partidas siguen idénticas.
  (b) El fixture del formato anterior (T003) → VersionIncompatible, sin
      migrar ni modificar el archivo.
  (c) --replay de un log de terreno-a → mismas acciones y mismo estado final.
  (d) --replay de un log de terreno-caras-distintas escrito a mano, en un
      subproceso → código 1 y el mensaje de DatosInvalidos.

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_persistencia_cazador
"""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

from cripta.adaptadores import partidaBinaria
from cripta.adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.adaptadores.registroArchivo import (
    PREFIJO_ENCABEZADO, CarpetaRegistros, RegistroArchivo)
from cripta.controlador.bench.reporte import Reporte
from cripta.controlador.controladorMenu import ControladorMenu
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.modoReplay import ModoReplay
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.modelo.actores.comportamientos import Cazador
from cripta.modelo.nucleo.accion import Esperar, Mover
from cripta.modelo.nucleo.diario import Diario
from cripta.modelo.nucleo.partida import Partida
from cripta.modelo.puertos.errores import VersionIncompatible
from cripta.vista.comando import Comando
from cripta.vista.vistaNula import VistaNula
from pruebas.apoyo_terreno import (
    CARPETA_TERRENO, RAIZ, VistaRegistradora, buscar_enemigo, cerrar_fuentes,
    servicio_terreno)

FIXTURE = CARPETA_TERRENO / "guardado_formato_anterior.bin"
CAMINO = ("N", "N", "E", "S")          # 1 → 2 → 4 → 6 (activa al cazador) → 5
SEMILLA = 3


def costos(partida):
    return {(sala.id, s.direccion): s.costo for sala in partida.mundo
            for s in sala.salidas if s is not None}


def foto(partida):
    """Lo observable de una partida, para comparar dos."""
    cazador = buscar_enemigo(partida, "e-601")
    return (partida.reloj, partida.jugador.sala, partida.jugador.vida, partida.fin,
            cazador.sala, cazador.vida, cazador.activo, partida.azar.getstate())


def partida_terreno_a():
    servicio = servicio_terreno()
    servicio.iniciar_cripta("terreno-a")
    partida = Partida(servicio)
    partida.conectar_diario(Diario())
    partida.iniciar(SEMILLA)
    for direccion in CAMINO:
        assert partida.aplicar_accion(Mover(direccion)).aceptada, direccion
    return partida


def caso_a_guardar_y_cargar():
    """(a) FR-022: guardar y cargar terreno-a en el formato nuevo."""
    original = partida_terreno_a()
    cazador = buscar_enemigo(original, "e-601")
    assert isinstance(cazador.comportamiento, Cazador) and cazador.activo
    antes = (cazador.comportamiento.decidir(cazador, original),)
    antes += (original.costo_de(cazador, antes[0]),)

    ruta = Path(tempfile.mkdtemp(prefix="prueba_persistencia_")) / "partida.bin"
    PartidaBinaria.guardar(original, ruta)
    with open(ruta, "rb") as archivo:
        encabezado = archivo.read(8)
    assert int.from_bytes(encabezado[4:8], "little") == partidaBinaria.FORMATO_VERSION == 2

    servicio = servicio_terreno()
    servicio.iniciar_cripta("terreno-a")              # como continuar_cargada
    cargada = PartidaBinaria.cargar(ruta, servicio)
    cargada.conectar_diario(Diario())

    # Los costos efectivos se conservan, y enlazar() corrió al cargar.
    assert costos(cargada) == costos(original), (costos(cargada), costos(original))
    assert costos(cargada)[(4, "S")] == 1 and costos(cargada)[(1, "E")] == 300
    for sala in cargada.mundo:
        for salida in sala.salidas:
            if salida is not None:
                assert salida.origen is sala and salida.sala_destino.id == salida.destino
    assert len(cargada.mundo.sala(5).entrantes) == len(original.mundo.sala(5).entrantes)
    assert cargada.mapa_distancias is not None
    assert cargada.mayor_rango_activo() == original.mayor_rango_activo() == 400

    # La decisión del cazador después de cargar es la de antes de guardar.
    cazador_cargado = buscar_enemigo(cargada, "e-601")
    despues = (cazador_cargado.comportamiento.decidir(cazador_cargado, cargada),)
    despues += (cargada.costo_de(cazador_cargado, despues[0]),)
    assert despues == antes, (despues, antes)

    # Y las dos partidas siguen idénticas: mismas acciones, mismo resultado.
    assert foto(cargada) == foto(original)
    for accion in (Esperar(), Mover("N"), Esperar(), Mover("S"), Esperar()):
        original.aplicar_accion(accion)
        cargada.aplicar_accion(accion)
        assert foto(cargada) == foto(original), accion


def caso_b_formato_anterior():
    """(b) FR-022, principio V: el archivo del formato 1 se reporta
    incompatible, sin migrarlo ni modificarlo."""
    huella = hashlib.sha1(FIXTURE.read_bytes()).hexdigest()
    servicio = servicio_terreno()
    try:
        PartidaBinaria.cargar(FIXTURE, servicio)
    except VersionIncompatible as error:
        assert error.encontrada == 1 and error.esperada == partidaBinaria.FORMATO_VERSION, error
    else:
        raise AssertionError("el formato anterior debía reportarse incompatible")
    assert hashlib.sha1(FIXTURE.read_bytes()).hexdigest() == huella, "el fixture cambió"


def caso_c_replay_fiel():
    """(c) FR-022, SC-005: --replay de un log de terreno-a reproduce las mismas
    acciones y llega al mismo estado final."""
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_persistencia_replay_"))
    vista = VistaRegistradora()
    menu = ControladorMenu(
        servicio_terreno(), vista, GestorGuardado(AlmacenPartidaDisco(carpeta / "guardados")),
        PuntajesArchivo(carpeta / "puntajes.jsonl"), CarpetaRegistros(carpeta / "partidas"),
        ReporteFinal(Reporte(imprimir=False)), semilla_fija=SEMILLA,
        # 003-resolubilidad: terreno-a no es resoluble (FR-001) ni tiene
        # llaves.json; se inicia con --forzar y se acepta el reporte.
        forzar=True)
    menu.iniciar()
    menu.procesar(Comando("jugar", ("terreno-a",)))
    menu.procesar(Comando("aceptar_resolubilidad"))
    for direccion in CAMINO + ("N", "S"):
        menu.procesar(Comando("mover", (direccion,)))
    menu.procesar(Comando("esperar"))
    assert vista.errores == [], vista.errores
    original = menu._juego.partida
    logs = list((carpeta / "partidas").glob("*.log"))
    assert len(logs) == 1, logs
    acciones = logs[0].read_text(encoding="utf-8").splitlines()[1:]
    assert len(acciones) == len(CAMINO) + 3, acciones

    reporte = Reporte(imprimir=False)
    replay = ModoReplay(servicio_terreno(), VistaNula(), ReporteFinal(Reporte(imprimir=False)),
                        reporte)
    assert replay.ejecutar(RegistroArchivo(logs[0])), [n for n in reporte.notas]
    assert foto(replay.partida) == foto(original)


def caso_d_replay_caras_distintas():
    """(d) FR-027: un log de terreno-caras-distintas (encabezado mínimo, sin
    acciones) reproducido con main.py --replay en un subproceso sale con
    código 1 e imprime el mensaje de DatosInvalidos."""
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_persistencia_log_"))
    log = carpeta / "caras.log"
    log.write_text(f"{PREFIJO_ENCABEZADO}terreno-caras-distintas v1 cat-terreno-1 7\n",
                   encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, "main.py", f"--offline={CARPETA_TERRENO}", "--replay", str(log)],
        cwd=RAIZ, capture_output=True, text=True, timeout=120)
    salida = resultado.stdout + resultado.stderr
    assert resultado.returncode == 1, (resultado.returncode, salida)
    for parte in ("declaran costos distintos", "sala 1", "sala 2", "300", "200"):
        assert parte in salida, f"falta '{parte}' en:\n{salida}"


CASOS = (caso_a_guardar_y_cargar, caso_b_formato_anterior, caso_c_replay_fiel,
         caso_d_replay_caras_distintas)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:                  # se reportan todos los casos
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_persistencia_cazador OK ({len(CASOS)} casos)")


main()
