"""Grafo propio de la verificación de resolubilidad (research.md R1,
data-model.md §2).

Se arma de nuevo en cada verificación a partir de las salas del esqueleto, de
los datos generales y de la ubicación de llaves (FR-017), y se descarta al
terminar: no es estado de la partida ni se guarda (principio V).

DECISIÓN (R1): las referencias (salida -> sala destino, salida -> llave que la
abre, ubicación -> sala) se resuelven ORDENANDO con ordenamiento.mezcla y
FUSIONANDO dos secuencias ordenadas en una pasada, nunca buscando por id
(principio I: sin dict ni set como índice). Buscar cada destino recorriendo el
esqueleto costaría O(E · S); D73 midió 64,79 ms solo en enlazar el Mundo de
1024 salas con búsqueda lineal. Ordenar deja además todo en un orden canónico
que no depende del orden de llegada de las páginas ni de las entradas de
llaves (FR-010, SC-004).

Costo de la construcción: O((S + E + L) log(S + E + L)), con S salas, E caras
de puerta y L entradas de la ubicación de llaves.

DECISIÓN: los campos de trabajo del verificador (alcanzada, obtenida,
pendientes, índices de Tarjan, etiqueta...) son atributos públicos de los
nodos, como el sello del mapa de distancias en Sala (D71): son estado de una
sola verificación sobre un grafo que nadie más ve. Lo que identifica a cada
nodo (id, salidas, ubicaciones) es de solo lectura, con propiedades.
"""
from __future__ import annotations

from typing import Iterable, Optional

from ..estructuras.listaEnlazada import ListaEnlazada
from ..ordenamiento import ClaveOrden, mezcla
from ..puertos.dto import DIRECCIONES, DatosCriptaDTO, UbicacionLlaveDTO
from ..puertos.errores import DatosInvalidos

def indice_direccion(direccion: str) -> int:
    """Posición de la dirección en el orden fijo N, S, E, O. O(1)."""
    posicion = 0
    for candidata in DIRECCIONES:
        if candidata == direccion:
            return posicion
        posicion += 1
    raise DatosInvalidos(f"Dirección desconocida '{direccion}' en el esqueleto")


def clave_ubicacion(ubicacion: UbicacionLlaveDTO) -> tuple:
    """Orden canónico de las ubicaciones: por sala y, dentro de la sala, la
    del suelo antes que las de enemigos, y estas por id de instancia."""
    enemigo = ubicacion.enemigo
    return (ubicacion.sala, enemigo is not None, enemigo if enemigo is not None else "")


class NodoSala:
    """Una sala del esqueleto en el grafo de verificación."""

    def __init__(self, id_sala: int) -> None:
        self._id = id_sala
        self._salidas = ListaEnlazada()      # AristaSalida, en orden N, S, E, O
        self._llaves_aqui = ListaEnlazada()  # NodoLlave ubicadas en esta sala
        # Campos de trabajo (ver DECISIÓN del módulo).
        self.alcanzada = False
        self.indice = None
        self.enlace = 0
        self.en_pila = False
        self.componente = None
        self.etiqueta = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def salidas(self) -> ListaEnlazada:
        return self._salidas

    @property
    def llaves_aqui(self) -> ListaEnlazada:
        return self._llaves_aqui

    def __repr__(self) -> str:
        return f"NodoSala({self._id})"


class AristaSalida:
    """Una cara de puerta, en el sentido en que se recorre (FR-006)."""

    def __init__(self, origen: NodoSala, direccion: str, id_destino: int,
                 cerrada: bool, id_llave: Optional[str]) -> None:
        self._origen = origen
        self._direccion = direccion
        self._indice_direccion = indice_direccion(direccion)
        self._id_destino = id_destino
        self._cerrada = cerrada
        self._id_llave = id_llave
        self.destino: Optional[NodoSala] = None    # se resuelve por fusión
        self.llave: Optional["NodoLlave"] = None   # solo si está cerrada y declara llave

    @property
    def origen(self) -> NodoSala:
        return self._origen

    @property
    def direccion(self) -> str:
        return self._direccion

    @property
    def indice_direccion(self) -> int:
        return self._indice_direccion

    @property
    def id_destino(self) -> int:
        return self._id_destino

    @property
    def cerrada(self) -> bool:
        return self._cerrada

    @property
    def id_llave(self) -> Optional[str]:
        return self._id_llave

    def transitable(self) -> bool:
        """Abierta, o cerrada con su llave ya obtenida (FR-002, FR-005)."""
        return (not self._cerrada) or (self.llave is not None and self.llave.obtenida)

    def clave_canonica(self) -> tuple:
        """(sala de origen, dirección en N, S, E, O): el orden de la frontera
        y de las puertas de un ciclo (FR-012, FR-015)."""
        return (self._origen.id, self._indice_direccion)

    def __repr__(self) -> str:
        return f"AristaSalida({self._origen.id} {self._direccion} -> {self._id_destino})"


class UbicacionEnlazada:
    """Una entrada de la ubicación de llaves con su sala ya resuelta."""

    def __init__(self, dto: UbicacionLlaveDTO) -> None:
        self._dto = dto
        self.sala: Optional[NodoSala] = None       # se resuelve por fusión
        self.llave: Optional["NodoLlave"] = None   # se resuelve al deduplicar ids

    @property
    def dto(self) -> UbicacionLlaveDTO:
        return self._dto


class NodoLlave:
    """Una llave (id distinto) en el grafo de verificación. Se ordena por id
    como texto (__lt__): es lo que usa el HeapMinimo de disponibles (FR-009)."""

    def __init__(self, id_llave: str) -> None:
        self._id = id_llave
        self._ubicaciones = ListaEnlazada()   # UbicacionEnlazada, por (sala, enemigo)
        self._puertas = ListaEnlazada()       # AristaSalida cerradas que la requieren
        # Campos de trabajo (ver DECISIÓN del módulo).
        self.pendientes = ListaEnlazada()
        self.disponible = False
        self.obtenida = False
        self.indice = None
        self.enlace = 0
        self.en_pila = False
        self.componente = None
        self.posicion_paseo = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def ubicaciones(self) -> ListaEnlazada:
        return self._ubicaciones

    @property
    def puertas(self) -> ListaEnlazada:
        return self._puertas

    def __lt__(self, otra: "NodoLlave") -> bool:
        return self._id < otra.id

    def __repr__(self) -> str:
        return f"NodoLlave({self._id!r})"


class GrafoVerificacion:
    """Salas y llaves enlazadas, en orden canónico (salas por id, llaves por
    id como texto)."""

    def __init__(self, salas: ListaEnlazada, llaves: ListaEnlazada, inicial: NodoSala,
                 salida: Optional[NodoSala], llave_salida: NodoLlave) -> None:
        self._salas = salas
        self._llaves = llaves
        self._inicial = inicial
        self._salida = salida
        self._llave_salida = llave_salida

    @property
    def salas(self) -> ListaEnlazada:
        return self._salas

    @property
    def llaves(self) -> ListaEnlazada:
        return self._llaves

    @property
    def inicial(self) -> NodoSala:
        return self._inicial

    @property
    def salida(self) -> Optional[NodoSala]:
        return self._salida

    @property
    def llave_salida(self) -> NodoLlave:
        return self._llave_salida


# ---------------------------------------------------------------------------
# Construcción por ordenamiento y fusión
# ---------------------------------------------------------------------------

def _ordenados(pares: ListaEnlazada) -> ListaEnlazada:
    """mezcla() sobre ClaveOrden: estable, O(n log n)."""
    return mezcla(pares)


def _salas_ordenadas(salas_dto: Iterable) -> ListaEnlazada:
    pares = ListaEnlazada()
    for sala in salas_dto:
        pares.agregar_al_final(ClaveOrden(sala.id, (NodoSala(sala.id), sala)))
    ordenados = _ordenados(pares)
    anterior = None
    for par in ordenados:
        if anterior is not None and anterior == par.clave:
            raise DatosInvalidos(f"La sala {par.clave} aparece dos veces en el esqueleto")
        anterior = par.clave
    return ordenados


def _crear_aristas(salas: ListaEnlazada) -> ListaEnlazada:
    """Crea las aristas de cada sala en orden N, S, E, O (sin importar el
    orden en que vengan las salidas del DTO) y devuelve los pares
    (id_destino, arista) para fusionar."""
    por_destino = ListaEnlazada()
    for par in salas:
        nodo, sala_dto = par.valor
        for direccion in DIRECCIONES:
            for salida in sala_dto.salidas:
                if salida.direccion == direccion:
                    llave = salida.llave if salida.cerrada else None
                    arista = AristaSalida(nodo, direccion, salida.sala, salida.cerrada, llave)
                    nodo.salidas.agregar_al_final(arista)
                    por_destino.agregar_al_final(ClaveOrden(salida.sala, arista))
    return por_destino


def _fusionar_destinos(salas: ListaEnlazada, por_destino: ListaEnlazada) -> None:
    """Una pasada sobre las dos secuencias ordenadas por id de sala."""
    iterador_salas = iter(salas)
    actual = next(iterador_salas, None)
    for par in _ordenados(por_destino):
        while actual is not None and actual.clave < par.clave:
            actual = next(iterador_salas, None)
        if actual is None or actual.clave != par.clave:
            arista = par.valor
            raise DatosInvalidos(
                f"La salida {arista.direccion} de la sala {arista.origen.id} lleva a la "
                f"sala {par.clave}, que no existe en el esqueleto")
        par.valor.destino = actual.valor[0]


def _crear_llaves(salas: ListaEnlazada, ubicaciones: Iterable,
                  llave_salida: str) -> "tuple[ListaEnlazada, NodoLlave, ListaEnlazada]":
    """Junta los ids de llave de las salidas cerradas con llave, de las
    ubicaciones y de llave_salida; ordena y deduplica en una pasada."""
    pares = ListaEnlazada()
    for par in salas:
        for arista in par.valor[0].salidas:
            if arista.cerrada and arista.id_llave is not None:
                pares.agregar_al_final(ClaveOrden(
                    (arista.id_llave, 0, arista.origen.id, arista.indice_direccion), arista))
    enlazadas = ListaEnlazada()
    for ubicacion in ubicaciones:
        enlazada = UbicacionEnlazada(ubicacion)
        enlazadas.agregar_al_final(enlazada)
        pares.agregar_al_final(ClaveOrden((ubicacion.id, 1) + clave_ubicacion(ubicacion), enlazada))
    pares.agregar_al_final(ClaveOrden((llave_salida, 2), None))

    llaves = ListaEnlazada()
    nodo_salida = None
    actual = None
    for par in _ordenados(pares):
        id_llave = par.clave[0]
        if actual is None or actual.id != id_llave:
            actual = NodoLlave(id_llave)
            llaves.agregar_al_final(actual)
        tipo = par.clave[1]
        if tipo == 0:
            par.valor.llave = actual
            actual.puertas.agregar_al_final(par.valor)
        elif tipo == 1:
            actual.ubicaciones.agregar_al_final(par.valor)
            par.valor.llave = actual
        else:
            nodo_salida = actual
    return llaves, nodo_salida, enlazadas


def _fusionar_ubicaciones(salas: ListaEnlazada, enlazadas: ListaEnlazada) -> None:
    pares = ListaEnlazada()
    for enlazada in enlazadas:
        pares.agregar_al_final(ClaveOrden(enlazada.dto.sala, enlazada))
    iterador_salas = iter(salas)
    actual = next(iterador_salas, None)
    for par in _ordenados(pares):
        while actual is not None and actual.clave < par.clave:
            actual = next(iterador_salas, None)
        if actual is None or actual.clave != par.clave:
            raise DatosInvalidos(
                f"La entrada de la llave '{par.valor.dto.id}' en la ubicación de llaves está "
                f"en la sala {par.clave}, que no existe en el esqueleto")
        nodo = actual.valor[0]
        par.valor.sala = nodo
        nodo.llaves_aqui.agregar_al_final(par.valor.llave)


def _buscar(salas: ListaEnlazada, id_sala: int) -> Optional[NodoSala]:
    """Búsqueda lineal: se usa solo dos veces (sala inicial y de salida)."""
    for par in salas:
        if par.clave == id_sala:
            return par.valor[0]
    return None


def construir_grafo(datos: DatosCriptaDTO, salas_dto: Iterable,
                    ubicaciones: Iterable) -> GrafoVerificacion:
    """El grafo de verificación. Lanza DatosInvalidos si una salida o una
    ubicación nombra una sala que no existe (FR-030)."""
    salas = _salas_ordenadas(salas_dto)
    _fusionar_destinos(salas, _crear_aristas(salas))
    llaves, nodo_salida, enlazadas = _crear_llaves(salas, ubicaciones, datos.llave_salida)
    _fusionar_ubicaciones(salas, enlazadas)
    inicial = _buscar(salas, datos.sala_inicial)
    if inicial is None:
        raise DatosInvalidos(f"La sala inicial {datos.sala_inicial} no existe en el esqueleto")
    salida = _buscar(salas, datos.sala_salida)
    nodos = ListaEnlazada()
    for par in salas:
        nodos.agregar_al_final(par.valor[0])
    return GrafoVerificacion(nodos, llaves, inicial, salida, nodo_salida)
