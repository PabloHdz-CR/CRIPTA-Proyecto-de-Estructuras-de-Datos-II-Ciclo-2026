"""Salida de una sala (§2.5)."""
from __future__ import annotations

from typing import Optional

from .registroPuertas import RegistroPuertas

COSTO_POR_OMISION = 100     # FR-001: una salida sin costo declarado cuesta 100


class Salida:
    """Una salida N, S, E u O. Cada sala tiene las suyas: la puerta de A hacia
    B y la de B hacia A son objetos distintos (así vienen en el esqueleto).

    Los cambios de estado (abrir, cerrar) los hace la Partida a través del
    Mutador; esta clase solo guarda datos y responde consultas.

    Costo de tránsito (001-terreno-cazador, FR-001, FR-002): guarda el costo
    que trajo el esqueleto (costo_declarado, None si no lo declaró) y, después
    de Mundo.enlazar(), el costo efectivo, resuelto con la contraparte de la
    puerta. También quedan en el enlace las referencias directas a su sala de
    origen y a su sala de destino (research R4), y el RegistroPuertas que
    avisa al mapa de distancias cuando cambia cerrada (R2).
    """

    def __init__(self, direccion: str, destino: int, cerrada: bool = False,
                 llave: str = None, cierre_automatico: int = None,
                 costo: Optional[int] = None) -> None:
        self.direccion = direccion
        # DECISIÓN (SUPUESTO): cada lado de una puerta es una Salida independiente
        # (así vienen en el esqueleto): abrir A->B no abre B->A.
        self.destino = destino                     # id de la sala a la que conduce
        # DECISIÓN: _registro va ANTES que cerrada, porque asignar cerrada ya
        # pasa por el setter, que lo consulta. Antes del enlace es None: cambiar
        # cerrada no avisa a nadie (construcción y carga de una partida).
        self._registro: Optional[RegistroPuertas] = None
        self.cerrada = cerrada
        self.llave = llave                         # id de la llave que la abre
        self.cierre_automatico = cierre_automatico  # None = no se cierra sola
        self.evento_cierre = None                  # EventoCierrePuerta pendiente
        self._costo_declarado = costo              # None = no declarado
        self._costo: Optional[int] = None          # efectivo; lo fija enlazar()
        self._origen = None                        # Sala; lo fija enlazar()
        self._sala_destino = None                  # Sala; lo fija enlazar()

    # ------------------------------------------------------------------
    # Estado de la puerta
    # ------------------------------------------------------------------

    @property
    def cerrada(self) -> bool:
        """True si la salida está cerrada (intransitable)."""
        return self._cerrada

    @cerrada.setter
    def cerrada(self, valor: bool) -> None:
        # DECISIÓN (R2): el aviso vive en el setter y no en el Mutador: así
        # también lo disparan deshacer (Diario, con setattr) y cualquier
        # camino futuro que escriba cerrada. Se avisa en cada escritura,
        # aunque el valor no cambie: invalidar de más nunca cambia una
        # decisión del cazador, solo cuesta un recálculo.
        self._cerrada = valor
        if self._registro is not None:
            self._registro.avisar_cambio()

    def transitable(self) -> bool:
        return not self.cerrada

    def se_abre_con_llave(self) -> bool:
        return self.llave is not None

    # ------------------------------------------------------------------
    # Costo y referencias del enlace
    # ------------------------------------------------------------------

    @property
    def costo_declarado(self) -> Optional[int]:
        """El costo que trajo el esqueleto, o None si no lo declaró."""
        return self._costo_declarado

    @property
    def costo(self) -> int:
        """Costo de tránsito efectivo, entero >= 1. Antes del enlace es el
        declarado, o 100 si no se declaró (FR-001)."""
        if self._costo is not None:
            return self._costo
        if self._costo_declarado is not None:
            return self._costo_declarado
        return COSTO_POR_OMISION

    @property
    def origen(self):
        """La Sala a la que pertenece esta salida (None antes del enlace)."""
        return self._origen

    @property
    def sala_destino(self):
        """La Sala a la que conduce (None antes del enlace)."""
        return self._sala_destino

    def enlazar(self, origen, sala_destino, costo: int,
                registro: RegistroPuertas) -> None:
        """Fija las referencias directas, el costo efectivo y el registro de
        puertas. Lo llama Mundo.enlazar(); repetirlo deja el mismo estado."""
        self._origen = origen
        self._sala_destino = sala_destino
        self._costo = costo
        self._registro = registro
