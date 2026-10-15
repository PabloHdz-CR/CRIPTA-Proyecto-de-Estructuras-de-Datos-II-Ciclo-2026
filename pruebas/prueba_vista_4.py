"""Prueba de PantallaMenu (Paso 4) (§10.2).

Corre con ventana real (xvfb-run en un servidor sin pantalla, ver
ejecutar_pruebas.py). Confirma: el cursor se mueve con las flechas sin salir
de rango, ENTER arma el Comando "jugar" con el id de la cripta seleccionada
(no con su nombre ni su posición), "P" pide puntajes, ESCAPE sigue
funcionando igual que en cualquier pantalla, y una lista vacía de criptas no
revienta ni deja elegir nada.
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import CriptaVisible
from cripta.vista.vistaArcade import VistaArcade
from cripta.vista.pantallaMenu import PantallaMenu


def _criptas_de_prueba() -> ListaEnlazada:
    criptas = ListaEnlazada()
    criptas.agregar_al_final(CriptaVisible(id="c1", nombre="La Entrada", salas=5, dificultad=1))
    criptas.agregar_al_final(CriptaVisible(id="c2", nombre="El Pozo", salas=12, dificultad=3))
    criptas.agregar_al_final(CriptaVisible(id="c3", nombre="El Abismo", salas=30, dificultad=5))
    return criptas


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    vista.mostrar_menu(_criptas_de_prueba())
    pantalla = vista._pantalla_actual
    assert isinstance(pantalla, PantallaMenu)
    assert vista.ventana.current_view is pantalla
    vista.actualizar()

    # 1. Empieza en la primera cripta
    assert pantalla.indice_seleccionado == 0

    # 2. Flechas mueven el cursor, sin salir del rango (clampa, no da la vuelta)
    pantalla.on_key_press(arcade.key.UP, 0)
    assert pantalla.indice_seleccionado == 0          # ya estaba en el primero
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert pantalla.indice_seleccionado == 1
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert pantalla.indice_seleccionado == 2
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert pantalla.indice_seleccionado == 2          # ya estaba en el último
    vista.actualizar()                                # redibuja con el cursor movido

    # moverse no encola ningún Comando por sí solo
    assert vista.pedir_comando() is None

    # 3. ENTER arma "jugar" con el id de la cripta seleccionada (c3: "El Abismo")
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("jugar", ("c3",))
    assert vista.pedir_comando() is None

    # 4. Volver arriba y confirmar que selecciona la cripta correcta (no
    # siempre la misma): c1, no c3
    pantalla.on_key_press(arcade.key.UP, 0)
    pantalla.on_key_press(arcade.key.UP, 0)
    assert pantalla.indice_seleccionado == 0
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("jugar", ("c1",))

    # 5. "P" pide puntajes, sin tocar el cursor
    pantalla.on_key_press(arcade.key.P, 0)
    assert vista.pedir_comando() == Comando("ver_puntajes")
    assert pantalla.indice_seleccionado == 0

    # 6. ESCAPE sigue funcionando igual que en cualquier pantalla
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")

    # 7. Sin criptas: no revienta, ENTER/flechas/P no hacen nada
    vista.mostrar_menu(ListaEnlazada())
    pantalla_vacia = vista._pantalla_actual
    assert pantalla_vacia.indice_seleccionado == -1
    vista.actualizar()
    pantalla_vacia.on_key_press(arcade.key.DOWN, 0)
    pantalla_vacia.on_key_press(arcade.key.ENTER, 0)
    pantalla_vacia.on_key_press(arcade.key.P, 0)
    assert vista.pedir_comando() is None
    # pero ESCAPE sigue sirviendo para salir
    pantalla_vacia.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")
finally:
    vista.cerrar()

print("Sección vista_4 (PantallaMenu) OK")