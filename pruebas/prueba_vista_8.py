"""Prueba de PantallaFin (Paso 7) (§10.2).

Corre con ventana real (xvfb-run en un servidor sin pantalla). Confirma:
victoria y derrota no revientan y arman el Comando "volver" con ENTER;
ESCAPE sigue siendo "salir" (D45).
"""
import arcade

from cripta.vista.comando import Comando
from cripta.vista.estadoVista import ResultadoFinVisible
from cripta.vista.pantallaFin import PantallaFin
from cripta.vista.vistaArcade import VistaArcade

vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Victoria
    victoria = ResultadoFinVisible(resultado="victoria", acciones=40,
                                    enemigos_derrotados=5, tiempo_final=300)
    vista.mostrar_fin(victoria)
    pantalla = vista._pantalla_actual
    assert isinstance(pantalla, PantallaFin)
    assert vista.ventana.current_view is pantalla
    vista.actualizar()

    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")
    assert vista.pedir_comando() is None

    # ESCAPE sigue siendo "salir"
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")

    # 2. Derrota (no revienta con el otro caso)
    derrota = ResultadoFinVisible(resultado="derrota", acciones=12,
                                   enemigos_derrotados=1, tiempo_final=90)
    vista.mostrar_fin(derrota)
    vista.actualizar()
    pantalla_derrota = vista._pantalla_actual
    pantalla_derrota.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")
finally:
    vista.cerrar()

print("Sección vista_8 (PantallaFin) OK")