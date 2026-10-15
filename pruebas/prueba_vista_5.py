"""Prueba de PantallaJuego (Paso 5a) (§10.2).

Corre con ventana real (xvfb-run en un servidor sin pantalla). Confirma: las
4 salidas se describen bien (abierta/cerrada con llave/sin salida/no hay
salida en esa dirección), enemigos/objetos/efectos/inventario se listan
(o dicen "ninguno"/"vacío" cuando no hay), el objeto bajo el cursor del
inventario se marca y el equipado se etiqueta, y las flechas/espacio arman
los Comando correctos (no se reinterpretan como en el Menú).
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    ActorVisible, EfectoVisible, EstadoVista, InventarioVisible,
    JugadorVisible, ObjetoVisible, SalaVisible, SalidaVisible,
    SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE, SALIDA_SIN_SALIDA)
from cripta.vista.pantallaJuego import PantallaJuego
from cripta.vista.vistaArcade import VistaArcade


def _estado_completo() -> EstadoVista:
    enemigos = ListaEnlazada()
    enemigos.agregar_al_final(ActorVisible("Rata gigante #1", 15, 20))
    objetos_suelo = ListaEnlazada()
    objetos_suelo.agregar_al_final(ObjetoVisible(100, "Antorcha vieja", "herramienta", 1, 2))
    sala = SalaVisible(
        nombre="Entrada",
        salidas=(SalidaVisible("N", SALIDA_ABIERTA),
                 SalidaVisible("S", SALIDA_CERRADA_CON_LLAVE),
                 SalidaVisible("E", SALIDA_SIN_SALIDA),
                 None),
        enemigos=enemigos, objetos=objetos_suelo,
    )
    jugador = JugadorVisible(vida=18, vida_max=20, ataque_efectivo=10,
                              defensa_efectiva=2, velocidad=100,
                              antorcha_encendida=True, acciones=5,
                              enemigos_derrotados=1)
    inv_objetos = ListaEnlazada()
    inv_objetos.agregar_al_final(ObjetoVisible(1, "Escudo", "armadura", 4, 8, equipado=True))
    inv_objetos.agregar_al_final(ObjetoVisible(2, "Poción", "pocion", 1, 5))
    inventario = InventarioVisible(objetos=inv_objetos, indice_actual=1,
                                    capacidad=8, cantidad_pergaminos=0)
    efectos = ListaEnlazada()
    efectos.agregar_al_final(EfectoVisible("veneno", "Envenenado (2 pulsos)"))
    mensajes = ListaEnlazada()
    mensajes.agregar_al_final("Entras a Entrada.")
    return EstadoVista(id_cripta="c1", version_cripta="v1", reloj=10,
                        terminada=False, resultado=None, jugador=jugador,
                        sala=sala, efectos=efectos, inventario=inventario,
                        mensajes=mensajes)


def _estado_vacio() -> EstadoVista:
    jugador = JugadorVisible(vida=20, vida_max=20, ataque_efectivo=10,
                              defensa_efectiva=2, velocidad=100,
                              antorcha_encendida=False, acciones=0,
                              enemigos_derrotados=0)
    sala = SalaVisible(nombre="Sala vacía", salidas=(None, None, None, None),
                        enemigos=ListaEnlazada(), objetos=ListaEnlazada())
    inventario = InventarioVisible(objetos=ListaEnlazada(), indice_actual=-1,
                                    capacidad=8, cantidad_pergaminos=0)
    return EstadoVista(id_cripta="c1", version_cripta="v1", reloj=0,
                        terminada=False, resultado=None, jugador=jugador,
                        sala=sala, efectos=ListaEnlazada(),
                        inventario=inventario, mensajes=ListaEnlazada())


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Estado completo: cada texto dice lo que corresponde
    vista.mostrar_estado(_estado_completo())
    pantalla = vista._pantalla_actual
    assert isinstance(pantalla, PantallaJuego)
    assert vista.ventana.current_view is pantalla
    vista.actualizar()                 # no debe reventar con datos reales

    assert pantalla._texto_salidas() == (
        "Salidas: N: abierta  S: cerrada con llave  E: sin salida")
    assert pantalla._texto_enemigos() == "Enemigos: Rata gigante #1 (15/20)"
    assert pantalla._texto_objetos_suelo() == "En el suelo: Antorcha vieja"
    assert pantalla._texto_efectos() == "Efectos: Envenenado (2 pulsos)"
    # índice 1 (Poción) tiene el cursor; índice 0 (Escudo) está equipado
    assert pantalla._texto_inventario() == (
        "Inventario (2/8):  Escudo [equipado], >Poción")

    # 2. Las flechas/espacio arman los Comando de mover/esperar (no los del
    # Menú: aquí no hay cursor que mover)
    pantalla.on_key_press(arcade.key.UP, 0)
    assert vista.pedir_comando() == Comando("mover", ("N",))
    pantalla.on_key_press(arcade.key.DOWN, 0)
    assert vista.pedir_comando() == Comando("mover", ("S",))
    pantalla.on_key_press(arcade.key.LEFT, 0)
    assert vista.pedir_comando() == Comando("mover", ("O",))
    pantalla.on_key_press(arcade.key.RIGHT, 0)
    assert vista.pedir_comando() == Comando("mover", ("E",))
    pantalla.on_key_press(arcade.key.SPACE, 0)
    assert vista.pedir_comando() == Comando("esperar")
    assert vista.pedir_comando() is None

    # ESCAPE sigue funcionando igual que en cualquier pantalla
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert vista.pedir_comando() == Comando("salir")

    # 3. Estado vacío: nada revienta, y todo dice "ninguno"/"nada"/"vacío"
    vista.mostrar_estado(_estado_vacio())
    pantalla_vacia = vista._pantalla_actual
    vista.actualizar()
    assert pantalla_vacia._texto_salidas() == "Salidas: "
    assert pantalla_vacia._texto_enemigos() == "Enemigos: ninguno"
    assert pantalla_vacia._texto_objetos_suelo() == "En el suelo: nada"
    assert pantalla_vacia._texto_efectos() == "Efectos: ninguno"
    assert pantalla_vacia._texto_inventario() == "Inventario (0/8): vacío"
finally:
    vista.cerrar()

print("Sección vista_5 (PantallaJuego) OK")