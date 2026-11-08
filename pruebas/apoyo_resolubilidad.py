"""Ayudas compartidas por las pruebas de 003-resolubilidad (T009).

No es una prueba y no va en ejecutar_pruebas.py, igual que apoyo_terreno.py.
Vive en pruebas/, así que puede usar estructuras de Python; lo que se entrega
al programa (DTOs) usa ListaEnlazada.

Contenido:
  - Cripta: descripción compacta de una cripta sintética (salas con salidas,
    sala inicial, sala de salida, llave de salida y ubicaciones de llaves).
  - abierta() y cerrada(): salidas de la descripción.
  - datos_dto(), salas_dto() y ubicaciones_dto(): la descripción en DTOs, con
    la opción de DESORDENAR salas, salidas y entradas de llaves con una
    semilla (FR-010, SC-004).
  - verificar() y texto(): corren la verificación y el formateador del
    programa sobre una descripción.
  - FuenteLlaves: FuenteDatos en memoria con llaves() y contadores; falla si
    se le pide contenido o catálogo y no se permitió (FR-017).
  - generar_cripta(semilla): criptas pequeñas al azar con random.Random
    (research.md R13).
  - a_tuplas(resultado): el ResultadoResolubilidad del programa en tuplas,
    con la misma forma que el oráculo (oraculo_resolubilidad.py).
  - VistaRegistradora (reexportada de apoyo_terreno).

Una salida de la descripción es (direccion, destino, cerrada, llave,
cierre_automatico). Una ubicación es (id_llave, sala, enemigo o None).
"""
from __future__ import annotations

import random

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.dto import (
    DIRECCIONES, ContenidoSalaDTO, DatosCriptaDTO, JugadorDTO, PaginaSalasDTO,
    ResumenCriptaDTO, SalaDTO, SalidaDTO, UbicacionLlaveDTO)
from cripta.modelo.puertos.fuenteDatos import FuenteDatos, validar_lote

from pruebas.apoyo_terreno import VistaRegistradora  # noqa: F401  (reexportada)

ID_CRIPTA = "res-sintetica"
VERSION_CRIPTA = "v1"
VERSION_CATALOGO = "cat-res-1"


# ---------------------------------------------------------------------------
# Descripción de una cripta
# ---------------------------------------------------------------------------

def abierta(direccion, destino):
    return (direccion, destino, False, None, None)


def cerrada(direccion, destino, llave=None, cierre_automatico=None):
    return (direccion, destino, True, llave, cierre_automatico)


class Cripta:
    """salas: secuencia de (id, secuencia de salidas). ubicaciones: secuencia
    de (id_llave, sala, enemigo o None)."""

    def __init__(self, salas, sala_salida, llave_salida, ubicaciones=(),
                 sala_inicial=1, id_cripta=ID_CRIPTA, version=VERSION_CRIPTA):
        self.salas = [(id_sala, list(salidas)) for id_sala, salidas in salas]
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.ubicaciones = [tuple(u) if len(u) == 3 else (u[0], u[1], None)
                            for u in ubicaciones]
        self.id_cripta = id_cripta
        self.version = version

    def __repr__(self):
        return (f"Cripta(salas={self.salas!r}, sala_inicial={self.sala_inicial}, "
                f"sala_salida={self.sala_salida}, llave_salida={self.llave_salida!r}, "
                f"ubicaciones={self.ubicaciones!r})")


def _le(elementos):
    lista = ListaEnlazada()
    lista.agregar_todos(elementos)
    return lista


def datos_dto(cripta: Cripta) -> DatosCriptaDTO:
    return DatosCriptaDTO(
        id=cripta.id_cripta, version=cripta.version, salas_total=len(cripta.salas),
        paginas=1, salas_por_pagina=max(1, len(cripta.salas)),
        sala_inicial=cripta.sala_inicial, sala_salida=cripta.sala_salida,
        llave_salida=cripta.llave_salida, presupuesto_solicitudes=50, inventario_max=10,
        jugador=JugadorDTO(vida_max=40, ataque=6, defensa=2, velocidad=100))


def salas_dto(cripta: Cripta, semilla_desorden=None) -> ListaEnlazada:
    """Las salas en SalaDTO. Sin semilla, en el orden de la descripción y con
    las salidas en N, S, E, O (como las entrega el convertidor); con semilla,
    las salas y las salidas de cada sala en un orden al azar."""
    azar = random.Random(semilla_desorden) if semilla_desorden is not None else None
    salas = list(cripta.salas)
    if azar is not None:
        azar.shuffle(salas)
    resultado = []
    for id_sala, salidas in salas:
        if azar is None:
            salidas = sorted(salidas, key=lambda s: DIRECCIONES.index(s[0]))
        else:
            salidas = list(salidas)
            azar.shuffle(salidas)
        resultado.append(SalaDTO(id=id_sala, nombre=f"Sala {id_sala}", salidas=_le(
            SalidaDTO(direccion=d, sala=destino, cerrada=c, llave=llave,
                      cierre_automatico=cierre)
            for d, destino, c, llave, cierre in salidas)))
    return _le(resultado)


def ubicaciones_dto(cripta: Cripta, semilla_desorden=None) -> ListaEnlazada:
    ubicaciones = list(cripta.ubicaciones)
    if semilla_desorden is not None:
        random.Random(semilla_desorden + 1).shuffle(ubicaciones)
    return _le(UbicacionLlaveDTO(id=i, sala=s, enemigo=e) for i, s, e in ubicaciones)


def verificar(cripta: Cripta, semilla_desorden=None):
    """El ResultadoResolubilidad del programa para esta descripción."""
    from cripta.modelo.resolubilidad.verificadorResolubilidad import verificar_resolubilidad
    return verificar_resolubilidad(datos_dto(cripta), salas_dto(cripta, semilla_desorden),
                                   ubicaciones_dto(cripta, semilla_desorden))


def texto(resultado) -> str:
    """El reporte del programa como un solo texto, una línea por renglón."""
    from cripta.controlador.textoResolubilidad import lineas_reporte
    return "\n".join(lineas_reporte(resultado))


# ---------------------------------------------------------------------------
# Fuente en memoria
# ---------------------------------------------------------------------------

class FuenteLlaves(FuenteDatos):
    """FuenteDatos en memoria para una Cripta. Cuenta las llamadas a llaves().
    Si permitir_contenido es False, pedir contenido o catálogo es un error de
    la prueba (FR-017: la verificación no los necesita)."""

    def __init__(self, cripta: Cripta, permitir_contenido: bool = False,
                 sin_llaves: bool = False) -> None:
        self._cripta = cripta
        self._permitir_contenido = permitir_contenido
        self._sin_llaves = sin_llaves
        self.llamadas_llaves = 0
        self.llamadas_contenido = 0
        self.llamadas_catalogo = 0

    def listar_criptas(self):
        return _le((ResumenCriptaDTO(id=self._cripta.id_cripta, nombre="Sintética",
                                     salas=len(self._cripta.salas), dificultad=1),))

    def datos_generales(self, id_cripta):
        return datos_dto(self._cripta)

    def esqueleto(self, id_cripta, pagina):
        return PaginaSalasDTO(pagina=1, total_paginas=1, salas=salas_dto(self._cripta))

    def contenido(self, id_cripta, ids_salas):
        self.llamadas_contenido += 1
        assert self._permitir_contenido, "la verificación pidió contenido de salas (FR-017)"
        validar_lote("contenido", ids_salas)
        return _le(ContenidoSalaDTO(sala=i, enemigos=ListaEnlazada(), objetos=ListaEnlazada(),
                                    trampas=ListaEnlazada()) for i in ids_salas)

    def catalogo(self, ids):
        self.llamadas_catalogo += 1
        assert self._permitir_contenido, "la verificación pidió el catálogo (FR-017)"
        return ListaEnlazada()

    def llaves(self, id_cripta):
        from cripta.modelo.puertos.errores import ErrorDeRed
        self.llamadas_llaves += 1
        if self._sin_llaves:
            raise ErrorDeRed("leer la ubicación de llaves", "no hay ubicación de llaves")
        return ubicaciones_dto(self._cripta)

    def version_cripta(self, id_cripta):
        return self._cripta.version

    def version_catalogo(self):
        return VERSION_CATALOGO

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass


# ---------------------------------------------------------------------------
# Criptas al azar (R13)
# ---------------------------------------------------------------------------

def generar_cripta(semilla: int) -> Cripta:
    """Una cripta pequeña al azar: de 3 a 12 salas y de 0 a 5 llaves, más
    llave_salida. Incluye puertas de una sola cara, cerradas sin llave, con
    cierre automático, llaves repetidas, llaves que suelta un enemigo y llaves
    que piden las puertas pero no tienen ubicación."""
    azar = random.Random(semilla)
    cantidad = azar.randint(3, 12)
    ids = list(range(1, cantidad + 1))
    llaves = [f"k_{chr(ord('a') + i)}" for i in range(azar.randint(0, 5))]
    llave_salida = "k_salida"
    usables = llaves + [llave_salida]
    inexistente = "k_zz_sin_ubicacion"

    salidas = {i: {} for i in ids}

    def nueva_cara():
        if azar.random() < 0.45:
            return (False, None, None)
        sorteo = azar.random()
        if sorteo < 0.1:
            return (True, None, None)                    # cerrada sin llave
        if sorteo < 0.15:
            return (True, inexistente, None)             # llave sin ubicación
        cierre = azar.choice((None, None, 300))
        return (True, azar.choice(usables), cierre)

    for origen in ids:
        for direccion in DIRECCIONES:
            if direccion in salidas[origen] or azar.random() < 0.45:
                continue
            destino = azar.choice([i for i in ids if i != origen])
            salidas[origen][direccion] = (destino,) + nueva_cara()
            opuesta = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
            # Cara de vuelta: a veces falta (puerta de una sola cara) y a
            # veces tiene su propio estado y su propia llave (FR-006).
            if opuesta not in salidas[destino] and azar.random() < 0.8:
                if azar.random() < 0.6:
                    cara = salidas[origen][direccion][1:]
                else:
                    cara = nueva_cara()
                salidas[destino][opuesta] = (origen,) + cara

    sala_inicial = 1
    sala_salida = azar.choice(ids[1:])
    ubicaciones = []
    for llave in usables:
        for _ in range(azar.choice((0, 1, 1, 1, 2))):
            sala = azar.choice(ids)
            enemigo = f"e-{sala}{azar.randint(0, 9)}" if azar.random() < 0.25 else None
            ubicaciones.append((llave, sala, enemigo))

    salas = []
    for i in ids:
        salas.append((i, [(d,) + salidas[i][d] for d in DIRECCIONES if d in salidas[i]]))
    return Cripta(salas, sala_salida, llave_salida, ubicaciones, sala_inicial=sala_inicial)


# ---------------------------------------------------------------------------
# Resultado del programa en tuplas (misma forma que el oráculo)
# ---------------------------------------------------------------------------

def _puerta_tupla(puerta):
    return (puerta.origen, puerta.direccion, puerta.destino, puerta.llave)


def a_tuplas(resultado):
    """(veredicto, motivo, sala_salida_solo_sin_puerta, orden, no_obtenibles,
    frontera, ciclos), con:
      orden: tupla de (id, sala, enemigo);
      no_obtenibles: tupla de (id, tupla de (sala, enemigo));
      frontera: tupla de (origen, direccion, destino, llave o None);
      ciclos: tupla de ciclos, cada uno tupla de (llave, origen, direccion,
              destino, llave_requerida)."""
    orden = tuple((l.id, l.ubicacion.sala, l.ubicacion.enemigo) for l in resultado.orden)
    no_obtenibles = tuple(
        (l.id, tuple((u.sala, u.enemigo) for u in l.ubicaciones))
        for l in resultado.no_obtenibles)
    frontera = tuple(_puerta_tupla(p) for p in resultado.frontera)
    ciclos = tuple(
        tuple((paso.llave,) + _puerta_tupla(paso.puerta) for paso in ciclo.pasos)
        for ciclo in resultado.ciclos)
    return (resultado.veredicto, resultado.motivo, resultado.sala_salida_solo_sin_puerta,
            orden, no_obtenibles, frontera, ciclos)
