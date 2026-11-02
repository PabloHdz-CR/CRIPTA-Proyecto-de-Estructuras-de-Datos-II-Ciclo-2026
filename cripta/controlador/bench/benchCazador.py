"""Mediciones del cazador (001-terreno-cazador, FR-025, FR-026; research R12).

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    py -m cripta.controlador.bench.benchCazador            (completo)
    py -m cripta.controlador.bench.benchCazador --rapido   (versión corta)
y también lo corre benchTodo (py main.py --bench).

Mide cinco cosas:
  1. El ciclo completo de eventos entre dos decisiones del jugador con 20, 50
     y 100 cazadores, en la cripta de referencia y en una malla de 1024 salas.
     Criterio: mínimo < 20 ms (FR-025).
  2. El bench de la cota: 100 cazadores con rangos distintos, activados en
     orden creciente, decreciente y al azar, con las políticas P1, P2 y P3.
     Reporta recálculos por ciclo, salas examinadas y tiempo, con PASA/FALLA.
  3. Salas examinadas en una cripta base y en otra 10 veces más grande con
     la misma región alcanzable (FR-026, SC-004). Es la evidencia principal:
     no depende de la máquina.
  4. El mapa compartido contra la búsqueda por cazador (R1): mismas
     decisiones y su costo.
  5. El costo de Mundo.enlazar() (R4).

La cripta de referencia es la de más salas que lista la fuente sin conexión
sobre datos_offline/: se elige en ejecución, sin ids en el código (principio
IV), y recibe costos sintéticos deterministas. Las partidas son reales
(Partida, agenda, Mutador) sobre un servicio sintético en memoria: sin red,
sin disco y sin hilos.
"""
from __future__ import annotations

import random
import sys
import time

from ...adaptadores.fuenteOffline import FuenteOffline
from ...modelo.actores.comportamientos import crear_comportamiento
from ...modelo.actores.enemigo import Enemigo
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.mundo.mapaDistancias import MapaDistancias
from ...modelo.mundo.mundo import Mundo
from ...modelo.nucleo.accion import Mover
from ...modelo.nucleo.constantes import calcular_intervalo
from ...modelo.nucleo.partida import Partida
from ...modelo.puertos.dto import (
    DIRECCIONES, ContenidoSalaDTO, DatosCriptaDTO, FichaEnemigoDTO, JugadorDTO, SalaDTO,
    SalidaDTO)
from .alternativasCazador import (
    BusquedaPorCazador, MapaDistanciasP1, MapaDistanciasP2, MapaDistanciasP4)
from .medidor import Medidor
from .reporte import Reporte

SEMILLA = 2026
LIMITE_CICLO_MS = 20          # constitución y FR-025: ciclo de eventos < 20 ms
CARPETA_OFFLINE = "datos_offline"
LADO_MALLA = 32               # 32 × 32 = 1024 salas (prueba de estrés, R12)
CANTIDADES = (20, 50, 100)
RANGO_GRANDE = 10 ** 6        # "cotas grandes": el mapa cubre toda la cripta
COSTOS_SINTETICOS = (1, 50, 100, 100, 150, 250, 300)
ORDENES = ("creciente", "decreciente", "al azar")
POLITICAS = ("P1", "P2", "P3", "P4")
VIDA_JUGADOR = 10 ** 9        # los cazadores lo atacan: que nunca termine la partida


# ---------------------------------------------------------------------------
# Criptas
# ---------------------------------------------------------------------------

def costo_sintetico(a: int, b: int) -> int:
    """Costo determinista de la puerta entre a y b, el mismo en las dos caras
    (depende del par, no del sentido): FR-002 y FR-027 se cumplen solos."""
    menor = a if a < b else b
    mayor = b if a < b else a
    return COSTOS_SINTETICOS[(menor * 7919 + mayor * 104729 + SEMILLA) % len(COSTOS_SINTETICOS)]


def _con_costos(salas_dto) -> ListaEnlazada:
    """Las mismas salas con costos sintéticos en todas sus salidas."""
    resultado = ListaEnlazada()
    for sala in salas_dto:
        salidas = ListaEnlazada()
        for s in sala.salidas:
            salidas.agregar_al_final(SalidaDTO(
                direccion=s.direccion, sala=s.sala, cerrada=s.cerrada, llave=s.llave,
                cierre_automatico=s.cierre_automatico, costo=costo_sintetico(sala.id, s.sala)))
        resultado.agregar_al_final(SalaDTO(id=sala.id, nombre=sala.nombre, salidas=salidas))
    return resultado


def _datos(salas: int, sala_inicial: int, sala_salida: int) -> DatosCriptaDTO:
    return DatosCriptaDTO(
        id="bench-cazador", version="v1", salas_total=salas, paginas=1,
        salas_por_pagina=salas, sala_inicial=sala_inicial, sala_salida=sala_salida,
        llave_salida="ninguna", presupuesto_solicitudes=0, inventario_max=10,
        jugador=JugadorDTO(vida_max=VIDA_JUGADOR, ataque=1, defensa=0, velocidad=100))


class Cripta:
    """Salas (SalaDTO con costos) y su sala de salida, listas para una Partida."""

    def __init__(self, nombre: str, salas: ListaEnlazada, sala_salida: int) -> None:
        self.nombre = nombre
        self.salas = salas
        self.sala_salida = sala_salida

    def __len__(self) -> int:
        return len(self.salas)


def cripta_de_referencia() -> Cripta:
    """La cripta con más salas de datos_offline/, elegida en ejecución por
    cantidad de salas (ningún id en el código), con costos sintéticos."""
    fuente = FuenteOffline(CARPETA_OFFLINE)
    elegida = None
    for resumen in fuente.listar_criptas():
        if elegida is None or resumen.salas > elegida.salas:
            elegida = resumen
    datos = fuente.datos_generales(elegida.id)
    salas = ListaEnlazada()
    for pagina in range(1, datos.paginas + 1):
        for sala in fuente.esqueleto(elegida.id, pagina).salas:
            salas.agregar_al_final(sala)
    return Cripta(f"referencia ({len(salas)} salas)", _con_costos(salas), datos.sala_salida)


def malla(lado: int) -> Cripta:
    """Malla lado × lado con costos sintéticos. Su sala de salida no existe,
    así la partida no termina por llegar a ella."""
    salas = ListaEnlazada()
    for fila in range(lado):
        for columna in range(lado):
            id_sala = fila * lado + columna + 1
            salidas = ListaEnlazada()
            if fila > 0:
                salidas.agregar_al_final(SalidaDTO("N", id_sala - lado))
            if fila < lado - 1:
                salidas.agregar_al_final(SalidaDTO("S", id_sala + lado))
            if columna < lado - 1:
                salidas.agregar_al_final(SalidaDTO("E", id_sala + 1))
            if columna > 0:
                salidas.agregar_al_final(SalidaDTO("O", id_sala - 1))
            salas.agregar_al_final(SalaDTO(id_sala, f"Sala {id_sala}", salidas))
    return Cripta(f"malla {lado}x{lado} ({lado * lado} salas)", _con_costos(salas),
                  lado * lado + 1)


# ---------------------------------------------------------------------------
# Partida sobre un servicio sintético
# ---------------------------------------------------------------------------

class _Entrada:
    def __init__(self, sala) -> None:
        self.sala = sala


class _ServicioSintetico:
    """Lo que Partida usa del ServicioDatos: datos, esqueleto, contenido (vacío:
    los cazadores se colocan aparte) y precarga (no hace nada)."""

    def __init__(self, datos: DatosCriptaDTO, salas: ListaEnlazada) -> None:
        self._datos = datos
        self._esqueleto = ListaEnlazada()
        for sala in salas:
            self._esqueleto.agregar_al_final(_Entrada(sala))

    def datos_cripta(self):
        return self._datos

    def esqueleto(self):
        return self._esqueleto

    def asegurar_contenido(self, id_sala):
        return ContenidoSalaDTO(sala=id_sala, enemigos=ListaEnlazada(),
                                objetos=ListaEnlazada(), trampas=ListaEnlazada())

    def precargar(self, id_sala_actual):
        return None


def _par_del_jugador(mundo, sala_salida: int):
    """Dos salas unidas en los dos sentidos por puertas abiertas de costo 100,
    para que el jugador vaya y venga: (sala, dirección de ida, de vuelta)."""
    for sala in mundo:
        if sala.id == sala_salida:
            continue
        for salida in sala.salidas:
            if (salida is None or salida.cerrada or salida.costo != 100
                    or salida.destino == sala_salida):
                continue
            vuelta = salida.sala_destino.salida(DIRECCIONES[DIRECCIONES.index(salida.direccion) ^ 1])
            if vuelta is not None and not vuelta.cerrada and vuelta.destino == sala.id:
                return sala.id, salida.direccion, vuelta.direccion
    raise ValueError("no hay dos salas unidas por puertas abiertas de costo 100")


def rangos_ordenados(cantidad: int, orden: str, paso: int) -> ListaEnlazada:
    """Rangos distintos paso, 2·paso, ..., en el orden pedido. 'al azar' usa un
    Random propio con semilla fija (determinismo)."""
    rangos = ListaEnlazada()
    for i in range(cantidad):
        valor = (i + 1) * paso if orden != "decreciente" else (cantidad - i) * paso
        rangos.agregar_al_final(valor)
    if orden != "al azar":
        return rangos
    azar = random.Random(SEMILLA)
    mezclados = ListaEnlazada()
    while not rangos.esta_vacia():
        mezclados.agregar_al_final(rangos.eliminar_en(azar.randrange(len(rangos))))
    return mezclados


class EscenarioCiclo:
    """Una partida real con 'cantidad' cazadores activos que persiguen al
    jugador; ejecutar() es UN ciclo completo de eventos entre dos decisiones
    del jugador (que va y viene entre dos salas, así el mapa se recalcula en
    cada ciclo). preparar() devuelve los cazadores a sus salas iniciales; la
    partida se arma una sola vez porque Mundo.enlazar() cuesta O(salas²)."""

    def __init__(self, cripta: Cripta, rangos: ListaEnlazada, politica: str = "P3") -> None:
        self.cantidad = len(rangos)
        self._cripta = cripta
        self._politica = politica
        sala_jugador = self._armar(rangos)
        self._sala_jugador = sala_jugador

    def _armar(self, rangos) -> int:
        cripta = self._cripta
        # Primero una Partida para encontrar el par de salas del jugador.
        mundo = Mundo(_datos(len(cripta), 1, cripta.sala_salida))
        mundo.agregar_esqueleto(cripta.salas)
        mundo.enlazar()
        sala_jugador, self._ida, self._vuelta = _par_del_jugador(mundo, cripta.sala_salida)
        servicio = _ServicioSintetico(_datos(len(cripta), sala_jugador, cripta.sala_salida),
                                      cripta.salas)
        partida = Partida(servicio)
        partida.iniciar(SEMILLA)
        self.partida = partida
        self.mapa = self._crear_mapa(partida)
        partida._mapa_distancias = self.mapa       # el bench elige la política

        # Cazadores en salas al azar (semilla fija), activados en el orden de 'rangos':
        # ese es el orden en que deciden dentro de cada ciclo.
        azar = random.Random(SEMILLA)
        ids = ListaEnlazada()
        for sala in partida.mundo:
            if sala.id != sala_jugador:
                ids.agregar_al_final(sala.id)
        self._cazadores = ListaEnlazada()           # (enemigo, id de su sala inicial)
        partida.mutador.pausar()
        numero = 0
        for rango in rangos:
            numero += 1
            id_sala = ids.obtener(azar.randrange(len(ids)))
            ficha = FichaEnemigoDTO(id=f"ent_cazador_{rango}", nombre="Cazador", vida_max=10 ** 6,
                                    ataque=1, defensa=0, velocidad=100, comportamiento="cazador",
                                    suelta=ListaEnlazada(), rango=rango)
            enemigo = Enemigo(f"c-{numero:04d}", ficha, ficha.vida_max, id_sala,
                              crear_comportamiento(ficha.comportamiento, ficha.rango))
            sala = partida.mundo.sala(id_sala)
            sala.contenido_cargado = True
            sala.agregar_dormido(enemigo)
            enemigo.activar(partida)
            self._cazadores.agregar_al_final((enemigo, id_sala))
        partida.mutador.reanudar()
        self._en_ida = True
        return sala_jugador

    def _crear_mapa(self, partida):
        """P3 es la del juego (MapaDistancias con el R_activos de la partida)."""
        if self._politica == "P1":
            return MapaDistanciasP1(partida.mundo)
        if self._politica == "P2":
            return MapaDistanciasP2(partida.mundo)
        if self._politica == "P4":
            return MapaDistanciasP4(partida.mundo, partida.mayor_rango_activo)
        return MapaDistancias(partida.mundo, partida.mayor_rango_activo)

    def preparar(self, n) -> None:
        """Deja la partida en el mismo estado antes de cada repetición (no se
        cronometra): cada cazador vuelve a su sala inicial y su próximo turno
        se reprograma a reloj + intervalo(100), en el orden de activación.
        Sin esto, los costos sintéticos (1 a 300) desfasan los turnos: un
        cazador que cruza salidas de costo 1 actúa varias veces por ciclo y
        uno que cruza una de 300 se salta ciclos, así que cada repetición
        mediría otra carga (entre 82 y 125 decisiones medidas) y el orden
        del escenario se perdería. Así, cada ciclo son exactamente 'cantidad'
        decisiones en el orden pedido."""
        partida = self.partida
        partida.mutador.pausar()
        for enemigo, id_inicial in self._cazadores:
            if enemigo.sala != id_inicial:
                partida.mutador.enemigo_mover(enemigo, partida.mundo.sala(enemigo.sala),
                                              partida.mundo.sala(id_inicial))
            turno = partida.mutador.agenda_reprogramar(
                enemigo.evento_accion,
                partida.reloj + calcular_intervalo(100, enemigo.velocidad))
            partida.mutador.asignar(enemigo, "evento_accion", turno)
        partida.mutador.reanudar()

    def ejecutar(self) -> None:
        """Un ciclo: el jugador se mueve (costo 100) y la agenda corre hasta su
        siguiente decisión, con un turno de cada cazador."""
        direccion = self._ida if self._en_ida else self._vuelta
        self._en_ida = not self._en_ida
        self.partida.aplicar_accion(Mover(direccion))

    def ciclo_contado(self):
        """Un ciclo más, contando (recálculos del mapa, salas examinadas)."""
        self.preparar(self.cantidad)
        calculos = self.mapa.calculos
        examinadas = self.mapa.salas_examinadas
        self.ejecutar()
        return self.mapa.calculos - calculos, self.mapa.salas_examinadas - examinadas


def _iguales(cantidad: int, rango: int) -> ListaEnlazada:
    rangos = ListaEnlazada()
    for _ in range(cantidad):
        rangos.agregar_al_final(rango)
    return rangos


def escenarios_rendimiento(rapido: bool = False) -> ListaEnlazada:
    """(nombre, EscenarioCiclo) que verifica prueba_rendimiento_cazador (H4.E1):
    20, 50 y 100 cazadores en la cripta de referencia y en la malla de 1024
    salas, y 100 de rangos distintos en los tres órdenes, con la política del
    juego (P3, MapaDistancias)."""
    escenarios = ListaEnlazada()
    for cripta in (cripta_de_referencia(), malla(LADO_MALLA)):
        for cantidad in CANTIDADES:
            escenarios.agregar_al_final((f"{cripta.nombre}, {cantidad} cazadores",
                                         EscenarioCiclo(cripta, _iguales(cantidad, RANGO_GRANDE))))
        paso = _paso_de_rangos(cripta)
        for orden in ORDENES:
            escenarios.agregar_al_final((f"{cripta.nombre}, 100 rangos distintos, {orden}",
                                         EscenarioCiclo(cripta, rangos_ordenados(100, orden, paso))))
    return escenarios


def _paso_de_rangos(cripta: Cripta) -> int:
    """Paso de los 100 rangos distintos: el mayor llega a cubrir la cripta
    entera (100 × paso >= salas × costo máximo), así hay rangos chicos y
    grandes."""
    costo_maximo = 0
    for costo in COSTOS_SINTETICOS:
        if costo > costo_maximo:
            costo_maximo = costo
    return max(1, len(cripta) * costo_maximo // 100)


# ---------------------------------------------------------------------------
# Secciones del reporte
# ---------------------------------------------------------------------------

def _ms(segundos: float) -> str:
    return f"{segundos * 1000:.2f}"


def _pasa(segundos: float) -> str:
    return "PASA" if segundos * 1000 < LIMITE_CICLO_MS else "FALLA"


def _seccion_ciclo(reporte, medidor, criptas) -> None:
    filas = ListaEnlazada()
    for cripta in criptas:
        for cantidad in CANTIDADES:
            escenario = EscenarioCiclo(cripta, _iguales(cantidad, RANGO_GRANDE))
            medicion = medidor.medir(escenario, cantidad)
            calculos, examinadas = escenario.ciclo_contado()
            filas.agregar_al_final((cripta.nombre, str(cantidad), _ms(medicion.minimo),
                                    _ms(medicion.promedio), str(calculos), str(examinadas),
                                    _pasa(medicion.minimo)))
    reporte.tabla(f"1. Ciclo completo de eventos, rango grande (criterio: mínimo < "
                  f"{LIMITE_CICLO_MS} ms, FR-025)",
                  ("cripta", "cazadores", "mínimo ms", "promedio ms", "recálculos",
                   "salas examinadas", "resultado"), filas)


def _seccion_cota(reporte, medidor, criptas) -> None:
    filas = ListaEnlazada()
    for cripta in criptas:
        paso = _paso_de_rangos(cripta)
        for orden in ORDENES:
            for politica in POLITICAS:
                escenario = EscenarioCiclo(cripta, rangos_ordenados(100, orden, paso), politica)
                medicion = medidor.medir(escenario, 100)
                calculos, examinadas = escenario.ciclo_contado()
                filas.agregar_al_final((cripta.nombre, orden, politica, str(calculos),
                                        str(examinadas), _ms(medicion.minimo),
                                        f"{LIMITE_CICLO_MS - medicion.minimo * 1000:.2f}",
                                        _pasa(medicion.minimo)))
    reporte.tabla("2. Bench de la cota: 100 cazadores con rangos distintos, por ciclo "
                  "(P1 max(anterior, rango); P2 duplicar; P3 duplicar con tope R_activos, "
                  "la del juego; P4 directo a R_activos)",
                  ("cripta", "orden", "política", "recálculos", "salas examinadas",
                   "mínimo ms", f"margen a {LIMITE_CICLO_MS} ms", "resultado"), filas)


def _conteos_en_malla(lado: int, rango: int):
    """(salas que examina una decisión, salas que examina el cálculo) con el
    jugador al centro de una malla de costo 100 y un cazador a dos pasos."""
    salas = ListaEnlazada()
    for fila in range(lado):
        for columna in range(lado):
            id_sala = fila * lado + columna + 1
            salidas = ListaEnlazada()
            if fila > 0:
                salidas.agregar_al_final(SalidaDTO("N", id_sala - lado, costo=100))
            if fila < lado - 1:
                salidas.agregar_al_final(SalidaDTO("S", id_sala + lado, costo=100))
            if columna < lado - 1:
                salidas.agregar_al_final(SalidaDTO("E", id_sala + 1, costo=100))
            if columna > 0:
                salidas.agregar_al_final(SalidaDTO("O", id_sala - 1, costo=100))
            salas.agregar_al_final(SalaDTO(id_sala, f"Sala {id_sala}", salidas))
    mundo = Mundo(_datos(lado * lado, 1, lado * lado + 1))
    mundo.agregar_esqueleto(salas)
    mundo.enlazar()
    centro = lado // 2
    jugador = centro * lado + centro + 1
    mapa = MapaDistancias(mundo)
    mapa.asegurar(jugador, rango)
    cazador = mundo.sala(jugador - lado + 1)            # a costo 200 del jugador
    consultadas = 0
    for salida in cazador.salidas:
        if salida is not None and not salida.cerrada:
            consultadas += 1                             # la decisión lee distancia(destino)
    return consultadas, mapa.examinadas_ultimo_calculo


def _seccion_conteos(reporte) -> None:
    filas = ListaEnlazada()
    for lado in (9, 29):
        for rango in (100, 300):
            decision, calculo = _conteos_en_malla(lado, rango)
            filas.agregar_al_final((f"malla {lado}x{lado} ({lado * lado} salas)", str(rango),
                                    str(decision), str(calculo)))
    reporte.tabla("3. Salas examinadas (FR-026, SC-004): base y 10 veces más grande, misma "
                  "región alcanzable",
                  ("cripta", "rango", "por decisión", "por cálculo del mapa"), filas)


def _seccion_comparacion(reporte, medidor, criptas) -> None:
    filas = ListaEnlazada()
    for cripta in criptas:
        for rango in (300, RANGO_GRANDE):
            escenario = EscenarioCiclo(cripta, _iguales(100, rango))
            partida = escenario.partida
            busqueda = BusquedaPorCazador(partida.mundo)
            iguales = 0
            for enemigo, _ in escenario._cazadores:
                mapa_dice = enemigo.comportamiento.decidir(enemigo, partida)
                if mapa_dice == busqueda.decidir(partida, enemigo, rango):
                    iguales += 1
            compartido = medidor.medir(_DecisionesCompartidas(escenario), 100)
            por_cazador = medidor.medir(_DecisionesPorCazador(escenario, rango), 100)
            filas.agregar_al_final((cripta.nombre, "total" if rango == RANGO_GRANDE else str(rango),
                                    _ms(por_cazador.minimo), _ms(compartido.minimo),
                                    f"{iguales}/100"))
    reporte.tabla("4. 100 decisiones: búsqueda por cazador desde cero frente al mapa "
                  "compartido (research R1)",
                  ("cripta", "rango", "por cazador ms", "mapa compartido ms",
                   "misma decisión"), filas)


class _DecisionesCompartidas:
    """100 decisiones con un mapa nuevo (se calcula una vez y se comparte)."""

    def __init__(self, escenario: EscenarioCiclo) -> None:
        self._escenario = escenario

    def preparar(self, n) -> None:
        partida = self._escenario.partida
        partida._mapa_distancias = MapaDistancias(partida.mundo, partida.mayor_rango_activo)

    def ejecutar(self) -> None:
        partida = self._escenario.partida
        for enemigo, _ in self._escenario._cazadores:
            enemigo.comportamiento.decidir(enemigo, partida)


class _DecisionesPorCazador:
    """100 decisiones, cada una con su propia búsqueda desde cero."""

    def __init__(self, escenario: EscenarioCiclo, rango: int) -> None:
        self._escenario = escenario
        self._rango = rango
        self._busqueda = BusquedaPorCazador(escenario.partida.mundo)

    def preparar(self, n) -> None:
        return None

    def ejecutar(self) -> None:
        partida = self._escenario.partida
        for enemigo, _ in self._escenario._cazadores:
            self._busqueda.decidir(partida, enemigo, self._rango)


class _Enlace:
    """Mundo.enlazar() de una cripta ya construida."""

    def __init__(self, cripta: Cripta) -> None:
        self._cripta = cripta
        self._mundo = None

    def preparar(self, n) -> None:
        self._mundo = Mundo(_datos(len(self._cripta), 1, self._cripta.sala_salida))
        self._mundo.agregar_esqueleto(self._cripta.salas)

    def ejecutar(self) -> None:
        self._mundo.enlazar()


def _seccion_enlace(reporte, medidor, criptas) -> None:
    filas = ListaEnlazada()
    for cripta in criptas:
        medicion = medidor.medir(_Enlace(cripta), len(cripta))
        filas.agregar_al_final((cripta.nombre, _ms(medicion.minimo)))
    reporte.tabla("5. Costo de Mundo.enlazar(), una vez por partida (research R4)",
                  ("cripta", "mínimo ms"), filas)


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 7)
    criptas = (cripta_de_referencia(), malla(LADO_MALLA))
    reporte.titulo("Cazador: mediciones (001-terreno-cazador, FR-025, FR-026)")
    inicio = time.perf_counter()
    _seccion_ciclo(reporte, medidor, criptas)
    _seccion_cota(reporte, medidor, criptas)
    _seccion_conteos(reporte)
    _seccion_comparacion(reporte, medidor, criptas)
    _seccion_enlace(reporte, medidor, criptas)
    reporte.nota("")
    reporte.nota(f"Las cifras de salas examinadas no dependen de la máquina; los tiempos son "
                 f"el mínimo de {3 if rapido else 7} repeticiones (Medidor). Duración del bench: "
                 f"{time.perf_counter() - inicio:.1f} s.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
