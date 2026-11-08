"""ModoVerificar: `--verificar ID` (003-resolubilidad, FR-022 a FR-024,
contracts/linea-de-comandos.md).

Solo verifica la cripta: descarga (o lee sin conexión) datos generales,
esqueleto y ubicación de llaves, imprime el reporte canónico y el resumen de
red, y devuelve el código de salida:
    0  RESOLUBLE
    1  NO_RESOLUBLE
    2  NO_VERIFICADA (red, datos, presupuesto o falta de datos sin conexión)

No crea Partida, log ni puntaje (FR-023), y no conoce la Vista: lo arma
FabricaAplicacion sin importar vistaArcade (principio III).

DECISIÓN: los códigos son propios de este modo. En --replay, 1 significa
que la reproducción falló; aquí, 1 es un veredicto válido y los errores van
con 2 (spec, Assumptions).

DECISIÓN (como ReporteFinal): la salida va por Reporte, el formateador que
ya imprime --bench y --replay; las pruebas lo inyectan callado y leen
`lineas`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.puertos.errores import ErrorCripta
from ..modelo.resolubilidad.resultadoResolubilidad import (
    NO_RESOLUBLE, RESOLUBLE, ResultadoResolubilidad, no_verificada)
from ..modelo.resolubilidad.verificacion import verificar_cripta
from .bench.reporte import Reporte
from .reporteFinal import ReporteFinal
from .textoResolubilidad import lineas_reporte

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos

CODIGO_RESOLUBLE = 0
CODIGO_NO_RESOLUBLE = 1
CODIGO_NO_VERIFICADA = 2


def codigo_de(resultado: ResultadoResolubilidad) -> int:
    if resultado.veredicto == RESOLUBLE:
        return CODIGO_RESOLUBLE
    if resultado.veredicto == NO_RESOLUBLE:
        return CODIGO_NO_RESOLUBLE
    return CODIGO_NO_VERIFICADA


class ModoVerificar:

    def __init__(self, servicio: "ServicioDatos", reporte: Reporte,
                 reporte_final: ReporteFinal) -> None:
        self._servicio = servicio
        self._reporte = reporte
        self._reporte_final = reporte_final
        self._lineas = ListaEnlazada()

    @property
    def lineas(self) -> ListaEnlazada:
        """Las líneas del último reporte impreso (para las pruebas)."""
        return self._lineas

    def ejecutar(self, id_cripta: str) -> int:
        """Verifica, imprime y devuelve el código de salida."""
        try:
            self._servicio.iniciar_cripta(id_cripta)
        except ErrorCripta as error:
            resultado = no_verificada(id_cripta, None, None, None, str(error))
        else:
            resultado = verificar_cripta(self._servicio)
        self._lineas = lineas_reporte(resultado)
        for linea in self._lineas:
            self._reporte.nota(linea)
        self._reporte_final.imprimir(self._servicio)
        return codigo_de(resultado)
