"""Ayudas compartidas por las pruebas de 002-niebla-guerra (T003).

No es una prueba y no va en ejecutar_pruebas.py. Como vive en pruebas/, puede
usar estructuras de Python; lo que se entrega al modelo (DTOs) usa las
estructuras propias.

Contenido:
  - Descripción de criptas sintéticas con ids enteros, costos, puertas
    cerradas con llave, cierre automático, salidas de un solo sentido,
    enemigos dormidos, trampas y objetos en el suelo (sn, sala_n, FuenteNiebla).
  - partida_sobre() y aplicar(): una Partida real con Diario conectado, sin
    disco ni red; dar_objeto() pone un objeto en el inventario.
  - huella_conocimiento(): foto comparable del conocimiento del jugador
    (FR-001, FR-006), armada desde la prueba recorriendo el mundo.
  - RegistroEnMemoria (implementa RegistroAcciones, con comentarios) y
    controlador_sobre(): un ControladorJuego real con VistaRegistradora.
  - secuencias_sc003(): el generador de secuencias de 1 a 5 acciones que
    comparten las pruebas de SC-003 (T038 y T039).

Descripción: tupla de salas (id, salidas, contenido); cada salida es un dict
de sn(); el contenido es un dict con "enemigos" [(instancia, tipo)],
"trampas" [(instancia, tipo)] y "objetos" [id de ficha].
"""
from __future__ import annotations

import random
import tempfile
from pathlib import Path

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.controlador.controladorJuego import ControladorJuego
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.nucleo.accion import AbrirPuerta, Esperar, Mover, Usar
from cripta.modelo.nucleo.diario import Diario
from cripta.modelo.nucleo.partida import Partida
from cripta.modelo.puertos.dto import (
    DIRECCIONES, ContenidoSalaDTO, DatosCriptaDTO, EnemigoInstanciaDTO,
    FichaAntorchaDTO, FichaEnemigoDTO, FichaLlaveDTO, FichaPergaminoRetrocesoDTO,
    FichaTrampaDTO, JugadorDTO, PaginaSalasDTO, ResumenCriptaDTO, SalaDTO,
    SalidaDTO, TrampaInstanciaDTO)
from cripta.modelo.puertos.errores import ErrorDeRed
from cripta.modelo.puertos.fuenteDatos import FuenteDatos, validar_lote
from cripta.modelo.puertos.registroAcciones import RegistroAcciones

from pruebas.apoyo_terreno import VistaRegistradora, le

ID_CRIPTA = "c-niebla"
VERSION_CRIPTA = "v1"
VERSION_CATALOGO = "cat-niebla"
OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}

# Fichas fijas del catálogo sintético.
RATA = "rata"                 # guardián: no se mueve, ataca si está en la sala
ERRANTE = "errante"           # se mueve al azar
PINCHOS = "pinchos"           # trampa de 5 de daño
ANTORCHA = "antorcha"
ANTORCHA_CORTA = "antorcha_corta"   # se apaga a los 250 de tiempo
LLAVE = "llave_roja"
PERGAMINO = "pergamino"
CAZADOR = "cazador"           # persigue y ataca (rango enorme, rápido)
CAZADOR_MANSO = "cazador_manso"  # persigue al paso del jugador: llega cuando ya se fue


def fichas_base() -> tuple:
    return (
        FichaEnemigoDTO(id=RATA, nombre="Rata", vida_max=5, ataque=3, defensa=0,
                        velocidad=100, comportamiento="guardián", suelta=ListaEnlazada()),
        FichaEnemigoDTO(id=ERRANTE, nombre="Errante", vida_max=5, ataque=0, defensa=0,
                        velocidad=100, comportamiento="errante", suelta=ListaEnlazada()),
        FichaTrampaDTO(id=PINCHOS, nombre="Pinchos", dano=5),
        FichaAntorchaDTO(id=ANTORCHA, nombre="Antorcha", peso=1, valor=1, duracion=100000),
        FichaAntorchaDTO(id=ANTORCHA_CORTA, nombre="Antorcha corta", peso=1, valor=1,
                         duracion=250),
        FichaLlaveDTO(id=LLAVE, nombre="Llave roja", peso=1, valor=1, abre=LLAVE),
        FichaPergaminoRetrocesoDTO(id=PERGAMINO, nombre="Pergamino", peso=1, valor=1),
        FichaEnemigoDTO(id=CAZADOR, nombre="Cazador", vida_max=50, ataque=3, defensa=0,
                        velocidad=300, comportamiento="cazador", suelta=ListaEnlazada(),
                        rango=10 ** 6),
        FichaEnemigoDTO(id=CAZADOR_MANSO, nombre="Manso", vida_max=50, ataque=0, defensa=0,
                        velocidad=100, comportamiento="cazador", suelta=ListaEnlazada(),
                        rango=10 ** 6),
    )


# ---------------------------------------------------------------------------
# Descripciones
# ---------------------------------------------------------------------------

def sn(direccion: str, destino: int, costo=None, cerrada: bool = False,
       llave=None, cierre=None) -> dict:
    """Una salida de la descripción."""
    return {"dir": direccion, "destino": destino, "costo": costo, "cerrada": cerrada,
            "llave": llave, "cierre": cierre}


def sala_n(id_sala: int, *salidas, enemigos=(), trampas=(), objetos=(), nombre=None) -> tuple:
    """Una sala de la descripción: (id, salidas, contenido, nombre)."""
    contenido = {"enemigos": tuple(enemigos), "trampas": tuple(trampas),
                 "objetos": tuple(objetos)}
    return (id_sala, tuple(salidas), contenido, nombre or f"Sala {id_sala}")


def doble(a: int, direccion: str, b: int, costo=None, cerrada=False, llave=None,
          cierre=None) -> tuple:
    """Las dos caras de una puerta entre a y b: (salida de a, salida de b)."""
    return (sn(direccion, b, costo, cerrada, llave, cierre),
            sn(OPUESTA[direccion], a, costo, cerrada, llave, cierre))


def pasillo_n(n: int, costo=None) -> tuple:
    """Salas 1..n de oeste a este, con puertas abiertas en los dos sentidos."""
    salas = []
    for i in range(1, n + 1):
        salidas = []
        if i < n:
            salidas.append(sn("E", i + 1, costo))
        if i > 1:
            salidas.append(sn("O", i - 1, costo))
        salas.append(sala_n(i, *salidas))
    return tuple(salas)


def malla_n(lado: int, costo=None, cerradas_prob: float = 0.0, azar=None) -> tuple:
    """Malla lado × lado con puertas en los dos sentidos (la fila 0 al norte)."""
    salas = []
    for fila in range(lado):
        for columna in range(lado):
            i = fila * lado + columna + 1
            salidas = []
            for d, f2, c2 in (("N", fila - 1, columna), ("S", fila + 1, columna),
                              ("E", fila, columna + 1), ("O", fila, columna - 1)):
                if 0 <= f2 < lado and 0 <= c2 < lado:
                    cerrada = azar is not None and azar.random() < cerradas_prob
                    salidas.append(sn(d, f2 * lado + c2 + 1, costo, cerrada))
            salas.append(sala_n(i, *salidas))
    return tuple(salas)


def con_contenido(descripcion, id_sala: int, enemigos=(), trampas=(), objetos=()) -> tuple:
    """La misma descripción con contenido agregado a una sala."""
    resultado = []
    for i, salidas, contenido, nombre in descripcion:
        if i == id_sala:
            contenido = {"enemigos": contenido["enemigos"] + tuple(enemigos),
                         "trampas": contenido["trampas"] + tuple(trampas),
                         "objetos": contenido["objetos"] + tuple(objetos)}
        resultado.append((i, salidas, contenido, nombre))
    return tuple(resultado)


def renombrar(descripcion, nombres) -> tuple:
    """La misma descripción con nombres nuevos: nombres es una función id → nombre."""
    return tuple((i, salidas, contenido, nombres(i)) for i, salidas, contenido, _ in descripcion)


def salas_dto(descripcion) -> ListaEnlazada:
    resultado = ListaEnlazada()
    for id_sala, salidas, _, nombre in descripcion:
        ordenadas = sorted(salidas, key=lambda s: DIRECCIONES.index(s["dir"]))
        dtos = ListaEnlazada()
        for s in ordenadas:
            dtos.agregar_al_final(SalidaDTO(
                direccion=s["dir"], sala=s["destino"], cerrada=s["cerrada"],
                llave=s["llave"], cierre_automatico=s["cierre"], costo=s["costo"]))
        resultado.agregar_al_final(SalaDTO(id=id_sala, nombre=nombre, salidas=dtos))
    return resultado


def datos_cripta(descripcion, sala_inicial: int, sala_salida=None,
                 vida_jugador: int = 100) -> DatosCriptaDTO:
    if sala_salida is None:
        sala_salida = max(i for i, *_ in descripcion) + 1000   # inexistente: nunca se gana
    return DatosCriptaDTO(
        id=ID_CRIPTA, version=VERSION_CRIPTA, salas_total=len(descripcion), paginas=1,
        salas_por_pagina=max(1, len(descripcion)), sala_inicial=sala_inicial,
        sala_salida=sala_salida, llave_salida="itm_llave_salida",
        presupuesto_solicitudes=10 ** 6, inventario_max=10,
        jugador=JugadorDTO(vida_max=vida_jugador, ataque=50, defensa=0, velocidad=100))


class FuenteNiebla(FuenteDatos):
    """FuenteDatos en memoria para una cripta sintética de la niebla."""

    def __init__(self, descripcion, sala_inicial: int = 1, sala_salida=None,
                 vida_jugador: int = 100, fichas=None) -> None:
        self._descripcion = descripcion
        self._datos = datos_cripta(descripcion, sala_inicial, sala_salida, vida_jugador)
        self._fichas = tuple(fichas) if fichas is not None else fichas_base()

    def listar_criptas(self):
        return le(ResumenCriptaDTO(id=ID_CRIPTA, nombre="Niebla",
                                   salas=len(self._descripcion), dificultad=1))

    def datos_generales(self, id_cripta):
        return self._datos

    def esqueleto(self, id_cripta, pagina):
        return PaginaSalasDTO(pagina=1, total_paginas=1, salas=salas_dto(self._descripcion))

    def contenido(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        resultado = ListaEnlazada()
        for id_sala in ids_salas:
            enemigos = ListaEnlazada()
            trampas = ListaEnlazada()
            objetos = ListaEnlazada()
            for i, _, contenido, _ in self._descripcion:
                if i != id_sala:
                    continue
                for instancia, tipo in contenido["enemigos"]:
                    enemigos.agregar_al_final(EnemigoInstanciaDTO(instancia=instancia, tipo=tipo))
                for instancia, tipo in contenido["trampas"]:
                    trampas.agregar_al_final(TrampaInstanciaDTO(instancia=instancia, tipo=tipo))
                for id_ficha in contenido["objetos"]:
                    objetos.agregar_al_final(id_ficha)
            resultado.agregar_al_final(ContenidoSalaDTO(
                sala=id_sala, enemigos=enemigos, objetos=objetos, trampas=trampas))
        return resultado

    def catalogo(self, ids):
        validar_lote("catalogo", ids)
        resultado = ListaEnlazada()
        for id_ficha in ids:
            encontrada = None
            for ficha in self._fichas:
                if ficha.id == id_ficha:
                    encontrada = ficha
            if encontrada is None:
                raise ErrorDeRed("catalogo", f"la ficha {id_ficha} no existe")
            resultado.agregar_al_final(encontrada)
        return resultado

    def llaves(self, id_cripta):
        return ListaEnlazada()

    def version_cripta(self, id_cripta):
        return VERSION_CRIPTA

    def version_catalogo(self):
        return VERSION_CATALOGO

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass


_ASINCRONAS = []


def servicio_niebla(descripcion, **opciones) -> ServicioDatos:
    """ServicioDatos sobre una FuenteNiebla, con la caché de fichas en una
    carpeta temporal. Llamar a cerrar_fuentes() al final de la prueba."""
    fuente = FuenteNiebla(descripcion, **opciones)
    asincrona = FuenteAsincrona(fuente)
    _ASINCRONAS.append(asincrona)
    carpeta = Path(tempfile.mkdtemp(prefix="apoyo_niebla_"))
    servicio = ServicioDatos(fuente, asincrona, CacheFichas(25), AlmacenLocalDisco(carpeta))
    servicio.iniciar_cripta(ID_CRIPTA)
    return servicio


def cerrar_fuentes() -> None:
    while _ASINCRONAS:
        _ASINCRONAS.pop().cerrar()


def partida_sobre(descripcion, semilla: int = 1, sala_inicial: int = 1, sala_salida=None,
                  vida_jugador: int = 100, diario: bool = True) -> Partida:
    """Partida real e iniciada, con un Diario conectado antes de iniciar
    (como el Controlador)."""
    servicio = servicio_niebla(descripcion, sala_inicial=sala_inicial,
                               sala_salida=sala_salida, vida_jugador=vida_jugador)
    partida = Partida(servicio)
    if diario:
        partida.conectar_diario(Diario())
    partida.iniciar(semilla)
    return partida


def aplicar(partida: Partida, *acciones) -> list:
    """Aplica las acciones en orden y exige que todas se acepten."""
    resultados = []
    for accion in acciones:
        resultado = partida.aplicar_accion(accion)
        assert resultado.aceptada, f"{accion!r} rechazada: {resultado.motivo}"
        resultados.append(resultado)
    return resultados


def mover(partida: Partida, *direcciones) -> list:
    return aplicar(partida, *[Mover(d) for d in direcciones])


def dar_objeto(partida: Partida, id_ficha: str):
    """Pone un objeto nuevo en el inventario del jugador sin registrarlo (es
    preparación de la prueba, no una acción del juego)."""
    ficha = partida.servicio.resolver_fichas(le(id_ficha)).ver_primero()
    objeto = partida._fabrica.crear_objeto(ficha)
    partida.mutador.pausar()
    try:
        partida.jugador.inventario.recoger(objeto)
    finally:
        partida.mutador.reanudar()
    return objeto


def encender_antorcha(partida: Partida, ficha: str = ANTORCHA) -> None:
    """Da una antorcha y la usa (acción del juego, con su tiempo)."""
    objeto = dar_objeto(partida, ficha)
    aplicar(partida, Usar(objeto.id_instancia))


def sala(partida: Partida, id_sala: int):
    return partida.mundo.sala(id_sala)


def conocer(partida: Partida, *ids) -> None:
    """Preparación de la prueba (no es una acción del juego): deja cada sala
    explorada y sus caras observadas con su estado real, como si el jugador
    ya las hubiera visto, sin entrar ni activar nada. Corre con el Mutador en
    pausa: no queda en el Diario."""
    from cripta.modelo.mundo.conocimiento import ABIERTA, CERRADA, DESCONOCIDA, EXPLORADA
    partida.mutador.pausar()
    try:
        for id_sala in ids:
            s = partida.mundo.sala(id_sala)
            if s.conocimiento == DESCONOCIDA:
                partida.mundo.conocidas.agregar(s)
            s.conocimiento = EXPLORADA
            for salida in s.salidas:
                if salida is not None:
                    salida.recordada = CERRADA if salida.cerrada else ABIERTA
                    destino = salida.sala_destino
                    if destino.conocimiento == DESCONOCIDA:
                        partida.mundo.conocidas.agregar(destino)
                        destino.conocimiento = 1
    finally:
        partida.mutador.reanudar()


# ---------------------------------------------------------------------------
# Huella del conocimiento
# ---------------------------------------------------------------------------

def huella_conocimiento(partida: Partida) -> tuple:
    """((id, conocimiento) por sala, (id, dirección, recordada) por salida),
    ordenadas por id. Se arma recorriendo el mundo desde la prueba."""
    salas = []
    caras = []
    for s in partida.mundo:
        salas.append((s.id, s.conocimiento))
        for indice, salida in enumerate(s.salidas):
            if salida is not None:
                caras.append((s.id, DIRECCIONES[indice], salida.recordada))
    return (tuple(sorted(salas)), tuple(sorted(caras)))


def ids_conocidas(partida: Partida) -> list:
    """Ids del registro de conocidas, en su orden."""
    return [s.id for s in partida.mundo.conocidas]


# ---------------------------------------------------------------------------
# Registro y Controlador
# ---------------------------------------------------------------------------

class RegistroEnMemoria(RegistroAcciones):
    """RegistroAcciones en memoria: guarda las líneas, comentarios incluidos."""

    def __init__(self) -> None:
        self.encabezado = None
        self.lineas = []          # ("accion", Accion) o ("comentario", texto)

    def iniciar(self, encabezado) -> None:
        self.encabezado = encabezado
        self.lineas = []

    def registrar_accion(self, accion) -> None:
        self.lineas.append(("accion", accion))

    def registrar_comentario(self, texto: str) -> None:
        self.lineas.append(("comentario", texto))

    def leer(self):
        acciones = ListaEnlazada()
        for tipo, valor in self.lineas:
            if tipo == "accion":
                acciones.agregar_al_final(valor)
        return self.encabezado, acciones

    def respaldar(self) -> None:
        pass

    def restaurar(self) -> bool:
        return False

    def acciones(self) -> list:
        return [v for t, v in self.lineas if t == "accion"]

    def comentarios(self) -> list:
        return [v for t, v in self.lineas if t == "comentario"]


class VistaNiebla(VistaRegistradora):
    """VistaRegistradora que también guarda los mensajes."""

    def __init__(self) -> None:
        super().__init__()
        self.mensajes = []

    def mostrar_mensajes(self, mensajes) -> None:
        super().mostrar_mensajes(mensajes)
        for texto in mensajes:
            self.mensajes.append(texto)


def viajar(controlador, id_sala: int, maximo: int = 60) -> list:
    """Ordena «ir a id_sala» y da vueltas con None hasta que el viaje
    termine. Devuelve los mensajes de "Viaje detenido" que mostró la vista."""
    from cripta.vista.comando import Comando
    vista = controlador._vista
    antes = len(vista.mensajes)
    controlador.procesar(Comando("ir_a", (id_sala,)))
    for _ in range(maximo):
        if controlador.viaje is None:
            break
        controlador.procesar(None)
    assert controlador.viaje is None, "el viaje no terminó"
    return [m for m in vista.mensajes[antes:] if m.startswith("Viaje detenido")]


def controlador_sobre(descripcion, semilla: int = 1, sala_inicial: int = 1,
                      sala_salida=None, vida_jugador: int = 100, registro=None,
                      reloj_real=None):
    """(ControladorJuego, VistaNiebla, registro) con una partida nueva iniciada
    sobre la descripción. Por omisión el registro es un RegistroEnMemoria."""
    servicio = servicio_niebla(descripcion, sala_inicial=sala_inicial,
                               sala_salida=sala_salida, vida_jugador=vida_jugador)
    vista = VistaNiebla()
    if registro is None:
        registro = RegistroEnMemoria()
    carpeta = Path(tempfile.mkdtemp(prefix="apoyo_niebla_ctrl_"))
    controlador = ControladorJuego(
        servicio, vista, registro, GestorGuardado(AlmacenPartidaDisco(carpeta / "guardados")),
        PuntajesArchivo(carpeta / "puntajes.jsonl"), ReporteFinal(), reloj_real=reloj_real)
    controlador.iniciar_nueva(ID_CRIPTA, semilla)
    return controlador, vista, registro


# ---------------------------------------------------------------------------
# Secuencias de SC-003 (T038 y T039)
# ---------------------------------------------------------------------------

def cripta_sc003(azar: random.Random) -> tuple:
    """Malla 3 × 3 con algunas puertas cerradas con llave, alguna con cierre
    automático y todas las salas con su contenido vacío."""
    lado = 3
    salas = []
    for fila in range(lado):
        for columna in range(lado):
            i = fila * lado + columna + 1
            salidas = []
            for d, f2, c2 in (("N", fila - 1, columna), ("S", fila + 1, columna),
                              ("E", fila, columna + 1), ("O", fila, columna - 1)):
                if 0 <= f2 < lado and 0 <= c2 < lado:
                    cerrada = azar.random() < 0.25
                    cierre = azar.choice((None, None, 150, 400))
                    salidas.append(sn(d, f2 * lado + c2 + 1, azar.choice((None, 50, 100)),
                                      cerrada, LLAVE if cerrada else None, cierre))
            salas.append(sala_n(i, *salidas))
    # costos coherentes entre caras (FR-027 de 001): copiar el de la ida a la vuelta
    por_id = {i: {s["dir"]: s for s in salidas} for i, salidas, _, _ in salas}
    for i, salidas, _, _ in salas:
        for s in salidas:
            vuelta = por_id[s["destino"]].get(OPUESTA[s["dir"]])
            if vuelta is not None and vuelta["destino"] == i:
                vuelta["costo"] = s["costo"]
    return tuple(salas)


def secuencias_sc003(semilla: int, cantidad: int):
    """Genera `cantidad` casos (descripción, semilla de la partida, antorcha,
    lista de acciones como texto, fracción del punto de guardado). Las acciones
    son de 1 a 5 entre "mover", "abrir" y "esperar", con antorcha encendida o
    no al empezar. Las direcciones se eligen en ejecución sobre la partida real
    (aplicar_paso). La fracción (en [0, 1)) elige con la semilla el punto donde
    T039 guarda y carga: int(fracción * (acciones + 1))."""
    azar = random.Random(semilla)
    for _ in range(cantidad):
        descripcion = cripta_sc003(azar)
        acciones = [azar.choice(("mover", "mover", "mover", "abrir", "esperar"))
                    for _ in range(azar.randint(1, 5))]
        yield descripcion, azar.randint(1, 10 ** 6), azar.random() < 0.5, acciones, azar.random()


def aplicar_paso(partida: Partida, tipo: str, azar: random.Random) -> bool:
    """Aplica una acción del tipo dado eligiendo la dirección con el azar de la
    prueba. Devuelve True si se aplicó (las que no tienen dirección válida se
    reemplazan por esperar)."""
    sala_actual = partida.mundo.sala(partida.jugador.sala)
    if tipo == "mover":
        opciones = [d for d in DIRECCIONES
                    if sala_actual.salida(d) is not None and sala_actual.salida(d).transitable()]
        accion = Mover(azar.choice(opciones)) if opciones else Esperar()
    elif tipo == "abrir":
        opciones = [d for d in DIRECCIONES
                    if sala_actual.salida(d) is not None and sala_actual.salida(d).cerrada]
        accion = AbrirPuerta(azar.choice(opciones)) if opciones else Esperar()
    else:
        accion = Esperar()
    return partida.aplicar_accion(accion).aceptada
