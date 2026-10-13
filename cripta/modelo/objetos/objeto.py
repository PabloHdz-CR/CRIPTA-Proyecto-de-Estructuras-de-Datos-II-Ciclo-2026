"""Objetos del juego (§2.7): instancias que referencian su ficha compartida."""
from __future__ import annotations

from ..puertos.errores import ErrorCripta


class Objeto:
    """Una instancia de objeto. La ficha (inmutable) se comparte entre todas
    las instancias del mismo tipo; la pertenencia (suelo, inventario) es de la
    instancia."""

    def __init__(self, id_instancia: int, ficha) -> None:
        self.id_instancia = id_instancia
        self.ficha = ficha

    @property
    def clase(self) -> str:
        return self.ficha.clase

    @property
    def nombre(self) -> str:
        return self.ficha.nombre

    def es_usable(self) -> bool:
        return False

    def es_equipable(self) -> bool:
        return False

    def usar(self, partida) -> str:
        raise ErrorCripta(f"'{self.nombre}' no se puede usar")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(#{self.id_instancia}, {self.ficha.id})"


class Arma(Objeto):
    def es_equipable(self) -> bool:
        return True


class Armadura(Objeto):
    def es_equipable(self) -> bool:
        return True


class Pocion(Objeto):
    def es_usable(self) -> bool:
        return True

    def usar(self, partida) -> str:
        jugador = partida.jugador
        ficha = self.ficha
        # DECISIÓN: la poción hace las dos cosas (cura y velocidad) si la ficha trae
        # ambos campos; ninguno es obligatorio en el catálogo.
        if ficha.cura:
            partida.curar(jugador, ficha.cura)           # sin pasar de vida_max
        if ficha.modificador_velocidad and ficha.duracion:
            partida.aplicar_velocidad(jugador, ficha.modificador_velocidad, ficha.duracion)
        return f"Bebes {self.nombre}."


class Antidoto(Objeto):
    def es_usable(self) -> bool:
        return True

    def usar(self, partida) -> str:
        partida.curar_veneno(partida.jugador)
        return f"Usas {self.nombre}."


class Llave(Objeto):
    """La llave no se consume: se usa con AbrirPuerta, no con Usar."""

    def abre_a(self, id_llave: str) -> bool:
        # DECISIÓN: se compara con el id de la ficha Y con el campo 'abre': el
        # enunciado dado no deja claro cuál usa la salida; aceptar ambos evita
        # puertas imposibles de abrir.
        return self.ficha.id == id_llave or self.ficha.abre == id_llave


class Antorcha(Objeto):
    def es_usable(self) -> bool:
        return True

    def usar(self, partida) -> str:
        partida.encender_antorcha(partida.jugador, self.ficha.duracion)
        return f"Enciendes {self.nombre}."


class PergaminoRetroceso(Objeto):
    """Se usa con la acción UsarPergamino, que invoca Partida.deshacer()."""


def crear_objeto(id_instancia: int, ficha) -> Objeto:
    """Crea la subclase según la clase de la ficha (if/elif: sin dict)."""
    clase = ficha.clase
    if clase == "arma":
        return Arma(id_instancia, ficha)
    if clase == "armadura":
        return Armadura(id_instancia, ficha)
    if clase == "pocion":
        return Pocion(id_instancia, ficha)
    if clase == "antidoto":
        return Antidoto(id_instancia, ficha)
    if clase == "llave":
        return Llave(id_instancia, ficha)
    if clase == "antorcha":
        return Antorcha(id_instancia, ficha)
    if clase == "pergamino_retroceso":
        return PergaminoRetroceso(id_instancia, ficha)
    raise ErrorCripta(f"La ficha '{ficha.id}' (clase '{clase}') no es un objeto")