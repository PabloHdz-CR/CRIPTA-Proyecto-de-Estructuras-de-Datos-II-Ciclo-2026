"""TraductorComandos: convierte un Comando (lo que Vista empaquetó sin
interpretar, §6) en una Accion del modelo, resolviendo el objetivo
(enemigo por etiqueta, objeto por id_instancia, dirección) y reportando
errores de sintaxis sin tocar el modelo (§10.2).

Vocabulario reconocido (D45/D46 más los verbos de §10.2 que VistaArcade
todavía no dispara con ninguna tecla; quedan listos aquí):
    "mover"     (direccion: "N"/"S"/"E"/"O")            -> Mover
    "abrir"     (direccion)                              -> AbrirPuerta
    "atacar"    (etiqueta, p. ej. "Rata gigante #1")     -> Atacar
    "esperar"   ()                                       -> Esperar
    "recoger"   (id_objeto del suelo)                    -> Recoger
    "soltar"    (id_objeto)                              -> Soltar
    "usar"      (id_objeto)                              -> Usar
    "equipar"   (id_objeto)                              -> Equipar
    "pergamino" ()                                       -> UsarPergamino

Complejidad: O(1) por comando, salvo "atacar", que es O(k) en MapaEtiquetas.

DECISIÓN: cadena de if por verbo. Alternativa descartada: un dict
verbo -> función (prohibido como tabla de búsqueda, §7). Con 9 verbos fijos
la cadena cuesta a lo sumo 9 comparaciones de texto: O(1) en la práctica.

DECISIÓN: el Traductor solo valida SINTAXIS (verbo conocido, cantidad y
forma de argumentos). Las REGLAS (¿la puerta está abierta?, ¿cabe en el
inventario?) son del Modelo (ValidadorAcciones): así la regla vive en un
solo lugar y --replay la aplica igual.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..modelo.nucleo.accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar,
    UsarPergamino)
from ..modelo.puertos.dto import DIRECCIONES
from ..modelo.puertos.errores import ErrorCripta

if TYPE_CHECKING:
    from ..modelo.nucleo.accion import Accion
    from ..vista.comando import Comando
    from .mapaEtiquetas import MapaEtiquetas


class ErrorTraduccion(ErrorCripta):
    """Comando mal formado o verbo desconocido: error de SINTAXIS del
    jugador, no de reglas (eso lo rechaza ValidadorAcciones)."""


class TraductorComandos:

    def __init__(self, mapa_etiquetas: "MapaEtiquetas") -> None:
        # DECISIÓN: el mapa se INYECTA: el Traductor y el Constructor de la
        # misma partida comparten exactamente la misma asociación.
        self._etiquetas = mapa_etiquetas

    def traducir(self, comando: "Comando") -> "Accion":
        """Comando -> Accion. Lanza ErrorTraduccion si no se reconoce."""
        verbo = comando.verbo
        argumentos = comando.argumentos
        try:
            if verbo == "mover":
                return Mover(direccion=self._direccion(argumentos))
            if verbo == "abrir":
                return AbrirPuerta(direccion=self._direccion(argumentos))
            if verbo == "atacar":
                return Atacar(objetivo=self._objetivo_por_etiqueta(argumentos))
            if verbo == "esperar":
                self._sin_argumentos(verbo, argumentos)
                return Esperar()
            if verbo == "recoger":
                return Recoger(id_objeto=self._id_objeto(argumentos))
            if verbo == "soltar":
                return Soltar(id_objeto=self._id_objeto(argumentos))
            if verbo == "usar":
                return Usar(id_objeto=self._id_objeto(argumentos))
            if verbo == "equipar":
                return Equipar(id_objeto=self._id_objeto(argumentos))
            if verbo == "pergamino":
                self._sin_argumentos(verbo, argumentos)
                return UsarPergamino()
        except (IndexError, ValueError, TypeError) as error:
            raise ErrorTraduccion(
                f"El comando '{verbo}' no trae los argumentos esperados: {error}") from error
        raise ErrorTraduccion(f"No reconozco el comando '{verbo}'.")

    def _direccion(self, argumentos: tuple) -> str:
        if len(argumentos) != 1:
            raise ErrorTraduccion("Falta la dirección (N, S, E u O).")
        direccion = argumentos[0]
        # DIRECCIONES es una tupla de 4: el 'in' es O(1).
        if direccion not in DIRECCIONES:
            raise ErrorTraduccion(
                f"'{direccion}' no es una dirección válida (N, S, E u O).")
        return direccion

    def _objetivo_por_etiqueta(self, argumentos: tuple) -> str:
        if len(argumentos) != 1:
            raise ErrorTraduccion("Falta a quién atacar.")
        etiqueta = argumentos[0]
        id_instancia = self._etiquetas.resolver(etiqueta)
        if id_instancia is None:
            raise ErrorTraduccion(f"'{etiqueta}' no corresponde a ningún enemigo visible.")
        return id_instancia

    def _id_objeto(self, argumentos: tuple) -> int:
        if len(argumentos) != 1:
            raise ErrorTraduccion("Falta el objeto sobre el que actuar.")
        # ObjetoVisible.id_objeto YA es el id de instancia real: no hace falta
        # un mapa como el de enemigos (O(1)).
        return int(argumentos[0])

    def _sin_argumentos(self, verbo: str, argumentos: tuple) -> None:
        if len(argumentos) != 0:
            raise ErrorTraduccion(f"'{verbo}' no espera argumentos.")
