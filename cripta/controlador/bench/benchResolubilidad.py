"""Mediciones de la verificación de resolubilidad (003-resolubilidad,
FR-032 a FR-035, SC-002, SC-003; research.md R11).

Dos tablas:
  1. Cripta de referencia: la de más salas de datos_offline/, elegida en
     ejecución por cantidad de salas (sin ids en el código, FR-036). Se mide
     construir el grafo y verificar, sin red ni renderizado (los datos ya
     están en memoria), contra 200 ms (FR-032). Si esa cripta no tiene
     llaves.json, la fila dice SIN DATOS y el resultado NO es PASA: nunca se
     mide con una ubicación de llaves inventada ni vacía.
  2. Cadenas sintéticas de 100, 200 y 400 llaves (la llave i abre la zona de
     la i+1), resolubles y con ciclo: tiempo (informativo) y salidas
     examinadas de la verificación y de la alternativa ingenua, si el reporte
     es el mismo (FR-035), y los cocientes de SALIDAS EXAMINADAS al duplicar
     las llaves, contra <= 2,5 y >= 3,5 (SC-003). El contador es
     determinista: el cociente no depende del equipo ni del ruido.

Desde la carpeta que contiene 'cripta':
    python -m cripta.controlador.bench.benchResolubilidad [--rapido]
--rapido reduce las repeticiones, no los tamaños.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from ...adaptadores.fuenteOffline import FuenteOffline
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.puertos.dto import DatosCriptaDTO, JugadorDTO, SalaDTO, SalidaDTO, UbicacionLlaveDTO
from ...modelo.puertos.errores import ErrorCripta
from ...modelo.resolubilidad.verificadorResolubilidad import verificar_resolubilidad
from ..textoResolubilidad import lineas_reporte
from .alternativasResolubilidad import verificar_ingenua
from .medidor import Medidor
from .reporte import Reporte

CARPETA_OFFLINE = Path(__file__).resolve().parents[3] / "datos_offline"
LIMITE_MS = 200.0
TAMANOS = (100, 200, 400)
COCIENTE_MAXIMO_VERIFICACION = 2.5
COCIENTE_MINIMO_INGENUA = 3.5


# ---------------------------------------------------------------------------
# Cripta de referencia
# ---------------------------------------------------------------------------

class Referencia:
    """Lo medido sobre la cripta de referencia, o por qué no se pudo."""

    def __init__(self, salas: int = 0, salidas: int = 0, llaves: int = 0,
                 ms_minimo: Optional[float] = None, motivo: Optional[str] = None) -> None:
        self.salas = salas
        self.salidas = salidas
        self.llaves = llaves
        self.ms_minimo = ms_minimo
        self.motivo = motivo

    @property
    def sin_datos(self) -> bool:
        return self.ms_minimo is None


class _EscenarioVerificar:
    """Para Medidor: preparar no hace nada (los DTO ya están en memoria) y
    ejecutar arma el grafo y verifica."""

    def __init__(self, datos, salas, ubicaciones, funcion=verificar_resolubilidad) -> None:
        self._datos = datos
        self._salas = salas
        self._ubicaciones = ubicaciones
        self._funcion = funcion
        self.resultado = None

    def preparar(self, n) -> None:
        pass

    def ejecutar(self) -> None:
        self.resultado = self._funcion(self._datos, self._salas, self._ubicaciones)


def medir_referencia(repeticiones: int = 10, carpeta=CARPETA_OFFLINE) -> Referencia:
    try:
        fuente = FuenteOffline(carpeta)
        elegida = None
        for resumen in fuente.listar_criptas():
            if elegida is None or resumen.salas > elegida.salas:
                elegida = resumen
        if elegida is None:
            return Referencia(motivo="no hay criptas en el paquete sin conexión")
        datos = fuente.datos_generales(elegida.id)
        salas = ListaEnlazada()
        salidas = 0
        for pagina in range(1, datos.paginas + 1):
            for sala in fuente.esqueleto(elegida.id, pagina).salas:
                salas.agregar_al_final(sala)
                salidas += len(sala.salidas)
    except ErrorCripta as error:
        return Referencia(motivo=f"no se pudo leer la cripta de referencia: {error}")
    try:
        ubicaciones = fuente.llaves(elegida.id)
    except ErrorCripta as error:
        return Referencia(salas=len(salas), salidas=salidas, motivo=str(error))
    escenario = _EscenarioVerificar(datos, salas, ubicaciones)
    medicion = Medidor(repeticiones).medir(escenario, 0)
    return Referencia(salas=len(salas), salidas=salidas, llaves=len(ubicaciones),
                      ms_minimo=medicion.minimo * 1000)


# ---------------------------------------------------------------------------
# Cadenas sintéticas
# ---------------------------------------------------------------------------

LLAVE_SALIDA = "k_salida"


def _id_llave(numero: int) -> str:
    return f"k_{numero:04d}"


def cadena(llaves: int, con_ciclo: bool):
    """(datos, salas, ubicaciones) de una cadena de 'llaves' llaves: la sala i
    (1 a llaves) tiene la llave i, la puerta i E -> i+1 requiere la llave i y
    la sala i+1 vuelve a la i por una salida abierta. La última llave es
    llave_salida, y su puerta lleva a la sala de salida. Con ciclo,
    llave_salida está DETRÁS de su propia puerta: la fase 2 también corre."""
    salas = ListaEnlazada()
    ubicaciones = ListaEnlazada()
    sala_salida = llaves + 1
    for numero in range(1, llaves + 2):
        salidas = ListaEnlazada()
        if numero <= llaves:
            llave = LLAVE_SALIDA if numero == llaves else _id_llave(numero)
            salidas.agregar_al_final(SalidaDTO("E", numero + 1, True, llave))
            if not (con_ciclo and numero == llaves):
                ubicaciones.agregar_al_final(UbicacionLlaveDTO(llave, numero))
        if numero > 1:
            salidas.agregar_al_final(SalidaDTO("O", numero - 1))
        salas.agregar_al_final(SalaDTO(numero, f"Sala {numero}", salidas))
    if con_ciclo:
        ubicaciones.agregar_al_final(UbicacionLlaveDTO(LLAVE_SALIDA, sala_salida))
    datos = DatosCriptaDTO(
        id="bench-resolubilidad", version="v1", salas_total=llaves + 1, paginas=1,
        salas_por_pagina=llaves + 1, sala_inicial=1, sala_salida=sala_salida,
        llave_salida=LLAVE_SALIDA, presupuesto_solicitudes=0, inventario_max=10,
        jugador=JugadorDTO(vida_max=1, ataque=1, defensa=1, velocidad=100))
    return datos, salas, ubicaciones


class MedicionCadena:
    def __init__(self, llaves: int, con_ciclo: bool, ms_verificacion: float, ms_ingenua: float,
                 salidas_verificacion: int, salidas_ingenua: int, mismo_reporte: bool) -> None:
        self.llaves = llaves
        self.con_ciclo = con_ciclo
        self.ms_verificacion = ms_verificacion
        self.ms_ingenua = ms_ingenua
        self.salidas_verificacion = salidas_verificacion
        self.salidas_ingenua = salidas_ingenua
        self.mismo_reporte = mismo_reporte


def _texto(resultado) -> str:
    return "\n".join(lineas_reporte(resultado))


def medir_cadena(llaves: int, con_ciclo: bool, repeticiones: int = 5) -> MedicionCadena:
    datos, salas, ubicaciones = cadena(llaves, con_ciclo)
    medidor = Medidor(repeticiones)
    rapida = _EscenarioVerificar(datos, salas, ubicaciones)
    lenta = _EscenarioVerificar(datos, salas, ubicaciones, verificar_ingenua)
    ms_rapida = medidor.medir(rapida, 0).minimo * 1000
    ms_lenta = medidor.medir(lenta, 0).minimo * 1000
    return MedicionCadena(llaves, con_ciclo, ms_rapida, ms_lenta,
                          rapida.resultado.salidas_examinadas,
                          lenta.resultado.salidas_examinadas,
                          _texto(rapida.resultado) == _texto(lenta.resultado))


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def _pasa(condicion: bool) -> str:
    return "PASA" if condicion else "FALLA"


def ejecutar(reporte: Reporte, rapido: bool = False) -> None:
    repeticiones = 3 if rapido else 10
    reporte.titulo("Resolubilidad: verificación (003-resolubilidad)")

    referencia = medir_referencia(repeticiones)
    filas = ListaEnlazada()
    if referencia.sin_datos:
        filas.agregar_al_final((f"{referencia.salas}", f"{referencia.salidas}", "-", "-",
                                "SIN DATOS"))
        reporte.nota(f"Cripta de referencia: SIN DATOS ({referencia.motivo}). "
                     "Hay que regenerar datos_offline/ con llaves.json (tasks.md T003).")
    else:
        filas.agregar_al_final((f"{referencia.salas}", f"{referencia.salidas}",
                                f"{referencia.llaves}", f"{referencia.ms_minimo:.3f}",
                                _pasa(referencia.ms_minimo < LIMITE_MS)))
    reporte.tabla(f"Cripta de referencia (la de más salas de datos_offline/), límite {LIMITE_MS:.0f} ms",
                  ("salas", "salidas", "llaves", "ms mínimo", "resultado"), filas)

    filas = ListaEnlazada()
    cocientes = ListaEnlazada()
    for con_ciclo in (False, True):
        variante = "con ciclo" if con_ciclo else "resoluble"
        anterior = None
        for llaves in TAMANOS:
            medicion = medir_cadena(llaves, con_ciclo, repeticiones)
            filas.agregar_al_final((
                variante, f"{llaves}", f"{medicion.ms_verificacion:.3f}",
                f"{medicion.ms_ingenua:.3f}", f"{medicion.salidas_verificacion}",
                f"{medicion.salidas_ingenua}", "sí" if medicion.mismo_reporte else "NO"))
            if anterior is not None:
                rapida = medicion.salidas_verificacion / anterior.salidas_verificacion
                lenta = medicion.salidas_ingenua / anterior.salidas_ingenua
                cocientes.agregar_al_final((
                    variante, f"{anterior.llaves} -> {llaves}", f"{rapida:.2f}",
                    _pasa(rapida <= COCIENTE_MAXIMO_VERIFICACION), f"{lenta:.2f}",
                    _pasa(lenta >= COCIENTE_MINIMO_INGENUA)))
            anterior = medicion
    reporte.tabla("Cadenas de llaves: verificación frente a la alternativa ingenua",
                  ("cadena", "llaves", "ms verif.", "ms ingenua", "salidas verif.",
                   "salidas ingenua", "mismo reporte"), filas)
    reporte.tabla("Cocientes de salidas examinadas al duplicar las llaves (SC-003)",
                  ("cadena", "llaves", "verif.", "<= 2,5", "ingenua", ">= 3,5"), cocientes)


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
