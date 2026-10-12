"""Puntajes (§2.12)."""
from __future__ import annotations

from dataclasses import dataclass

from ..estructuras.listaEnlazada import ListaEnlazada
from ..ordenamiento import ClaveOrden, ordenar

CRITERIOS_PUNTAJE = ("tiempo", "acciones", "derrotados")


@dataclass(frozen=True)
class RegistroPuntaje:
    nombre: str
    id_cripta: str
    version_cripta: str
    acciones: int
    enemigos_derrotados: int
    tiempo_final: int
    resultado: str               # "victoria" o "derrota"


class TablaPuntajes:
    """Registros en orden de llegada; la vista ordenada es una lista NUEVA
    (usa Ordenamiento con selector automático: inserción o mezcla)."""

    def __init__(self) -> None:
        self._registros = ListaEnlazada()

    def __len__(self) -> int:
        return len(self._registros)

    def __iter__(self):
        return iter(self._registros)

    def agregar(self, registro: RegistroPuntaje) -> None:
        self._registros.agregar_al_final(registro)

    def vista_ordenada(self, criterio: str) -> ListaEnlazada:
        """Mejor primero: menos tiempo, menos acciones o más enemigos derrotados."""
        if criterio not in CRITERIOS_PUNTAJE:
            raise ValueError(f"Criterio desconocido: {criterio}")
        claves = ListaEnlazada()
        for registro in self._registros:
            if criterio == "tiempo":
                clave = registro.tiempo_final
            elif criterio == "acciones":
                clave = registro.acciones
            else:
                # DECISIÓN: 'mejor primero' siempre ascendente: para derrotados (más es
                # mejor) se usa la clave negativa, así basta un ordenamiento ascendente.
                clave = -registro.enemigos_derrotados
            claves.agregar_al_final(ClaveOrden(clave, registro))
        resultado = ListaEnlazada()
        for envoltorio in ordenar(claves):
            resultado.agregar_al_final(envoltorio.valor)
        return resultado