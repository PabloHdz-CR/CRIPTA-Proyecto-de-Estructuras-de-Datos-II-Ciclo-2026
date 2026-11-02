"""Alternativas al mapa de distancias del cazador, solo para medir
(001-terreno-cazador, research R1 y R3; plan.md, "Política de cota del mapa").

Siguen el patrón de alternativasAgenda.py: viven en el bench, no las usa el
juego. Como están en cripta/, prueba_reglas también las revisa: sin list,
dict, set, sorted ni heapq; se usan ListaEnlazada y HeapMinimo.

- MapaDistanciasP1, MapaDistanciasP2 y MapaDistanciasP4: el mismo
  MapaDistancias del juego, con otra política de cota. Sobrescriben SOLO
  _cota_nueva(). La política P3 (duplicar con tope R_activos) es la que hoy
  usa MapaDistancias.
- BusquedaPorCazador: la alternativa descartada de R1, un Dijkstra hacia
  adelante desde la sala de cada cazador, acotado por su rango. Es otro
  algoritmo y no reutiliza MapaDistancias, para que la comparación no
  comparta errores.
"""
from __future__ import annotations

from ...modelo.estructuras.heapMinimo import HeapMinimo
from ...modelo.mundo.mapaDistancias import EntradaMapa, MapaDistancias
from ...modelo.nucleo.accion import Atacar, Esperar, Mover
from ...modelo.puertos.dto import DIRECCIONES


class MapaDistanciasP1(MapaDistancias):
    """P1: max(cota anterior, rango). Explora exactamente lo pedido, pero con
    rangos distintos recalcula una vez por cada rango mayor que la cota."""

    def _cota_nueva(self, cota_minima: int) -> int:
        return max(self._cota_reutilizable, cota_minima)


class MapaDistanciasP2(MapaDistancias):
    """P2, duplicar: max(rango, 2 × cota anterior). Recalcula
    O(log2(R_max / R_min)) veces por ciclo, pero puede explorar hasta casi 2R
    (excede FR-026(b) tal como está redactado)."""

    def _cota_nueva(self, cota_minima: int) -> int:
        return max(cota_minima, 2 * self._cota_reutilizable)


class MapaDistanciasP4(MapaDistancias):
    """P4, directo al tope: al recalcular, cota = R_activos (el mayor rango
    entre los cazadores activos), sin duplicar. Un solo recálculo por ciclo
    sea cual sea el orden en que deciden los cazadores; explora siempre hasta
    R_activos, que es la cota de FR-026(b) enmendado. Sin fuente de R_activos,
    el tope es el rango pedido (como P1)."""

    def _cota_nueva(self, cota_minima: int) -> int:
        if self._mayor_rango_activo is None:
            return cota_minima
        return max(cota_minima, self._mayor_rango_activo())


class BusquedaPorCazador:
    """Dijkstra HACIA ADELANTE desde la sala del cazador hasta la del jugador,
    acotado por su rango (la alternativa descartada de R1).

    Para cumplir el desempate de FR-014 sin guardar nada más por sala, cada
    sala anota una CLAVE = distancia × base + (id de la primera vecina × 4 +
    índice de la dirección de la primera salida). Comparar claves es comparar
    (distancia, id de la primera vecina, orden N, S, E, O): el mismo orden
    lexicográfico que pide FR-014. Una arista suma costo × base y conserva la
    primera salida. Usa los campos de búsqueda de las salas con un sello nuevo
    del mundo (Mundo.nuevo_sello_mapa), así que no se mezcla con el mapa
    compartido: si los pisa, ese mapa lo detecta y recalcula.
    """

    def __init__(self, mundo) -> None:
        self._mundo = mundo
        mayor = 0
        for sala in mundo:
            if sala.id > mayor:
                mayor = sala.id
        self._base = 4 * (mayor + 1)
        self._salas_examinadas = 0
        self._busquedas = 0

    @property
    def salas_examinadas(self) -> int:
        """Salas examinadas por todas las búsquedas (acumulado)."""
        return self._salas_examinadas

    @property
    def busquedas(self) -> int:
        """Cuántas búsquedas se hicieron."""
        return self._busquedas

    def decidir(self, partida, cazador, rango: int):
        """La acción del cazador, calculada desde cero con su propia búsqueda."""
        jugador = partida.jugador
        if jugador.vivo and cazador.sala == jugador.sala:
            return Atacar(jugador.id_instancia)
        return self._buscar(self._mundo.sala(cazador.sala), jugador.sala, rango)

    def _buscar(self, origen, id_objetivo: int, rango: int):
        self._busquedas += 1
        base = self._base
        sello = self._mundo.nuevo_sello_mapa()
        origen.anotar_distancia(sello, 0)             # el origen no tiene primera salida
        examinadas = 1
        heap = HeapMinimo()
        indice = 0
        for salida in origen.salidas:                 # N, S, E, O
            if salida is not None and not salida.cerrada and salida.costo <= rango:
                vecina = salida.sala_destino
                clave = salida.costo * base + vecina.id * 4 + indice
                if vecina.sello_mapa != sello:
                    examinadas += 1
                    vecina.anotar_distancia(sello, clave)
                    heap.insertar(EntradaMapa(clave, vecina))
                elif clave < vecina.distancia_mapa:
                    vecina.anotar_distancia(sello, clave)
                    heap.insertar(EntradaMapa(clave, vecina))
            indice += 1
        while not heap.esta_vacio():
            entrada = heap.extraer_minimo()
            sala = entrada.sala
            clave = entrada.distancia
            if clave != sala.distancia_mapa:
                continue                              # entrada vieja (eliminación perezosa)
            if sala.id == id_objetivo:
                self._salas_examinadas += examinadas
                return Mover(DIRECCIONES[(clave % base) % 4])
            for salida in sala.salidas:
                if salida is None or salida.cerrada:
                    continue
                nueva = clave + salida.costo * base
                if nueva // base > rango:
                    continue                          # fuera del rango: no se explora
                vecina = salida.sala_destino
                if vecina.sello_mapa != sello:
                    examinadas += 1
                elif nueva >= vecina.distancia_mapa:
                    continue
                vecina.anotar_distancia(sello, nueva)
                heap.insertar(EntradaMapa(nueva, vecina))
        self._salas_examinadas += examinadas
        return Esperar()
