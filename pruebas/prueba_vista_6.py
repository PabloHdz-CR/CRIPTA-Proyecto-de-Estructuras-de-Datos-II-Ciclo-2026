"""Prueba del modo objetivo de PantallaJuego (Paso 5b) (§10.2).

Corre con ventana real (xvfb-run en un servidor sin pantalla). Confirma:
  - A/U/Q/S entran a modo objetivo con la lista correcta (enemigos para
    atacar, inventario para usar/equipar/soltar); si esa lista está vacía,
    no entra a ningún modo ni revienta.
  - Dentro de modo objetivo, las flechas mueven el cursor sin salir de
    rango, y ENTER arma el Comando correcto: "atacar" con la ETIQUETA del
    enemigo (no su posición), "usar"/"equipar"/"soltar" con el ID_OBJETO
    real del objeto (no su nombre).
  - ESCAPE en modo objetivo cancela y vuelve a modo normal SIN encolar
    "salir" (a diferencia de ESCAPE en modo normal, que sí sale).
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    ActorVisible, EstadoVista, InventarioVisible, JugadorVisible,
    ObjetoVisible, SalaVisible)
from cripta.vista.vistaArcade import VistaArcade


def _jugador() -> JugadorVisible:
    return JugadorVisible(vida=20, vida_max=20, ataque_efectivo=10,
                           defensa_efectiva=2, velocidad=100,
                           antorcha_encendida=False, acciones=0,
                           enemigos_derrotados=0)


def _estado_con_enemigos_e_inventario() -> EstadoVista:
    enemigos = ListaEnlazada()
    enemigos.agregar_al_final(ActorVisible("Rata gigante #1", 15, 20))
    enemigos.agregar_al_final(ActorVisible("Esqueleto #1", 8, 10))
    sala = SalaVisible(nombre="Entrada", salidas=(None, None, None, None),
                        enemigos=enemigos, objetos=ListaEnlazada())
    inv_objetos = ListaEnlazada()
    inv_objetos.agregar_al_final(ObjetoVisible(1, "Escudo", "armadura", 4, 8, equipado=True))
    inv_objetos.agregar_al_final(ObjetoVisible(2, "Poción", "pocion", 1, 5))
    inventario = InventarioVisible(objetos=inv_objetos, indice_actual=0,
                                    capacidad=8, cantidad_pergaminos=0)
    return EstadoVista(id_cripta="c1", version_cripta="v1", reloj=0,
                        terminada=False, resultado=None, jugador=_jugador(),
                        sala=sala, efectos=ListaEnlazada(),
                        inventario=inventario, mensajes=ListaEnlazada())


def _estado_sin_enemigos_ni_inventario() -> EstadoVista:
    sala = SalaVisible(nombre="Sala vacía", salidas=(None, None, None, None),
                        enemigos=ListaEnlazada(), objetos=ListaEnlazada())
    inventario = InventarioVisible(objetos=ListaEnlazada(), indice_actual=-1,
                                    capacidad=8, cantidad_pergaminos=0)
    return EstadoVista(id_cripta="c1", version_cripta="v1", reloj=0,
                        terminada=False, resultado=None, jugador=_jugador(),
                        sala=sala, efectos=ListaEnlazada(),
                        inventario=inventario, mensajes=ListaEnlazada())


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    vista.mostrar_estado(_estado_con_enemigos_e_inventario())
    pantalla = vista._pantalla_actual
    vista.actualizar()
    assert pantalla.modo == "normal"

    # 1. 'A' entra a modo objetivo apuntando a los enemigos
    pantalla.on_key_press(arcade.key.A, 0)
    assert pantalla.modo == "objetivo"
    assert pantalla.verbo_objetivo == "atacar"
    assert pantalla.cursor_objetivo == 0
    vista.actualizar()

    # 2. Las flechas mueven el cursor sin salirse de rango (solo 2 enemigos)
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert pantalla.cursor_objetivo == 1
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert pantalla.cursor_objetivo == 1          # ya estaba en el último

    # 3. ENTER arma "atacar" con la ETIQUETA del enemigo bajo el cursor
    # (índice 1: "Esqueleto #1"), y vuelve a modo normal
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("atacar", ("Esqueleto #1",))
    assert pantalla.modo == "normal"
    assert vista.pedir_comando() is None
    vista.actualizar()

    # 4. 'U' entra a modo objetivo apuntando al inventario; ESCAPE cancela
    # SIN encolar "salir" (a diferencia del modo normal)
    pantalla.on_key_press(arcade.key.U, 0)
    assert pantalla.modo == "objetivo"
    assert pantalla.verbo_objetivo == "usar"
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert pantalla.modo == "normal"
    assert vista.pedir_comando() is None          # no encoló "salir"

    # ESCAPE en modo normal sí encola "salir" (el comportamiento de siempre)
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")

    # 5. 'Q' (equipar) y 'S' (soltar) arman el Comando con el ID_OBJETO real
    # del objeto bajo el cursor, no con su nombre ni su posición
    pantalla.on_key_press(arcade.key.Q, 0)
    assert pantalla.verbo_objetivo == "equipar"
    pantalla.on_key_press(arcade.key.DOWN, 0)     # cursor a "Poción" (id_objeto=2)
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("equipar", (2,))

    pantalla.on_key_press(arcade.key.S, 0)
    assert pantalla.verbo_objetivo == "soltar"
    assert pantalla.cursor_objetivo == 0          # cada vez que se entra, arranca en 0
    pantalla.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("soltar", (1,))   # "Escudo"

    # 6. Sin enemigos ni inventario: A/U/Q/S no hacen nada, sigue en modo normal
    vista.mostrar_estado(_estado_sin_enemigos_ni_inventario())
    pantalla_vacia = vista._pantalla_actual
    vista.actualizar()
    pantalla_vacia.on_key_press(arcade.key.A, 0)
    assert pantalla_vacia.modo == "normal"
    pantalla_vacia.on_key_press(arcade.key.U, 0)
    assert pantalla_vacia.modo == "normal"
    pantalla_vacia.on_key_press(arcade.key.Q, 0)
    assert pantalla_vacia.modo == "normal"
    pantalla_vacia.on_key_press(arcade.key.S, 0)
    assert pantalla_vacia.modo == "normal"
    assert vista.pedir_comando() is None
finally:
    vista.cerrar()

print("Sección vista_6 (PantallaJuego, modo objetivo) OK")