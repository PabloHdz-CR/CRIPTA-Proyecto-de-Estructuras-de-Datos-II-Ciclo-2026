"""Actores: jugador y enemigos (§2.2)."""
from __future__ import annotations

from ..estructuras.listaDoble import ListaDoble


def clave_instancia(texto: str) -> tuple:
    """Clave para ordenar ids de instancia 'ascendentemente': 'e-9' antes que
    'e-10' (compara el sufijo numérico como número, no como texto)."""
    posicion = texto.rfind("-")
    if posicion >= 0 and texto[posicion + 1:].isdigit():
        return (texto[:posicion], int(texto[posicion + 1:]), texto)
    return (texto, -1, texto)


class Actor:
    """Datos y consultas comunes. Los atributos NO se modifican desde fuera:
    todo cambio pasa por partida.mutador (punto único de mutación)."""

    def __init__(self, id_instancia: str, nombre: str, ficha, vida: int, vida_max: int,
                 ataque: int, defensa: int, velocidad: int, sala: int) -> None:
        self.id_instancia = id_instancia
        self.nombre = nombre
        self.ficha = ficha
        self.vida = vida
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.velocidad_base = velocidad
        self.sala = sala                       # id de la sala donde está
        self.vivo = True
        self.evento_accion = None              # su próximo turno en la agenda
        self.efectos = ListaDoble()            # Efecto activos
        # DECISIÓN: la clave de orden se calcula una vez al crear el actor, no en
        # cada comparación al insertar o activar.
        self.clave_id = clave_instancia(id_instancia)

    def ataque_efectivo(self) -> int:
        return self.ataque

    def defensa_efectiva(self) -> int:
        return self.defensa

    # DECISIÓN: Actor solo CALCULA la vida nueva; quien la asigna es el Mutador,
    # para que el cambio quede registrado (desvío de la guía, que pone recibir_dano
    # y curar dentro de Actor).
    def vida_tras_dano(self, dano: int) -> int:
        return max(0, self.vida - dano)

    def vida_tras_curar(self, cura: int) -> int:
        return min(self.vida_max, self.vida + cura)

    def buscar_efecto(self, tipo: str):
        for efecto in self.efectos:
            if efecto.TIPO == tipo:
                return efecto
        return None

    def morir(self, partida) -> None:
        """Deja de ejecutar eventos: cancela su turno y todos sus efectos."""
        if self.evento_accion is not None:
            partida.mutador.agenda_cancelar(self.evento_accion)
        nodo = self.efectos.primero()
        while nodo is not None:
            siguiente = self.efectos.siguiente_de(nodo)
            nodo.dato.cancelar(partida)
            nodo = siguiente