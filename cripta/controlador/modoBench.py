"""ModoBench: `--bench` (§5.3). Punto de entrada estable que delega en
bench/benchTodo.py; nunca recibe ni instancia una Vista (§6).

DECISIÓN: --bench usa cargas sintéticas (no red, ni caché real, ni hilo de
fondo): así las mediciones no dependen de la latencia del API (~400 ms por
solicitud, §3.4) y se repiten igual en la defensa.
"""
from __future__ import annotations

from .bench.benchTodo import ejecutar_todo
from .bench.reporte import Reporte


class ModoBench:

    def ejecutar(self, rapido: bool = False) -> Reporte:
        return ejecutar_todo(Reporte(), rapido)
