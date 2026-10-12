"""Equipo del jugador (§2.7)."""
from __future__ import annotations


class Equipo:
    """Como máximo un arma y una armadura. Equipar otra del mismo tipo
    sustituye a la anterior, que SIGUE en el inventario."""

    def __init__(self) -> None:
        self.arma = None
        self.armadura = None

    def equipar(self, objeto):
        """Equipa 'objeto' y devuelve el que reemplazó (o None)."""
        # DECISIÓN: el equipo guarda referencias y NO saca el objeto del inventario:
        # §2.7 dice que el reemplazado SIGUE en el inventario.
        if objeto.clase == "arma":
            anterior, self.arma = self.arma, objeto
        elif objeto.clase == "armadura":
            anterior, self.armadura = self.armadura, objeto
        else:
            raise ValueError(f"No se puede equipar un objeto de clase '{objeto.clase}'")
        return anterior

    def desequipar(self, objeto) -> bool:
        """Si 'objeto' estaba equipado lo quita. Devuelve True si lo estaba."""
        if self.arma is objeto:
            self.arma = None
            return True
        if self.armadura is objeto:
            self.armadura = None
            return True
        return False

    def esta_equipado(self, objeto) -> bool:
        return self.arma is objeto or self.armadura is objeto

    def bono_ataque(self) -> int:
        return self.arma.ficha.ataque_bonus if self.arma is not None else 0

    def bono_defensa(self) -> int:
        return self.armadura.ficha.defensa_bonus if self.armadura is not None else 0