"""Prueba de PantallaPuntajes (Paso 6) (§10.2).

Corre con ventana real (xvfb-run en un servidor sin pantalla). Confirma: con
la tabla vacía no revienta (y lo dice en vez de mostrar una tabla vacía
confusa), con datos arma una fila por puntaje en el mismo orden en que
llegó la ListaEnlazada (el orden ya lo decidió el Controlador, Vista no
reordena nada), y ENTER arma "volver" mientras que ESCAPE sigue siendo
"salir" (D45).
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import PuntajeVisible
from cripta.vista.pantallaPuntajes import PantallaPuntajes
from cripta.vista.vistaArcade import VistaArcade


def _puntajes_de_prueba() -> ListaEnlazada:
    puntajes = ListaEnlazada()
    puntajes.agregar_al_final(PuntajeVisible(
        nombre="Ana", id_cripta="c1", version_cripta="v1", acciones=40,
        enemigos_derrotados=5, tiempo_final=300, resultado="victoria"))
    puntajes.agregar_al_final(PuntajeVisible(
        nombre="Beto", id_cripta="c1", version_cripta="v1", acciones=12,
        enemigos_derrotados=1, tiempo_final=90, resultado="derrota"))
    return puntajes


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Con datos: una fila por puntaje, en el orden recibido
    vista.mostrar_puntajes(_puntajes_de_prueba())
    pantalla = vista._pantalla_actual
    assert isinstance(pantalla, PantallaPuntajes)
    assert vista.ventana.current_view is pantalla
    vista.actualizar()

    assert "Ana" in pantalla._texto_fila(pantalla._puntajes.obtener(0))
    assert "victoria" in pantalla._texto_fila(pantalla._puntajes.obtener(0))
    assert "Beto" in pantalla._texto_fila(pantalla._puntajes.obtener(1))
    assert "derrota" in pantalla._texto_fila(pantalla._puntajes.obtener(1))

    # 2. ENTER vuelve al menú ("volver"), no sale del juego
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")
    assert vista.pedir_comando() is None

    # ESCAPE sigue siendo "salir", igual que en cualquier pantalla
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")

    # 3. Sin puntajes guardados: no revienta
    vista.mostrar_puntajes(ListaEnlazada())
    vista.actualizar()
    pantalla_vacia = vista._pantalla_actual
    pantalla_vacia.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")
finally:
    vista.cerrar()

print("Sección vista_7 (PantallaPuntajes) OK")