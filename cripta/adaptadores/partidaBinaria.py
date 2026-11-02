"""Guardado y carga de una partida en un archivo binario de formato propio
(§4.10).

Formato (todo escrito con EscritorBinario/LectorBinario, little-endian):

  ENCABEZADO FIJO (tamaño constante, siempre en el mismo lugar):
    magic:            4 bytes crudos "CRPB"
    version_formato:  uentero32  (FORMATO_VERSION de este módulo)
    offset_indice:    entero     (dónde empieza el índice de salas; se
                                  rellena al final, cuando ya se sabe)

  ENCABEZADO LÓGICO (datos de la cripta + estado global de la partida):
    id_cripta, version_cripta, version_catalogo (texto, el 2do opcional)
    semilla, reloj                  (entero)
    fin                             (texto opcional: None/"victoria"/"derrota")
    secuencia_agenda                (entero: Agenda._secuencia)
    siguiente_id_objeto             (entero: FabricaEntidades._siguiente_id_objeto)
    estado de random.Random: version(entero), 625 enteros, gauss_next(flotante opcional)

  JUGADOR (un solo bloque, fuera del índice de salas)

  SALAS: cantidad(entero), luego cada Sala una tras otra (se recuerda el
  offset y la longitud de cada una para el índice). Cada salida guarda
  destino, cerrada, llave, cierre_automatico y, desde la versión 2, su
  costo EFECTIVO (entero >= 1, 001-terreno-cazador): al cargar,
  Mundo.enlazar() vuelve a resolver origen, destino y entrantes, y la Partida
  recrea su mapa de distancias (specs/001-terreno-cazador/contracts/
  partida-binaria.md).

  EVENTOS PENDIENTES DE LA AGENDA: cantidad(entero), luego cada evento

  ÍNDICE DE SALAS (al final; su posición es 'offset_indice'):
    cantidad(entero), luego (id_sala:entero, offset:entero, longitud:entero)
    por cada sala — permite cargar_sala() sin leer el archivo completo
    (§4.10: "recuperarse una sala específica sin leer el archivo completo").

REFERENCIAS CRUZADAS (evento.duenio, Efecto.evento, Salida.evento_cierre,
Trampa.evento_rearme, Actor.evento_accion): en vez de inventar ids propios,
se identifica cada actor/trampa/salida por una CLAVE NATURAL (su sala + su
id de instancia, o su sala + dirección), y cada Efecto por (clave del actor
dueño, su TIPO) — como mucho hay un efecto de cada TIPO por actor (lo
garantiza el propio modelo: siempre cancela el anterior antes de aplicar
otro igual). Así, reconstruir los eventos pendientes es una ÚLTIMA pasada,
después de tener todas las salas y el jugador ya armados, que simplemente
busca cada clave y conecta los punteros (nunca hace falta serializar un id
sintético ni un puntero crudo).
"""
from __future__ import annotations

import random
import types

from ..modelo.actores.comportamientos import crear_comportamiento
from ..modelo.actores.enemigo import Enemigo
from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.actores.jugador import Jugador
from ..modelo.mundo.mundo import Mundo
from ..modelo.mundo.registroPuertas import RegistroPuertas
from ..modelo.mundo.salida import Salida
from ..modelo.mundo.sala import Sala
from ..modelo.mundo.trampa import Trampa
from ..modelo.nucleo.partida import Partida
from ..modelo.nucleo.mutador import Mutador
from ..modelo.nucleo.validadorAcciones import ValidadorAcciones
from ..modelo.nucleo.constantes import TAMANO_BITACORA
from ..modelo.estructuras.colaAcotada import ColaAcotada
from ..modelo.nucleo.fabricaEntidades import FabricaEntidades
from ..modelo.objetos.objeto import crear_objeto
from ..modelo.puertos.dto import DIRECCIONES
from ..modelo.puertos.errores import VersionIncompatible
from ..modelo.reloj.agenda import Agenda
from ..modelo.reloj.efecto import (
    EfectoAntorcha, EfectoRegeneracion, EfectoVelocidad, EfectoVeneno)
from ..modelo.reloj.eventos import (
    EventoAccionActor, EventoApagarAntorcha, EventoCambioVelocidad,
    EventoCierrePuerta, EventoRearmeTrampa, EventoRegeneracion, EventoVeneno)
from .codificadorBinario import EscritorBinario, LectorBinario

MAGIC = b"CRPB"
# 2 desde 001-terreno-cazador (costo por salida). Provisional según el orden
# de merge a main: si otra feature toma el 2 antes, se ajusta al integrarse
# (contracts/partida-binaria.md, T048). Un archivo de otra versión se reporta
# incompatible y no se migra (principio V).
FORMATO_VERSION = 2

# Nombres de tipo de evento, para no depender del nombre de la clase de Python
# (si se refactoriza un nombre de clase, el formato de archivo no se rompe).
_TIPOS_EVENTO = ("ACCION", "VENENO", "VELOCIDAD", "ANTORCHA", "REGENERACION",
                 "REARME_TRAMPA", "CIERRE_PUERTA")


def _clave_actor(actor, jugador) -> tuple:
    """Clave natural de un actor: identifica al jugador o a un enemigo por su
    sala + id de instancia, sin inventar ningún id propio."""
    if actor is jugador:
        return ("jugador",)
    return ("enemigo", actor.sala, actor.id_instancia)


class PartidaBinaria:
    """Adaptador de guardado/carga: lee y escribe el estado completo de una
    Partida en un archivo binario propio. No conoce reglas del juego más
    allá de cómo están organizados los atributos de cada clase del modelo."""

    # ------------------------------------------------------------------
    # Guardar
    # ------------------------------------------------------------------

    @staticmethod
    def guardar(partida: Partida, ruta) -> None:
        escritor = EscritorBinario()
        escritor.crudo(MAGIC)
        escritor.uentero32(FORMATO_VERSION)
        posicion_offset_indice = len(escritor)
        escritor.entero(0)                     # placeholder: se rellena al final

        PartidaBinaria._escribir_encabezado_logico(escritor, partida)
        PartidaBinaria._escribir_jugador(escritor, partida.jugador)

        # DECISIÓN: se extraen TODOS los eventos pendientes de la agenda para
        # poder escribirlos, y se devuelven exactamente igual (mismo tiempo y
        # secuencia, vía reinsertar()) antes de seguir: guardar no debe
        # alterar una partida que sigue en curso (p. ej. un autoguardado).
        eventos_extraidos = ListaEnlazada()
        while True:
            evento = partida.agenda.extraer_siguiente()
            if evento is None:
                break
            eventos_extraidos.agregar_al_final(evento)

        salas_con_offset = ListaEnlazada()
        escritor.entero(len(partida.mundo))
        for sala in partida.mundo:
            inicio = len(escritor)
            PartidaBinaria._escribir_sala(escritor, sala)
            salas_con_offset.agregar_al_final((sala.id, inicio, len(escritor) - inicio))

        PartidaBinaria._escribir_eventos(escritor, eventos_extraidos, partida)

        # Se restaura la agenda exactamente como estaba (mismo orden, mismas
        # secuencias): reinsertar() no toca el contador de secuencia.
        for evento in eventos_extraidos:
            partida.agenda.reinsertar(evento)

        offset_indice = len(escritor)
        escritor.entero(len(salas_con_offset))
        for id_sala, inicio, longitud in salas_con_offset:
            escritor.entero(id_sala)
            escritor.entero(inicio)
            escritor.entero(longitud)

        escritor.sobrescribir_entero(posicion_offset_indice, offset_indice)

        with open(ruta, "wb") as archivo:
            archivo.write(escritor.bytes())

    @staticmethod
    def _escribir_encabezado_logico(escritor, partida) -> None:
        escritor.texto(partida.datos.id)
        escritor.texto(partida.datos.version)
        escritor.texto(getattr(partida, "version_catalogo", None))
        escritor.entero(partida.semilla)
        escritor.entero(partida.reloj)
        escritor.texto(partida.fin)
        escritor.entero(partida.agenda.secuencia)
        escritor.entero(partida._fabrica._siguiente_id_objeto)
        PartidaBinaria._escribir_estado_azar(escritor, partida.azar)
        # Datos fijos de la cripta que necesita Mundo, para no depender de
        # volver a pedirle 'datos_cripta()' al servicio al cargar.
        escritor.entero(partida.mundo.sala_inicial)
        escritor.entero(partida.mundo.sala_salida)
        escritor.texto(partida.mundo.llave_salida)
        escritor.entero(partida.mundo.inventario_max)
        estadisticas = partida.mundo.estadisticas_jugador
        escritor.entero(estadisticas.vida_max)
        escritor.entero(estadisticas.ataque)
        escritor.entero(estadisticas.defensa)
        escritor.entero(estadisticas.velocidad)

    @staticmethod
    def _escribir_estado_azar(escritor, azar: random.Random) -> None:
        version, estado_interno, gauss_next = azar.getstate()
        escritor.entero(version)
        escritor.entero(len(estado_interno))
        for numero in estado_interno:
            escritor.entero(numero)
        escritor.flotante_opcional(gauss_next)

    @staticmethod
    def _escribir_ficha_id(escritor, ficha) -> None:
        escritor.texto(ficha.id)

    @staticmethod
    def _escribir_efectos(escritor, efectos) -> None:
        """Escribe los Efecto activos de un actor (ListaDoble de Efecto). El
        puntero a su Evento pendiente NO se guarda aquí: se reconstruye en la
        pasada de eventos, buscando (actor, TIPO)."""
        escritor.entero(len(efectos))
        for efecto in efectos:
            escritor.texto(efecto.TIPO)
            if efecto.TIPO == EfectoVelocidad.TIPO:
                escritor.entero(efecto.modificador)
                escritor.entero(efecto.duracion)
            elif efecto.TIPO == EfectoAntorcha.TIPO:
                escritor.entero(efecto.duracion)
            elif efecto.TIPO == EfectoRegeneracion.TIPO:
                escritor.entero(efecto.cantidad)
            # EfectoVeneno no tiene campos propios.

    @staticmethod
    def _escribir_jugador(escritor, jugador: Jugador) -> None:
        escritor.entero(jugador.vida)
        escritor.entero(jugador.vida_max)
        escritor.entero(jugador.ataque)
        escritor.entero(jugador.defensa)
        escritor.entero(jugador.velocidad)
        escritor.entero(jugador.velocidad_base)
        escritor.booleano(jugador.vivo)
        escritor.entero(jugador.sala)
        escritor.booleano(jugador.antorcha_encendida)
        escritor.entero(jugador.acciones)
        escritor.entero(jugador.enemigos_derrotados)

        escritor.entero(jugador.inventario.capacidad)
        objetos = ListaEnlazada()
        for objeto in jugador.inventario:
            objetos.agregar_al_final(objeto)
        escritor.entero(len(objetos))
        for objeto in objetos:
            escritor.entero(objeto.id_instancia)
            PartidaBinaria._escribir_ficha_id(escritor, objeto.ficha)
        indice_actual = jugador.inventario.indice_de(jugador.inventario.actual()) \
            if jugador.inventario.actual() is not None else -1
        escritor.entero(indice_actual)

        arma = jugador.equipo.arma
        armadura = jugador.equipo.armadura
        escritor.entero(arma.id_instancia if arma is not None else -1)
        escritor.entero(armadura.id_instancia if armadura is not None else -1)

        PartidaBinaria._escribir_efectos(escritor, jugador.efectos)

    @staticmethod
    def _escribir_sala(escritor, sala: Sala) -> None:
        escritor.entero(sala.id)
        escritor.texto(sala.nombre)
        for salida in sala.salidas:
            escritor.booleano(salida is not None)
            if salida is not None:
                escritor.entero(salida.destino)
                escritor.booleano(salida.cerrada)
                escritor.texto(salida.llave)
                escritor.entero_opcional(salida.cierre_automatico)
                escritor.entero(salida.costo)          # versión 2: costo efectivo
        escritor.entero_opcional(sala.rastro)
        escritor.booleano(sala.contenido_cargado)

        escritor.entero(len(sala.dormidos))
        for enemigo in sala.dormidos:
            PartidaBinaria._escribir_enemigo(escritor, enemigo)
        escritor.entero(len(sala.activos))
        for enemigo in sala.activos:
            PartidaBinaria._escribir_enemigo(escritor, enemigo)

        escritor.entero(len(sala.suelo))
        for objeto in sala.suelo:
            escritor.entero(objeto.id_instancia)
            PartidaBinaria._escribir_ficha_id(escritor, objeto.ficha)

        escritor.entero(len(sala.trampas))
        for trampa in sala.trampas:
            escritor.texto(trampa.id_instancia)
            PartidaBinaria._escribir_ficha_id(escritor, trampa.ficha)
            escritor.booleano(trampa.armada)

    @staticmethod
    def _escribir_enemigo(escritor, enemigo: Enemigo) -> None:
        escritor.texto(enemigo.id_instancia)
        PartidaBinaria._escribir_ficha_id(escritor, enemigo.ficha)
        escritor.entero(enemigo.vida)
        escritor.entero(enemigo.vida_max)
        escritor.entero(enemigo.ataque)
        escritor.entero(enemigo.defensa)
        escritor.entero(enemigo.velocidad)
        escritor.entero(enemigo.velocidad_base)
        escritor.booleano(enemigo.activo)
        escritor.entero(enemigo.regeneracion)
        escritor.entero(len(enemigo.suelta))
        for ficha in enemigo.suelta:
            escritor.texto(ficha.id)
        PartidaBinaria._escribir_efectos(escritor, enemigo.efectos)

    @staticmethod
    def _escribir_eventos(escritor, eventos, partida) -> None:
        escritor.entero(len(eventos))
        for evento in eventos:
            PartidaBinaria._escribir_evento(escritor, evento, partida)

    @staticmethod
    def _escribir_evento(escritor, evento, partida) -> None:
        if isinstance(evento, EventoAccionActor):
            tipo, efecto, extra = "ACCION", None, None
        elif isinstance(evento, EventoVeneno):
            tipo, efecto, extra = "VENENO", evento.efecto, evento.numero
        elif isinstance(evento, EventoCambioVelocidad):
            tipo, efecto, extra = "VELOCIDAD", evento.efecto, None
        elif isinstance(evento, EventoApagarAntorcha):
            tipo, efecto, extra = "ANTORCHA", evento.efecto, None
        elif isinstance(evento, EventoRegeneracion):
            tipo, efecto, extra = "REGENERACION", evento.efecto, evento.cantidad
        elif isinstance(evento, EventoRearmeTrampa):
            tipo, efecto, extra = "REARME_TRAMPA", None, None
        elif isinstance(evento, EventoCierrePuerta):
            tipo, efecto, extra = "CIERRE_PUERTA", None, None
        else:
            raise ValueError(f"Tipo de evento desconocido: {type(evento).__name__}")

        escritor.texto(tipo)
        escritor.entero(evento.tiempo)
        escritor.entero(evento.secuencia)
        PartidaBinaria._escribir_duenio(escritor, evento, tipo, partida)
        escritor.texto(efecto.TIPO if efecto is not None else None)
        escritor.entero_opcional(extra)

    @staticmethod
    def _escribir_duenio(escritor, evento, tipo, partida) -> None:
        duenio = evento.duenio
        if tipo in ("ACCION", "VENENO", "VELOCIDAD", "ANTORCHA", "REGENERACION"):
            clave = _clave_actor(duenio, partida.jugador)
            escritor.texto(clave[0])
            if clave[0] == "enemigo":
                escritor.entero(clave[1])
                escritor.texto(clave[2])
        elif tipo == "REARME_TRAMPA":
            escritor.entero(duenio.sala)
            escritor.texto(duenio.id_instancia)
        elif tipo == "CIERRE_PUERTA":
            sala_id, indice = PartidaBinaria._ubicar_salida(partida.mundo, duenio)
            escritor.entero(sala_id)
            escritor.entero32(indice)

    @staticmethod
    def _ubicar_salida(mundo, salida):
        """Una Salida no sabe en qué sala ni en qué dirección está (solo
        guarda su propio 'destino'): se la ubica recorriendo las salas (a lo
        más 4 comparaciones por sala; solo ocurre para una puerta con cierre
        automático pendiente, un caso raro, nunca para cada sala guardada)."""
        for sala in mundo:
            for indice, candidata in enumerate(sala.salidas):
                if candidata is salida:
                    return sala.id, indice
        raise ValueError("La Salida de un EventoCierrePuerta no está en ninguna sala del mundo")

    # ------------------------------------------------------------------
    # Cargar (partida completa)
    # ------------------------------------------------------------------

    @staticmethod
    def cargar(ruta, servicio) -> Partida:
        with open(ruta, "rb") as archivo:
            datos = archivo.read()
        lector = LectorBinario(datos)
        PartidaBinaria._leer_encabezado_fijo(lector)

        partida = Partida.__new__(Partida)
        partida.servicio = servicio
        partida.mutador = Mutador()
        partida.validador = ValidadorAcciones()
        partida.bitacora = ColaAcotada(TAMANO_BITACORA)
        partida.diario = None
        partida._mensajes = ListaEnlazada()

        id_cripta, version_cripta, version_catalogo, siguiente_id_objeto = \
            PartidaBinaria._leer_encabezado_logico(lector, partida, servicio)
        partida.datos = types.SimpleNamespace(id=id_cripta, version=version_cripta)
        partida.version_catalogo = version_catalogo
        partida._fabrica = FabricaEntidades(servicio)
        partida._fabrica._siguiente_id_objeto = siguiente_id_objeto

        jugador = PartidaBinaria._leer_jugador(lector, partida.mundo, servicio)
        partida.jugador = jugador
        partida.mutador.agenda = partida.agenda

        cantidad_salas = lector.entero()
        for _ in range(cantidad_salas):
            sala = PartidaBinaria._leer_sala(lector, servicio)
            partida.mundo._salas.agregar_al_final(sala)

        eventos = PartidaBinaria._leer_eventos(lector, partida)
        for evento in eventos:
            partida.agenda.reinsertar(evento)

        # 001-terreno-cazador: referencias directas, entrantes y registro de
        # puertas (los costos guardados son los efectivos, así que las caras
        # coinciden), y el mapa de distancias y los cazadores de la Partida.
        partida.mundo.enlazar()
        partida.reconstruir_tras_cargar()
        return partida

    @staticmethod
    def _leer_encabezado_fijo(lector: LectorBinario) -> int:
        magic = lector.crudo(4)
        if magic != MAGIC:
            raise ValueError("El archivo no es una partida guardada de Cripta")
        version_formato = lector.uentero32()
        if version_formato != FORMATO_VERSION:
            raise VersionIncompatible(
                "formato de archivo de partida", FORMATO_VERSION, version_formato)
        return lector.entero()     # offset_indice: no hace falta para la carga completa

    @staticmethod
    def _leer_encabezado_logico(lector, partida, servicio):
        id_cripta = lector.texto()
        version_cripta = lector.texto()
        version_catalogo = lector.texto()
        partida.semilla = lector.entero()
        partida.reloj = lector.entero()
        partida.fin = lector.texto()
        secuencia_agenda = lector.entero()
        siguiente_id_objeto = lector.entero()
        partida.azar = PartidaBinaria._leer_estado_azar(lector)

        sala_inicial = lector.entero()
        sala_salida = lector.entero()
        llave_salida = lector.texto()
        inventario_max = lector.entero()
        vida_max = lector.entero()
        ataque = lector.entero()
        defensa = lector.entero()
        velocidad = lector.entero()

        mundo = Mundo.__new__(Mundo)
        mundo.sala_inicial = sala_inicial
        mundo.sala_salida = sala_salida
        mundo.llave_salida = llave_salida
        mundo.inventario_max = inventario_max
        mundo.estadisticas_jugador = types.SimpleNamespace(
            vida_max=vida_max, ataque=ataque, defensa=defensa, velocidad=velocidad)
        mundo._salas = ListaEnlazada()
        mundo.registro_puertas = RegistroPuertas()
        partida.mundo = mundo

        partida.agenda = Agenda()
        partida.agenda.secuencia = secuencia_agenda

        return id_cripta, version_cripta, version_catalogo, siguiente_id_objeto

    @staticmethod
    def _leer_estado_azar(lector) -> random.Random:
        version = lector.entero()
        cantidad = lector.entero()
        estado_interno = tuple(lector.entero() for _ in range(cantidad))
        gauss_next = lector.flotante_opcional()
        azar = random.Random()
        azar.setstate((version, estado_interno, gauss_next))
        return azar

    @staticmethod
    def _resolver_ficha(servicio, id_ficha):
        ids = ListaEnlazada()
        ids.agregar_al_final(id_ficha)
        return servicio.resolver_fichas(ids).ver_primero()

    @staticmethod
    def _leer_efectos(lector, actor, servicio) -> None:
        cantidad = lector.entero()
        for _ in range(cantidad):
            tipo = lector.texto()
            if tipo == EfectoVelocidad.TIPO:
                modificador = lector.entero()
                duracion = lector.entero()
                efecto = EfectoVelocidad(actor, modificador, duracion)
            elif tipo == EfectoAntorcha.TIPO:
                duracion = lector.entero()
                efecto = EfectoAntorcha(actor, duracion)
            elif tipo == EfectoRegeneracion.TIPO:
                cantidad_cura = lector.entero()
                efecto = EfectoRegeneracion(actor, cantidad_cura)
            elif tipo == EfectoVeneno.TIPO:
                efecto = EfectoVeneno(actor)
            else:
                raise ValueError(f"Tipo de efecto desconocido en el archivo: {tipo!r}")
            # DECISIÓN: se agrega directo a la lista (no por partida.mutador.
            # efecto_agregar, que también llamaría a al_aplicar y programaría
            # un evento NUEVO): el evento de este efecto ya existe, guardado
            # tal cual, y se conecta después en la pasada de eventos.
            actor.efectos.agregar_al_final(efecto)

    @staticmethod
    def _leer_jugador(lector, mundo, servicio) -> Jugador:
        vida = lector.entero()
        vida_max = lector.entero()
        ataque = lector.entero()
        defensa = lector.entero()
        velocidad = lector.entero()
        velocidad_base = lector.entero()
        vivo = lector.booleano()
        sala = lector.entero()
        antorcha_encendida = lector.booleano()
        acciones = lector.entero()
        enemigos_derrotados = lector.entero()

        capacidad = lector.entero()
        cantidad_objetos = lector.entero()
        objetos_guardados = ListaEnlazada()
        for _ in range(cantidad_objetos):
            id_instancia = lector.entero()
            id_ficha = lector.texto()
            ficha = PartidaBinaria._resolver_ficha(servicio, id_ficha)
            objetos_guardados.agregar_al_final(crear_objeto(id_instancia, ficha))
        indice_actual = lector.entero()
        id_arma = lector.entero()
        id_armadura = lector.entero()

        jugador = Jugador(mundo.estadisticas_jugador, sala, capacidad)
        jugador.vida = vida
        jugador.vida_max = vida_max
        jugador.ataque = ataque
        jugador.defensa = defensa
        jugador.velocidad = velocidad
        jugador.velocidad_base = velocidad_base
        jugador.vivo = vivo
        jugador.antorcha_encendida = antorcha_encendida
        jugador.acciones = acciones
        jugador.enemigos_derrotados = enemigos_derrotados

        for objeto in objetos_guardados:
            jugador.inventario.recoger(objeto)
            if objeto.id_instancia == id_arma or objeto.id_instancia == id_armadura:
                jugador.equipo.equipar(objeto)
        if indice_actual >= 0:
            # Inventario no expone 'obtener' por posición: se recorre hasta
            # el índice guardado (a lo más 'capacidad' objetos, pequeño).
            objeto_actual = None
            contador = 0
            for objeto in jugador.inventario:
                if contador == indice_actual:
                    objeto_actual = objeto
                    break
                contador += 1
            if objeto_actual is not None:
                jugador.inventario.enfocar(objeto_actual)

        PartidaBinaria._leer_efectos(lector, jugador, servicio)
        return jugador

    @staticmethod
    def _leer_sala(lector, servicio) -> Sala:
        id_sala = lector.entero()
        nombre = lector.texto()
        # DECISIÓN: 4 variables (no una lista de Python) para armar la tupla
        # fija de salidas, igual que Mundo._construir_salidas.
        norte = sur = este = oeste = None
        for indice in range(4):
            hay_salida = lector.booleano()
            if not hay_salida:
                continue
            destino = lector.entero()
            cerrada = lector.booleano()
            llave = lector.texto()
            cierre_automatico = lector.entero_opcional()
            costo = lector.entero()                    # versión 2: costo efectivo
            salida = Salida(DIRECCIONES[indice], destino, cerrada, llave, cierre_automatico,
                            costo)
            if indice == 0:
                norte = salida
            elif indice == 1:
                sur = salida
            elif indice == 2:
                este = salida
            else:
                oeste = salida

        sala = Sala(id_sala, nombre, (norte, sur, este, oeste))
        sala.rastro = lector.entero_opcional()
        sala.contenido_cargado = lector.booleano()

        cantidad_dormidos = lector.entero()
        for _ in range(cantidad_dormidos):
            enemigo = PartidaBinaria._leer_enemigo(lector, id_sala, servicio, activo=False)
            sala.dormidos.agregar_al_final(enemigo)
        cantidad_activos = lector.entero()
        for _ in range(cantidad_activos):
            enemigo = PartidaBinaria._leer_enemigo(lector, id_sala, servicio, activo=True)
            sala.activos.agregar_al_final(enemigo)

        cantidad_objetos = lector.entero()
        for _ in range(cantidad_objetos):
            id_instancia = lector.entero()
            id_ficha = lector.texto()
            ficha = PartidaBinaria._resolver_ficha(servicio, id_ficha)
            sala.suelo.agregar_al_final(crear_objeto(id_instancia, ficha))

        cantidad_trampas = lector.entero()
        for _ in range(cantidad_trampas):
            id_instancia = lector.texto()
            id_ficha = lector.texto()
            armada = lector.booleano()
            ficha = PartidaBinaria._resolver_ficha(servicio, id_ficha)
            trampa = Trampa(id_instancia, ficha, id_sala)
            trampa.armada = armada
            sala.trampas.agregar_al_final(trampa)

        return sala

    @staticmethod
    def _leer_enemigo(lector, id_sala, servicio, activo: bool) -> Enemigo:
        id_instancia = lector.texto()
        id_ficha = lector.texto()
        vida = lector.entero()
        vida_max = lector.entero()
        ataque = lector.entero()
        defensa = lector.entero()
        velocidad = lector.entero()
        velocidad_base = lector.entero()
        activo_guardado = lector.booleano()
        regeneracion = lector.entero()
        cantidad_suelta = lector.entero()
        ids_suelta = ListaEnlazada()
        for _ in range(cantidad_suelta):
            ids_suelta.agregar_al_final(lector.texto())

        ficha = PartidaBinaria._resolver_ficha(servicio, id_ficha)
        enemigo = Enemigo(id_instancia, ficha, vida, id_sala,
                          crear_comportamiento(ficha.comportamiento, ficha.rango))
        enemigo.vida_max = vida_max
        enemigo.ataque = ataque
        enemigo.defensa = defensa
        enemigo.velocidad = velocidad
        enemigo.velocidad_base = velocidad_base
        enemigo.activo = activo_guardado
        enemigo.regeneracion = regeneracion
        for id_suelta in ids_suelta:
            enemigo.suelta.agregar_al_final(PartidaBinaria._resolver_ficha(servicio, id_suelta))

        PartidaBinaria._leer_efectos(lector, enemigo, servicio)
        return enemigo

    @staticmethod
    def _leer_eventos(lector, partida) -> ListaEnlazada:
        jugador = partida.jugador
        cantidad = lector.entero()
        eventos = ListaEnlazada()
        for _ in range(cantidad):
            tipo = lector.texto()
            tiempo = lector.entero()
            secuencia = lector.entero()
            duenio = PartidaBinaria._leer_duenio(lector, tipo, partida)
            tipo_efecto = lector.texto()
            extra = lector.entero_opcional()
            efecto = duenio.buscar_efecto(tipo_efecto) \
                if tipo_efecto is not None and hasattr(duenio, "buscar_efecto") else None

            if tipo == "ACCION":
                evento = EventoAccionActor(tiempo, duenio)
            elif tipo == "VENENO":
                evento = EventoVeneno(tiempo, duenio, efecto, extra)
            elif tipo == "VELOCIDAD":
                evento = EventoCambioVelocidad(tiempo, duenio, efecto)
            elif tipo == "ANTORCHA":
                evento = EventoApagarAntorcha(tiempo, duenio, efecto)
            elif tipo == "REGENERACION":
                evento = EventoRegeneracion(tiempo, duenio, efecto, extra)
            elif tipo == "REARME_TRAMPA":
                evento = EventoRearmeTrampa(tiempo, duenio)
            elif tipo == "CIERRE_PUERTA":
                evento = EventoCierrePuerta(tiempo, duenio)
            else:
                raise ValueError(f"Tipo de evento desconocido en el archivo: {tipo!r}")

            evento.secuencia = secuencia
            evento.cancelado = False
            evento.en_agenda = False

            if tipo == "ACCION":
                duenio.evento_accion = evento
            elif tipo == "REARME_TRAMPA":
                duenio.evento_rearme = evento
            elif tipo == "CIERRE_PUERTA":
                duenio.evento_cierre = evento
            if efecto is not None:
                efecto.evento = evento

            eventos.agregar_al_final(evento)
        return eventos

    @staticmethod
    def _leer_duenio(lector, tipo, partida):
        jugador = partida.jugador
        if tipo in ("ACCION", "VENENO", "VELOCIDAD", "ANTORCHA", "REGENERACION"):
            clase = lector.texto()
            if clase == "jugador":
                return jugador
            sala_id = lector.entero()
            id_instancia = lector.texto()
            return PartidaBinaria._buscar_enemigo(partida.mundo, sala_id, id_instancia)
        if tipo == "REARME_TRAMPA":
            sala_id = lector.entero()
            id_instancia = lector.texto()
            return PartidaBinaria._buscar_trampa(partida.mundo, sala_id, id_instancia)
        if tipo == "CIERRE_PUERTA":
            sala_id = lector.entero()
            indice = lector.entero32()
            return partida.mundo.sala(sala_id).salidas[indice]
        raise ValueError(f"Tipo de evento desconocido al leer su dueño: {tipo!r}")

    @staticmethod
    def _buscar_enemigo(mundo, sala_id, id_instancia):
        sala = mundo.sala(sala_id)
        enemigo = sala.buscar_enemigo(id_instancia)
        if enemigo is not None:
            return enemigo
        for enemigo in sala.dormidos:
            if enemigo.id_instancia == id_instancia:
                return enemigo
        return None

    @staticmethod
    def _buscar_trampa(mundo, sala_id, id_instancia):
        for trampa in mundo.sala(sala_id).trampas:
            if trampa.id_instancia == id_instancia:
                return trampa
        return None

    # ------------------------------------------------------------------
    # Cargar una sola sala (§4.10: sin leer el archivo completo)
    # ------------------------------------------------------------------

    @staticmethod
    def cargar_sala(ruta, id_sala: int, servicio) -> Sala:
        """Lee únicamente los bytes de 'id_sala': salta directo al índice
        (al final del archivo) para encontrar su offset, y de ahí a sus
        propios bytes, sin tocar el resto del archivo."""
        with open(ruta, "rb") as archivo:
            archivo.seek(0)
            encabezado = archivo.read(4 + 4 + 8)
            lector_encabezado = LectorBinario(encabezado)
            magic = lector_encabezado.crudo(4)
            if magic != MAGIC:
                raise ValueError("El archivo no es una partida guardada de Cripta")
            version_formato = lector_encabezado.uentero32()
            if version_formato != FORMATO_VERSION:
                raise VersionIncompatible(
                    "formato de archivo de partida", FORMATO_VERSION, version_formato)
            offset_indice = lector_encabezado.entero()

            archivo.seek(offset_indice)
            resto = archivo.read()
            lector_indice = LectorBinario(resto)
            cantidad = lector_indice.entero()
            offset_sala = None
            longitud_sala = None
            for _ in range(cantidad):
                id_actual = lector_indice.entero()
                inicio = lector_indice.entero()
                longitud = lector_indice.entero()
                if id_actual == id_sala:
                    offset_sala, longitud_sala = inicio, longitud
            if offset_sala is None:
                raise ValueError(f"La sala {id_sala} no está en este archivo de partida")

            archivo.seek(offset_sala)
            bloque = archivo.read(longitud_sala)

        return PartidaBinaria._leer_sala(LectorBinario(bloque), servicio)