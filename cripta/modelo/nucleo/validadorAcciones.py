"""Precondiciones de las acciones del jugador (§2.5, Apéndice B).

Es de solo lectura: nunca modifica el estado. Devuelve el motivo del rechazo
(texto) o None si la acción es válida. Que el contenido de la sala destino esté
en memoria NO se rechaza aquí: Partida lo asegura (esperando la red sin mover
el reloj) antes de confirmar el movimiento.
"""
from __future__ import annotations

from .accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar,
    UsarPergamino)


class ValidadorAcciones:
    def validar(self, partida, accion):
        # DECISIÓN: isinstance en cadena y no un dict clase -> función (§3). El validador
        # SOLO LEE: así un rechazo no puede dejar el estado a medias (Apéndice B).
        if isinstance(accion, Mover):
            return self._mover(partida, accion)
        if isinstance(accion, AbrirPuerta):
            return self._abrir(partida, accion)
        if isinstance(accion, Atacar):
            return self._atacar(partida, accion)
        if isinstance(accion, Recoger):
            return self._recoger(partida, accion)
        if isinstance(accion, Soltar):
            return self._objeto_en_inventario(partida, accion.id_objeto)
        if isinstance(accion, Usar):
            return self._usar(partida, accion)
        if isinstance(accion, Equipar):
            return self._equipar(partida, accion)
        if isinstance(accion, UsarPergamino):
            return self._pergamino(partida)
        if isinstance(accion, Esperar):
            return None
        return f"Acción desconocida: {accion!r}"

    def _sala_actual(self, partida):
        return partida.mundo.sala(partida.jugador.sala)

    def _mover(self, partida, accion):
        salida = self._sala_actual(partida).salida(accion.direccion)
        if salida is None:
            return f"No hay salida hacia el {accion.direccion}."
        if not salida.transitable():
            return f"La puerta hacia el {accion.direccion} está cerrada."
        return None

    def _abrir(self, partida, accion):
        salida = self._sala_actual(partida).salida(accion.direccion)
        if salida is None:
            return f"No hay salida hacia el {accion.direccion}."
        if not salida.cerrada:
            return "La puerta ya está abierta."
        if not salida.se_abre_con_llave():
            return "Esta puerta no se puede abrir."
        if partida.jugador.inventario.buscar_llave(salida.llave) is None:
            return "No tienes la llave correcta."
        return None

    def _atacar(self, partida, accion):
        if self._sala_actual(partida).buscar_enemigo(accion.objetivo) is None:
            return "Ese enemigo no está en esta sala."
        return None

    def _recoger(self, partida, accion):
        if self._sala_actual(partida).buscar_objeto(accion.id_objeto) is None:
            return "Ese objeto no está en el suelo de esta sala."
        if partida.jugador.inventario.esta_lleno():
            return "El inventario está lleno."
        return None

    def _objeto_en_inventario(self, partida, id_objeto):
        if partida.jugador.inventario.buscar(id_objeto) is None:
            return "Ese objeto no está en tu inventario."
        return None

    def _usar(self, partida, accion):
        motivo = self._objeto_en_inventario(partida, accion.id_objeto)
        if motivo is not None:
            return motivo
        if not partida.jugador.inventario.buscar(accion.id_objeto).es_usable():
            return "Ese objeto no se puede usar así."
        return None

    def _equipar(self, partida, accion):
        motivo = self._objeto_en_inventario(partida, accion.id_objeto)
        if motivo is not None:
            return motivo
        if not partida.jugador.inventario.buscar(accion.id_objeto).es_equipable():
            return "Ese objeto no se puede equipar."
        return None

    def _pergamino(self, partida):
        if partida.jugador.inventario.cantidad_pergaminos() == 0:
            return "No tienes pergaminos de retroceso."
        if not partida.puede_retroceder():
            return "No hay acciones que retroceder."
        return None