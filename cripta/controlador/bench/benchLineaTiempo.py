"""Mediciones de la línea de tiempo (004-linea-tiempo, FR-019 a FR-024, §5.5,
§6.3). Ver specs/004-linea-tiempo/research.md (R1 a R4, R6, R10).

    python -m cripta.controlador.bench.benchLineaTiempo [--rapido]

Partida determinista por semilla sobre la cripta de más salas de
datos_offline/ (elegida por cantidad de salas, sin ids en el código), con el
jugador sin daño letal para llegar a miles de acciones (solo para medir):
70 % movimientos y 30 % esperas al azar con random.Random(semilla).

  1. Memoria y tiempo de consulta con K = 10, 25 y 50 y sin puntos de control.
  2. Adelante contra atrás: re-simular desde el punto de control (decisión)
     contra copiar el estado actual y deshacer K acciones con el Diario.
  3. Ubicar el bloque de un instante: búsqueda binaria en el ArregloArbol
     contra búsqueda lineal, con 10² a 10⁵ bloques.
  4. Recorte con el pergamino según el largo de la historia.
  5. Tamaño y tiempo de un punto de control y del guardado del formato 4.
"""
from __future__ import annotations

import random
import sys
import tempfile
import time
import tracemalloc

from ...adaptadores.almacenLocalDisco import AlmacenLocalDisco
from ...adaptadores.fuenteOffline import FuenteOffline
from ...adaptadores.partidaBinaria import CopiadorBinario, PartidaBinaria
from ...modelo.datos.cacheFichas import CacheFichas
from ...modelo.datos.fuenteAsincrona import FuenteAsincrona
from ...modelo.datos.servicioDatos import ServicioDatos
from ...modelo.estructuras.arregloArbol import ArregloArbol
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.nucleo.accion import Esperar, Mover
from ...modelo.nucleo.diario import Diario
from ...modelo.nucleo.lineaTiempo import K_POR_OMISION, LineaTiempo
from ...modelo.nucleo.partida import Partida
from .alternativasLineaTiempo import K_SIN_PUNTOS_DE_CONTROL, BloquesLineales
from .reporte import Reporte

CARPETA_OFFLINE = "datos_offline"
SEMILLA = 123
VIDA_SIN_LIMITE = 10 ** 9
LIMITE_MS = 50                 # §6.1
VALORES_K = (10, 25, 50)


def _servicio():
    fuente = FuenteOffline(CARPETA_OFFLINE)
    mayor = None
    for resumen in fuente.listar_criptas():
        if mayor is None or resumen.salas > mayor.salas:
            mayor = resumen
    servicio = ServicioDatos(fuente, FuenteAsincrona(fuente), CacheFichas(500),
                             AlmacenLocalDisco(tempfile.mkdtemp(prefix="bench_linea_")))
    servicio.iniciar_cripta(mayor.id)
    return servicio, mayor


def _partida(servicio, k, acciones):
    """Una partida jugada con la línea de K, determinista por semilla."""
    partida = Partida(servicio)
    partida.iniciar(SEMILLA)
    partida.jugador.vida_max = VIDA_SIN_LIMITE
    partida.jugador.vida = VIDA_SIN_LIMITE
    tracemalloc.start()
    partida.conectar_linea(LineaTiempo(k, CopiadorBinario()))
    azar = random.Random(SEMILLA)
    while partida.jugador.acciones < acciones and not partida.terminada():
        sala = partida.mundo.sala(partida.jugador.sala)
        direcciones = ListaEnlazada()
        for salida in sala.salidas:
            if salida is not None and salida.transitable():
                direcciones.agregar_al_final(salida.direccion)
        if not direcciones.esta_vacia() and azar.random() < 0.7:
            partida.aplicar_accion(Mover(direcciones.obtener(azar.randrange(len(direcciones)))))
        else:
            partida.aplicar_accion(Esperar())
    memoria, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return partida, memoria


def _tiempos_de_consulta(partida, consultas, semilla):
    """(mediana, peor) en ms de reconstruir instantes al azar (mínimo de 2
    repeticiones por instante)."""
    azar = random.Random(semilla)
    tiempos = ListaEnlazada()
    for _ in range(consultas):
        t = azar.randint(0, partida.reloj)
        mejor = None
        for _ in range(2):
            inicio = time.perf_counter()
            partida.linea.reconstruir_instante(t, partida)
            duracion = (time.perf_counter() - inicio) * 1000
            mejor = duracion if mejor is None else min(mejor, duracion)
        tiempos.agregar_al_final(mejor)
    ordenados = _ordenar(tiempos)
    return ordenados.obtener(len(ordenados) // 2), ordenados.obtener(len(ordenados) - 1)


def _ordenar(valores: ListaEnlazada) -> ListaEnlazada:
    """Inserción sobre ListaEnlazada (pocos valores; sin sorted)."""
    resultado = ListaEnlazada()
    for valor in valores:
        posicion = 0
        for existente in resultado:
            if existente > valor:
                break
            posicion += 1
        nueva = ListaEnlazada()
        indice = 0
        for existente in resultado:
            if indice == posicion:
                nueva.agregar_al_final(valor)
            nueva.agregar_al_final(existente)
            indice += 1
        if indice == posicion:
            nueva.agregar_al_final(valor)
        resultado = nueva
    return resultado


def _tabla_k(reporte, servicio, acciones, rapido):
    filas = ListaEnlazada()
    consultas = 10 if rapido else 30
    for k in VALORES_K:
        partida, memoria = _partida(servicio, k, acciones)
        mediana, peor = _tiempos_de_consulta(partida, consultas, k)
        filas.agregar_al_final((str(k), str(len(partida.linea.bloques)), f"{memoria // 1024}",
                                f"{mediana:.1f}", f"{peor:.1f}",
                                "sí" if peor < LIMITE_MS else "no"))
    sin, memoria = _partida(servicio, K_SIN_PUNTOS_DE_CONTROL, acciones // (5 if rapido else 10))
    mediana, peor = _tiempos_de_consulta(sin, 3, 1)
    filas.agregar_al_final((f"sin puntos ({sin.jugador.acciones} acciones)",
                            str(len(sin.linea.bloques)), f"{memoria // 1024}",
                            f"{mediana:.1f}", f"{peor:.1f}", "sí" if peor < LIMITE_MS else "no"))
    reporte.tabla(f"1. Memoria y consulta según K ({acciones} acciones del jugador)",
                  ("K", "bloques", "memoria KiB", "consulta mediana ms", "consulta peor ms",
                   f"< {LIMITE_MS} ms"), filas)


def _tabla_adelante_atras(reporte, servicio, acciones):
    """(a) re-simular desde el punto de control contra (c) copiar el estado
    actual y deshacer K acciones con el Diario (sobre una copia)."""
    filas = ListaEnlazada()
    copiador = CopiadorBinario()
    partida, _ = _partida(servicio, K_POR_OMISION, acciones)
    adelante, _ = _tiempos_de_consulta(partida, 10, 3)
    inicio = time.perf_counter()
    datos = copiador.tomar(partida)
    copia = copiador.restaurar(datos, servicio)
    copiar_ms = (time.perf_counter() - inicio) * 1000
    copia.jugador.vida = VIDA_SIN_LIMITE
    copia.conectar_diario(Diario(K_POR_OMISION))
    azar = random.Random(9)
    for _ in range(K_POR_OMISION):
        copia.aplicar_accion(Mover("N") if azar.random() < 0.5 else Esperar())
    inicio = time.perf_counter()
    while copia.deshacer():
        pass
    deshacer_ms = (time.perf_counter() - inicio) * 1000
    filas.agregar_al_final(("adelante (decisión): restaurar + re-simular ≤ K",
                            f"{adelante:.1f}", "acciones de la historia (unos 100 B por acción)"))
    filas.agregar_al_final(("atrás: copiar el estado actual", f"{copiar_ms:.1f}", "—"))
    filas.agregar_al_final(("atrás: + deshacer K acciones con el Diario",
                            f"{copiar_ms + deshacer_ms:.1f}",
                            "todos los cambios de la partida, no solo 5 acciones"))
    reporte.tabla(f"2. Reconstruir hacia adelante o hacia atrás (K = {K_POR_OMISION}), ms",
                  ("estrategia", "consulta ms", "qué hay que guardar"), filas)


class _BloqueFalso:
    __slots__ = ("tiempo_inicio",)

    def __init__(self, tiempo_inicio: int) -> None:
        self.tiempo_inicio = tiempo_inicio


def _tabla_busqueda(reporte, rapido):
    filas = ListaEnlazada()
    for n in ((100, 1000, 10_000) if rapido else (100, 1000, 10_000, 100_000)):
        arbol = ArregloArbol()
        lineal = BloquesLineales()
        for i in range(n):
            bloque = _BloqueFalso(i * 100)
            arbol.agregar_al_final(bloque)
            lineal.agregar_al_final(bloque)
        linea = LineaTiempo(1)
        linea._bloques = arbol
        azar = random.Random(n)
        instantes = ListaEnlazada()
        for _ in range(200):
            instantes.agregar_al_final(azar.randint(0, n * 100))
        inicio = time.perf_counter()
        for t in instantes:
            linea._posicion_de_instante(t)
        binaria = (time.perf_counter() - inicio) / 200 * 1e6
        inicio = time.perf_counter()
        for t in instantes:
            lineal.posicion_de_instante(t)
        recorrido = (time.perf_counter() - inicio) / 200 * 1e6
        filas.agregar_al_final((str(n), f"{binaria:.1f}", f"{recorrido:.1f}",
                                f"{recorrido / binaria:.0f}x"))
    reporte.tabla("3. Ubicar el bloque de un instante, µs por consulta",
                  ("bloques", "árbol (decisión)", "lineal", "lineal / árbol"), filas)


def _tabla_recorte(reporte, servicio, rapido):
    filas = ListaEnlazada()
    for n in ((100, 1000) if rapido else (100, 1000, 5000)):
        partida, _ = _partida(servicio, K_POR_OMISION, n)
        inicio = time.perf_counter()
        partida.linea.al_usar_pergamino(partida)
        microsegundos = (time.perf_counter() - inicio) * 1e6
        filas.agregar_al_final((str(n), str(partida.linea.ultimo_recorte), f"{microsegundos:.0f}"))
    reporte.tabla("4. Recortar la línea con el pergamino según el largo de la historia",
                  ("acciones", "entradas y bloques tocados", "µs"), filas)


def _tabla_punto_control(reporte, servicio, acciones):
    """Un punto de control (sin la línea) y el guardado del formato 4 de una
    partida de 'acciones' acciones (con la línea completa, T033 punto 5)."""
    filas = ListaEnlazada()
    partida, _ = _partida(servicio, K_POR_OMISION, acciones)
    for nombre, con_linea in (("punto de control", False), ("guardado formato 4", True)):
        inicio = time.perf_counter()
        datos = PartidaBinaria.a_bytes(partida, con_linea=con_linea)
        escribir = (time.perf_counter() - inicio) * 1000
        inicio = time.perf_counter()
        PartidaBinaria.desde_bytes(datos, servicio)
        leer = (time.perf_counter() - inicio) * 1000
        filas.agregar_al_final((nombre, f"{len(datos) // 1024}", f"{escribir:.1f}", f"{leer:.1f}"))
    reporte.tabla(f"5. Punto de control y guardado con la línea ({acciones} acciones, K = "
                  f"{K_POR_OMISION})", ("qué", "KiB", "escribir ms", "leer ms"), filas)


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    servicio, cripta = _servicio()
    acciones = 1000 if rapido else 5000
    reporte.titulo("Línea de tiempo: mediciones (004, §5.5, §6.3)")
    reporte.nota(f"Cripta de referencia: la de más salas ({cripta.salas} salas); "
                 f"semilla {SEMILLA}; K por omisión {K_POR_OMISION}.")
    _tabla_k(reporte, servicio, acciones, rapido)
    _tabla_adelante_atras(reporte, servicio, 300 if rapido else 1000)
    _tabla_busqueda(reporte, rapido)
    _tabla_recorte(reporte, servicio, rapido)
    _tabla_punto_control(reporte, servicio, acciones)
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
