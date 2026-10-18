"""Prueba del menú nuevo y del replay en la ventana (ControladorReplay), con
el Modelo REAL en modo offline y un reloj falso (no espera de verdad).

Escenarios: nombre del jugador (recorte y valor por defecto) y su paso al
EstadoVista; replay pedido sin partida; partida ganada y replay desde la
pantalla de fin, que llega al mismo final (coincide); pausa, paso a paso y
velocidad; dos partidas en la misma cripta con distinto nombre y tiempo, y
el replay de la PRIMERA desde puntajes reproduce esa y no la última (log
archivado por partida), con el nombre de quien la jugó, y vuelve a
puntajes; un puntaje viejo sin id no tiene replay; un log archivado
adulterado detiene el replay con un error; y el benchmark desde el menú.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.adaptadores.registroArchivo import CarpetaRegistros
from cripta.controlador import controladorReplay
from cripta.controlador.bench.reporte import Reporte
from cripta.controlador.controladorMenu import ControladorMenu
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.vistaNula import VistaNula

ID = "c-replay"
PAQUETE = {
    "criptas.json": {"criptas": [{"id": ID, "nombre": "Prueba", "salas": 3, "dificultad": 2}]},
    f"criptas/{ID}/general.json": {
        "id": ID, "version": "v1", "salas_total": 3, "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 3,
        "llave_salida": "itm_llave", "presupuesto_solicitudes": 99,
        "inventario_max": 4,
        "jugador": {"vida_max": 100, "ataque": 50, "defensa": 5, "velocidad": 100}},
    f"criptas/{ID}/version.json": {"id": ID, "version": "v1"},
    f"criptas/{ID}/esqueleto/pagina_1.json": {"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {
            "S": {"sala": 1},
            "E": {"sala": 3, "cerrada": True, "llave": "itm_llave"}}},
        {"id": 3, "nombre": "Salida", "salidas": {"O": {"sala": 2}}}]},
    f"criptas/{ID}/contenido/1.json": {"sala": 1, "enemigos": [], "trampas": [], "objetos": []},
    f"criptas/{ID}/contenido/2.json": {
        "sala": 2, "objetos": [], "trampas": [],
        "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 5}]},
    f"criptas/{ID}/contenido/3.json": {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
    "catalogo/version.json": {"version": "cat-1"},
    "catalogo/ent_rata.json": {
        "id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 5,
        "ataque": 1, "defensa": 0, "velocidad": 100, "comportamiento": "guardian",
        "suelta": ["itm_llave"]},
    "catalogo/itm_llave.json": {
        "id": "itm_llave", "clase": "llave", "nombre": "Llave", "peso": 1,
        "valor": 1, "abre": "itm_llave"},
}

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = Path(tempfile.mkdtemp(prefix="prueba_replay_menu_"))
for relativa, contenido in PAQUETE.items():
    ruta = CARPETA / "offline" / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
os.chdir(CARPETA)


def nuevo_servicio():
    sincrona = FuenteOffline(CARPETA / "offline")
    return ServicioDatos(sincrona, FuenteAsincrona(sincrona), CacheFichas(25),
                         AlmacenLocalDisco(CARPETA / "fichas"))


class VistaEspia(VistaNula):
    def __init__(self):
        super().__init__()
        self.estados = []
        self.errores = []
        self.menu = None
        self.fin = None
        self.nombre = None
        self.benchmark = None
        self.espera = None
        self.puntajes = None
        self.ultimo_lugar = None

    def mostrar_estado(self, estado):
        self.estados.append(estado)

    def mostrar_error(self, mensaje):
        self.errores.append(mensaje)

    def mostrar_menu(self, criptas):
        self.menu = criptas
        self.fin = None
        self.ultimo_lugar = "menu"

    def mostrar_puntajes(self, puntajes):
        self.puntajes = puntajes
        self.fin = None
        self.ultimo_lugar = "puntajes"

    def mostrar_fin(self, resultado):
        self.fin = resultado

    def mostrar_nombre_jugador(self, nombre):
        self.nombre = nombre

    def mostrar_benchmark(self, resultado):
        self.benchmark = resultado

    def mostrar_espera(self, texto):
        self.espera = texto

    @property
    def estado(self):
        return self.estados[-1]


class RelojFalso:
    def __init__(self):
        self.ahora = 0.0

    def __call__(self):
        return self.ahora


class BenchFalso:
    """No mide de verdad (eso lo prueba prueba_2_3 y compañía): solo deja
    una nota y una tabla, como haría benchTodo."""

    def ejecutar(self, rapido=False, reporte=None):
        assert rapido and reporte is not None
        reporte.nota("nota de prueba")
        filas = ListaEnlazada()
        filas.agregar_al_final(("100", "1.0"))
        reporte.tabla("Tabla de prueba", ("n", "us"), filas)
        return reporte


def enviar(verbo, *argumentos):
    menu.procesar(Comando(verbo, tuple(argumentos)))


def tic(segundos):
    """Avanza el reloj falso y le da una vuelta al bucle (sin comando)."""
    reloj.ahora += segundos
    menu.procesar(None)


def sin_errores():
    assert vista.errores == [], vista.errores


def con_error(texto):
    assert len(vista.errores) == 1 and texto in vista.errores[0], vista.errores
    vista.errores.clear()


reloj = RelojFalso()

try:
    vista = VistaEspia()
    menu = ControladorMenu(
        nuevo_servicio(), vista, GestorGuardado(AlmacenPartidaDisco(CARPETA / "guardados")),
        PuntajesArchivo(CARPETA / "puntajes.jsonl"), CarpetaRegistros(CARPETA / "partidas"),
        ReporteFinal(Reporte(imprimir=False)), semilla_fija=7, modo_bench=BenchFalso(),
        reloj=reloj)

    # --- Nombre -----------------------------------------------------------
    menu.iniciar()
    assert vista.nombre == "Jugador"
    enviar("cambiar_nombre", "   Pablo Hernández Esquivel  ")
    assert vista.nombre == "Pablo Hernández", repr(vista.nombre)    # 16 caracteres, sin espacios
    enviar("cambiar_nombre", "    ")
    assert vista.nombre == "Jugador", "vacío vuelve al nombre por defecto"
    enviar("cambiar_nombre", "Ana")
    assert menu.nombre_jugador == "Ana"

    # --- Replay sin partida: error, se queda donde estaba ------------------
    enviar("ver_replay")                     # desde "fin" sin partida previa
    con_error("no tiene un replay")
    enviar("ver_replay_partida", "no-existe")
    con_error("no tiene un replay")

    # --- Partida ganada: el nombre llega al EstadoVista --------------------
    def ganar(esperas):
        enviar("jugar", ID, "nueva")
        sin_errores()
        enviar("mover", "N")
        enviar("atacar", "Rata #1")
        sin_errores()
        (llave,) = [o.id_objeto for o in vista.estado.sala.objetos]
        enviar("recoger", llave)
        for _ in range(esperas):
            enviar("esperar")
        enviar("abrir", "E")
        enviar("mover", "E")
        sin_errores()
        assert vista.fin is not None and vista.fin.resultado == "victoria"
        return vista.fin

    final = ganar(0)
    assert vista.estados[0].nombre_jugador == "Ana" and vista.estados[0].replay is None
    assert final.puede_ver_replay and not final.es_replay

    # --- Replay desde la pantalla de fin ----------------------------------
    estados_antes = len(vista.estados)
    enviar("ver_replay")
    sin_errores()
    inicial = vista.estado
    assert len(vista.estados) == estados_antes + 1
    assert inicial.replay is not None and inicial.replay.paso == 0 and inicial.replay.total == 5
    assert inicial.sala.nombre == "Entrada" and inicial.nombre_jugador == "Ana"
    assert "Ana" in inicial.replay.titulo and "victoria" in inicial.replay.titulo
    tic(0.5)                                  # todavía dentro de la espera inicial
    assert vista.estado.replay.paso == 0
    tic(controladorReplay.ESPERA_INICIAL)
    assert vista.estado.replay.paso == 1 and vista.estado.sala.nombre == "Pasillo"

    # pausa: el tiempo pasa pero no avanza; "paso" avanza de a uno igual
    enviar("replay_pausa")
    assert vista.estado.replay.pausado
    tic(10)
    assert vista.estado.replay.paso == 1
    enviar("replay_paso")
    assert vista.estado.replay.paso == 2 and vista.estado.sala.enemigos.esta_vacia()
    enviar("replay_pausa")                    # continúa

    # velocidad: x2 avanza con la mitad del intervalo; no baja de x1
    enviar("replay_velocidad", "+")
    assert vista.estado.replay.velocidad == 2
    tic(controladorReplay.SEGUNDOS_POR_PASO / 2)
    assert vista.estado.replay.paso == 3
    enviar("replay_velocidad", "-")
    enviar("replay_velocidad", "-")
    assert vista.estado.replay.velocidad == 1
    for _ in range(10):
        tic(controladorReplay.SEGUNDOS_POR_PASO)
    assert vista.fin is not None and vista.fin.es_replay
    assert vista.fin.coincide is True, "el replay llega al mismo final que la partida"
    assert (vista.fin.resultado, vista.fin.acciones, vista.fin.tiempo_final) == (
        final.resultado, final.acciones, final.tiempo_final)

    # en la pantalla de fin del replay: R lo repite, ENTER vuelve al menú
    enviar("ver_replay")
    assert vista.estado.replay.paso == 0 and vista.fin is not None
    enviar("volver")
    assert vista.menu is not None and vista.fin is None

    # --- Otra partida en la MISMA cripta, con otro nombre y otro tiempo ----
    enviar("cambiar_nombre", "Beto")
    final_beto = ganar(2)
    assert final_beto.tiempo_final > final.tiempo_final
    enviar("volver")

    # --- Puntajes: cada partida tiene su propio replay ---------------------
    enviar("ver_puntajes")
    filas = [p for p in vista.puntajes]
    assert [(p.nombre, p.tiene_replay) for p in filas] == [("Ana", True), ("Beto", True)]
    id_ana, id_beto = filas[0].id_partida, filas[1].id_partida
    assert id_ana and id_beto and id_ana != id_beto
    assert (CARPETA / "partidas" / f"{ID}.log").is_file(), "el log activo sigue ahí"

    # el replay de Ana es el de Ana, aunque Beto jugó después en la misma cripta
    enviar("ver_replay_partida", id_ana)
    sin_errores()
    assert vista.estado.nombre_jugador == "Ana", "el nombre es el de quien jugó"
    assert "Ana" in vista.estado.replay.titulo
    for _ in range(12):
        tic(controladorReplay.SEGUNDOS_POR_PASO)
    assert vista.fin.es_replay and vista.fin.coincide is True
    assert vista.fin.tiempo_final == final.tiempo_final != final_beto.tiempo_final
    enviar("volver")                          # vuelve a PUNTAJES, no al menú
    assert vista.ultimo_lugar == "puntajes"

    # ESC durante el replay también vuelve a puntajes, sin cerrar el juego
    enviar("ver_replay_partida", id_beto)
    tic(controladorReplay.ESPERA_INICIAL)
    enviar("salir")
    assert not menu.terminado() and vista.ultimo_lugar == "puntajes"

    # --- Un puntaje viejo (sin id de partida) no tiene replay -------------
    with open(CARPETA / "puntajes.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps({"nombre": "Viejo", "id_cripta": ID, "version_cripta": "v1",
                                  "acciones": 1, "enemigos_derrotados": 0,
                                  "tiempo_final": 1, "resultado": "derrota"}) + "\n")
    enviar("ver_puntajes")
    viejo = [p for p in vista.puntajes if p.nombre == "Viejo"][0]
    assert viejo.id_partida is None and not viejo.tiene_replay

    # --- Log archivado adulterado: la acción rechazada detiene el replay ---
    log = CARPETA / "partidas" / "historial" / f"{id_beto}.log"
    lineas = log.read_text(encoding="utf-8").splitlines()
    adulterado = [lineas[0], lineas[1], "MOVER O"] + lineas[2:]
    log.write_text("\n".join(adulterado) + "\n", encoding="utf-8")
    enviar("ver_replay_partida", id_beto)
    sin_errores()
    for _ in range(6):
        tic(controladorReplay.SEGUNDOS_POR_PASO)
    con_error("rechazada")
    paso_detenido = vista.estado.replay.paso
    tic(30)
    assert vista.estado.replay.paso == paso_detenido, "detenido: ya no avanza"
    enviar("salir")
    assert vista.ultimo_lugar == "puntajes"
    enviar("volver")
    assert vista.ultimo_lugar == "menu"

    # --- Benchmark desde el menú ------------------------------------------
    enviar("benchmark")
    assert vista.espera is not None
    assert vista.benchmark is not None and vista.benchmark.rapido
    assert [n for n in vista.benchmark.notas] == ["nota de prueba"]
    (titulo, encabezados, filas), = [t for t in vista.benchmark.tablas]
    assert titulo == "Tabla de prueba" and encabezados == ("n", "us")
    enviar("volver")

    enviar("salir")
    assert menu.terminado()
finally:
    os.chdir(RAIZ)
    shutil.rmtree(CARPETA, ignore_errors=True)

print("Sección replay y menú OK")
