"""Resultado de la verificación de resolubilidad (003-resolubilidad).

Datos puros e inmutables que entrega el modelo (data-model.md §3). No llevan
texto de interfaz: el Controlador los convierte en el reporte canónico
(contracts/reporte.md). Todas las colecciones son ListaEnlazada, en el orden
canónico que fija la spec:
  - orden: el de obtención (FR-007, FR-009);
  - no_obtenibles: por id de llave como texto (FR-011);
  - frontera: por (sala de origen, dirección N, S, E, O) (FR-012);
  - ciclos: uno por grupo, por el menor id del grupo (FR-015).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.dto import UbicacionLlaveDTO

# Veredictos (FR-001, FR-031)
RESOLUBLE = "RESOLUBLE"
NO_RESOLUBLE = "NO_RESOLUBLE"
NO_VERIFICADA = "NO_VERIFICADA"

# Motivos de NO_RESOLUBLE (FR-011)
LLAVE_SALIDA_NO_OBTENIBLE = "LLAVE_SALIDA_NO_OBTENIBLE"     # (a)
SIN_PUERTA_DE_SALIDA = "SIN_PUERTA_DE_SALIDA"               # (b)


@dataclass(frozen=True)
class LlaveOrdenada:
    """Una posición del orden de obtención: la llave y la ubicación por la que
    se obtiene (la primera, por sala y enemigo, ya alcanzada al elegirla)."""
    id: str
    ubicacion: UbicacionLlaveDTO


@dataclass(frozen=True)
class LlaveNoObtenible:
    """Una llave que no puede obtenerse, con todas sus ubicaciones (vacía =
    "sin ubicación", FR-013, FR-016)."""
    id: str
    ubicaciones: ListaEnlazada


@dataclass(frozen=True)
class PuertaFrontera:
    """Una cara de puerta cerrada, en el sentido en que se recorre (FR-006,
    FR-012). llave None = "sin llave"."""
    origen: int
    direccion: str
    destino: int
    llave: Optional[str]


@dataclass(frozen=True)
class PasoCiclo:
    """K está encerrada por 'puerta', que requiere la llave del paso
    siguiente (FR-014, FR-015)."""
    llave: str
    puerta: PuertaFrontera


@dataclass(frozen=True)
class CicloLlaves:
    """Un ciclo de dependencia: el último paso vuelve a la llave del primero."""
    pasos: ListaEnlazada


@dataclass(frozen=True)
class ResultadoResolubilidad:
    """El veredicto y su explicación (FR-007 a FR-016, FR-031).

    motivo y sala_salida_solo_sin_puerta solo tienen sentido si el veredicto
    es NO_RESOLUBLE; orden, si es RESOLUBLE; error, si es NO_VERIFICADA.
    salidas_examinadas es el contador del bench (FR-033).
    """
    veredicto: str
    id_cripta: Optional[str]
    version_cripta: Optional[str]
    llave_salida: Optional[str]
    sala_salida: Optional[int]
    orden: ListaEnlazada = field(default_factory=ListaEnlazada)
    motivo: Optional[str] = None
    sala_salida_solo_sin_puerta: bool = False
    no_obtenibles: ListaEnlazada = field(default_factory=ListaEnlazada)
    frontera: ListaEnlazada = field(default_factory=ListaEnlazada)
    ciclos: ListaEnlazada = field(default_factory=ListaEnlazada)
    error: Optional[str] = None
    salidas_examinadas: int = 0

    @property
    def resoluble(self) -> bool:
        return self.veredicto == RESOLUBLE


def no_verificada(id_cripta: Optional[str], version_cripta: Optional[str],
                  llave_salida: Optional[str], sala_salida: Optional[int],
                  error: str) -> ResultadoResolubilidad:
    """El resultado cuando la verificación no pudo hacerse (FR-031)."""
    return ResultadoResolubilidad(
        veredicto=NO_VERIFICADA, id_cripta=id_cripta, version_cripta=version_cripta,
        llave_salida=llave_salida, sala_salida=sala_salida, error=error)
