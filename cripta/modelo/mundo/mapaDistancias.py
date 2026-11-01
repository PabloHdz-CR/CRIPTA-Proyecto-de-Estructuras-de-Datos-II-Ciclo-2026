"""MapaDistancias: distancias de costo mínimo HACIA la sala del jugador
(001-terreno-cazador, FR-011, FR-015, FR-017, FR-026; research R1 a R6)."""
from __future__ import annotations

from typing import Callable, Optional

from ..estructuras.heapMinimo import HeapMinimo


class EntradaMapa:
    """Entrada del heap: (distancia, sala), ordenada por (distancia, sala.id).

    El orden es total y determinista: dos entradas vivas de la misma sala
    nunca tienen la misma distancia, porque solo se inserta al mejorar.
    """

    def __init__(self, distancia: int, sala) -> None:
        self.distancia = distancia
        self.sala = sala

    def __lt__(self, otra: "EntradaMapa") -> bool:
        if self.distancia != otra.distancia:
            return self.distancia < otra.distancia
        return self.sala.id < otra.sala.id


class MapaDistancias:
    """Mapa compartido por todos los cazadores: para cada sala a costo <= cota
    de la sala del jugador, el costo mínimo de llegar desde ella hasta el
    jugador, usando solo salidas abiertas en el sentido del recorrido (FR-011).

    Se calcula con un Dijkstra HACIA ATRÁS desde la sala del jugador, por las
    salidas entrantes abiertas (research R4), con el HeapMinimo propio y
    eliminación perezosa (R6), sin pasar de la cota (R3). El estado de la
    búsqueda vive en dos campos de cada sala con un sello (R5): sin dict ni
    set, y empezar un cálculo nuevo cuesta O(1).

    Validez (R2): el mapa se reutiliza solo si la sala del jugador y la
    versión de las puertas (RegistroPuertas) son las mismas que cuando se
    calculó y su cota alcanza el rango pedido. En otro caso se recalcula
    desde cero. Las distancias dependen solo del esqueleto (costos incluidos),
    del estado de las puertas y de la sala objetivo; si nada de eso cambió, el
    mapa es idéntico al de un cálculo nuevo, y la decisión también (FR-017).

    Corrección de la cota (R3): después de asegurar(), cota >= rango del
    cazador que consulta. Si ese cazador puede moverse, existe u → v con
    costo + dist(v) <= rango, así que dist(v) < rango <= cota y v está en el
    mapa con su distancia exacta. Una v fuera del mapa tiene dist(v) > cota >=
    rango y nunca es parte de una ruta admisible: leer "sin distancia" para
    ella da la misma decisión que el cálculo completo.

    Trabajo (FR-026(b)): cada cálculo examina solo las salas a costo <= cota
    del jugador (las que fija) y sus vecinas inmediatas hacia atrás (las que
    anota sin llegar a fijar). No depende del tamaño total de la cripta.

    Política de cota P3 (T044, plan.md "Política de cota del mapa"): al
    recalcular con el mismo objetivo y la misma versión, la cota se duplica
    para no recalcular una vez por cada rango distinto, pero nunca pasa de
    R_activos, el mayor rango entre los cazadores activos (FR-026(b)).

    No es estado reversible (principio V): es caché derivada. Se invalida,
    nunca se restaura; deshacer o cargar cambian la versión de las puertas.
    """

    def __init__(self, mundo,
                 mayor_rango_activo: Optional[Callable[..., int]] = None) -> None:
        """mayor_rango_activo: función que devuelve R_activos (la Partida pasa
        Partida.mayor_rango_activo). Sin ella, el tope es el rango pedido: la
        cota nunca pasa de lo que se consulta."""
        self._mundo = mundo
        self._mayor_rango_activo = mayor_rango_activo
        self._registro = mundo.registro_puertas
        self._sello = 0                      # 0 = todavía no se calculó
        self._id_objetivo: Optional[int] = None
        self._version_puertas = -1
        self._cota = -1
        self._cota_reutilizable = 0          # la usa _cota_nueva (ver asegurar)
        self._salas_examinadas = 0           # acumulado (bench, FR-026)
        self._examinadas_ultimo = 0          # del último cálculo (FR-026, SC-004)
        self._calculos = 0                   # cuántas veces se recalculó (bench)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    @property
    def cota(self) -> int:
        """Costo máximo explorado por el cálculo vigente (-1 si no hay)."""
        return self._cota

    @property
    def id_objetivo(self) -> Optional[int]:
        """Sala del jugador cuando se calculó (None si no se calculó)."""
        return self._id_objetivo

    @property
    def salas_examinadas(self) -> int:
        """Salas examinadas por todos los cálculos (acumulado)."""
        return self._salas_examinadas

    @property
    def examinadas_ultimo_calculo(self) -> int:
        """Salas examinadas por el último cálculo: las fijadas a costo <= cota
        más sus vecinas inmediatas (FR-026(b))."""
        return self._examinadas_ultimo

    @property
    def calculos(self) -> int:
        """Cuántas veces se recalculó el mapa."""
        return self._calculos

    def distancia(self, sala) -> Optional[int]:
        """Distancia exacta de la sala al jugador, o None si no está en el mapa
        vigente (no alcanzada, o un valor provisional mayor que la cota, como
        el de una vecina del borde anotada sin fijarse). O(1)."""
        if (self._sello == 0 or sala.sello_mapa != self._sello
                or self._mundo.sello_mapa != self._sello):
            return None
        distancia = sala.distancia_mapa
        return distancia if distancia <= self._cota else None

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------

    def asegurar(self, id_objetivo: int, cota_minima: int) -> None:
        """Deja el mapa válido hacia la sala id_objetivo con cota >= cota_minima.

        Reutiliza el vigente si el objetivo y la versión de las puertas no
        cambiaron, ninguna otra búsqueda sobre este mundo lo pisó y su cota
        alcanza. Si no, recalcula desde cero con la cota de _cota_nueva().
        Recibe el id (no la Sala) para no buscarla en el mundo cuando el mapa
        sigue valiendo, que es lo más común entre cazadores del mismo ciclo.
        """
        version = self._registro.version
        mismo_estado = (self._id_objetivo == id_objetivo
                        and self._version_puertas == version
                        and self._mundo.sello_mapa == self._sello)
        if mismo_estado and self._cota >= cota_minima:
            return
        self._cota_reutilizable = self._cota if mismo_estado else 0
        cota = self._cota_nueva(cota_minima)
        self._calcular(self._mundo.sala(id_objetivo), version, cota)

    def _cota_nueva(self, cota_minima: int) -> int:
        """Regla de la cota al recalcular (plan.md, "Política de cota del mapa").

        Política P3, elegida con el bench (T044): duplicar con tope,
        max(cota_minima, min(max(cota_minima, 2 × anterior), R_activos)).
        'anterior' es la cota vigente si el objetivo y la versión no
        cambiaron, o 0 si cambiaron (self._cota_reutilizable). Así, 100
        cazadores con rangos distintos recalculan O(log2(R_max / R_min))
        veces por ciclo y no una vez por rango, y la cota nunca pasa del
        mayor rango entre los cazadores activos (FR-026(b) enmendado). Las
        alternativas del bench (P1, P2) sobrescriben solo este método.
        """
        duplicada = max(cota_minima, 2 * self._cota_reutilizable)
        if self._mayor_rango_activo is None:
            tope = cota_minima
        else:
            tope = self._mayor_rango_activo()
        return max(cota_minima, min(duplicada, tope))

    def _calcular(self, objetivo, version: int, cota: int) -> None:
        """Dijkstra hacia atrás desde 'objetivo', sin pasar de 'cota'."""
        sello = self._mundo.nuevo_sello_mapa()
        self._sello = sello
        self._id_objetivo = objetivo.id
        self._version_puertas = version
        self._cota = cota
        self._calculos += 1

        examinadas = 1
        objetivo.anotar_distancia(sello, 0)
        heap = HeapMinimo()
        heap.insertar(EntradaMapa(0, objetivo))
        while not heap.esta_vacio():
            entrada = heap.extraer_minimo()
            sala = entrada.sala
            # Eliminación perezosa: una entrada vieja ya no coincide con la
            # distancia de la sala (solo este cálculo escribe con este sello).
            if entrada.distancia != sala.distancia_mapa:
                continue
            for salida in sala.entrantes:
                if salida.cerrada:
                    continue
                origen = salida.origen
                nueva = entrada.distancia + salida.costo
                if origen.sello_mapa != sello:
                    examinadas += 1                      # primera vez en este cálculo
                elif nueva >= origen.distancia_mapa:
                    continue
                origen.anotar_distancia(sello, nueva)
                # Solo entra al heap lo que puede quedar dentro de la cota: una
                # vecina a más de la cota queda anotada (examinada) y nada más.
                if nueva <= cota:
                    heap.insertar(EntradaMapa(nueva, origen))
        self._examinadas_ultimo = examinadas
        self._salas_examinadas += examinadas
