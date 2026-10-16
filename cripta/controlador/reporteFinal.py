"""ReporteFinal (§5.1, §13): al terminar cada partida (y cada --replay)
reporta solicitudes realizadas, presupuesto, aciertos y fallos de caché.
Solo consulta ServicioDatos, nunca ClienteHttp ni CacheFichas directamente.
O(1): son cuatro contadores.

DECISIÓN (excepción documentada a "el Controlador no usa print", guía §4):
el reporte se escribe con Reporte, el formateador que el equipo ya usa en
--bench, que imprime a la salida estándar. Razones:
  - §5.1 exige el reporte también en --replay, que corre con VistaNula
    (no muestra nada); si pasara por la Vista, el replay fallaría en
    silencio.
  - Es salida para quien evalúa (terminal), no parte de la interfaz del
    juego, igual que la de --bench.
  - El print queda encerrado en una sola clase (Reporte) que se INYECTA:
    las pruebas usan Reporte(imprimir=False) y leen `notas`.
Alternativa descartada: un método nuevo en VistaJuego para el reporte, que
obligaría a VistaNula a imprimir y mezclaría dos responsabilidades.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .bench.reporte import Reporte

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos


class ReporteFinal:

    def __init__(self, reporte: Optional[Reporte] = None) -> None:
        self._reporte = reporte if reporte is not None else Reporte()

    def imprimir(self, servicio_datos: "ServicioDatos") -> None:
        realizadas = servicio_datos.solicitudes_realizadas()
        presupuesto = servicio_datos.presupuesto()
        aciertos = servicio_datos.aciertos_cache()
        fallos = servicio_datos.fallos_cache()

        self._reporte.titulo("Resumen de la partida")
        # presupuesto None = modo --offline: no hay red, no hay presupuesto.
        texto_presupuesto = str(presupuesto) if presupuesto is not None else "sin red"
        self._reporte.nota(f"Solicitudes de red realizadas: {realizadas}")
        self._reporte.nota(f"Presupuesto de solicitudes:    {texto_presupuesto}")
        self._reporte.nota(f"Aciertos de caché:              {aciertos}")
        self._reporte.nota(f"Fallos de caché:                {fallos}")
        if presupuesto is not None:
            self._reporte.nota(f"Solicitudes restantes:          {presupuesto - realizadas}")

    def texto(self, servicio_datos: "ServicioDatos") -> str:
        """Igual que imprimir(), pero devuelve el texto sin imprimirlo."""
        callado = Reporte(imprimir=False)
        ReporteFinal(callado).imprimir(servicio_datos)
        return "\n".join(callado.notas)
