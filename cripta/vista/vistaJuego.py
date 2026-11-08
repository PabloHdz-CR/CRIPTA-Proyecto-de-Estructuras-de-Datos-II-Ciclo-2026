"""VistaJuego: la interfaz que debe implementar cualquier Vista (§6).

El Controlador solo conoce esta interfaz, nunca una implementación concreta
(VistaArcade, VistaNula...): así --replay y --bench pueden correr con
VistaNula sin que el Controlador sepa la diferencia.

pedir_comando() NO bloquea (ver DECISIONES.md, entrada de pyarcade): una
Vista con un bucle propio (como pyarcade, que nunca para a esperar input())
junta los Comando que el jugador va generando en una cola interna, y
pedir_comando() saca el siguiente si hay uno, o devuelve None si no. El
Controlador debe tratar None como "todavía no hay decisión" y seguir su
propio bucle (dibujar, atender eventos) en vez de quedarse esperando.

El Controlador es SIEMPRE el dueño del bucle (ver DECISIONES.md, entrada
"dueño del bucle"): nunca se llama arcade.run(). Por eso existe
actualizar(): en cada vuelta del bucle del Controlador, antes de pedir el
próximo comando, se llama actualizar() para que la Vista atienda lo que
tenga que atender una sola vez (en VistaArcade: bombear los eventos
pendientes de la ventana -- teclado, redibujado -- sin bloquear; en
VistaNula: no hacer nada, no hay ventana). Así una misma Vista real puede
correr dentro del bucle del Controlador sin que éste sepa si hay una
ventana de verdad detrás o no.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class VistaJuego(ABC):

    @abstractmethod
    def mostrar_estado(self, estado) -> None:
        """estado: EstadoVista. Redibuja la pantalla de juego completa."""

    @abstractmethod
    def mostrar_mensajes(self, mensajes) -> None:
        """mensajes: ListaEnlazada de texto (los que produjo la última
        acción). Puede ser una notificación incremental, sin redibujar
        mostrar_estado entero."""

    @abstractmethod
    def pedir_comando(self):
        """Devuelve el próximo Comando ya decidido por el jugador, o None si
        todavía no hay ninguno. NUNCA bloquea."""

    @abstractmethod
    def mostrar_menu(self, criptas) -> None:
        """criptas: ListaEnlazada de CriptaVisible."""

    @abstractmethod
    def mostrar_puntajes(self, puntajes) -> None:
        """puntajes: ListaEnlazada de PuntajeVisible, ya en el orden que
        decidió el Controlador (ConstructorEstadoVista/TablaPuntajes)."""

    @abstractmethod
    def mostrar_fin(self, resultado) -> None:
        """resultado: ResultadoFinVisible."""

    @abstractmethod
    def mostrar_error(self, mensaje: str) -> None:
        """Un rechazo de ResultadoAccion, o cualquier error que el jugador
        deba ver (p. ej. 'no se puede garantizar la reproducción fiel')."""

    # DECISIÓN: estos dos NO son abstractos: una Vista que no los tenga (las
    # Vistas de prueba, VistaNula) simplemente no muestra nada, y el menú
    # sigue funcionando.
    def mostrar_benchmark(self, resultado) -> None:
        """resultado: BenchmarkVisible (las mediciones de --bench)."""

    def mostrar_titulo(self) -> None:
        """La pantalla de bienvenida, antes del menú. Su ENTER manda
        Comando("entrar")."""

    def mostrar_nombre_jugador(self, nombre: str) -> None:
        """El nombre con el que se va a jugar, para que el menú lo muestre.
        El Controlador lo manda antes de cada mostrar_menu."""

    def mostrar_resolubilidad(self, reporte) -> None:
        """reporte: ReporteResolubilidadVisible. La pantalla de reporte antes
        de una partida en una cripta no resoluble (003-resolubilidad, FR-019,
        FR-020): ENTER manda "volver" o, si reporte.puede_continuar,
        "aceptar_resolubilidad"; ESC manda "volver"."""

    def mostrar_espera(self, texto: str) -> None:
        """Un aviso mientras el Controlador hace algo que tarda (p. ej. el
        benchmark). La próxima pantalla lo reemplaza."""

    @abstractmethod
    def actualizar(self) -> None:
        """Se llama una vez por vuelta del bucle del Controlador, antes de
        pedir_comando(). No bloquea ni avanza el juego: solo le da a la
        Vista la oportunidad de atender lo suyo (en VistaArcade, bombear los
        eventos pendientes de la ventana). En VistaNula no hace nada."""