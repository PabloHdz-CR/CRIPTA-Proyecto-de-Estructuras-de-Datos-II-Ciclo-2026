"""Mutador: ÚNICO punto por el que cambia el estado del modelo (§2.11).

Todo cambio (vida, ubicación, agenda, inventario, puertas...) se hace llamando
a un método de esta clase. Cada método:
  1. toma el valor anterior,
  2. aplica el cambio,
  3. avisa al 'diario' (si hay uno conectado) con lo necesario para revertirlo.

Así el futuro Diario de retroceso se engancha en UN lugar y no hay que buscar
mutaciones sueltas por el código. Sin diario conectado, avisar no cuesta nada.

Protocolo del diario (lo implementará el Diario):
    registrar(tipo, objetivo, detalle, anterior, nuevo)
"""
from __future__ import annotations

ATRIBUTO = "atributo"                       # objetivo.detalle: anterior -> nuevo
AGENDA_PROGRAMAR = "agenda_programar"       # objetivo = evento
AGENDA_EXTRAER = "agenda_extraer"           # objetivo = evento que salió
AGENDA_CANCELAR = "agenda_cancelar"         # objetivo = evento
SUELO_AGREGAR = "suelo_agregar"             # objetivo = sala, nuevo = objeto
SUELO_QUITAR = "suelo_quitar"               # objetivo = sala, anterior = objeto
INVENTARIO_AGREGAR = "inventario_agregar"   # objetivo = jugador, nuevo = objeto
INVENTARIO_QUITAR = "inventario_quitar"     # anterior = (objeto, posición, estaba_equipado)
INVENTARIO_EQUIPAR = "inventario_equipar"   # anterior = (objeto, posición, reemplazado)
ENEMIGO_ACTIVAR = "enemigo_activar"         # objetivo = sala, nuevo = enemigo
ENEMIGO_MOVER = "enemigo_mover"             # objetivo = enemigo, anterior = sala origen, nuevo = destino
ENEMIGO_QUITAR = "enemigo_quitar"           # objetivo = sala, anterior = enemigo
EFECTO_AGREGAR = "efecto_agregar"           # objetivo = actor, nuevo = efecto
EFECTO_QUITAR = "efecto_quitar"             # objetivo = actor, anterior = efecto


class Mutador:
    def __init__(self) -> None:
        self.agenda = None
        self.diario = None          # observador opcional (el Diario de retroceso)
        self._registrando = True

    def pausar(self) -> None:
        """Los cambios hechos mientras está en pausa no se registran (carga
        inicial, consumo del pergamino)."""
        self._registrando = False

    def reanudar(self) -> None:
        self._registrando = True

    def _avisar(self, tipo, objetivo, detalle, anterior, nuevo) -> None:
        # DECISIÓN: sin diario no hay costo alguno: el modelo funciona (y se prueba)
        # antes de que exista el Diario.
        if self.diario is not None and self._registrando:
            self.diario.registrar(tipo, objetivo, detalle, anterior, nuevo)

    # ------------------------------------------------------------------
    # Atributos simples: vida, vivo, velocidad, sala, reloj, rastro, cerrada,
    # armada, acciones, fin, evento_accion, antorcha_encendida...
    # ------------------------------------------------------------------

    # DECISIÓN: un solo método genérico por nombre de atributo en vez de uno por
    # campo: revertir cualquier asignación es siempre setattr(objeto, detalle,
    # anterior). Costo: un nombre mal escrito falla en ejecución, no antes.
    def asignar(self, objeto, nombre: str, nuevo) -> None:
        anterior = getattr(objeto, nombre)
        self._avisar(ATRIBUTO, objeto, nombre, anterior, nuevo)
        setattr(objeto, nombre, nuevo)

    # ------------------------------------------------------------------
    # Agenda
    # ------------------------------------------------------------------

    def agenda_programar(self, evento) -> None:
        self.agenda.programar(evento)
        self._avisar(AGENDA_PROGRAMAR, evento, None, None, None)

    def agenda_extraer(self):
        evento = self.agenda.extraer_siguiente()
        self._avisar(AGENDA_EXTRAER, evento, None, None, None)
        return evento

    def agenda_cancelar(self, evento) -> None:
        self.agenda.cancelar(evento)
        self._avisar(AGENDA_CANCELAR, evento, None, None, None)

    def agenda_reprogramar(self, evento, nuevo_tiempo: int):
        """Cancela y programa una copia; devuelve la copia."""
        self.agenda_cancelar(evento)
        nuevo = evento.duplicar(nuevo_tiempo)
        self.agenda_programar(nuevo)
        return nuevo

    # ------------------------------------------------------------------
    # Suelo, inventario y equipo
    # ------------------------------------------------------------------

    def suelo_agregar(self, sala, objeto) -> None:
        sala.suelo.agregar_al_final(objeto)
        self._avisar(SUELO_AGREGAR, sala, None, None, objeto)

    def suelo_quitar(self, sala, objeto) -> None:
        sala.suelo.eliminar_nodo(sala.suelo.buscar(objeto))
        self._avisar(SUELO_QUITAR, sala, None, objeto, None)

    def inventario_agregar(self, jugador, objeto) -> None:
        jugador.inventario.recoger(objeto)
        self._avisar(INVENTARIO_AGREGAR, jugador, None, None, objeto)

    def inventario_quitar(self, jugador, objeto) -> None:
        estaba_equipado = jugador.equipo.desequipar(objeto)
        posicion = jugador.inventario.quitar(objeto)
        self._avisar(INVENTARIO_QUITAR, jugador, None,
                     (objeto, posicion, estaba_equipado), None)

    def inventario_equipar(self, jugador, objeto) -> None:
        posicion = jugador.inventario.mover_al_frente(objeto)
        reemplazado = jugador.equipo.equipar(objeto)
        self._avisar(INVENTARIO_EQUIPAR, jugador, None,
                     (objeto, posicion, reemplazado), objeto)

    # ------------------------------------------------------------------
    # Enemigos y efectos
    # ------------------------------------------------------------------

    def enemigo_activar(self, sala, enemigo) -> None:
        sala.dormidos.eliminar_nodo(sala.dormidos.buscar(enemigo))
        sala.activos.agregar_al_final(enemigo)
        enemigo.activo = True
        self._avisar(ENEMIGO_ACTIVAR, sala, None, None, enemigo)

    def enemigo_mover(self, enemigo, origen, destino) -> None:
        origen.activos.eliminar_nodo(origen.activos.buscar(enemigo))
        destino.activos.agregar_al_final(enemigo)
        enemigo.sala = destino.id
        self._avisar(ENEMIGO_MOVER, enemigo, None, origen, destino)

    def enemigo_quitar(self, sala, enemigo) -> None:
        sala.activos.eliminar_nodo(sala.activos.buscar(enemigo))
        self._avisar(ENEMIGO_QUITAR, sala, None, enemigo, None)

    def efecto_agregar(self, actor, efecto) -> None:
        actor.efectos.agregar_al_final(efecto)
        self._avisar(EFECTO_AGREGAR, actor, None, None, efecto)

    def efecto_quitar(self, actor, efecto) -> None:
        actor.efectos.eliminar_nodo(actor.efectos.buscar(efecto))
        self._avisar(EFECTO_QUITAR, actor, None, efecto, None)