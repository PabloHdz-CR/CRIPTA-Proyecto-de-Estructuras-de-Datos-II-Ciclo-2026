"""Mediciones del guardado binario contra guardar el mismo estado en JSON
(§4.10: "Deben comparar tamaño en disco y tiempo de carga contra guardar el
mismo estado en JSON").

Arma una partida sintética (sin red) de tamaño creciente y mide, para cada
tamaño: tamaño en disco y tiempo de carga de PartidaBinaria contra un
volcado JSON equivalente (mismos datos, con json.dumps/json.loads).

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchGuardado            (completo)
    python -m cripta.controlador.bench.benchGuardado --rapido   (versión corta)
"""
import json
import os
import random
import sys
import tempfile

from ...adaptadores.partidaBinaria import PartidaBinaria
from ...modelo.actores.comportamientos import crear_comportamiento
from ...modelo.actores.enemigo import Enemigo
from ...modelo.actores.jugador import Jugador
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.mundo.mundo import Mundo
from ...modelo.mundo.sala import Sala
from ...modelo.mundo.salida import Salida
from ...modelo.mundo.trampa import Trampa
from ...modelo.nucleo.mutador import Mutador
from ...modelo.nucleo.fabricaEntidades import FabricaEntidades
from ...modelo.nucleo.partida import Partida
from ...modelo.objetos.objeto import crear_objeto
from ...modelo.puertos.dto import (
    FichaArmaDTO, FichaEnemigoDTO, FichaTrampaDTO, JugadorDTO)
from ...modelo.reloj.agenda import Agenda
from ...modelo.reloj.eventos import EventoAccionActor
from .medidor import Medidor
from .reporte import Reporte

SEMILLA = 2026
FICHA_ENEMIGO = FichaEnemigoDTO("e-tipo", "Enemigo", 20, 5, 2, 90, "guardian", ListaEnlazada())
FICHA_OBJETO = FichaArmaDTO("o-tipo", "Objeto", 2, 5, 1)
FICHA_TRAMPA = FichaTrampaDTO("t-tipo", "Trampa", 3, None)


class _ServicioSoloFichas:
    """Lo único que PartidaBinaria.cargar() necesita del servicio en esta
    medición: resolver siempre la misma ficha (no hay red ni disco de por
    medio; el bench no mide la resolución de fichas, solo el guardado)."""

    def resolver_fichas(self, ids):
        resultado = ListaEnlazada()
        for id_pedido in ids:
            if id_pedido == FICHA_ENEMIGO.id:
                resultado.agregar_al_final(FICHA_ENEMIGO)
            elif id_pedido == FICHA_OBJETO.id:
                resultado.agregar_al_final(FICHA_OBJETO)
            else:
                resultado.agregar_al_final(FICHA_TRAMPA)
        return resultado


def construir_partida_sintetica(cantidad_salas: int) -> Partida:
    """Una partida con 'cantidad_salas' salas en fila, cada una con un
    enemigo activo (con turno pendiente en la agenda), un objeto en el suelo
    y una trampa armada: una carga pareja, ni vacía ni artificialmente densa."""
    servicio = _ServicioSoloFichas()
    partida = Partida.__new__(Partida)
    partida.servicio = servicio
    partida.mutador = Mutador()
    partida.datos = type("Datos", (), {"id": "cripta-bench", "version": "v1"})()
    partida.version_catalogo = "cat-1"
    partida.semilla = SEMILLA
    partida.azar = random.Random(SEMILLA)
    partida.reloj = 1000
    partida.fin = None
    partida.diario = None
    partida._mensajes = ListaEnlazada()
    partida.agenda = Agenda()
    partida.mutador.agenda = partida.agenda

    datos_mundo = type("D", (), {
        "sala_inicial": 1, "sala_salida": cantidad_salas,
        "llave_salida": None, "inventario_max": 8,
        "jugador": JugadorDTO(30, 6, 3, 100)})()
    partida.mundo = Mundo(datos_mundo)

    siguiente_id_objeto = 1
    for numero in range(1, cantidad_salas + 1):
        siguiente = numero + 1 if numero < cantidad_salas else None
        salida_norte = Salida("N", siguiente) if siguiente is not None else None
        sala = Sala(numero, f"Sala {numero}", (salida_norte, None, None, None))
        sala.contenido_cargado = True
        partida.mundo._salas.agregar_al_final(sala)

        enemigo = Enemigo(f"e-{numero}", FICHA_ENEMIGO, 20, numero,
                           crear_comportamiento(FICHA_ENEMIGO.comportamiento))
        enemigo.activo = True
        turno = EventoAccionActor(partida.reloj + numero, enemigo)
        partida.agenda.programar(turno)
        enemigo.evento_accion = turno
        sala.activos.agregar_al_final(enemigo)

        objeto = crear_objeto(siguiente_id_objeto, FICHA_OBJETO)
        siguiente_id_objeto += 1
        sala.suelo.agregar_al_final(objeto)

        trampa = Trampa(f"t-{numero}", FICHA_TRAMPA, numero)
        sala.trampas.agregar_al_final(trampa)

    jugador = Jugador(datos_mundo.jugador, 1, 8)
    turno_jugador = EventoAccionActor(partida.reloj, jugador)
    partida.agenda.programar(turno_jugador)
    jugador.evento_accion = turno_jugador
    partida.jugador = jugador
    partida._fabrica = FabricaEntidades(servicio)
    partida._fabrica._siguiente_id_objeto = siguiente_id_objeto

    return partida, servicio


def _volcar_json_equivalente(partida) -> str:
    """Arma una estructura con, al menos, la misma información que guarda
    PartidaBinaria, y la serializa con json.dumps: es la comparación justa
    que pide §4.10 (mismo estado, el otro formato). Usar dict/list aquí
    sirve SOLO para hablar con json.dumps, igual que en puntajesArchivo.py
    y almacenLocalDisco.py; no sustituye ninguna estructura del programa."""
    salas = []
    for sala in partida.mundo:
        salas.append({
            "id": sala.id,
            "nombre": sala.nombre,
            "salidas": [
                None if salida is None else {
                    "destino": salida.destino, "cerrada": salida.cerrada,
                    "llave": salida.llave, "cierre_automatico": salida.cierre_automatico,
                }
                for salida in sala.salidas
            ],
            "rastro": sala.rastro,
            "activos": [
                {"id_instancia": e.id_instancia, "id_ficha": e.ficha.id, "vida": e.vida,
                 "vida_max": e.vida_max, "ataque": e.ataque, "defensa": e.defensa,
                 "velocidad": e.velocidad}
                for e in sala.activos
            ],
            "suelo": [{"id_instancia": o.id_instancia, "id_ficha": o.ficha.id}
                      for o in sala.suelo],
            "trampas": [{"id_instancia": t.id_instancia, "id_ficha": t.ficha.id,
                         "armada": t.armada} for t in sala.trampas],
        })
    version, estado_interno, gauss_next = partida.azar.getstate()
    datos = {
        "id_cripta": partida.datos.id, "version_cripta": partida.datos.version,
        "semilla": partida.semilla, "reloj": partida.reloj, "fin": partida.fin,
        "azar": {"version": version, "estado": list(estado_interno), "gauss_next": gauss_next},
        "jugador": {
            "vida": partida.jugador.vida, "vida_max": partida.jugador.vida_max,
            "ataque": partida.jugador.ataque, "defensa": partida.jugador.defensa,
            "velocidad": partida.jugador.velocidad, "sala": partida.jugador.sala,
            "acciones": partida.jugador.acciones,
            "enemigos_derrotados": partida.jugador.enemigos_derrotados,
        },
        "salas": salas,
    }
    return json.dumps(datos)


def _archivo_temporal(sufijo: str) -> str:
    descriptor, ruta = tempfile.mkstemp(suffix=sufijo, prefix="bench_guardado_")
    os.close(descriptor)
    return ruta


class EscenarioGuardarBinario:
    def __init__(self, partida, ruta):
        self._partida = partida
        self._ruta = ruta

    def preparar(self, n):
        pass

    def ejecutar(self):
        PartidaBinaria.guardar(self._partida, self._ruta)


class EscenarioCargarBinario:
    def __init__(self, ruta, servicio):
        self._ruta = ruta
        self._servicio = servicio

    def preparar(self, n):
        pass

    def ejecutar(self):
        PartidaBinaria.cargar(self._ruta, self._servicio)


class EscenarioGuardarJson:
    def __init__(self, partida, ruta):
        self._partida = partida
        self._ruta = ruta

    def preparar(self, n):
        pass

    def ejecutar(self):
        with open(self._ruta, "w", encoding="utf-8") as archivo:
            archivo.write(_volcar_json_equivalente(self._partida))


class EscenarioCargarJson:
    def __init__(self, ruta):
        self._ruta = ruta

    def preparar(self, n):
        pass

    def ejecutar(self):
        with open(self._ruta, "r", encoding="utf-8") as archivo:
            json.loads(archivo.read())


class EscenarioCargarUnaSalaBinario:
    """El punto fuerte real del binario: leer UNA sala sin tocar el resto
    del archivo (§4.10), usando el índice. Se compara contra cargar TODO el
    JSON equivalente solo para leer una sala de ahí (JSON no tiene índice:
    no hay forma más barata de sacar una sola sala que parsearlo entero)."""

    def __init__(self, ruta, id_sala, servicio):
        self._ruta = ruta
        self._id_sala = id_sala
        self._servicio = servicio

    def preparar(self, n):
        pass

    def ejecutar(self):
        PartidaBinaria.cargar_sala(self._ruta, self._id_sala, self._servicio)


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    tamanios = (10, 50) if rapido else (10, 50, 200)

    reporte.titulo("Guardado de partida: binario contra JSON (§4.10)")
    reporte.nota("Misma partida sintética (N salas, cada una con un enemigo activo, "
                 "un objeto y una trampa) guardada de las dos formas.")

    filas_tamano = ListaEnlazada()
    filas_tiempo = ListaEnlazada()
    filas_parcial = ListaEnlazada()
    for cantidad_salas in tamanios:
        partida, servicio = construir_partida_sintetica(cantidad_salas)
        ruta_bin = _archivo_temporal(".bin")
        ruta_json = _archivo_temporal(".json")
        try:
            PartidaBinaria.guardar(partida, ruta_bin)
            with open(ruta_json, "w", encoding="utf-8") as archivo:
                archivo.write(_volcar_json_equivalente(partida))

            tamano_bin = os.path.getsize(ruta_bin)
            tamano_json = os.path.getsize(ruta_json)
            filas_tamano.agregar_al_final((
                str(cantidad_salas), f"{tamano_bin:,}", f"{tamano_json:,}",
                f"{tamano_json / tamano_bin:.2f}x"))

            medicion_carga_bin = medidor.medir(EscenarioCargarBinario(ruta_bin, servicio), cantidad_salas)
            medicion_carga_json = medidor.medir(EscenarioCargarJson(ruta_json), cantidad_salas)
            medicion_guarda_bin = medidor.medir(EscenarioGuardarBinario(partida, ruta_bin), cantidad_salas)
            medicion_guarda_json = medidor.medir(EscenarioGuardarJson(partida, ruta_json), cantidad_salas)
            filas_tiempo.agregar_al_final((
                str(cantidad_salas),
                f"{medicion_guarda_bin.minimo * 1000:.3f}", f"{medicion_guarda_json.minimo * 1000:.3f}",
                f"{medicion_carga_bin.minimo * 1000:.3f}", f"{medicion_carga_json.minimo * 1000:.3f}"))

            sala_del_medio = max(1, cantidad_salas // 2)
            medicion_parcial = medidor.medir(
                EscenarioCargarUnaSalaBinario(ruta_bin, sala_del_medio, servicio), cantidad_salas)
            filas_parcial.agregar_al_final((
                str(cantidad_salas),
                f"{medicion_carga_bin.minimo * 1000:.3f}",
                f"{medicion_parcial.minimo * 1000:.3f}",
                f"{medicion_carga_bin.minimo / medicion_parcial.minimo:.1f}x"))
        finally:
            for ruta in (ruta_bin, ruta_json):
                if os.path.exists(ruta):
                    os.remove(ruta)

    reporte.tabla("1. Tamaño en disco (bytes)",
                  ("salas", "binario", "json", "json / binario"), filas_tamano)
    reporte.tabla("2. Tiempo mínimo de guardar y cargar la partida COMPLETA (milisegundos)",
                  ("salas", "guardar bin", "guardar json", "cargar bin", "cargar json"),
                  filas_tiempo)
    reporte.tabla("3. Cargar la partida completa contra cargar UNA sola sala (binario, ms)",
                  ("salas", "cargar completa", "cargar 1 sala", "cuánto más rápido"),
                  filas_parcial)

    reporte.nota("")
    reporte.nota("El binario pesa menos en disco (sin comas, llaves ni nombres de campo "
                 "repetidos por cada sala): la tabla 1 lo confirma. En tiempo de carga "
                 "COMPLETA, el parser de json de la biblioteca estándar (en C) le gana al "
                 "lector binario (en Python puro) para estos tamaños: la tabla 2 lo muestra "
                 "tal cual salió, sin maquillar el resultado. La ventaja real del binario no "
                 "es esa: es poder recuperar UNA sala sin leer el archivo completo (§4.10), "
                 "algo que el JSON de esta comparación no ofrece en absoluto (no tiene "
                 "índice: la única forma de sacar una sala de ahí es parsearlo entero). La "
                 "tabla 3 lo mide: cargar_sala() no paga el costo de las demás salas.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()