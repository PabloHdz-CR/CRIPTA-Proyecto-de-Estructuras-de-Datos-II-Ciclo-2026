"""Combate (§2.6)."""
from __future__ import annotations

from .constantes import DANO_AZAR_MAX


class Combate:
    @staticmethod
    def calcular_dano(ataque: int, defensa: int, azar) -> int:
        """daño = max(1, ataque + azar.randint(0, 4) - defensa). 'azar' es el
        random.Random propio de la partida, nunca el generador global."""
        # DECISIÓN: Combate no guarda estado ni importa Partida; recibe el azar por
        # parámetro, así se prueba con un Random de semilla fija.
        return max(1, ataque + azar.randint(0, DANO_AZAR_MAX) - defensa)

    @staticmethod
    def resolver_ataque(partida, atacante, objetivo) -> int:
        """Calcula y aplica el daño. Si el objetivo muere, Partida.danar lo
        mata y suelta sus objetos. Devuelve el daño hecho."""
        dano = Combate.calcular_dano(
            atacante.ataque_efectivo(), objetivo.defensa_efectiva(), partida.azar)
        partida.avisar(f"{atacante.nombre} ataca a {objetivo.nombre}: {dano} de daño.")
        partida.danar(objetivo, dano)
        return dano