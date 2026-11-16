"""Conocimiento del jugador: niebla de guerra (002-niebla-guerra, §3.3, §5.3).

El conocimiento NO es otro grafo: es un estado por sala (`Sala.conocimiento`)
y un recuerdo por cara de puerta (`Salida.recordada`), guardados en los
objetos que ya existen (research R1). Consultarlo es leer un campo del objeto
que ya se tiene: O(1), sin dict ni set y sin buscar salas por id (FR-032).

Todo cambio pasa por el Mutador y solo si el valor cambia (research R2): el
pergamino lo revierte con el Diario existente, sin copias (principio V), y
registrar o invertir una entrada cuesta en proporción a lo revelado (FR-033).
"""
from __future__ import annotations

from ..estructuras.listaDoble import ListaDoble
from ..estructuras.listaEnlazada import ListaEnlazada
from ..ordenamiento import ClaveOrden, mezcla
from ..puertos.errores import ErrorCripta

# Estado de una sala para el jugador (FR-001). Enteros y no texto: se guardan
# con el codificador binario y se comparan en O(1).
DESCONOCIDA = 0
AVISTADA = 1
EXPLORADA = 2

# Recuerdo de una cara de puerta (FR-005 a FR-007).
NO_OBSERVADA = 0
ABIERTA = 1
CERRADA = 2


class RegistroConocidas:
    """Salas que dejaron de ser desconocidas, en ORDEN DE DESCUBRIMIENTO.

    DECISIÓN (research R4, cambia la orientación inicial del equipo): no se
    mantiene ordenado por id. Insertar en orden cuesta O(conocidas) por sala
    revelada (18,6 µs frente a 0,9 µs con 300 conocidas, mediciones previas
    del plan), y eso haría que explorar dependiera del tamaño del mapa
    conocido, contra FR-033. Agregar y quitar al final es O(1): el Diario
    revierte siempre en orden inverso al de los cambios, así que la sala que
    hay que quitar es siempre la última agregada. El orden por id se obtiene
    solo al armar el panel del mapa (ordenadas_por_id), con la mezcla propia.

    Invariante: una sala está aquí si y solo si su conocimiento no es
    DESCONOCIDA, y aparece una sola vez.
    """

    def __init__(self) -> None:
        self._salas = ListaDoble()

    def agregar(self, sala) -> None:
        """Agrega al final. O(1). Lo llama el Mutador (conocida_agregar)."""
        self._salas.agregar_al_final(sala)

    def quitar_ultima(self, sala) -> None:
        """Quita la última sala agregada, que debe ser `sala`. O(1). Es el
        inverso de agregar en el Diario; si la última no es `sala`, el orden de
        reversión se rompió y se avisa en vez de dejar el registro inconsistente."""
        if self._salas.esta_vacia() or self._salas.ver_ultimo() is not sala:
            raise ErrorCripta(
                f"El registro de conocidas no termina en la sala {getattr(sala, 'id', sala)}: "
                "la reversión del conocimiento salió de orden")
        self._salas.eliminar_ultimo()

    def vaciar(self) -> None:
        self._salas.vaciar()

    def __iter__(self):
        return iter(self._salas)

    def __len__(self) -> int:
        return len(self._salas)

    def ordenadas_por_id(self) -> ListaEnlazada:
        """ListaEnlazada nueva con las mismas salas ordenadas por id numérico
        (FR-016). Copia y ordena con la mezcla propia: O(k log k), k =
        conocidas. Solo la usa el panel del mapa conocido; no cambia el
        registro."""
        claves = ListaEnlazada()
        for sala in self._salas:
            claves.agregar_al_final(ClaveOrden(sala.id, sala))
        ordenadas = ListaEnlazada()
        for clave in mezcla(claves):
            ordenadas.agregar_al_final(clave.valor)
        return ordenadas


class ConocimientoJugador:
    """Servicio del Modelo que cambia el conocimiento del jugador. Uno por
    Partida. No guarda estado propio: lee y escribe `Sala.conocimiento`,
    `Salida.recordada` y `Mundo.conocidas`, siempre por el Mutador y solo si
    el valor cambia (research R2).

    Llega a las salas por referencia (`Salida.sala_destino`, del enlace de
    001): nunca busca una sala por id (FR-032).
    """

    def __init__(self, mundo, mutador) -> None:
        self._mundo = mundo
        self._mutador = mutador

    # ------------------------------------------------------------------
    # Consultas, O(1) (FR-032)
    # ------------------------------------------------------------------

    @staticmethod
    def estado(sala) -> int:
        """DESCONOCIDA, AVISTADA o EXPLORADA."""
        return sala.conocimiento

    @staticmethod
    def recuerdo(salida) -> int:
        """NO_OBSERVADA, ABIERTA o CERRADA."""
        return salida.recordada

    # ------------------------------------------------------------------
    # Cambios
    # ------------------------------------------------------------------

    def iniciar(self, sala_inicial) -> None:
        """Instante 0 (FR-001, FR-003): la inicial explorada y sus destinos
        avistados. La Partida lo llama con el Mutador en pausa: es el punto
        de partida, no un cambio reversible."""
        self.entrar(sala_inicial)

    def entrar(self, sala) -> None:
        """El jugador entra a `sala` (FR-004): queda explorada y los destinos
        desconocidos de sus salidas quedan avistados. O(salidas de la sala)."""
        self._subir(sala, EXPLORADA)
        self._avistar_destinos(sala)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _avistar_destinos(self, sala) -> None:
        for salida in sala.salidas:
            if salida is not None and salida.sala_destino is not None:
                self._subir(salida.sala_destino, AVISTADA)

    def _subir(self, sala, nuevo: int) -> None:
        """Sube el estado de la sala a `nuevo` si estaba por debajo; nunca lo
        baja (solo el Diario baja estados al revertir). Si la sala deja de ser
        desconocida, la agrega al registro en el mismo cambio."""
        anterior = sala.conocimiento
        if anterior >= nuevo:
            return
        if anterior == DESCONOCIDA:
            self._mutador.conocida_agregar(self._mundo.conocidas, sala)
        self._mutador.asignar(sala, "conocimiento", nuevo)
