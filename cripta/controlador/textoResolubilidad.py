"""Texto canónico del reporte de resolubilidad (contracts/reporte.md).

Un solo formateador para la terminal (--verificar) y la ventana (pantalla de
reporte y panel de la tecla V): así "idéntico carácter por carácter" (SC-004)
se prueba sobre un solo texto. Recibe el ResultadoResolubilidad del modelo y
devuelve una ListaEnlazada de líneas, sin espacios al final.

Complejidad: O(tamaño del reporte).
"""
from __future__ import annotations

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.resolubilidad.resultadoResolubilidad import (
    LLAVE_SALIDA_NO_OBTENIBLE, NO_VERIFICADA, RESOLUBLE, PuertaFrontera,
    ResultadoResolubilidad)

# FR-019: el aviso corto en la bitácora al iniciar una cripta resoluble.
AVISO_RESOLUBLE = "La cripta es resoluble. V muestra el reporte."
# FR-021 (tasks.md T037): V en una partida sin reporte (cargada).
AVISO_SIN_REPORTE = "Esta partida no tiene reporte de resolubilidad."


def _ubicacion(ubicacion) -> str:
    if ubicacion.enemigo is not None:
        return f"sala {ubicacion.sala} (suelta {ubicacion.enemigo})"
    return f"sala {ubicacion.sala}"


def _puerta(puerta: PuertaFrontera) -> str:
    return f"sala {puerta.origen} {puerta.direccion} -> sala {puerta.destino}"


def _ubicaciones(ubicaciones) -> str:
    texto = ""
    for ubicacion in ubicaciones:
        if texto:
            texto += "; "
        texto += _ubicacion(ubicacion)
    return texto if texto else "sin ubicación"


def _ciclo(ciclo) -> str:
    texto = ""
    primera = None
    for paso in ciclo.pasos:
        if primera is None:
            primera = paso.llave
        else:
            texto += " -> "
        texto += f"{paso.llave}, encerrada por {_puerta(paso.puerta)} (requiere {paso.puerta.llave})"
    return f"{texto} -> {primera}"


def lineas_reporte(resultado: ResultadoResolubilidad) -> ListaEnlazada:
    """Las líneas del reporte, en el formato exacto de contracts/reporte.md."""
    lineas = ListaEnlazada()
    if resultado.veredicto == NO_VERIFICADA:
        lineas.agregar_al_final(f"Cripta {resultado.id_cripta}: NO SE PUDO VERIFICAR")
        lineas.agregar_al_final(f"Motivo: {resultado.error}")
        return lineas

    encabezado = f"Cripta {resultado.id_cripta} (versión {resultado.version_cripta}): "
    if resultado.veredicto == RESOLUBLE:
        lineas.agregar_al_final(encabezado + "RESOLUBLE")
        lineas.agregar_al_final(f"Orden de obtención de llaves ({len(resultado.orden)}):")
        numero = 1
        for llave in resultado.orden:
            lineas.agregar_al_final(f"  {numero}. {llave.id}: {_ubicacion(llave.ubicacion)}")
            numero += 1
        return lineas

    lineas.agregar_al_final(encabezado + "NO RESOLUBLE")
    if resultado.motivo == LLAVE_SALIDA_NO_OBTENIBLE:
        lineas.agregar_al_final(
            f"Motivo: la llave de salida {resultado.llave_salida} no se puede obtener.")
    else:
        lineas.agregar_al_final(
            f"Motivo: ninguna salida que requiere {resultado.llave_salida} da acceso a la "
            f"sala de salida {resultado.sala_salida} desde la región alcanzable.")
        if resultado.sala_salida_solo_sin_puerta:
            lineas.agregar_al_final(
                f"  La sala de salida {resultado.sala_salida} solo se alcanza por caminos "
                "sin esa salida.")

    lineas.agregar_al_final(f"Llaves no obtenibles ({len(resultado.no_obtenibles)}):")
    for llave in resultado.no_obtenibles:
        lineas.agregar_al_final(f"  - {llave.id}: {_ubicaciones(llave.ubicaciones)}")

    lineas.agregar_al_final(f"Frontera bloqueada ({len(resultado.frontera)}):")
    for puerta in resultado.frontera:
        requisito = f"requiere {puerta.llave}" if puerta.llave is not None else "sin llave"
        lineas.agregar_al_final(f"  - {_puerta(puerta)}: {requisito}")

    if resultado.ciclos.esta_vacia():
        lineas.agregar_al_final("Ciclos: ninguno.")
    else:
        lineas.agregar_al_final(f"Ciclos ({len(resultado.ciclos)}):")
        numero = 1
        for ciclo in resultado.ciclos:
            lineas.agregar_al_final(f"  {numero}. {_ciclo(ciclo)}")
            numero += 1
    return lineas
