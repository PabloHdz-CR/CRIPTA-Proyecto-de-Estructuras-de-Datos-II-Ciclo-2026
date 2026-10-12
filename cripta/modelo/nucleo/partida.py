"""Partida: fachada del modelo y dueña del estado (§2.3, §2.4, §2.12)."""
from __future__ import annotations

import random

from ..actores.jugador import Jugador
from ..estructuras.colaAcotada import ColaAcotada
from ..estructuras.listaEnlazada import ListaEnlazada
from ..mundo.mundo import Mundo
from ..reloj.agenda import Agenda
from ..reloj.efecto import EfectoAntorcha, EfectoVelocidad, EfectoVeneno
from ..reloj.eventos import EventoAccionActor, EventoCierrePuerta
from .accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar,
    UsarPergamino)
from .combate import Combate
from .constantes import (
    ESTADO_DERROTA, ESTADO_VICTORIA, TAMANO_BITACORA, calcular_intervalo,
    reescalar_restante)
from .fabricaEntidades import FabricaEntidades
from .mutador import Mutador
from .puntajes import RegistroPuntaje
from .resultadoAccion import ResultadoAccion
from .validadorAcciones import ValidadorAcciones


class Partida:
    """Dueña del reloj, la semilla, el Random propio, la agenda, el jugador y
    el mundo. Es lo único que el Controlador necesita conocer del modelo.

    'servicio' es el ServicioDatos (duck typing). Se usan estos cuatro métodos:
    datos_cripta(), esqueleto() (iterable de entradas con .sala), asegurar_contenido(id),
    precargar(id) y resolver_fichas(ids). iniciar_cripta() ya debe haberse llamado.

    Flujo de una acción (§9): valida -> asegura el contenido de la sala destino
    (si hace falta espera la red SIN mover el reloj) -> ejecuta la acción del
    jugador -> programa su siguiente turno -> procesa eventos en orden de
    (tiempo, secuencia) hasta que el turno del jugador vuelva a ser el menor.
    """

    def __init__(self, servicio) -> None:
        self.servicio = servicio
        self.mutador = Mutador()
        self.validador = ValidadorAcciones()
        self.bitacora = ColaAcotada(TAMANO_BITACORA)
        self.diario = None                     # lo conecta conectar_diario()
        self.reloj = 0
        self.semilla = None
        self.azar = None                       # random.Random(semilla), propio
        self.agenda = None
        self.mundo = None
        self.jugador = None
        self.datos = None
        self.fin = None                        # None, "victoria" o "derrota"
        self._fabrica = FabricaEntidades(servicio)
        self._mensajes = ListaEnlazada()

    # ------------------------------------------------------------------
    # Inicio y consultas
    # ------------------------------------------------------------------

    def iniciar(self, semilla: int) -> None:
        """Reloj en 0, jugador en la sala inicial con acción en t=0, rastro de
        esa sala en 0 y sus enemigos activados (§2.3, §2.4)."""
        self.mutador.pausar()
        self.datos = self.servicio.datos_cripta()
        self.semilla = semilla
        # DECISIÓN: Random propio por partida (nunca el generador global): misma
        # semilla + mismas acciones = misma partida (determinismo, §2.12).
        self.azar = random.Random(semilla)
        self.reloj = 0
        self.fin = None
        self.bitacora.vaciar()
        self.agenda = Agenda()
        self.mutador.agenda = self.agenda
        self.mundo = Mundo(self.datos)
        salas = ListaEnlazada()
        for entrada in self.servicio.esqueleto():
            salas.agregar_al_final(entrada.sala)
        self.mundo.agregar_esqueleto(salas)
        self.jugador = Jugador(self.datos.jugador, self.mundo.sala_inicial,
                               self.mundo.inventario_max)

        inicial = self.mundo.sala_inicial
        self._asegurar_contenido(inicial)
        sala = self.mundo.sala(inicial)
        sala.rastro = 0
        # DECISIÓN: el turno del jugador se programa ANTES de activar enemigos: es el
        # evento más antiguo (secuencia 0) y gana cualquier empate de tiempo.
        primer_turno = EventoAccionActor(0, self.jugador)    # primero: secuencia 0
        self.agenda.programar(primer_turno)
        self.jugador.evento_accion = primer_turno
        sala.activar_enemigos(self)
        self.servicio.precargar(inicial)
        self._procesar_eventos()
        self.mutador.reanudar()

    def conectar_diario(self, diario) -> None:
        """Engancha el Diario de retroceso al punto único de mutación."""
        self.diario = diario
        self.mutador.diario = diario

    def terminada(self) -> bool:
        return self.fin is not None

    def resultado(self, nombre: str) -> RegistroPuntaje:
        """El registro de la partida terminada (§2.12)."""
        if self.fin is None:
            raise ValueError("La partida todavía no termina")
        return RegistroPuntaje(nombre, self.datos.id, self.datos.version,
                               self.jugador.acciones, self.jugador.enemigos_derrotados,
                               self.reloj, self.fin)

    def puede_retroceder(self) -> bool:
        return self.diario is not None and self.diario.hay_cambios()

    def deshacer(self) -> bool:
        """Revierte hasta antes de la última acción del jugador (máx. 5). Sin
        diario conectado no hace nada y devuelve False."""
        if self.diario is None:
            return False
        return self.diario.deshacer(self)

    # ------------------------------------------------------------------
    # Acción del jugador
    # ------------------------------------------------------------------

    def aplicar_accion(self, accion) -> ResultadoAccion:
        """Valida, ejecuta y procesa eventos hasta la próxima decisión. Un
        rechazo no consume tiempo ni cambia nada (Apéndice B)."""
        if self.fin is not None:
            return ResultadoAccion.rechazada("La partida ya terminó.")
        motivo = self.validador.validar(self, accion)
        if motivo is not None:
            return ResultadoAccion.rechazada(motivo)
        self._mensajes = ListaEnlazada()
        if isinstance(accion, UsarPergamino):
            self._usar_pergamino()
            return ResultadoAccion.aceptada_con(self._mensajes)
        # DECISIÓN: el contenido se asegura ANTES de abrir el intervalo y de cualquier
        # mutación: si la red falla el estado queda intacto, y esperar la red no
        # mueve el reloj virtual (§2.5).
        if isinstance(accion, Mover):
            destino = self._sala_actual().salida(accion.direccion).destino
            self._asegurar_contenido(destino)      # puede esperar red; el reloj no se mueve

        if self.diario is not None:
            self.diario.abrir_intervalo(self)
        # DECISIÓN: el turno del jugador se EXTRAE y se vuelve a programar al final con
        # el costo de la acción: un rechazo no toca la agenda; un acierto queda todo
        # registrado en el Mutador.
        turno = self.mutador.agenda_extraer()      # el turno del jugador, siempre el primero
        self.mutador.asignar(self, "reloj", turno.tiempo)
        self.mutador.asignar(self.jugador, "evento_accion", None)
        # DECISIÓN (SUPUESTO): se sigue el Apéndice B (el rastro de la sala actual se
        # refresca en cada acción); §2.9 dice 'al completar un movimiento'. Confirmar.
        self.mutador.asignar(self._sala_actual(), "rastro", self.reloj)   # Apéndice B
        self._ejecutar_accion_jugador(accion)
        self.mutador.asignar(self.jugador, "acciones", self.jugador.acciones + 1)
        if self.fin is None:
            self.programar_accion(self.jugador, accion.costo_base)
        self._procesar_eventos()
        if self.diario is not None:
            self.diario.cerrar_intervalo()
        return ResultadoAccion.aceptada_con(self._mensajes)

    def _ejecutar_accion_jugador(self, accion) -> None:
        if isinstance(accion, Mover):
            self._mover_jugador(accion)
        elif isinstance(accion, AbrirPuerta):
            self._abrir_puerta(accion)
        elif isinstance(accion, Atacar):
            objetivo = self._sala_actual().buscar_enemigo(accion.objetivo)
            Combate.resolver_ataque(self, self.jugador, objetivo)
        elif isinstance(accion, Recoger):
            sala = self._sala_actual()
            objeto = sala.buscar_objeto(accion.id_objeto)
            self.mutador.suelo_quitar(sala, objeto)
            self.mutador.inventario_agregar(self.jugador, objeto)
            self.avisar(f"Recoges {objeto.nombre}.")
        elif isinstance(accion, Soltar):
            objeto = self.jugador.inventario.buscar(accion.id_objeto)
            self.mutador.inventario_quitar(self.jugador, objeto)
            self.mutador.suelo_agregar(self._sala_actual(), objeto)
            self.avisar(f"Sueltas {objeto.nombre}.")
        elif isinstance(accion, Usar):
            objeto = self.jugador.inventario.buscar(accion.id_objeto)
            self.avisar(objeto.usar(self))
            self.mutador.inventario_quitar(self.jugador, objeto)     # se consume
        elif isinstance(accion, Equipar):
            objeto = self.jugador.inventario.buscar(accion.id_objeto)
            self.mutador.inventario_equipar(self.jugador, objeto)
            self.avisar(f"Te equipas {objeto.nombre}.")
        elif isinstance(accion, Esperar):
            self.avisar("Esperas.")

    def _mover_jugador(self, accion) -> None:
        origen = self._sala_actual()
        destino = self.mundo.sala(origen.salida(accion.direccion).destino)
        self.mutador.asignar(self.jugador, "sala", destino.id)
        self.mutador.asignar(destino, "rastro", self.reloj)
        self.avisar(f"Entras a {destino.nombre}.")
        # DECISIÓN (SUPUESTO): primero las trampas y luego la activación de enemigos;
        # el enunciado solo dice que la trampa va justo después del movimiento.
        destino.disparar_trampas(self)               # justo después del movimiento
        if self.jugador.vivo:
            destino.activar_enemigos(self)           # por id de instancia ascendente
            # DECISIÓN (SUPUESTO): victoria = entrar a la sala de salida; llegar ahí
            # exige haber abierto su puerta con llave. No se exige un flag extra.
            if destino.id == self.mundo.sala_salida:
                self._terminar(ESTADO_VICTORIA)
        self.servicio.precargar(destino.id)          # no bloquea

    def _abrir_puerta(self, accion) -> None:
        salida = self._sala_actual().salida(accion.direccion)
        # DECISIÓN: el cierre automático es un EVENTO (§2.5) contado desde el instante
        # en que se abre; la llave no se consume.
        self.mutador.asignar(salida, "cerrada", False)
        if salida.cierre_automatico is not None:
            cierre = EventoCierrePuerta(self.reloj + salida.cierre_automatico, salida)
            self.mutador.agenda_programar(cierre)
            self.mutador.asignar(salida, "evento_cierre", cierre)
        self.avisar(f"Abres la puerta hacia el {accion.direccion}.")

    def _usar_pergamino(self) -> None:
        """No consume tiempo ni cuenta como acción. El pergamino se gasta DESPUÉS
        de retroceder y sin registrarse, así su cantidad queda fuera de la reversión."""
        pergamino = self.jugador.inventario.primer_pergamino()
        self.deshacer()
        # DECISIÓN: el pergamino se consume en pausa para que su cantidad quede fuera
        # de la reversión (§2.11).
        self.mutador.pausar()
        if self.jugador.inventario.indice_de(pergamino) >= 0:
            self.mutador.inventario_quitar(self.jugador, pergamino)
        self.mutador.reanudar()
        self.avisar("El pergamino retrocede el tiempo.")

    # ------------------------------------------------------------------
    # Bucle de eventos
    # ------------------------------------------------------------------

    def _procesar_eventos(self) -> None:
        """Ejecuta eventos en orden de (tiempo, secuencia) hasta que el turno
        del jugador sea el siguiente (o la partida termine). Nunca usa la hora
        real ni el orden de llegada de las respuestas HTTP (§2.3)."""
        # DECISIÓN: el bucle se detiene cuando el turno del jugador es el siguiente
        # (comparación por IDENTIDAD, no por tiempo): así los eventos con igual tiempo
        # y secuencia menor se ejecutan antes de pedirle su decisión.
        while self.fin is None:
            siguiente = self.agenda.ver_siguiente()
            if siguiente is None or siguiente is self.jugador.evento_accion:
                return
            evento = self.mutador.agenda_extraer()
            if evento.tiempo > self.reloj:
                self.mutador.asignar(self, "reloj", evento.tiempo)
            evento.ejecutar(self)

    def programar_accion(self, actor, costo_base: int) -> None:
        """Programa el siguiente turno: tiempo + max(1, costo * 100 // velocidad)."""
        turno = EventoAccionActor(
            self.reloj + calcular_intervalo(costo_base, actor.velocidad), actor)
        self.mutador.agenda_programar(turno)
        self.mutador.asignar(actor, "evento_accion", turno)

    def ejecutar_accion_enemigo(self, enemigo, accion) -> None:
        if isinstance(accion, Atacar):
            Combate.resolver_ataque(self, enemigo, self.jugador)
        elif isinstance(accion, Mover):
            origen = self.mundo.sala(enemigo.sala)
            salida = origen.salida(accion.direccion)
            # DECISIÓN: los enemigos no abren puertas: si la salida está cerrada no se
            # mueven, pero el turno igual se consume (se reprograma en el evento).
            if salida is not None and salida.transitable():    # no abren puertas
                self.mutador.enemigo_mover(enemigo, origen, self.mundo.sala(salida.destino))

    # ------------------------------------------------------------------
    # Servicios que usan objetos, efectos y eventos
    # ------------------------------------------------------------------

    def danar(self, actor, cantidad: int) -> None:
        if not actor.vivo or cantidad <= 0:
            return
        nueva = actor.vida_tras_dano(cantidad)
        self.mutador.asignar(actor, "vida", nueva)
        if nueva <= 0:
            self.matar(actor)

    def curar(self, actor, cantidad: int) -> None:
        """Cura sin pasar de vida_max."""
        if actor.vivo and cantidad > 0:
            self.mutador.asignar(actor, "vida", actor.vida_tras_curar(cantidad))

    def matar(self, actor) -> None:
        """El actor deja de ejecutar eventos y suelta sus objetos (§2.6)."""
        self.mutador.asignar(actor, "vivo", False)
        actor.morir(self)
        self.avisar(f"{actor.nombre} muere.")
        if actor is self.jugador:
            self._terminar(ESTADO_DERROTA)
            return
        sala = self.mundo.sala(actor.sala)
        self.mutador.enemigo_quitar(sala, actor)
        self.mutador.asignar(self.jugador, "enemigos_derrotados",
                             self.jugador.enemigos_derrotados + 1)
        # DECISIÓN: las fichas de lo que suelta ya se resolvieron al cargar la sala,
        # así morir nunca dispara una solicitud de red.
        for ficha in actor.suelta:
            self.mutador.suelo_agregar(sala, self._fabrica.crear_objeto(ficha))

    def envenenar(self, actor) -> None:
        """Aplica veneno (vuelve a empezar si ya estaba envenenado). Lo invocan
        las fuentes de veneno (por confirmar con el enunciado: ver notas)."""
        self.curar_veneno(actor)
        EfectoVeneno(actor).aplicar(self)

    def curar_veneno(self, actor) -> None:
        efecto = actor.buscar_efecto(EfectoVeneno.TIPO)
        if efecto is not None:
            efecto.cancelar(self)

    def aplicar_velocidad(self, actor, modificador: int, duracion: int) -> None:
        anterior = actor.buscar_efecto(EfectoVelocidad.TIPO)
        if anterior is not None:
            anterior.cancelar(self)
        EfectoVelocidad(actor, modificador, duracion).aplicar(self)

    def encender_antorcha(self, jugador, duracion: int) -> None:
        anterior = jugador.buscar_efecto(EfectoAntorcha.TIPO)
        if anterior is not None:
            anterior.cancelar(self)
        EfectoAntorcha(jugador, duracion).aplicar(self)

    def cambiar_velocidad(self, actor, nueva: int) -> None:
        """Cambia la velocidad y reescala el tiempo restante de su próximo turno:
        max(1, (t_sig - t) * v_ant // v_nueva), con secuencia nueva (§2.3)."""
        # DECISIÓN: solo se reescala el turno si está DENTRO de la agenda: si es el que
        # se ejecuta ahora, su próximo turno ya se calculará con la velocidad nueva.
        anterior = actor.velocidad
        self.mutador.asignar(actor, "velocidad", nueva)
        turno = actor.evento_accion
        if turno is not None and turno.en_agenda and not turno.cancelado:
            restante = reescalar_restante(turno.tiempo - self.reloj, anterior, nueva)
            nuevo = self.mutador.agenda_reprogramar(turno, self.reloj + restante)
            self.mutador.asignar(actor, "evento_accion", nuevo)

    # ------------------------------------------------------------------
    # Mensajes y apoyo
    # ------------------------------------------------------------------

    def avisar(self, texto: str) -> None:
        """Mensaje para el jugador: va al resultado de la acción y a la bitácora
        (buffer circular de 20). No se revierte al retroceder: es presentación."""
        self._mensajes.agregar_al_final(texto)
        self.bitacora.encolar(texto)

    def _terminar(self, estado: str) -> None:
        self.mutador.asignar(self, "fin", estado)
        self.avisar("¡Has ganado!" if estado == ESTADO_VICTORIA else "Has caído...")

    def _sala_actual(self):
        return self.mundo.sala(self.jugador.sala)

    def _asegurar_contenido(self, id_sala: int) -> None:
        """Deja el contenido de la sala en memoria ANTES de confirmar el
        movimiento. Si falta, el servicio lo pide y espera: tiempo real, nunca
        reloj virtual. Queda fuera de la reversión (como la caché)."""
        if self.mundo.tiene_contenido(id_sala):
            return
        contenido = self.servicio.asegurar_contenido(id_sala)
        enemigos, objetos, trampas = self._fabrica.construir(contenido, id_sala)
        self.mundo.incorporar_contenido(id_sala, enemigos, objetos, trampas)