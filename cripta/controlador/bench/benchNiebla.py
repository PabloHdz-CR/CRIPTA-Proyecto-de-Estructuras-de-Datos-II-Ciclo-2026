"""Mediciones de 002-niebla-guerra (T046; FR-031 a FR-033, SC-004, SC-005,
research R11, §5.3 y §6.3 del enunciado).

Cinco tablas, cada una con la alternativa que el plan descartó al lado:
  1. Un paso de «ir a» con el mapa conocido completo: cripta de referencia
     (recuerdos reales y todos abiertos) y malla de 1024 salas, frente a
     RutaHaciaAtras. Criterio: peor < 5 ms en la referencia (FR-031).
  2. Consultar el estado de una sala con 25, 100, 300 y 1200 conocidas:
     campo del objeto frente a ConsultaLineal. Criterio: al multiplicar por 4
     el mapa, la media no crece más de 1,5 veces (SC-005).
  3. Explorar con antorcha (revela 4 salas) con mapas de esos tamaños:
     registro en orden de descubrimiento frente a RegistroOrdenado. Mismo
     criterio (SC-005, FR-033).
  4. Registros del Diario y tiempo de deshacer una entrada con antorcha según
     las salas reveladas (1 a 4): crecen con lo revelado (FR-033).
  5. Armar el panel del mapa (copiar y ordenar las conocidas por id) con 300
     y 1200 conocidas (dato informativo, research R4).

La cripta de referencia es la de más salas de datos_offline/, elegida en
ejecución, sin ids en el código (principio IV).

Uso: py -m cripta.controlador.bench.benchNiebla [--rapido]
"""
from __future__ import annotations

import gc
import random
import sys
import time

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.mundo.buscadorRuta import BuscadorRuta
from ...modelo.mundo.conocimiento import (
    ABIERTA, CERRADA, EXPLORADA, ConocimientoJugador, RegistroConocidas)
from ...modelo.mundo.mundo import Mundo
from ...modelo.mundo.sala import Sala
from ...modelo.mundo.salida import Salida
from ...modelo.nucleo.diario import Diario
from ...modelo.nucleo.mutador import Mutador
from .alternativasNiebla import ConsultaLineal, RegistroOrdenado, RutaHaciaAtras
from .benchCazador import cripta_de_referencia, malla
from .medidor import Medidor
from .reporte import Reporte

LIMITE_PASO_MS = 5.0          # FR-031, §6.1
CRECIMIENTO_MAXIMO = 1.5      # SC-005: al multiplicar por 4 el mapa conocido
TAMANOS_MAPA = (25, 100, 300, 1200)
SEMILLA = 20261115


def _pasa(condicion: bool) -> str:
    return "PASA" if condicion else "NO PASA"


# ---------------------------------------------------------------------------
# 1. Un paso de «ir a»
# ---------------------------------------------------------------------------

class _DatosMundo:
    def __init__(self, inicial: int, salida: int) -> None:
        self.sala_inicial = inicial
        self.sala_salida = salida
        self.llave_salida = "x"
        self.inventario_max = 10
        self.jugador = None


def mundo_conocido(cripta, todas_abiertas: bool) -> Mundo:
    """El mundo de la cripta con todas las salas exploradas y cada cara
    recordada como está (o abierta, para el peor caso)."""
    mundo = Mundo(_DatosMundo(cripta.salas.ver_primero().id, cripta.sala_salida))
    mundo.agregar_esqueleto(cripta.salas)
    mundo.enlazar()
    for sala in mundo:
        sala.conocimiento = EXPLORADA
        for salida in sala.salidas:
            if salida is not None:
                salida.recordada = ABIERTA if todas_abiertas or not salida.cerrada else CERRADA
    return mundo


def medir_paso(mundo, pares: int, repeticiones: int):
    """(peor ms, media ms, salas fijadas medias, peor ms atrás, media ms
    atrás, fijadas atrás, pares con el mismo primer paso, pares)."""
    salas = ListaEnlazada()
    for sala in mundo:
        salas.agregar_al_final(sala)
    azar = random.Random(SEMILLA)
    elegidos = ListaEnlazada()
    for _ in range(pares):
        origen = salas.obtener(azar.randrange(len(salas)))
        destino = salas.obtener(azar.randrange(len(salas)))
        if origen is not destino:
            elegidos.agregar_al_final((origen, destino))
    adelante = BuscadorRuta(mundo)
    atras = RutaHaciaAtras()
    resultado_a = _medir_buscador(adelante, elegidos, repeticiones)
    resultado_b = _medir_buscador(atras, elegidos, repeticiones)
    iguales = 0
    for origen, destino in elegidos:
        if adelante.primer_paso(origen, destino) is atras.primer_paso(origen, destino):
            iguales += 1
    return resultado_a + resultado_b + (iguales, len(elegidos))


def _medir_buscador(buscador, elegidos, repeticiones: int):
    peor = 0.0
    total = 0.0
    total_fijadas = 0
    for origen, destino in elegidos:
        mejor = None
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            buscador.primer_paso(origen, destino)
            ms = (time.perf_counter() - inicio) * 1000
            mejor = ms if mejor is None or ms < mejor else mejor
        total_fijadas += buscador.salas_fijadas_ultima
        total += mejor
        peor = mejor if mejor > peor else peor
    cantidad = max(1, len(elegidos))
    return (peor, total / cantidad, total_fijadas / cantidad)


# ---------------------------------------------------------------------------
# 2. Consultas
# ---------------------------------------------------------------------------

def _salas_sueltas(cantidad: int) -> ListaEnlazada:
    salas = ListaEnlazada()
    for i in range(cantidad):
        sala = Sala(i + 1, f"Sala {i + 1}", (Salida("N", i + 2), None, None, None))
        sala.conocimiento = EXPLORADA
        salas.agregar_al_final(sala)
    return salas


# Una consulta por campo dura décimas de µs: una sola pasada mide ruido (en
# otra máquina una corrida dio 2,16x de 300 a 1200 conocidas). Cada medición
# recorre los objetivos REPETICIONES_CONSULTA veces con el recolector apagado,
# y se toma el MÍNIMO de CORRIDAS_CONSULTA mediciones, como en Medidor.
REPETICIONES_CONSULTA = 5
CORRIDAS_CONSULTA = 9
CORRIDAS_CONSULTA_RAPIDO = 5
CORRIDAS_LINEAL = 3


def _minimo_por_consulta(trabajo, operaciones: int, corridas: int) -> float:
    """µs por operación: el mínimo de `corridas` ejecuciones de trabajo()."""
    mejor = None
    for _ in range(corridas):
        gc.collect()
        gc.disable()
        try:
            inicio = time.perf_counter()
            trabajo()
            duracion = time.perf_counter() - inicio
        finally:
            gc.enable()
        if mejor is None or duracion < mejor:
            mejor = duracion
    return mejor / operaciones * 1e6


class _ConsultasCampo:
    """REPETICIONES_CONSULTA pasadas por los objetivos: estado de la sala y
    recuerdo de su primera salida, leyendo los campos (la decisión, R1)."""

    def __init__(self, objetivos: ListaEnlazada) -> None:
        self._objetivos = objetivos

    def __call__(self) -> None:
        for _ in range(REPETICIONES_CONSULTA):
            for sala in self._objetivos:
                ConocimientoJugador.estado(sala)
                ConocimientoJugador.recuerdo(sala.salidas[0])


class _ConsultasLineales:
    """Las primeras `muestra` consultas con la búsqueda lineal por id."""

    def __init__(self, lineal: ConsultaLineal, objetivos: ListaEnlazada, muestra: int) -> None:
        self._lineal = lineal
        self._objetivos = objetivos
        self._muestra = muestra

    def __call__(self) -> None:
        for indice, sala in enumerate(self._objetivos):
            if indice >= self._muestra:
                break
            self._lineal.estado(sala.id)


def medir_consultas(cantidad: int, consultas: int, corridas: int = CORRIDAS_CONSULTA):
    """(µs por consulta con el campo, µs por consulta con búsqueda lineal),
    cada uno el mínimo de varias corridas."""
    salas = _salas_sueltas(cantidad)
    registro = RegistroConocidas()
    for sala in salas:
        registro.agregar(sala)
    lineal = ConsultaLineal(registro)
    azar = random.Random(SEMILLA)
    objetivos = ListaEnlazada()
    for _ in range(consultas):
        objetivos.agregar_al_final(salas.obtener(azar.randrange(cantidad)))
    campo = _minimo_por_consulta(_ConsultasCampo(objetivos), consultas * REPETICIONES_CONSULTA, corridas)
    muestra = consultas if consultas <= 2000 else 2000
    busqueda = _minimo_por_consulta(_ConsultasLineales(lineal, objetivos, muestra), muestra,
                                    CORRIDAS_LINEAL)
    return campo, busqueda


# ---------------------------------------------------------------------------
# 3 y 4. Exploración con antorcha, registros y deshacer
# ---------------------------------------------------------------------------

ENTRADAS_POR_MEDICION = 200   # se miden 200 entradas juntas: una sola dura ~10 µs (ruido)


class _EscenarioAntorcha:
    """`centros` salas centrales, cada una con `reveladas` vecinas
    desconocidas, más un mapa conocido de `n` salas ya registradas.
    ejecutar() hace una entrada con antorcha en cada centro (o la
    alternativa: insertar en orden las vecinas de cada centro y quitarlas,
    para que el registro no crezca entre una entrada y la siguiente)."""

    def __init__(self, reveladas: int, ordenado: bool, centros: int = ENTRADAS_POR_MEDICION) -> None:
        self._reveladas = reveladas
        self._ordenado = ordenado
        self._centros = centros

    def _centro(self, numero: int):
        direcciones = ("N", "S", "E", "O")
        vecinas = ListaEnlazada()
        salidas = ListaEnlazada()
        base = 100000 + numero * 10
        for i in range(self._reveladas):
            vecina = Sala(base + i + 1, "vecina", (None, None, None, None))
            vecinas.agregar_al_final(vecina)
            salida = Salida(direcciones[i], vecina.id)
            salida.enlazar(None, vecina, 100, None)
            salidas.agregar_al_final(salida)
        tupla = (salidas.obtener(0) if self._reveladas > 0 else None,
                 salidas.obtener(1) if self._reveladas > 1 else None,
                 salidas.obtener(2) if self._reveladas > 2 else None,
                 salidas.obtener(3) if self._reveladas > 3 else None)
        centro = Sala(base, "centro", tupla)
        centro.conocimiento = EXPLORADA
        return centro, vecinas

    def preparar(self, n: int) -> None:
        mundo = Mundo.__new__(Mundo)
        mundo.conocidas = RegistroConocidas()
        self.ordenado = RegistroOrdenado()
        al_reves = ListaEnlazada()
        for sala in _salas_sueltas(n):
            mundo.conocidas.agregar(sala)
            al_reves.agregar_al_inicio(sala)
        if self._ordenado:
            # De mayor a menor id: cada una entra por la cabeza (preparar no se
            # cronometra; ejecutar sí, y las vecinas nuevas van al final).
            for sala in al_reves:
                self.ordenado.agregar(sala)
        self.centros = ListaEnlazada()
        for numero in range(self._centros):
            self.centros.agregar_al_final(self._centro(numero))
        self.mutador = Mutador()
        self.diario = Diario(self._centros + 1)
        self.mutador.diario = self.diario
        self.conocimiento = ConocimientoJugador(mundo, self.mutador)

    def ejecutar(self) -> None:
        if self._ordenado:
            for _, vecinas in self.centros:
                for vecina in vecinas:
                    self.ordenado.agregar(vecina)
                for vecina in vecinas:
                    self.ordenado.quitar(vecina)
            return
        for centro, _ in self.centros:
            self.diario.abrir_intervalo(None)
            self.conocimiento.entrar(centro, antorcha=True)
            self.diario.cerrar_intervalo()


def medir_exploracion(n: int, repeticiones: int):
    """(µs con el registro en orden de descubrimiento, µs con RegistroOrdenado)."""
    medidor = Medidor(repeticiones)
    propio = medidor.medir(_EscenarioAntorcha(4, False), n).minimo * 1e6
    alternativa = medidor.medir(_EscenarioAntorcha(4, True), n).minimo * 1e6
    return propio / ENTRADAS_POR_MEDICION, alternativa / ENTRADAS_POR_MEDICION


def medir_registros(reveladas: int, repeticiones: int):
    """(registros del Diario, µs de deshacer) de una entrada con antorcha."""
    mejor = None
    registros = 0
    for _ in range(repeticiones):
        escenario = _EscenarioAntorcha(reveladas, False, centros=1)
        escenario.preparar(300)
        escenario.ejecutar()
        registros = len(escenario.diario._intervalos.ver_tope())
        inicio = time.perf_counter()
        escenario.diario.deshacer(None)
        us = (time.perf_counter() - inicio) * 1e6
        mejor = us if mejor is None or us < mejor else mejor
    return registros, mejor


def medir_panel(n: int, repeticiones: int) -> float:
    registro = RegistroConocidas()
    azar = random.Random(SEMILLA)
    salas = _salas_sueltas(n)
    for i in range(n):
        registro.agregar(salas.obtener(azar.randrange(len(salas))))
    mejor = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        registro.ordenadas_por_id()
        ms = (time.perf_counter() - inicio) * 1000
        mejor = ms if mejor is None or ms < mejor else mejor
    return mejor


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def ejecutar(reporte: Reporte, rapido: bool = False) -> Reporte:
    """Las cinco tablas de la niebla (las llama benchTodo)."""
    pares = 60 if rapido else 300
    repeticiones = 3 if rapido else 5
    consultas = 20000 if rapido else 100000
    reporte.titulo("Niebla de guerra e «ir a» (002-niebla-guerra)")

    filas = ListaEnlazada()
    referencia = cripta_de_referencia()
    for cripta, todas_abiertas, nombre in (
            (referencia, False, f"{referencia.nombre}, recuerdos reales"),
            (referencia, True, f"{referencia.nombre}, todas abiertas"),
            (malla(32), True, "malla 32x32 (1024 salas), todas abiertas")):
        r = medir_paso(mundo_conocido(cripta, todas_abiertas), pares, repeticiones)
        es_referencia = cripta is referencia
        filas.agregar_al_final((
            nombre, f"{r[0]:.3f}", f"{r[1]:.3f}", f"{r[2]:.0f}", f"{r[3]:.3f}", f"{r[4]:.3f}",
            f"{r[5]:.0f}", f"{r[6]}/{r[7]}",
            _pasa(r[0] < LIMITE_PASO_MS) if es_referencia else "estrés"))
    reporte.tabla(f"1. Un paso de «ir a» con el mapa conocido completo (límite {LIMITE_PASO_MS:.0f} ms, "
                  "FR-031): adelante con parada frente a atrás completo",
                  ("cripta", "peor ms", "media ms", "fijadas", "peor ms atrás",
                   "media ms atrás", "fijadas atrás", "mismo paso", "resultado"), filas)

    filas = ListaEnlazada()
    anteriores = ListaEnlazada()
    for n in TAMANOS_MAPA:
        campo, lineal = medir_consultas(n, consultas,
                                        CORRIDAS_CONSULTA_RAPIDO if rapido else CORRIDAS_CONSULTA)
        anteriores.agregar_al_final((n, campo, lineal))
        filas.agregar_al_final((f"{n}", f"{campo:.4f}", f"{lineal:.3f}", "-", "-"))
    filas = _con_crecimiento(anteriores, filas)
    reporte.tabla("2. Consultar estado de sala y recuerdo de puerta (µs por consulta, mínimo de "
                  f"{CORRIDAS_CONSULTA_RAPIDO if rapido else CORRIDAS_CONSULTA} corridas de "
                  f"{REPETICIONES_CONSULTA} pasadas, FR-032, SC-005)",
                  ("conocidas", "campo", "búsqueda lineal", "crec. x4 campo", "<= 1,5"), filas)

    filas = ListaEnlazada()
    anteriores = ListaEnlazada()
    for n in TAMANOS_MAPA:
        propio, ordenado = medir_exploracion(n, repeticiones)
        anteriores.agregar_al_final((n, propio, ordenado))
        filas.agregar_al_final((f"{n}", f"{propio:.2f}", f"{ordenado:.2f}", "-", "-"))
    filas = _con_crecimiento(anteriores, filas)
    reporte.tabla("3. Explorar con antorcha (4 salas reveladas, µs por entrada, media de 200): orden de descubrimiento "
                  "frente a inserción ordenada (FR-033, SC-005)",
                  ("conocidas", "propio", "inserción ordenada", "crec. x4 propio", "<= 1,5"), filas)

    filas = ListaEnlazada()
    for reveladas in (1, 2, 3, 4):
        registros, us = medir_registros(reveladas, repeticiones * 4)
        filas.agregar_al_final((f"{reveladas}", f"{registros}", f"{us:.2f}"))
    reporte.tabla("4. Registrar e invertir una entrada con antorcha (300 conocidas, FR-033)",
                  ("salas reveladas", "registros del Diario", "µs deshacer"), filas)

    filas = ListaEnlazada()
    for n in (300, 1200):
        filas.agregar_al_final((f"{n}", f"{medir_panel(n, repeticiones):.3f}"))
    reporte.tabla("5. Armar el panel del mapa: copiar y ordenar por id (ms, informativo, R4)",
                  ("conocidas", "ms"), filas)
    return reporte


def _con_crecimiento(medidas, filas) -> ListaEnlazada:
    """Agrega el cociente del valor propio al multiplicar el mapa por 4
    (25 -> 100 y 300 -> 1200) y su criterio (SC-005)."""
    resultado = ListaEnlazada()
    indice = 0
    for fila in filas:
        n, propio, _ = medidas.obtener(indice)
        anterior = None
        for m in medidas:
            if m[0] * 4 == n:
                anterior = m
        if anterior is not None and anterior[1] > 0:
            cociente = propio / anterior[1]
            resultado.agregar_al_final(fila[:3] + (f"{cociente:.2f}",
                                                   _pasa(cociente <= CRECIMIENTO_MAXIMO)))
        else:
            resultado.agregar_al_final(fila)
        indice += 1
    return resultado


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
