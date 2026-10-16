"""VistaArcade: la implementación real de VistaJuego con pyarcade (§6).

Decisiones ya resueltas y ahora implementadas aquí (ver DECISIONES.md):

- "Cola de comandos" (D43): pyarcade nunca bloquea esperando una tecla, así
  que cada tecla que el jugador presiona se encola como Comando en una Cola
  interna; pedir_comando() saca el siguiente si hay uno, o devuelve None.

- "Dueño del bucle" (D44): el Controlador sigue siendo quien tiene el bucle
  principal; nunca se llama arcade.run(). En cambio, actualizar() bombea a
  mano los eventos pendientes de la ventana (equivalente a una vuelta de lo
  que arcade.run() haría solo) cada vez que el Controlador la llama.

- "Las teclas son de cada pantalla" (D45): esta clase no sabe qué tecla
  significa qué -- cada pantalla (PantallaMenu, PantallaJuego,
  PantallaPuntajes, PantallaFin) decide las suyas. Lo único que
  VistaArcade hace es cambiar de pantalla y sacar comandos de la cola.

Ya no queda ninguna pantalla de relleno: las 4 pantallas reales de §10.2
están construidas (Menú: Paso 4; Juego: Pasos 5a/5b; Puntajes: Paso 6;
Fin: Paso 7).
"""
from __future__ import annotations

import arcade

from ..modelo.estructuras.cola import Cola
from .pantallaBase import _PantallaCripta
from .pantallaFin import PantallaFin
from .pantallaJuego import PantallaJuego
from .pantallaMenu import PantallaMenu
from .pantallaPuntajes import PantallaPuntajes
from .vistaJuego import VistaJuego


class VistaArcade(VistaJuego):

    def __init__(self, ancho: int = 800, alto: int = 600, titulo: str = "Cripta",
                 visible: bool = True):
        self._comandos = Cola()
        self._ventana = arcade.Window(ancho, alto, titulo, visible=visible)
        self._pantalla_actual = None
        self._ultimo_estado = None      # para animar lo que cambió entre turnos

    @property
    def ventana(self) -> arcade.Window:
        """Expuesta solo para que las pruebas y el bootstrap (main.py) puedan
        inspeccionarla/cerrarla; el Controlador nunca la toca -- solo conoce
        la interfaz VistaJuego."""
        return self._ventana

    def cerrar(self) -> None:
        self._ventana.close()

    # -- VistaJuego --

    def actualizar(self) -> None:
        """Una vuelta manual del bombeo de eventos: atiende teclado/cierre de
        ventana (dispatch_events) y vuelve a dibujar la pantalla actual
        (on_draw + flip). No bloquea, no espera nada."""
        self._ventana.switch_to()
        self._ventana.dispatch_events()
        self._ventana.dispatch_event("on_draw")
        self._ventana.flip()

    def pedir_comando(self):
        if self._comandos.esta_vacia():
            return None
        return self._comandos.desencolar()

    def mostrar_estado(self, estado) -> None:
        self._mostrar(PantallaJuego(self, estado, self._ultimo_estado))
        self._ultimo_estado = estado

    def mostrar_mensajes(self, mensajes) -> None:
        """PantallaJuego ya dibuja estado.mensajes completo en cada
        mostrar_estado; esto solo cubre los avisos que NO traen un estado
        nuevo detrás (p. ej. "Partida guardada en ...")."""
        self._avisar(" ".join(mensajes))

    def mostrar_menu(self, criptas) -> None:
        self._ultimo_estado = None
        self._mostrar(PantallaMenu(self, criptas))

    def mostrar_puntajes(self, puntajes) -> None:
        self._mostrar(PantallaPuntajes(self, puntajes))

    def mostrar_fin(self, resultado) -> None:
        self._ultimo_estado = None
        self._mostrar(PantallaFin(self, resultado))

    def mostrar_error(self, mensaje: str) -> None:
        """Se dibuja sobre la pantalla actual sin cambiar de pantalla. Solo
        PantallaJuego tiene dónde mostrarlo; en las demás se ignora."""
        self._avisar(mensaje)

    # -- internos --

    def _avisar(self, texto: str) -> None:
        if texto and isinstance(self._pantalla_actual, PantallaJuego):
            self._pantalla_actual.mostrar_aviso(texto)

    def _mostrar(self, pantalla: _PantallaCripta) -> None:
        self._pantalla_actual = pantalla
        self._ventana.show_view(pantalla)

    def _encolar(self, comando) -> None:
        """Las pantallas llaman esto, no al revés: cada una sabe traducir
        sus propias teclas a un Comando, pero ninguna conoce la Cola -- solo
        VistaArcade."""
        self._comandos.encolar(comando)