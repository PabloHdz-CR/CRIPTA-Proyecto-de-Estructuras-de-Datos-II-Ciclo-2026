"""Línea de tiempo de la partida (004-linea-tiempo, §3.6, §5.5).

La historia de la partida tal como quedó, consultable en cualquier instante
pasado sin modificar la partida. Ver specs/004-linea-tiempo/plan.md y
research.md (R1 a R7).
"""
from __future__ import annotations

from ..estructuras.arregloArbol import ArregloArbol
from ..estructuras.listaDoble import ListaDoble
from ..estructuras.listaEnlazada import ListaEnlazada

K_POR_OMISION = 25


class EntradaAccion:
    """Una acción del jugador que sigue existiendo en la historia, con el
    instante de decisión en que la tomó."""

    __slots__ = ("accion", "tiempo_decision")

    def __init__(self, accion, tiempo_decision: int) -> None:
        self.accion = accion
        self.tiempo_decision = tiempo_decision


class AjustePergamino:
    """Lo que un pergamino cambió fuera de la reversión (FR-008, regla D50):
    el inventario y los pergaminos en el suelo de la partida real justo
    después de usarlo, en el instante al que volvió el reloj (research R6)."""

    __slots__ = ("tiempo", "inventario", "pergaminos_suelo")

    def __init__(self, tiempo: int, inventario: ListaEnlazada,
                 pergaminos_suelo: ListaEnlazada) -> None:
        self.tiempo = tiempo
        self.inventario = inventario                  # de (id_objeto, id_ficha, equipado)
        self.pergaminos_suelo = pergaminos_suelo      # de (id_sala, id_objeto, id_ficha)


class Bloque:
    """Un punto de control y las entradas que lo siguen (como mucho K
    acciones). El punto de control es el estado completo justo antes de la
    primera acción del bloque."""

    __slots__ = ("punto_control", "primera_accion", "tiempo_inicio", "entradas", "acciones")

    def __init__(self, punto_control: bytes, primera_accion: int, tiempo_inicio: int) -> None:
        self.punto_control = punto_control
        self.primera_accion = primera_accion
        self.tiempo_inicio = tiempo_inicio
        self.entradas = ListaDoble()                  # EntradaAccion o AjustePergamino
        self.acciones = 0


class LineaTiempo:
    """Bloques de K acciones con un punto de control al inicio de cada uno,
    en un ArregloArbol (acceso por posición O(log n), research R4).

    La Partida real la alimenta: antes_de_accion y registrar_accion en cada
    acción del jugador, registrar_contenido la primera vez que carga una sala,
    y al_usar_pergamino (US2). Fuera de los puntos de control solo guarda las
    acciones y los ajustes del pergamino (FR-020)."""

    def __init__(self, k: int = K_POR_OMISION, copiador=None) -> None:
        if not isinstance(k, int) or k < 1:
            raise ValueError("K debe ser un entero mayor o igual que 1")
        self._k = k
        self._copiador = copiador
        self._bloques = ArregloArbol()
        self._contenidos = ListaEnlazada()            # de (id_sala, ContenidoSalaDTO)
        self._acciones = 0
        self._pendiente = None                        # (bytes, tiempo) del próximo bloque

    # ------------------------------------------------------------------
    # Consultas simples
    # ------------------------------------------------------------------

    @property
    def k(self) -> int:
        return self._k

    @property
    def acciones(self) -> int:
        """Acciones del jugador que siguen existiendo en la historia (n)."""
        return self._acciones

    @property
    def bloques(self) -> ArregloArbol:
        return self._bloques

    @property
    def copiador(self):
        return self._copiador

    def contenidos(self) -> ListaEnlazada:
        return self._contenidos

    def contenido_registrado(self, id_sala: int):
        """El contenido inicial registrado de la sala, o None. O(salas
        registradas): solo se usa al re-simular una sala que la copia carga."""
        for id_registrado, contenido in self._contenidos:
            if id_registrado == id_sala:
                return contenido
        return None

    # ------------------------------------------------------------------
    # Alimentación desde la Partida real
    # ------------------------------------------------------------------

    def conectar(self, partida) -> None:
        """Registra el contenido de las salas que la partida ya cargó (por
        ejemplo la sala inicial, antes de conectar la línea)."""
        for sala in partida.mundo:
            if sala.contenido_cargado:
                contenido = partida.servicio.contenido_en_memoria(sala.id)
                if contenido is not None:
                    self.registrar_contenido(sala.id, contenido)

    def antes_de_accion(self, partida, tiempo_decision: int) -> None:
        """Al empezar un bloque (cada K acciones) toma el punto de control: el
        estado justo antes de la decisión. Queda pendiente hasta que la acción
        se acepte (registrar_accion), así una acción que falla no deja un
        bloque vacío. O(estado) cada K acciones; O(1) las demás."""
        if self._acciones % self._k == 0:
            self._pendiente = (self._copiador.tomar(partida), tiempo_decision)
        else:
            self._pendiente = None

    def registrar_accion(self, accion, tiempo_decision: int) -> None:
        """Agrega la acción aceptada a la historia. O(1) (O(log n) si abre un
        bloque)."""
        if self._pendiente is not None:
            datos, tiempo = self._pendiente
            self._bloques.agregar_al_final(Bloque(datos, self._acciones + 1, tiempo))
            self._pendiente = None
        bloque = self._bloques.ultimo()
        bloque.entradas.agregar_al_final(EntradaAccion(accion, tiempo_decision))
        bloque.acciones += 1
        self._acciones += 1

    def registrar_contenido(self, id_sala: int, contenido) -> None:
        """Contenido inicial de una sala, la primera vez que se carga (R5)."""
        if self.contenido_registrado(id_sala) is None:
            self._contenidos.agregar_al_final((id_sala, contenido))
