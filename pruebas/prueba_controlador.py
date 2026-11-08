"""Prueba de la capa Controlador de punta a punta, con el Modelo REAL y el
modo offline (sin red). Arma su propio paquete offline en una carpeta
temporal: una cripta de 3 salas con una rata que suelta una llave y un
pergamino, y una puerta cerrada hacia la sala de salida.

Escenarios: menú, errores de sintaxis, recoger/ordenar/equipar, combate por
etiqueta, pergamino (Apéndice B: el recogido no vuelve al suelo; el que suelta
un enemigo SÍ se revierte, sin duplicarse), inventario lleno, guardar/cargar
con log restaurado, puerta con llave, victoria, puntajes, replay fiel y
replay con versión incompatible.
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
from cripta.adaptadores.registroArchivo import CarpetaRegistros, RegistroArchivo
from cripta.controlador.bench.reporte import Reporte
from cripta.controlador.controladorMenu import ControladorMenu
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.modoReplay import ModoReplay
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.vista.comando import Comando
from cripta.vista.vistaNula import VistaNula

ID = "c-prueba"
PAQUETE = {
    "criptas.json": {"criptas": [{"id": ID, "nombre": "Prueba", "salas": 3, "dificultad": 1}]},
    f"criptas/{ID}/general.json": {
        "id": ID, "version": "v1", "salas_total": 3, "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 3,
        "llave_salida": "itm_llave", "presupuesto_solicitudes": 99,
        "inventario_max": 2,
        "jugador": {"vida_max": 100, "ataque": 50, "defensa": 5, "velocidad": 100}},
    f"criptas/{ID}/version.json": {"id": ID, "version": "v1"},
    # 003-resolubilidad (T031): la llave de salida la suelta la rata e-1, que
    # inicia en la sala 2; la puerta 2 E -> 3 la requiere: la cripta es
    # resoluble y la partida sigue el camino normal, sin --forzar.
    f"criptas/{ID}/llaves.json": {"llaves": [{"id": "itm_llave", "sala": 2, "enemigo": "e-1"}]},
    f"criptas/{ID}/esqueleto/pagina_1.json": {"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {
            "S": {"sala": 1},
            "E": {"sala": 3, "cerrada": True, "llave": "itm_llave"}}},
        {"id": 3, "nombre": "Salida", "salidas": {"O": {"sala": 2}}}]},
    f"criptas/{ID}/contenido/1.json": {
        "sala": 1, "enemigos": [], "trampas": [],
        "objetos": ["itm_pergamino", "itm_pergamino", "itm_espada"]},
    f"criptas/{ID}/contenido/2.json": {
        "sala": 2, "objetos": [], "trampas": [],
        "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 5}]},
    f"criptas/{ID}/contenido/3.json": {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
    "catalogo/version.json": {"version": "cat-1"},
    "catalogo/ent_rata.json": {
        "id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 5,
        "ataque": 1, "defensa": 0, "velocidad": 100, "comportamiento": "guardian",
        "suelta": ["itm_llave", "itm_pergamino"]},
    "catalogo/itm_pergamino.json": {
        "id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino",
        "peso": 1, "valor": 30},
    "catalogo/itm_espada.json": {
        "id": "itm_espada", "clase": "arma", "nombre": "Espada", "peso": 5,
        "valor": 20, "ataque_bonus": 2},
    "catalogo/itm_llave.json": {
        "id": "itm_llave", "clase": "llave", "nombre": "Llave", "peso": 1,
        "valor": 1, "abre": "itm_llave"},
}

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = Path(tempfile.mkdtemp(prefix="prueba_controlador_"))
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
        self.estado = None
        self.errores = []
        self.menu = None
        self.puntajes = None
        self.fin = None

    def mostrar_estado(self, estado):
        self.estado = estado

    def mostrar_error(self, mensaje):
        self.errores.append(mensaje)

    def mostrar_menu(self, criptas):
        self.menu = criptas

    def mostrar_puntajes(self, puntajes):
        self.puntajes = puntajes

    def mostrar_fin(self, resultado):
        self.fin = resultado


def a_lista(lista_enlazada):
    return [x for x in lista_enlazada]


def ids_suelo(clase):
    return [o.id_objeto for o in vista.estado.sala.objetos if o.clase == clase]


def enviar(verbo, *argumentos):
    menu.procesar(Comando(verbo, tuple(argumentos)))


def sin_errores():
    assert vista.errores == [], vista.errores


def con_error():
    assert len(vista.errores) == 1, vista.errores
    vista.errores.clear()


try:
    vista = VistaEspia()
    almacen_puntajes = PuntajesArchivo(CARPETA / "puntajes.jsonl")
    menu = ControladorMenu(
        nuevo_servicio(), vista, GestorGuardado(AlmacenPartidaDisco(CARPETA / "guardados")),
        almacen_puntajes, CarpetaRegistros(CARPETA / "partidas"),
        ReporteFinal(Reporte(imprimir=False)), nombre_jugador="Ana", semilla_fija=42)

    # --- Menú -------------------------------------------------------------
    menu.iniciar()
    assert [c.id for c in vista.menu] == [ID]
    enviar("jugar", ID, "cargar")                 # no hay guardado todavía
    con_error()
    enviar("jugar", ID, "rara")                   # modo desconocido
    con_error()
    enviar("jugar", ID)
    sin_errores()
    # FR-019 (003-resolubilidad, T031): una cripta resoluble avisa al iniciar.
    assert "La cripta es resoluble. V muestra el reporte." in a_lista(vista.estado.mensajes)
    assert vista.estado.sala.nombre == "Entrada"
    assert [s.estado for s in vista.estado.sala.salidas] == [
        "abierta", "sin_salida", "sin_salida", "sin_salida"]

    # --- Sintaxis: nada llega al modelo -----------------------------------
    reloj = vista.estado.reloj
    enviar("bailar")
    con_error()
    enviar("mover", "X")
    con_error()
    enviar("esperar", "de más")
    con_error()
    enviar("atacar", "Nadie #9")
    con_error()
    assert vista.estado.reloj == reloj

    # --- Pergamino: el recogido en el intervalo revertido no vuelve (Ap. B)
    p1, p2 = ids_suelo("pergamino_retroceso")
    enviar("recoger", p1)
    enviar("recoger", p2)
    sin_errores()
    assert vista.estado.inventario.cantidad_pergaminos == 2
    enviar("pergamino")
    sin_errores()
    assert vista.estado.inventario.cantidad_pergaminos == 1, "solo se consume la unidad usada"
    assert ids_suelo("pergamino_retroceso") == [], "el pergamino recogido no vuelve al suelo"

    # --- Recoger, ordenar y equipar ---------------------------------------
    (espada,) = ids_suelo("arma")
    enviar("recoger", espada)
    sin_errores()
    enviar("ordenar_inventario", "peso")
    assert [o.nombre for o in vista.estado.inventario.vista_ordenada] == ["Pergamino", "Espada"]
    enviar("ordenar_inventario", "real")
    assert vista.estado.inventario.vista_ordenada is None
    enviar("ordenar_inventario", "color")
    con_error()
    enviar("equipar", espada)
    sin_errores()
    assert vista.estado.jugador.ataque_efectivo == 52

    # --- Combate por etiqueta ---------------------------------------------
    enviar("mover", "N")
    sin_errores()
    assert vista.estado.sala.nombre == "Pasillo"
    (rata,) = [e.etiqueta for e in vista.estado.sala.enemigos]
    assert rata == "Rata #1", rata
    enviar("atacar", rata)
    sin_errores()
    assert a_lista(vista.estado.sala.enemigos) == []
    assert sorted(o.clase for o in vista.estado.sala.objetos) == ["llave", "pergamino_retroceso"]

    # --- Pergamino que soltó un enemigo: SÍ se revierte (sin duplicar) ----
    enviar("pergamino")
    sin_errores()
    assert [e.etiqueta for e in vista.estado.sala.enemigos] == [rata], "la etiqueta es estable"
    assert a_lista(vista.estado.sala.objetos) == [], "lo que soltó la rata vuelve a no existir"
    assert vista.estado.inventario.cantidad_pergaminos == 0
    enviar("pergamino")                            # sin pergaminos: rechazado
    con_error()
    enviar("atacar", rata)
    sin_errores()
    assert len(ids_suelo("pergamino_retroceso")) == 1, "no se duplicó el pergamino"

    # --- Inventario lleno (Ap. B): rechazado sin consumir tiempo ----------
    (llave,) = ids_suelo("llave")
    enviar("recoger", llave)
    sin_errores()
    reloj = vista.estado.reloj
    enviar("recoger", ids_suelo("pergamino_retroceso")[0])
    con_error()
    assert vista.estado.reloj == reloj

    # --- Guardar / cargar con log restaurado ------------------------------
    enviar("guardar")
    sin_errores()
    log = CARPETA / "partidas" / f"{ID}.log"
    lineas_al_guardar = log.read_text(encoding="utf-8")
    enviar("esperar")
    assert vista.estado.reloj > reloj
    enviar("cargar")
    sin_errores()
    assert vista.estado.reloj == reloj
    assert log.read_text(encoding="utf-8") == lineas_al_guardar, "la carga restaura el log"

    # --- Cursor del inventario (no consume tiempo) ------------------------
    enviar("inventario_siguiente")
    enviar("inventario_anterior")
    sin_errores()
    assert vista.estado.reloj == reloj

    # --- Puerta con llave y victoria --------------------------------------
    enviar("mover", "E")                           # cerrada: rechazado
    con_error()
    enviar("abrir", "E")
    sin_errores()
    enviar("mover", "E")
    sin_errores()
    assert vista.fin is not None and vista.fin.resultado == "victoria"
    reloj_final = vista.fin.tiempo_final

    # --- Puntajes ---------------------------------------------------------
    enviar("ver_puntajes")
    assert [(p.nombre, p.resultado) for p in vista.puntajes] == [("Ana", "victoria")]

    # --- Replay fiel ------------------------------------------------------
    reporte = Reporte(imprimir=False)
    replay = ModoReplay(nuevo_servicio(), VistaNula(), ReporteFinal(Reporte(imprimir=False)), reporte)
    assert replay.ejecutar(RegistroArchivo(log)), a_lista(reporte.notas)
    assert replay.partida.fin == "victoria"
    assert replay.partida.reloj == reloj_final, "el replay llega al mismo reloj final"

    # --- Replay con versión incompatible: se reporta, no se reproduce -----
    malo = CARPETA / "malo.log"
    malo.write_text(log.read_text(encoding="utf-8").replace(f"{ID} v1 ", f"{ID} v0 ", 1),
                    encoding="utf-8")
    reporte = Reporte(imprimir=False)
    replay = ModoReplay(nuevo_servicio(), VistaNula(), ReporteFinal(Reporte(imprimir=False)), reporte)
    assert not replay.ejecutar(RegistroArchivo(malo))
    assert any("versión" in nota for nota in reporte.notas)

    # --- Partida nueva explícita aunque haya guardado; salir --------------
    enviar("jugar", ID, "nueva")
    sin_errores()
    assert vista.estado.sala.nombre == "Entrada" and vista.estado.reloj == 0
    vista.menu = None
    enviar("salir")                  # ESC en la partida: vuelve al menú, no cierra (D65)
    assert not menu.terminado() and vista.menu is not None
    con_error()                      # el aviso "Volviste al menú..."
    enviar("salir")                  # ESC en el menú: ahora sí cierra
    assert menu.terminado()
finally:
    os.chdir(RAIZ)
    shutil.rmtree(CARPETA, ignore_errors=True)

print("Controlador OK")
