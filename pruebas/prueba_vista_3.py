"""Prueba de VistaArcade y _PantallaCripta (esqueleto de pyarcade) (§6).

Corre con ventana real de pyarcade/pyglet pero sin pantalla física (hace
falta Xvfb o un X real -- ver ejecutar_pruebas.py, que la corre con
xvfb-run). Confirma lo genérico, común a las 4 pantallas reales (cada una
se prueba aparte: Menú en prueba_vista_4.py, Juego en prueba_vista_5.py y
prueba_vista_6.py, Puntajes en prueba_vista_7.py, Fin en prueba_vista_8.py):
  - la cola de comandos: una tecla -> un Comando encolado; pedir_comando()
    lo saca una sola vez y después vuelve a dar None (nunca bloquea).
  - el cambio de pantalla: _mostrar() cambia la vista activa de la ventana
    real (arcade.Window.current_view).
  - ESCAPE -> "salir" funciona igual en cualquier pantalla que no lo
    intercepte ella misma (lo atiende _PantallaCripta, no cada pantalla por
    su cuenta), y ninguna otra tecla hace nada en una pantalla sin teclas
    propias.
  - actualizar() bombea los eventos sin reventar ni bloquear, con la ventana
    real abierta.
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.pantallaBase import _PantallaCripta
from cripta.vista.vistaArcade import VistaArcade


class _PantallaDePrueba(_PantallaCripta):
    """Una pantalla mínima, sin teclas propias: existe solo para confirmar
    el comportamiento genérico de _PantallaCripta sin depender de ninguna
    de las 4 pantallas reales."""

    def on_draw(self) -> None:
        self.clear()


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Sin ninguna tecla todavía, pedir_comando() no inventa nada
    assert vista.pedir_comando() is None

    # 2. _mostrar() cambia la pantalla activa de la ventana real
    pantalla = _PantallaDePrueba(vista)
    vista._mostrar(pantalla)
    assert vista.ventana.current_view is pantalla
    assert vista._pantalla_actual is pantalla
    vista.actualizar()                 # bombea de verdad, no debe reventar

    # 3. Sin teclas propias, solo ESCAPE hace algo (lo atiende la clase base)
    pantalla.on_key_press(arcade.key.UP, 0)
    pantalla.on_key_press(arcade.key.SPACE, 0)
    pantalla.on_key_press(arcade.key.Z, 0)
    assert vista.pedir_comando() is None        # ninguna de esas encoló nada

    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")
    assert vista.pedir_comando() is None        # una sola vez, no se repite

    # 4. mostrar_mensajes y mostrar_error no cambian de pantalla ni revientan
    pantalla_antes = vista._pantalla_actual
    vista.mostrar_mensajes(ListaEnlazada())
    vista.mostrar_error("algo salió mal")
    assert vista._pantalla_actual is pantalla_antes
finally:
    vista.cerrar()

print("Sección vista_3 (VistaArcade, esqueleto de pyarcade) OK")