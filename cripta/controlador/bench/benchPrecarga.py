"""Mediciones de la espera de red (§4.2, D1, D34): precarga por BFS en segundo
plano contra la alternativa descartada de pedir el contenido de cada sala
recién al entrar (todo síncrono y bajo demanda).

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchPrecarga            (completo)
    python -m cripta.controlador.bench.benchPrecarga --rapido   (versión corta)

Usa las piezas REALES del programa (ServicioDatos, FuenteAsincrona y
PlanificadorPrecarga) sobre una FuenteDatos simulada que tarda LATENCIA_MS en
cada solicitud. La cripta es una cuadrícula de ANCHO salas por fila, todas
las puertas abiertas, y el jugador la recorre entera en zigzag; en cada sala
se queda un tiempo "pensando" antes de moverse, igual que una persona.

Para que --bench no tarde minutos, el tiempo está escalado 1:10: 40 ms de
latencia representan los ~400 ms reales de una solicitud. Lo que importa es
la proporción entre el tiempo que piensa el jugador y la latencia.
"""
import sys
import threading
import time

from ...modelo.datos.cacheFichas import CacheFichas
from ...modelo.datos.fuenteAsincrona import FuenteAsincrona
from ...modelo.datos.servicioDatos import ServicioDatos
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.puertos.dto import (ContenidoSalaDTO, DatosCriptaDTO, JugadorDTO,
                                   PaginaSalasDTO, ResumenCriptaDTO, SalaDTO, SalidaDTO)
from ...modelo.puertos.fuenteDatos import FuenteDatos, validar_lote
from .reporte import Reporte

LATENCIA_MS = 40               # escala 1:10 de los ~400 ms reales
ANCHO = 5                      # salas por fila de la cuadrícula
SALAS_POR_PAGINA = 10
UMBRAL_ESPERA_MS = 2           # menos que esto no es "quedarse esperando"


def _salidas(id_sala, total):
    fila, columna = divmod(id_sala - 1, ANCHO)
    salidas = ListaEnlazada()
    if fila > 0:
        salidas.agregar_al_final(SalidaDTO(direccion="N", sala=id_sala - ANCHO))
    if id_sala + ANCHO <= total:
        salidas.agregar_al_final(SalidaDTO(direccion="S", sala=id_sala + ANCHO))
    if columna < ANCHO - 1 and id_sala < total:
        salidas.agregar_al_final(SalidaDTO(direccion="E", sala=id_sala + 1))
    if columna > 0:
        salidas.agregar_al_final(SalidaDTO(direccion="O", sala=id_sala - 1))
    return salidas


class FuenteLenta(FuenteDatos):
    """FuenteDatos simulada: cada solicitud tarda `latencia` segundos y se
    cuenta, como lo haría ContadorSolicitudes."""

    def __init__(self, total_salas, latencia):
        self._total = total_salas
        self._latencia = latencia
        self._solicitudes = 0
        self._cerrojo = threading.Lock()

    def _contar(self):
        with self._cerrojo:
            self._solicitudes += 1

    def listar_criptas(self):
        lista = ListaEnlazada()
        lista.agregar_al_final(ResumenCriptaDTO(id="bench", nombre="Bench",
                                                salas=self._total, dificultad=1))
        return lista

    def datos_generales(self, id_cripta):
        paginas = (self._total + SALAS_POR_PAGINA - 1) // SALAS_POR_PAGINA
        return DatosCriptaDTO(
            id=id_cripta, version="v1", salas_total=self._total, paginas=paginas,
            salas_por_pagina=SALAS_POR_PAGINA, sala_inicial=1, sala_salida=self._total,
            llave_salida="itm_llave", presupuesto_solicitudes=10_000, inventario_max=10,
            jugador=JugadorDTO(vida_max=30, ataque=5, defensa=2, velocidad=100))

    def esqueleto(self, id_cripta, pagina):
        salas = ListaEnlazada()
        primera = (pagina - 1) * SALAS_POR_PAGINA + 1
        for id_sala in range(primera, min(primera + SALAS_POR_PAGINA, self._total + 1)):
            salas.agregar_al_final(SalaDTO(id=id_sala, nombre=f"Sala {id_sala}",
                                           salidas=_salidas(id_sala, self._total)))
        paginas = (self._total + SALAS_POR_PAGINA - 1) // SALAS_POR_PAGINA
        return PaginaSalasDTO(pagina=pagina, total_paginas=paginas, salas=salas)

    def contenido(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        self._contar()
        time.sleep(self._latencia)
        resultado = ListaEnlazada()
        for id_sala in ids_salas:
            resultado.agregar_al_final(ContenidoSalaDTO(
                sala=id_sala, enemigos=ListaEnlazada(), objetos=ListaEnlazada(),
                trampas=ListaEnlazada()))
        return resultado

    def catalogo(self, ids):
        return ListaEnlazada()

    def version_cripta(self, id_cripta):
        return "v1"

    def version_catalogo(self):
        return "c1"

    def solicitudes_realizadas(self):
        with self._cerrojo:
            return self._solicitudes

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        with self._cerrojo:
            self._solicitudes = 0


def recorrido_zigzag(total):
    """Todas las salas, fila por fila, alternando el sentido: cada paso va a
    una sala vecina (como caminaría el jugador)."""
    camino = ListaEnlazada()
    filas = (total + ANCHO - 1) // ANCHO
    for fila in range(filas):
        columnas = range(ANCHO) if fila % 2 == 0 else range(ANCHO - 1, -1, -1)
        for columna in columnas:
            id_sala = fila * ANCHO + columna + 1
            if id_sala <= total:
                camino.agregar_al_final(id_sala)
    return camino


def jugar(total, pensar_ms, con_precarga, latencia_ms=LATENCIA_MS):
    """Recorre la cripta como lo hace Partida: al entrar, asegurar_contenido
    (bloquea si falta) y, con la decisión, precargar (no bloquea).
    Devuelve (esperas, espera_total_ms, solicitudes)."""
    fuente = FuenteLenta(total, latencia_ms / 1000)
    asincrona = FuenteAsincrona(fuente)
    try:
        servicio = ServicioDatos(fuente, asincrona, CacheFichas(), None)
        servicio.iniciar_cripta("bench")
        fuente.reiniciar_conteo()          # solo cuenta el contenido de salas
        esperas = 0
        espera_total = 0.0
        for id_sala in recorrido_zigzag(total):
            inicio = time.perf_counter()
            servicio.asegurar_contenido(id_sala)
            espera = (time.perf_counter() - inicio) * 1000
            if espera >= UMBRAL_ESPERA_MS:
                esperas += 1
                espera_total += espera
            if con_precarga:
                servicio.precargar(id_sala)
            time.sleep(pensar_ms / 1000)
        return esperas, espera_total, fuente.solicitudes_realizadas()
    finally:
        asincrona.cerrar()


def verificar_determinismo(total):
    """D19: con precarga, las solicitudes son las mismas con otra latencia."""
    lenta = jugar(total, 1, True, latencia_ms=LATENCIA_MS)[2]
    rapida = jugar(total, 1, True, latencia_ms=1)[2]
    if lenta != rapida:
        raise RuntimeError(f"Las solicitudes dependen de la latencia: {lenta} y {rapida}")
    return lenta


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    tamanos = (20,) if rapido else (20, 50)
    pensamientos = (LATENCIA_MS,) if rapido else (LATENCIA_MS // 2, 2 * LATENCIA_MS)

    reporte.titulo("Espera de red: precarga contra pedir al entrar (§4.2)")
    reporte.nota(f"Latencia simulada {LATENCIA_MS} ms por solicitud (escala 1:10 de ~400 ms); "
                 f"cuadrícula de {ANCHO} salas por fila recorrida entera en zigzag.")
    solicitudes = verificar_determinismo(tamanos[0])
    reporte.nota(f"Verificación: con precarga, {tamanos[0]} salas gastan {solicitudes} "
                 f"solicitudes tanto con {LATENCIA_MS} ms como con 1 ms de latencia.")

    filas = ListaEnlazada()
    for total in tamanos:
        for pensar in pensamientos:
            for con_precarga, nombre in ((True, "precarga BFS (decisión)"),
                                         (False, "pedir al entrar")):
                esperas, espera_total, solicitudes = jugar(total, pensar, con_precarga)
                filas.agregar_al_final((str(total), f"{pensar} ms", nombre, str(esperas),
                                        f"{espera_total:.0f}", str(solicitudes)))
    reporte.tabla("Esperas del jugador al entrar a una sala (tiempo real, la partida no cambia)",
                  ("salas", "piensa por sala", "estrategia", "veces que esperó",
                   "espera total ms", "solicitudes"), filas)
    reporte.nota("")
    reporte.nota("Pidiendo al entrar, el jugador espera una latencia completa en CADA sala "
                 "y gasta una solicitud por sala. Con la precarga solo espera al principio "
                 "(o si piensa menos que la latencia) y gasta unas salas/10 solicitudes. "
                 "El número de solicitudes no depende de la latencia (D19).")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
