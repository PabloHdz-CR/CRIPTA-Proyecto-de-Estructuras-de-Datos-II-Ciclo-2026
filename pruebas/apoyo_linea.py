"""Ayudas compartidas por las pruebas de 004-linea-tiempo (T003).

No es una prueba y no va en ejecutar_pruebas.py. Como vive en pruebas/, puede
usar estructuras de Python.

Contenido:
  - cripta_linea(): malla sintética con errantes, ratas, trampas y
    pergaminos en el suelo, determinista por semilla.
  - partida_con_linea(): Partida real (apoyo_niebla.partida_sobre) con la
    línea de tiempo conectada.
  - estado_de(), huella(), huella_partida(): foto comparable del resumen de un
    instante (FR-005, FR-006), armada con el mismo ConstructorEstadoVista que
    usa el juego y un MapaEtiquetas nuevo (no toca el de la partida).
  - OraculoVivo: la REFERENCIA de las pruebas (spec corregida en 67c1a83):
    captura en vivo la huella de la partida real en cada decisión del jugador
    y después de cada instante de evento distinto, y al usar un pergamino
    quita lo revertido y vuelve a capturar el estado actual.
  - secuencia_al_azar(): acciones deterministas por semilla (movimientos,
    esperas, recoger, ataques, viajes «ir a» paso a paso y pergaminos).
  - partida_referencia_inmortal(): la cripta de más salas de datos_offline/
    con el jugador sin daño letal (solo para medir).
"""
from __future__ import annotations

import random
import tempfile
from pathlib import Path

from cripta.controlador.constructorEstadoVista import ConstructorEstadoVista
from cripta.controlador.mapaEtiquetas import MapaEtiquetas
from cripta.modelo.nucleo.accion import Atacar, Esperar, Mover, Recoger, UsarPergamino
from pruebas.apoyo_niebla import (
    ERRANTE, PERGAMINO, PINCHOS, RATA, con_contenido, malla_n, partida_sobre)

VIDA_INMORTAL = 10 ** 9


# ---------------------------------------------------------------------------
# Criptas y partidas
# ---------------------------------------------------------------------------

def cripta_linea(semilla: int = 1, lado: int = 5) -> tuple:
    """Malla lado × lado con contenido al azar (determinista por semilla):
    errantes (generan eventos), ratas (atacan), pinchos y pergaminos."""
    azar = random.Random(semilla)
    descripcion = malla_n(lado)
    numero = 0
    for id_sala in range(2, lado * lado + 1):
        enemigos, trampas, objetos = [], [], []
        if azar.random() < 0.35:
            numero += 1
            enemigos.append((f"e{numero}", ERRANTE))
        if azar.random() < 0.15:
            numero += 1
            enemigos.append((f"r{numero}", RATA))
        if azar.random() < 0.10:
            trampas.append((f"t{id_sala}", PINCHOS))
        if azar.random() < 0.30:
            objetos.append(PERGAMINO)
        descripcion = con_contenido(descripcion, id_sala, enemigos=enemigos,
                                    trampas=trampas, objetos=objetos)
    return descripcion


def partida_con_linea(descripcion, k: int = 25, semilla: int = 1, sala_inicial: int = 1,
                      vida_jugador: int = VIDA_INMORTAL, con_linea: bool = True):
    """Partida real iniciada, con Diario y (si con_linea) la línea de tiempo."""
    partida = partida_sobre(descripcion, semilla=semilla, sala_inicial=sala_inicial,
                            vida_jugador=vida_jugador)
    if con_linea:
        from cripta.adaptadores.partidaBinaria import CopiadorBinario
        from cripta.modelo.nucleo.lineaTiempo import LineaTiempo
        partida.conectar_linea(LineaTiempo(k, CopiadorBinario()))
    return partida


# ---------------------------------------------------------------------------
# Huella del resumen
# ---------------------------------------------------------------------------

def estado_de(partida):
    """El EstadoVista de la partida con el mapa conocido (como el resumen)."""
    return ConstructorEstadoVista(MapaEtiquetas()).construir(partida, mapa_abierto=True)


def huella(estado) -> tuple:
    """Foto comparable de un EstadoVista (FR-005, FR-006). Deja fuera lo que es
    presentación y no estado del juego: el cursor del inventario y los
    mensajes de la bitácora."""
    jugador = estado.jugador
    sala = estado.sala
    mapa = estado.mapa
    return (
        estado.reloj, estado.terminada, estado.resultado,
        (jugador.vida, jugador.vida_max, jugador.ataque_efectivo, jugador.defensa_efectiva,
         jugador.velocidad, jugador.antorcha_encendida, jugador.acciones,
         jugador.enemigos_derrotados),
        sala.nombre,
        tuple((s.direccion, s.estado, s.costo) for s in sala.salidas),
        tuple((a.etiqueta, a.vida, a.vida_max) for a in sala.enemigos),
        tuple((o.id_objeto, o.nombre) for o in sala.objetos),
        tuple((e.tipo, e.descripcion) for e in estado.efectos),
        tuple((o.id_objeto, o.nombre, o.equipado) for o in estado.inventario.objetos),
        estado.inventario.cantidad_pergaminos,
        tuple((s.id, s.nombre, s.explorada, s.actual,
               tuple((x.direccion, x.destino, x.costo, x.estado)
                     for x in s.salidas if x is not None))
              for s in mapa.salas),
    )


def huella_partida(partida) -> tuple:
    return huella(estado_de(partida))


# ---------------------------------------------------------------------------
# Oráculo en vivo (la referencia de las pruebas)
# ---------------------------------------------------------------------------

class OraculoVivo:
    """Captura en vivo, en la partida REAL, la huella de cada instante de la
    historia que quedó:

    - en cada decisión del jugador (estado justo antes de decidir), por
      instante de decisión y por número de acción (#k);
    - después de cada instante de evento distinto (todos los eventos de ese
      tiempo ya ejecutados), enganchado al bucle de eventos solo en pruebas.

    Al usar un pergamino quita las capturas de lo revertido (decisiones con
    número ≥ la nueva próxima acción e instantes ≥ el nuevo instante de
    decisión) y vuelve a capturar el estado actual (FR-007, FR-008)."""

    def __init__(self, partida) -> None:
        self.partida = partida
        self.decisiones = {}        # k -> (instante, huella)
        self.instantes = {}         # t -> huella (eventos)
        self.acciones = []          # las acciones aceptadas, en orden (log)
        self._enganchar()
        self._capturar_decision()

    # -- consultas de la referencia --

    def huella_accion(self, k: int) -> tuple:
        return self.decisiones[k][1]

    def huella_instante(self, t: int) -> tuple:
        """La huella del instante t: la decisión de ese instante si la hay
        (estado justo antes de decidir, FR-001); si no, el evento."""
        for instante, valor in self.decisiones.values():
            if instante == t:
                return valor
        return self.instantes[t]

    def instantes_conocidos(self) -> list:
        """Todos los instantes con referencia (decisiones y eventos), en orden."""
        todos = set(self.instantes)
        for instante, _ in self.decisiones.values():
            todos.add(instante)
        return sorted(todos)

    def numeros_de_accion(self) -> list:
        return sorted(self.decisiones)

    # -- acciones --

    def aplicar(self, accion):
        """Aplica la acción en la partida real y actualiza las capturas."""
        partida = self.partida
        resultado = partida.aplicar_accion(accion)
        if not resultado.aceptada:
            return resultado
        self.acciones.append(accion)
        if isinstance(accion, UsarPergamino):
            k = partida.jugador.acciones + 1
            instante = partida.jugador.evento_accion.tiempo
            self.decisiones = {n: v for n, v in self.decisiones.items() if n < k}
            self.instantes = {t: v for t, v in self.instantes.items() if t < instante}
        self._capturar_decision()
        return resultado

    def _capturar_decision(self) -> None:
        partida = self.partida
        if partida.terminada():
            return
        k = partida.jugador.acciones + 1
        self.decisiones[k] = (partida.jugador.evento_accion.tiempo, huella_partida(partida))

    def _enganchar(self) -> None:
        """Reemplaza, solo en esta instancia, el bucle de eventos por uno
        idéntico al de Partida que además captura cada instante de evento."""
        partida = self.partida
        oraculo = self

        def procesar_eventos(limite=None):
            while partida.fin is None:
                siguiente = partida.agenda.ver_siguiente()
                if siguiente is None or siguiente is partida.jugador.evento_accion:
                    return
                if limite is not None and siguiente.tiempo > limite:
                    return
                evento = partida.mutador.agenda_extraer()
                if evento.tiempo > partida.reloj:
                    partida.mutador.asignar(partida, "reloj", evento.tiempo)
                evento.ejecutar(partida)
                proximo = partida.agenda.ver_siguiente()
                if proximo is not None and proximo.tiempo <= evento.tiempo:
                    continue            # quedan eventos de este mismo instante
                oraculo.instantes[evento.tiempo] = huella_partida(partida)

        partida._procesar_eventos = procesar_eventos


# ---------------------------------------------------------------------------
# Secuencias deterministas
# ---------------------------------------------------------------------------

def _direcciones_abiertas(partida) -> list:
    sala = partida.mundo.sala(partida.jugador.sala)
    return [s.direccion for s in sala.salidas if s is not None and s.transitable()]


def accion_al_azar(partida, azar: random.Random, con_pergaminos: bool = True):
    """Una acción posible elegida con 'azar' (puede ser rechazada)."""
    sala = partida.mundo.sala(partida.jugador.sala)
    if con_pergaminos and partida.puede_retroceder() and \
            partida.jugador.inventario.primer_pergamino() is not None and azar.random() < 0.08:
        return UsarPergamino()
    if not sala.activos.esta_vacia() and azar.random() < 0.6:
        return Atacar(sala.activos.ver_primero().id_instancia)
    if not sala.suelo.esta_vacia() and azar.random() < 0.5:
        return Recoger(sala.suelo.ver_primero().id_instancia)
    direcciones = _direcciones_abiertas(partida)
    if direcciones and azar.random() < 0.75:
        return Mover(azar.choice(direcciones))
    return Esperar()


def viaje_al_azar(oraculo: OraculoVivo, azar: random.Random, maximo: int = 6) -> int:
    """Un viaje «ir a» paso a paso (cada paso un Mover, FR-023 de 002) hacia
    una sala explorada elegida con 'azar'. Devuelve los pasos dados."""
    partida = oraculo.partida
    exploradas = [s.id for s in partida.mundo.conocidas
                  if s.conocimiento == 2 and s.id != partida.jugador.sala]
    if not exploradas:
        return 0
    destino_id = azar.choice(exploradas)
    if partida.validar_ir_a(destino_id) is not None:
        return 0
    destino = partida.mundo.sala(destino_id)
    pasos = 0
    while pasos < maximo and not partida.terminada() and partida.jugador.sala != destino_id:
        salida = partida.primer_paso_ir_a(destino)
        if salida is None:
            break
        if not oraculo.aplicar(Mover(salida.direccion)).aceptada:
            break
        pasos += 1
    return pasos


def secuencia_al_azar(oraculo: OraculoVivo, azar: random.Random, n: int,
                      con_pergaminos: bool = True, con_viajes: bool = True) -> int:
    """Aplica acciones al azar hasta que haya n acciones del jugador (o la
    partida termine). Devuelve cuántas acciones del jugador quedaron."""
    partida = oraculo.partida
    intentos = 0
    while partida.jugador.acciones < n and not partida.terminada() and intentos < n * 20:
        intentos += 1
        if con_viajes and azar.random() < 0.05:
            viaje_al_azar(oraculo, azar)
            continue
        oraculo.aplicar(accion_al_azar(partida, azar, con_pergaminos))
    return partida.jugador.acciones


# ---------------------------------------------------------------------------
# Cripta de referencia (mediciones)
# ---------------------------------------------------------------------------

def partida_referencia_inmortal(semilla: int = 123, k: int = 25, con_linea: bool = True):
    """La cripta con más salas de datos_offline/ (elegida por cantidad de
    salas, sin ids en el código), con el jugador sin daño letal: el truco solo
    sirve para llegar a miles de acciones al medir."""
    from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
    from cripta.adaptadores.fuenteOffline import FuenteOffline
    from cripta.adaptadores.partidaBinaria import CopiadorBinario
    from cripta.modelo.datos.cacheFichas import CacheFichas
    from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
    from cripta.modelo.datos.servicioDatos import ServicioDatos
    from cripta.modelo.nucleo.lineaTiempo import LineaTiempo
    from cripta.modelo.nucleo.partida import Partida
    raiz = Path(__file__).resolve().parent.parent
    fuente = FuenteOffline(raiz / "datos_offline")
    mayor = None
    for resumen in fuente.listar_criptas():
        if mayor is None or resumen.salas > mayor.salas:
            mayor = resumen
    carpeta = Path(tempfile.mkdtemp(prefix="apoyo_linea_"))
    servicio = ServicioDatos(fuente, FuenteAsincrona(fuente), CacheFichas(500),
                             AlmacenLocalDisco(carpeta))
    servicio.iniciar_cripta(mayor.id)
    partida = Partida(servicio)
    partida.iniciar(semilla)
    partida.jugador.vida_max = VIDA_INMORTAL
    partida.jugador.vida = VIDA_INMORTAL
    if con_linea:
        partida.conectar_linea(LineaTiempo(k, CopiadorBinario()))
    return partida
