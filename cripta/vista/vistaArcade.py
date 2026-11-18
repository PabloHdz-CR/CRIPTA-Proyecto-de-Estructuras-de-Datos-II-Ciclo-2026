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
from . import texturas
from .pantallaBase import _PantallaCripta
from .pantallaBenchmark import PantallaBenchmark, PantallaEspera
from .pantallaFin import PantallaFin
from .pantallaJuego import PantallaJuego
from .pantallaMenu import PantallaMenu
from .pantallaPuntajes import PantallaPuntajes
from .pantallaResolubilidad import PantallaResolubilidad
from .pantallaTitulo import PantallaTitulo
from .vistaJuego import VistaJuego


class VistaArcade(VistaJuego):

    def __init__(self, ancho: int = 800, alto: int = 600, titulo: str = "Cripta",
                 visible: bool = True):
        self._comandos = Cola()
        self._ventana = arcade.Window(ancho, alto, titulo, visible=visible)
        self._pantalla_actual = None
        self._ultimo_estado = None      # para animar lo que cambió entre turnos
        self._nombre_jugador = "Jugador" # lo manda el Controlador; lo muestra el menú
        # DECISIÓN: la skin del héroe es una preferencia de PRESENTACIÓN: la
        # elige el jugador en el menú y solo la usa la Vista para dibujar.
        # El Modelo y el Controlador no la conocen (no cambia el juego).
        self._skin = texturas.SKIN_POR_DEFECTO
        # Si la bitácora se ve completa (últimos 20 mensajes) o resumida: se
        # mantiene entre turnos (cada turno trae una PantallaJuego nueva).
        self._bitacora_completa = False
        # 003-resolubilidad: si el panel del reporte (tecla V) está abierto.
        # Presentación pura, como la bitácora: se mantiene entre turnos y se
        # cierra al salir de la partida.
        self._panel_resolubilidad = False
        self._desplazamiento_resolubilidad = 0
        # 002-niebla-guerra: desplazamiento del panel del mapa conocido (M). Si
        # el panel está abierto lo decide el Controlador (EstadoVista.mapa); el
        # desplazamiento es presentación pura y se mantiene entre turnos.
        self._desplazamiento_mapa = 0
        # 002-niebla-guerra (FR-035): id de la sala bajo el cursor de «ir a» en
        # el panel del mapa, o None (= la primera explorada). Presentación pura.
        self._cursor_mapa = None
        # 002-niebla-guerra (FR-037): selección de objetivo pedida con el mapa
        # abierto ("soltar", "usar"...). Se abre en la pantalla siguiente, la
        # que llega con el mapa ya cerrado. Presentación pura.
        self._objetivo_pendiente = None
        # 004-linea-tiempo (FR-017): la consulta de la tecla H. Si está abierta,
        # lo escrito y el desplazamiento del resumen. Presentación pura: se
        # mantiene entre turnos (cada EstadoVista trae una PantallaJuego nueva).
        self._historia_abierta = False
        self._texto_historia = ""
        self._desplazamiento_historia = 0

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
        self._panel_resolubilidad = False
        self._desplazamiento_resolubilidad = 0
        self._desplazamiento_mapa = 0
        self._cursor_mapa = None
        self._objetivo_pendiente = None
        self.cerrar_historia()
        self._mostrar(PantallaMenu(self, criptas, self._nombre_jugador))

    def mostrar_titulo(self) -> None:
        self._ultimo_estado = None
        self._mostrar(PantallaTitulo(self))

    def mostrar_nombre_jugador(self, nombre: str) -> None:
        self._nombre_jugador = nombre

    @property
    def skin(self) -> str:
        return self._skin

    @property
    def bitacora_completa(self) -> bool:
        return self._bitacora_completa

    def alternar_bitacora(self) -> None:
        self._bitacora_completa = not self._bitacora_completa

    @property
    def panel_resolubilidad(self) -> bool:
        return self._panel_resolubilidad

    def alternar_resolubilidad(self) -> None:
        self._panel_resolubilidad = not self._panel_resolubilidad
        self._desplazamiento_resolubilidad = 0

    @property
    def desplazamiento_resolubilidad(self) -> int:
        return self._desplazamiento_resolubilidad

    def desplazar_resolubilidad(self, delta: int, maximo: int) -> None:
        """Mueve la ventana del panel de V entre 0 y 'maximo' (presentación)."""
        self._desplazamiento_resolubilidad = max(
            0, min(maximo, self._desplazamiento_resolubilidad + delta))

    @property
    def desplazamiento_mapa(self) -> int:
        return self._desplazamiento_mapa

    def desplazar_mapa(self, delta: int, maximo: int) -> None:
        """Mueve la ventana del panel del mapa entre 0 y 'maximo' (presentación)."""
        self._desplazamiento_mapa = max(0, min(maximo, self._desplazamiento_mapa + delta))

    @property
    def cursor_mapa(self):
        """Id de la sala bajo el cursor de «ir a» (None = la primera explorada)."""
        return self._cursor_mapa

    def poner_cursor_mapa(self, id_sala) -> None:
        self._cursor_mapa = id_sala

    # -- 004-linea-tiempo: consulta de la línea de tiempo (tecla H) --

    @property
    def historia_abierta(self) -> bool:
        return self._historia_abierta

    @property
    def texto_historia(self) -> str:
        return self._texto_historia

    @property
    def desplazamiento_historia(self) -> int:
        return self._desplazamiento_historia

    def abrir_historia(self) -> None:
        self._historia_abierta = True
        self._texto_historia = ""
        self._desplazamiento_historia = 0

    def cerrar_historia(self) -> None:
        self._historia_abierta = False
        self._texto_historia = ""
        self._desplazamiento_historia = 0

    def escribir_historia(self, caracter: str) -> None:
        """Solo dígitos y '#' (t o #k); como mucho 12 caracteres."""
        if (caracter.isdigit() or caracter == "#") and len(self._texto_historia) < 12:
            self._texto_historia += caracter

    def borrar_historia(self) -> None:
        self._texto_historia = self._texto_historia[:-1]

    def desplazar_historia(self, delta: int, maximo: int) -> None:
        self._desplazamiento_historia = max(0, min(maximo, self._desplazamiento_historia + delta))

    def pedir_objetivo(self, verbo: str) -> None:
        """FR-037: abrir la selección `verbo` cuando el mapa ya esté cerrado."""
        self._objetivo_pendiente = verbo

    def tomar_objetivo_pendiente(self):
        """La selección pendiente (y la olvida), o None."""
        verbo = self._objetivo_pendiente
        self._objetivo_pendiente = None
        return verbo

    def cambiar_skin(self, id_skin: str) -> None:
        """Lo llama el menú (presentación pura, no pasa por la Cola)."""
        self._skin = id_skin

    def mostrar_resolubilidad(self, reporte) -> None:
        self._ultimo_estado = None
        self._panel_resolubilidad = False
        self._desplazamiento_resolubilidad = 0
        self._mostrar(PantallaResolubilidad(self, reporte))

    def mostrar_benchmark(self, resultado) -> None:
        self._mostrar(PantallaBenchmark(self, resultado))

    def mostrar_espera(self, texto: str) -> None:
        self._mostrar(PantallaEspera(self, texto))

    def mostrar_puntajes(self, puntajes) -> None:
        self._mostrar(PantallaPuntajes(self, puntajes))

    def mostrar_fin(self, resultado) -> None:
        self._ultimo_estado = None
        self._panel_resolubilidad = False
        self._desplazamiento_resolubilidad = 0
        self._mostrar(PantallaFin(self, resultado))

    def mostrar_error(self, mensaje: str) -> None:
        """Se dibuja sobre la pantalla actual sin cambiar de pantalla. Las
        pantallas que tienen dónde mostrarlo (juego y menú) definen
        mostrar_aviso; en las demás se ignora."""
        self._avisar(mensaje)

    # -- internos --

    def _avisar(self, texto: str) -> None:
        if texto and isinstance(self._pantalla_actual, (PantallaJuego, PantallaMenu)):
            self._pantalla_actual.mostrar_aviso(texto)

    def _mostrar(self, pantalla: _PantallaCripta) -> None:
        self._pantalla_actual = pantalla
        self._ventana.show_view(pantalla)

    def _encolar(self, comando) -> None:
        """Las pantallas llaman esto, no al revés: cada una sabe traducir
        sus propias teclas a un Comando, pero ninguna conoce la Cola -- solo
        VistaArcade."""
        self._comandos.encolar(comando)