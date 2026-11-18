"""Arma el resumen de un instante de la línea de tiempo (004-linea-tiempo,
FR-005, FR-006, FR-014; contracts/cli.md)."""
from __future__ import annotations

from typing import Optional

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..vista.estadoVista import EstadoVista, ResumenInstante
from .constructorEstadoVista import ConstructorEstadoVista
from .mapaEtiquetas import MapaEtiquetas


class ConstructorResumen:
    """Del estado de una copia reconstruida a un ResumenInstante: el mismo
    EstadoVista que dibuja el juego (con el mapa conocido de ese instante) y
    su texto. Usa un MapaEtiquetas propio: no toca las etiquetas de la
    partida real (FR-011)."""

    def construir(self, copia, pedido: str, instante: Optional[int] = None,
                  aviso: Optional[str] = None) -> ResumenInstante:
        estado = ConstructorEstadoVista(MapaEtiquetas()).construir(copia, mapa_abierto=True)
        numero = copia.jugador.acciones + 1
        return ResumenInstante(pedido=pedido, instante=instante, numero_accion=numero,
                               estado=estado,
                               lineas=lineas_resumen(estado, instante, numero, aviso),
                               aviso=aviso)


def lineas_resumen(estado: EstadoVista, instante: Optional[int], numero: int,
                   aviso: Optional[str]) -> ListaEnlazada:
    """El texto del resumen, en el orden de contracts/cli.md."""
    lineas = ListaEnlazada()
    if instante is None:
        lineas.agregar_al_final(f"Antes de la acción #{numero} (reloj {estado.reloj})")
    else:
        lineas.agregar_al_final(f"Instante {instante} (próxima acción #{numero})")
    actual = _sala_actual(estado)
    lineas.agregar_al_final(f"Sala {actual} - {estado.sala.nombre}" if actual is not None
                            else f"Sala {estado.sala.nombre}")
    jugador = estado.jugador
    lineas.agregar_al_final(
        f"Vida {jugador.vida}/{jugador.vida_max}   Ataque {jugador.ataque_efectivo}   "
        f"Defensa {jugador.defensa_efectiva}   Velocidad {jugador.velocidad}")
    lineas.agregar_al_final("Inventario: " + _unir(
        (f"{o.nombre} [equipado]" if o.equipado else o.nombre)
        for o in estado.inventario.objetos) if not estado.inventario.objetos.esta_vacia()
        else "Inventario: vacío")
    lineas.agregar_al_final("Efectos: " + _unir(e.descripcion for e in estado.efectos)
                            if not estado.efectos.esta_vacia() else "Efectos: ninguno")
    lineas.agregar_al_final("Enemigos en la sala: " + _unir(
        f"{a.etiqueta} {a.vida}/{a.vida_max}" for a in estado.sala.enemigos)
        if not estado.sala.enemigos.esta_vacia() else "Enemigos en la sala: ninguno")
    lineas.agregar_al_final("Mapa conocido:")
    for linea in lineas_mapa(estado.mapa):
        lineas.agregar_al_final(linea)
    if aviso is not None:
        lineas.agregar_al_final(aviso)
    return lineas


def lineas_mapa(mapa) -> ListaEnlazada:
    """Las salas exploradas con sus salidas y las avistadas, por id."""
    lineas = ListaEnlazada()
    if mapa is None:
        return lineas
    for sala in mapa.salas:
        if not sala.explorada:
            lineas.agregar_al_final(f"  {sala.id}  ? (avistada)")
            continue
        marca = "  (actual)" if sala.actual else ""
        lineas.agregar_al_final(f"  {sala.id}  {sala.nombre}{marca}")
        for salida in sala.salidas:
            if salida is not None:
                lineas.agregar_al_final(
                    f"      {salida.direccion} -> {salida.destino}  costo {salida.costo}  "
                    f"{salida.estado}")
    return lineas


def _sala_actual(estado: EstadoVista):
    if estado.mapa is None:
        return None
    for sala in estado.mapa.salas:
        if sala.actual:
            return sala.id
    return None


def _unir(textos) -> str:
    resultado = ""
    for texto in textos:
        resultado = texto if resultado == "" else f"{resultado}, {texto}"
    return resultado
