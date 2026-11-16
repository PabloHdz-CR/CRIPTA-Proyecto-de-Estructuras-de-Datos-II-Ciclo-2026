"""BuscadorRuta: el primer paso de «ir a» sobre el conocimiento del jugador
(002-niebla-guerra, FR-019 a FR-022, FR-030, FR-031; research R5)."""
from __future__ import annotations

from typing import Optional

from ..estructuras.heapMinimo import HeapMinimo
from .conocimiento import ABIERTA, EXPLORADA


class EntradaRuta:
    """Entrada del heap: (costo, paso, sala), ordenada por (costo, paso,
    sala.id). Orden total y determinista (FR-030): dos entradas vivas de la
    misma sala nunca empatan, porque solo se inserta al mejorar la etiqueta."""

    __slots__ = ("costo", "paso", "sala")

    def __init__(self, costo: int, paso: int, sala) -> None:
        self.costo = costo
        self.paso = paso
        self.sala = sala

    def __lt__(self, otra: "EntradaRuta") -> bool:
        if self.costo != otra.costo:
            return self.costo < otra.costo
        if self.paso != otra.paso:
            return self.paso < otra.paso
        return self.sala.id < otra.sala.id


class BuscadorRuta:
    """Dijkstra HACIA ADELANTE desde la sala del jugador sobre el subgrafo
    conocido, con el HeapMinimo propio y eliminación perezosa (research R5).

    Subgrafo conocido (FR-021): la cara u → v se recorre solo si u y v están
    EXPLORADA y la cara está recordada ABIERTA. Nunca lee `cerrada` (el estado
    real) ni nada que no sea conocimiento del jugador: por eso «ir a» no abre
    puertas (FR-022) y no usa caras no observadas.

    Desempate (FR-020): la etiqueta de cada sala es (costo, paso), con paso =
    id de la vecina del primer paso × 4 + índice de su dirección (N=0, S=1,
    E=2, O=3), y se compara en orden lexicográfico. El paso se hereda sin
    cambios al extender una ruta, así que el orden es compatible con
    Dijkstra: entre rutas de igual costo gana la de primer paso hacia la
    vecina de menor id (como número) y, hacia la misma vecina, la primera en
    N, S, E, O.

    Costo: O((V + E) log V) sobre lo que alcanza antes de fijar el destino;
    se detiene al fijarlo. Estado de búsqueda en campos de la sala con un
    sello nuevo por búsqueda (R5 de 001): sin dict ni set y empezar es O(1).
    Sin caché: la ruta se calcula desde cero en cada paso (FR-024).

    DECISIÓN (research R5): separado del mapa de distancias del cazador.
    Otro grafo (conocimiento frente a estado real), otro sentido (adelante
    frente a atrás) y sin cota ni clave de validez. En la malla de 1024 salas
    la parada temprana deja el peor paso en 3,99 ms frente a 7,47 ms de la
    búsqueda completa hacia atrás (mediciones previas del plan).
    """

    def __init__(self, mundo) -> None:
        self._mundo = mundo
        self._fijadas_ultima = 0

    @property
    def salas_fijadas_ultima(self) -> int:
        """Salas que fijó la última búsqueda (bench y pruebas)."""
        return self._fijadas_ultima

    def primer_paso(self, origen, destino) -> Optional[object]:
        """La Salida de `origen` por la que empieza la ruta conocida de menor
        costo hasta `destino`, o None si no hay ruta conocida, si son la misma
        sala o si alguna de las dos no está explorada."""
        self._fijadas_ultima = 0
        if (origen is destino or origen.conocimiento != EXPLORADA
                or destino.conocimiento != EXPLORADA):
            return None
        sello = self._mundo.nuevo_sello_ruta()
        heap = HeapMinimo()
        origen.anotar_ruta(sello, 0, -1)
        heap.insertar(EntradaRuta(0, -1, origen))
        while not heap.esta_vacio():
            entrada = heap.extraer_minimo()
            sala = entrada.sala
            if sala.fijada_ruta or entrada.costo != sala.costo_ruta or entrada.paso != sala.paso_ruta:
                continue                     # entrada vieja (eliminación perezosa)
            sala.fijar_ruta()
            self._fijadas_ultima += 1
            if sala is destino:
                return self._salida_del_paso(origen, sala.paso_ruta)
            self._relajar(sala, origen, sello, heap)
        return None

    @staticmethod
    def _relajar(sala, origen, sello: int, heap: HeapMinimo) -> None:
        indice = 0
        for salida in sala.salidas:
            if salida is not None and salida.recordada == ABIERTA:
                vecina = salida.sala_destino
                if vecina is not None and vecina.conocimiento == EXPLORADA:
                    costo = sala.costo_ruta + salida.costo
                    paso = vecina.id * 4 + indice if sala is origen else sala.paso_ruta
                    if vecina.sello_ruta != sello:
                        vecina.anotar_ruta(sello, costo, paso)
                        heap.insertar(EntradaRuta(costo, paso, vecina))
                    elif not vecina.fijada_ruta and (
                            costo < vecina.costo_ruta
                            or (costo == vecina.costo_ruta and paso < vecina.paso_ruta)):
                        vecina.anotar_ruta(sello, costo, paso)
                        heap.insertar(EntradaRuta(costo, paso, vecina))
            indice += 1

    @staticmethod
    def _salida_del_paso(origen, paso: int):
        """La salida de origen que corresponde a la clave del primer paso."""
        return origen.salidas[paso % 4]
