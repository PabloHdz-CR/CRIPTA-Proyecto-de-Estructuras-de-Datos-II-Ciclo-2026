"""Traduce el contenido de una sala (DTO) a entidades del juego, una sola vez."""
from __future__ import annotations

from ..actores.comportamientos import crear_comportamiento
from ..actores.enemigo import Enemigo
from ..estructuras.listaEnlazada import ListaEnlazada
from ..mundo.trampa import Trampa
from ..objetos.objeto import crear_objeto


def _agregar_unico(ids: ListaEnlazada, id_ficha: str) -> None:
    if not ids.contiene(id_ficha):
        ids.agregar_al_final(id_ficha)


def _buscar_ficha(fichas: ListaEnlazada, id_ficha):
    """Búsqueda lineal (clave, valor) por id, igual que EsqueletoCripta (D32):
    el equipo no usa una tabla hash como índice. Pocas fichas distintas por
    sala (decenas como mucho), así que O(fichas) es aceptable."""
    for id_guardado, ficha in fichas:
        if id_guardado == id_ficha:
            return ficha
    return None


def _tiene_ficha(fichas: ListaEnlazada, id_ficha) -> bool:
    return _buscar_ficha(fichas, id_ficha) is not None


class FabricaEntidades:
    """Convierte ContenidoSalaDTO en Enemigo, Objeto y Trampa.

    Las fichas se piden al servicio de datos en UNA consulta por fase (sin ids
    repetidos; el servicio las parte en lotes de 10): primero tipos de enemigo,
    objetos y trampas; luego lo que 'suelta' cada enemigo, para que la muerte
    de un enemigo nunca dispare una solicitud de red a mitad de combate.
    """

    def __init__(self, servicio) -> None:
        self._servicio = servicio
        self._siguiente_id_objeto = 1

    def crear_objeto(self, ficha):
        objeto = crear_objeto(self._siguiente_id_objeto, ficha)
        self._siguiente_id_objeto += 1
        return objeto

    def construir(self, contenido, id_sala: int):
        """Devuelve (enemigos, objetos, trampas) como ListaEnlazada."""
        ids = ListaEnlazada()
        for dto in contenido.enemigos:
            _agregar_unico(ids, dto.tipo)
        for id_ficha in contenido.objetos:
            _agregar_unico(ids, id_ficha)
        for dto in contenido.trampas:
            _agregar_unico(ids, dto.tipo)
        # DECISIÓN: ListaEnlazada de pares (id, ficha) y no TablaHash/dict (§7): se
        # busca linealmente para emparejar cada ficha con su id.
        fichas = ListaEnlazada()
        self._resolver(ids, fichas)

        ids_suelta = ListaEnlazada()
        for dto in contenido.enemigos:
            for id_ficha in _buscar_ficha(fichas, dto.tipo).suelta:
                if not _tiene_ficha(fichas, id_ficha):
                    _agregar_unico(ids_suelta, id_ficha)
        self._resolver(ids_suelta, fichas)

        enemigos = ListaEnlazada()
        for dto in contenido.enemigos:
            ficha = _buscar_ficha(fichas, dto.tipo)
            vida = dto.vida if dto.vida is not None else ficha.vida_max
            enemigo = Enemigo(dto.instancia, ficha, vida, id_sala,
                              crear_comportamiento(ficha.comportamiento))
            for id_ficha in ficha.suelta:
                enemigo.suelta.agregar_al_final(_buscar_ficha(fichas, id_ficha))
            enemigos.agregar_al_final(enemigo)

        objetos = ListaEnlazada()
        for id_ficha in contenido.objetos:
            objetos.agregar_al_final(self.crear_objeto(_buscar_ficha(fichas, id_ficha)))

        trampas = ListaEnlazada()
        for dto in contenido.trampas:
            trampas.agregar_al_final(
                Trampa(dto.instancia, _buscar_ficha(fichas, dto.tipo), id_sala))
        return enemigos, objetos, trampas

    def _resolver(self, ids: ListaEnlazada, destino: ListaEnlazada) -> None:
        if ids.esta_vacia():
            return
        resueltas = self._servicio.resolver_fichas(ids)   # mismo orden que ids
        iterador = iter(resueltas)
        for id_ficha in ids:
            destino.agregar_al_final((id_ficha, next(iterador)))