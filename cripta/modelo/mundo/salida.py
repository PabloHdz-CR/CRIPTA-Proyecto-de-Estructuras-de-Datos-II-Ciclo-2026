"""Salida de una sala (§2.5)."""
from __future__ import annotations


class Salida:
    """Una salida N, S, E u O. Cada sala tiene las suyas: la puerta de A hacia
    B y la de B hacia A son objetos distintos (así vienen en el esqueleto).

    Los cambios de estado (abrir, cerrar) los hace la Partida a través del
    Mutador; esta clase solo guarda datos y responde consultas.
    """

    def __init__(self, direccion: str, destino: int, cerrada: bool = False,
                 llave: str = None, cierre_automatico: int = None) -> None:
        self.direccion = direccion
        # DECISIÓN (SUPUESTO): cada lado de una puerta es una Salida independiente
        # (así vienen en el esqueleto): abrir A->B no abre B->A.
        self.destino = destino                     # id de la sala a la que conduce
        self.cerrada = cerrada
        self.llave = llave                         # id de la llave que la abre
        self.cierre_automatico = cierre_automatico  # None = no se cierra sola
        self.evento_cierre = None                  # EventoCierrePuerta pendiente

    def transitable(self) -> bool:
        return not self.cerrada

    def se_abre_con_llave(self) -> bool:
        return self.llave is not None