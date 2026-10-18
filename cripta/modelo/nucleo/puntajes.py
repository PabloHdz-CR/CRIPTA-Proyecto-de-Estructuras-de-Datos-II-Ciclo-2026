"""Puntajes (§2.12)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..estructuras.listaEnlazada import ListaEnlazada
from ..ordenamiento import ClaveOrden, ordenar
from .constantes import ESTADO_VICTORIA

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
    # El log archivado de ESTA partida (para verla en replay). None en los
    # puntajes guardados antes de que existiera el historial de logs.
    id_partida: Optional[str] = None


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
        """Mejor primero: las victorias antes que las derrotas y, dentro de
        cada grupo, menos tiempo, menos acciones o más enemigos derrotados.

        DECISIÓN (D59): escapar siempre es mejor que morir. Con solo el
        tiempo, una muerte rápida quedaba primera. La clave es una tupla
        (0 victoria / 1 derrota, valor): se compara con < como cualquier
        otra, así que el Ordenamiento propio (§4.9) no cambia y sigue
        siendo estable."""
        if criterio not in CRITERIOS_PUNTAJE:
            raise ValueError(f"Criterio desconocido: {criterio}")
        claves = ListaEnlazada()
        for registro in self._registros:
            grupo = 0 if registro.resultado == ESTADO_VICTORIA else 1
            if criterio == "tiempo":
                clave = registro.tiempo_final
            elif criterio == "acciones":
                clave = registro.acciones
            else:
                # DECISIÓN: 'mejor primero' siempre ascendente: para derrotados (más es
                # mejor) se usa la clave negativa, así basta un ordenamiento ascendente.
                clave = -registro.enemigos_derrotados
            claves.agregar_al_final(ClaveOrden((grupo, clave), registro))
        resultado = ListaEnlazada()
        for envoltorio in ordenar(claves):
            resultado.agregar_al_final(envoltorio.valor)
        return resultado