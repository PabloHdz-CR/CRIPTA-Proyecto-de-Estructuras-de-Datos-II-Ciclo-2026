"""Verificación de resolubilidad (003-resolubilidad, research.md R2 a R4).

verificar_resolubilidad(datos, salas, ubicaciones) arma el grafo
(grafoVerificacion) y corre:

FASE 1 (R2, R3): un solo recorrido en anchura desde la sala inicial que nunca
vuelve a empezar. Una salida cerrada con llave no obtenida queda PENDIENTE en
su llave; las llaves alcanzadas entran a un HeapMinimo de disponibles. Solo
cuando la cola se vacía se extrae la disponible de menor id, se marca
obtenida y se reexaminan sus pendientes. Da:
  - el orden lexicográficamente menor (FR-007, FR-009): obtener una llave solo
    agranda la región (FR-003), así que la elección codiciosa nunca impide
    una posterior;
  - el veredicto (FR-001): la marca entra_por_puerta_salida se pone al
    EXAMINAR una salida cerrada que requiere llave_salida, con esa llave ya
    obtenida y destino sala_salida, aunque sala_salida ya estuviera alcanzada
    (H1.E12);
  - la frontera (FR-012) y las no obtenibles (FR-011), de lo que dejó el
    mismo recorrido (FR-034).
Cada salida se examina a lo sumo dos veces. Costo O(S + E + L + K log K).

FASE 2 (R4, solo si NO_RESOLUBLE): una sola pasada para todas las llaves,
que continúa más allá de la frontera (FR-034):
  - Tarjan iterativo (Pila propia, sin recursión) sobre el grafo de bloqueo:
    salas no alcanzadas y llaves no obtenidas, con sala -> sala por salidas
    transitables, sala -> llave por ubicación y llave -> sala por cada salida
    cerrada que la requiere. Los grupos de FR-015 son las componentes con al
    menos una llave y más de un nodo;
  - relleno por prioridad: las puertas que requieren una llave de un grupo y
    llegan a una sala del mismo grupo, ordenadas por (id de la llave, sala de
    origen, dirección N, S, E, O), etiquetan cada sala del grupo una vez con
    la menor puerta que la alcanza. La dependencia mínima de cada llave es la
    menor etiqueta de sus ubicaciones, y da a la vez la llave y la puerta que
    muestra FR-015.
Costo O(S + E + K + D log D), con D puertas que entran a los grupos.
"""
from __future__ import annotations

from typing import Iterable, Optional

from ..estructuras.cola import Cola
from ..estructuras.heapMinimo import HeapMinimo
from ..estructuras.listaEnlazada import ListaEnlazada
from ..estructuras.pila import Pila
from ..ordenamiento import ClaveOrden, mezcla
from ..puertos.dto import DatosCriptaDTO
from .grafoVerificacion import AristaSalida, GrafoVerificacion, NodoLlave, NodoSala, construir_grafo
from .resultadoResolubilidad import (
    LLAVE_SALIDA_NO_OBTENIBLE, NO_RESOLUBLE, RESOLUBLE, SIN_PUERTA_DE_SALIDA, CicloLlaves,
    LlaveNoObtenible, LlaveOrdenada, PasoCiclo, PuertaFrontera, ResultadoResolubilidad)


class Contador:
    """Salidas examinadas por la verificación (FR-033): lo reporta --bench."""

    def __init__(self) -> None:
        self._valor = 0

    @property
    def valor(self) -> int:
        return self._valor

    def sumar(self) -> None:
        self._valor += 1


class EstadoFase1:
    """Lo que deja la fase 1 (o la alternativa ingenua, que la reemplaza)."""

    def __init__(self) -> None:
        self.orden = ListaEnlazada()                 # LlaveOrdenada
        self.entra_por_puerta_salida = False
        self.sin_llave = ListaEnlazada()             # AristaSalida cerradas sin llave


# ---------------------------------------------------------------------------
# Fase 1
# ---------------------------------------------------------------------------

def requiere_llave_salida(arista: AristaSalida, grafo: GrafoVerificacion) -> bool:
    """Salida cerrada cuya llave es llave_salida, hacia sala_salida (R3)."""
    return (arista.cerrada and arista.llave is grafo.llave_salida
            and grafo.salida is not None and arista.destino is grafo.salida)


def primera_ubicacion_alcanzada(llave: NodoLlave):
    """La primera ubicación, por (sala, enemigo), cuya sala ya está alcanzada."""
    for ubicacion in llave.ubicaciones:
        if ubicacion.sala.alcanzada:
            return ubicacion.dto
    return None


def _fase1(grafo: GrafoVerificacion, contador: Contador) -> EstadoFase1:
    estado = EstadoFase1()
    cola = Cola()
    disponibles = HeapMinimo()

    def alcanzar(sala: NodoSala) -> None:
        sala.alcanzada = True
        cola.encolar(sala)
        for llave in sala.llaves_aqui:
            if not llave.disponible:
                llave.disponible = True
                disponibles.insertar(llave)

    def examinar(arista: AristaSalida) -> None:
        contador.sumar()
        if arista.transitable():
            if requiere_llave_salida(arista, grafo):
                estado.entra_por_puerta_salida = True
            if not arista.destino.alcanzada:
                alcanzar(arista.destino)
        elif arista.llave is not None:
            arista.llave.pendientes.agregar_al_final(arista)
        else:
            estado.sin_llave.agregar_al_final(arista)

    alcanzar(grafo.inicial)
    while True:
        while not cola.esta_vacia():
            sala = cola.desencolar()
            for arista in sala.salidas:
                examinar(arista)
        if disponibles.esta_vacio():
            break
        llave = disponibles.extraer_minimo()
        llave.obtenida = True
        estado.orden.agregar_al_final(LlaveOrdenada(llave.id, primera_ubicacion_alcanzada(llave)))
        pendientes = llave.pendientes
        llave.pendientes = ListaEnlazada()
        for arista in pendientes:
            examinar(arista)
    return estado


# ---------------------------------------------------------------------------
# Resultado (frontera, no obtenibles y, si hace falta, la fase 2)
# ---------------------------------------------------------------------------

def _puerta(arista: AristaSalida, id_llave: Optional[str]) -> PuertaFrontera:
    return PuertaFrontera(arista.origen.id, arista.direccion, arista.destino.id, id_llave)


def _frontera(grafo: GrafoVerificacion, estado: EstadoFase1) -> ListaEnlazada:
    """Las puertas bloqueadas que dejó el recorrido (pendientes de llaves no
    obtenidas y cerradas sin llave) con destino no alcanzado, en orden
    canónico (FR-012)."""
    candidatas = ListaEnlazada()
    for llave in grafo.llaves:
        if not llave.obtenida:
            for arista in llave.pendientes:
                candidatas.agregar_al_final(arista)
    for arista in estado.sin_llave:
        candidatas.agregar_al_final(arista)
    pares = ListaEnlazada()
    for arista in candidatas:
        if not arista.destino.alcanzada:
            pares.agregar_al_final(ClaveOrden(arista.clave_canonica(), arista))
    frontera = ListaEnlazada()
    for par in mezcla(pares):
        llave = par.valor.llave
        frontera.agregar_al_final(_puerta(par.valor, llave.id if llave is not None else None))
    return frontera


def _no_obtenibles(grafo: GrafoVerificacion) -> ListaEnlazada:
    resultado = ListaEnlazada()
    for llave in grafo.llaves:                      # ya en orden por id
        if not llave.obtenida:
            ubicaciones = ListaEnlazada()
            for ubicacion in llave.ubicaciones:     # ya en orden (sala, enemigo)
                ubicaciones.agregar_al_final(ubicacion.dto)
            resultado.agregar_al_final(LlaveNoObtenible(llave.id, ubicaciones))
    return resultado


def resultado_desde(datos: DatosCriptaDTO, grafo: GrafoVerificacion, estado: EstadoFase1,
                    contador: Contador) -> ResultadoResolubilidad:
    """Arma el resultado a partir de lo que dejó la fase 1. Lo comparten la
    verificación y la alternativa ingenua del bench (R11)."""
    llave_salida = grafo.llave_salida
    resoluble = llave_salida.obtenida and estado.entra_por_puerta_salida
    frontera = _frontera(grafo, estado)
    no_obtenibles = _no_obtenibles(grafo)
    if resoluble:
        return ResultadoResolubilidad(
            veredicto=RESOLUBLE, id_cripta=datos.id, version_cripta=datos.version,
            llave_salida=datos.llave_salida, sala_salida=datos.sala_salida,
            orden=estado.orden, no_obtenibles=no_obtenibles, frontera=frontera,
            salidas_examinadas=contador.valor)
    if not llave_salida.obtenida:
        motivo, solo_sin_puerta = LLAVE_SALIDA_NO_OBTENIBLE, False
    else:
        motivo = SIN_PUERTA_DE_SALIDA
        solo_sin_puerta = grafo.salida is not None and grafo.salida.alcanzada
    ciclos = _fase2(grafo, contador)
    return ResultadoResolubilidad(
        veredicto=NO_RESOLUBLE, id_cripta=datos.id, version_cripta=datos.version,
        llave_salida=datos.llave_salida, sala_salida=datos.sala_salida,
        motivo=motivo, sala_salida_solo_sin_puerta=solo_sin_puerta,
        no_obtenibles=no_obtenibles, frontera=frontera, ciclos=ciclos,
        salidas_examinadas=contador.valor)


# ---------------------------------------------------------------------------
# Fase 2
# ---------------------------------------------------------------------------

def _sucesores(nodo, contador: Contador):
    """Sucesores en el grafo de bloqueo. Las salas alcanzadas no participan:
    desde ellas no se llega a ninguna ubicación no obtenible sin pasar por
    una puerta bloqueada."""
    if isinstance(nodo, NodoSala):
        for arista in nodo.salidas:
            contador.sumar()
            if arista.transitable() and not arista.destino.alcanzada:
                yield arista.destino
        for llave in nodo.llaves_aqui:
            if not llave.obtenida:
                yield llave
    else:
        for arista in nodo.puertas:
            if not arista.destino.alcanzada:
                yield arista.destino


class Componente:
    """Una componente fuertemente conexa del grafo de bloqueo."""

    def __init__(self) -> None:
        self.tamano = 0
        self.llaves = ListaEnlazada()

    def es_grupo(self) -> bool:
        return not self.llaves.esta_vacia() and self.tamano > 1


def _tarjan(nodos: ListaEnlazada, contador: Contador) -> ListaEnlazada:
    """Tarjan iterativo: una Pila de nodos de la componente en curso y otra de
    marcos (nodo, generador de sucesores). Devuelve las componentes."""
    componentes = ListaEnlazada()
    pila = Pila()
    marcos = Pila()
    siguiente_indice = 0
    for inicio in nodos:
        if inicio.indice is not None:
            continue
        inicio.indice = inicio.enlace = siguiente_indice
        siguiente_indice += 1
        pila.apilar(inicio)
        inicio.en_pila = True
        marcos.apilar((inicio, _sucesores(inicio, contador)))
        while not marcos.esta_vacia():
            nodo, sucesores = marcos.ver_tope()
            avanzo = False
            for sucesor in sucesores:
                if sucesor.indice is None:
                    sucesor.indice = sucesor.enlace = siguiente_indice
                    siguiente_indice += 1
                    pila.apilar(sucesor)
                    sucesor.en_pila = True
                    marcos.apilar((sucesor, _sucesores(sucesor, contador)))
                    avanzo = True
                    break
                if sucesor.en_pila and sucesor.indice < nodo.enlace:
                    nodo.enlace = sucesor.indice
            if avanzo:
                continue
            marcos.desapilar()
            if not marcos.esta_vacia():
                padre = marcos.ver_tope()[0]
                if nodo.enlace < padre.enlace:
                    padre.enlace = nodo.enlace
            if nodo.enlace == nodo.indice:
                componente = Componente()
                while True:
                    miembro = pila.desapilar()
                    miembro.en_pila = False
                    miembro.componente = componente
                    componente.tamano += 1
                    if isinstance(miembro, NodoLlave):
                        componente.llaves.agregar_al_final(miembro)
                    if miembro is nodo:
                        break
                componentes.agregar_al_final(componente)
    return componentes


def _rellenar(grupos: ListaEnlazada, contador: Contador) -> None:
    """Relleno por prioridad (R4): cada sala de un grupo queda etiquetada con
    la menor (llave, puerta) que la alcanza dentro del grupo."""
    semillas = ListaEnlazada()
    for grupo in grupos:
        for llave in grupo.llaves:
            for arista in llave.puertas:
                destino = arista.destino
                if not destino.alcanzada and destino.componente is grupo:
                    semillas.agregar_al_final(ClaveOrden(
                        (llave.id,) + arista.clave_canonica(), (llave, arista)))
    for semilla in mezcla(semillas):
        llave, arista = semilla.valor
        inicio = arista.destino
        if inicio.etiqueta is not None:
            continue
        grupo = inicio.componente
        etiqueta = (semilla.clave, llave, arista)
        inicio.etiqueta = etiqueta
        cola = Cola()
        cola.encolar(inicio)
        while not cola.esta_vacia():
            sala = cola.desencolar()
            for salida in sala.salidas:
                contador.sumar()
                destino = salida.destino
                if (salida.transitable() and not destino.alcanzada
                        and destino.componente is grupo and destino.etiqueta is None):
                    destino.etiqueta = etiqueta
                    cola.encolar(destino)


def _dependencia_minima(llave: NodoLlave):
    """(llave Y, puerta) de menor etiqueta entre las ubicaciones de la llave
    dentro de su grupo."""
    mejor = None
    for ubicacion in llave.ubicaciones:
        sala = ubicacion.sala
        if sala.componente is llave.componente and sala.etiqueta is not None:
            if mejor is None or sala.etiqueta[0] < mejor[0]:
                mejor = sala.etiqueta
    return mejor


def _ciclo(grupo: Componente) -> CicloLlaves:
    """FR-015: desde la llave de menor id del grupo, siguiendo la dependencia
    mínima hasta repetir una llave; el ciclo empieza en la repetida."""
    actual = None
    for llave in grupo.llaves:
        if actual is None or llave < actual:
            actual = llave
    pasos = ListaEnlazada()
    posicion = 0
    while actual.posicion_paseo is None:
        actual.posicion_paseo = posicion
        _, siguiente, arista = _dependencia_minima(actual)
        pasos.agregar_al_final(PasoCiclo(actual.id, _puerta(arista, siguiente.id)))
        actual = siguiente
        posicion += 1
    ciclo = ListaEnlazada()
    numero = 0
    for paso in pasos:
        if numero >= actual.posicion_paseo:
            ciclo.agregar_al_final(paso)
        numero += 1
    return CicloLlaves(ciclo)


def _fase2(grafo: GrafoVerificacion, contador: Contador) -> ListaEnlazada:
    nodos = ListaEnlazada()
    for sala in grafo.salas:
        if not sala.alcanzada:
            nodos.agregar_al_final(sala)
    for llave in grafo.llaves:
        if not llave.obtenida:
            nodos.agregar_al_final(llave)
    grupos = ListaEnlazada()
    for componente in _tarjan(nodos, contador):
        if componente.es_grupo():
            grupos.agregar_al_final(componente)
    _rellenar(grupos, contador)
    pares = ListaEnlazada()
    for grupo in grupos:
        menor = None
        for llave in grupo.llaves:
            if menor is None or llave < menor:
                menor = llave
        pares.agregar_al_final(ClaveOrden(menor.id, grupo))
    ciclos = ListaEnlazada()
    for par in mezcla(pares):
        ciclos.agregar_al_final(_ciclo(par.valor))
    return ciclos


# ---------------------------------------------------------------------------
# Entrada pública
# ---------------------------------------------------------------------------

def verificar_resolubilidad(datos: DatosCriptaDTO, salas: Iterable,
                            ubicaciones: Iterable) -> ResultadoResolubilidad:
    """Verifica la cripta con sus salas (SalaDTO) y la ubicación de llaves
    (UbicacionLlaveDTO). Lanza DatosInvalidos si los datos no son
    coherentes (FR-030); quien llama decide si eso es NO_VERIFICADA."""
    grafo = construir_grafo(datos, salas, ubicaciones)
    contador = Contador()
    estado = _fase1(grafo, contador)
    return resultado_desde(datos, grafo, estado, contador)
