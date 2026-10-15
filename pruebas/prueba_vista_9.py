"""Prueba de integración de Vista completa (Paso 8) (§6, §10.2).

Simula el ciclo de vida completo que haría el Controlador, llamando a los 7
métodos de VistaJuego en el orden real de una partida: Menú -> elegir
cripta -> Juego -> moverse/atacar -> fin de la partida -> volver al Menú ->
ver puntajes -> volver al Menú. En cada paso confirma que VistaArcade
cambió a la pantalla real correspondiente (ya no quedan pantallas de
relleno en ningún mostrar_*) y que actualizar() nunca revienta, sin
importar en qué pantalla esté.
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    ActorVisible, CriptaVisible, EstadoVista, InventarioVisible,
    JugadorVisible, PuntajeVisible, ResultadoFinVisible, SalaVisible)
from cripta.vista.pantallaFin import PantallaFin
from cripta.vista.pantallaJuego import PantallaJuego
from cripta.vista.pantallaMenu import PantallaMenu
from cripta.vista.pantallaPuntajes import PantallaPuntajes
from cripta.vista.vistaArcade import VistaArcade


def _estado_de_prueba() -> EstadoVista:
    enemigos = ListaEnlazada()
    enemigos.agregar_al_final(ActorVisible("Rata gigante #1", 15, 20))
    sala = SalaVisible(nombre="Entrada", salidas=(None, None, None, None),
                        enemigos=enemigos, objetos=ListaEnlazada())
    jugador = JugadorVisible(vida=20, vida_max=20, ataque_efectivo=10,
                              defensa_efectiva=2, velocidad=100,
                              antorcha_encendida=False, acciones=0,
                              enemigos_derrotados=0)
    inventario = InventarioVisible(objetos=ListaEnlazada(), indice_actual=-1,
                                    capacidad=8, cantidad_pergaminos=0)
    return EstadoVista(id_cripta="c1", version_cripta="v1", reloj=0,
                        terminada=False, resultado=None, jugador=jugador,
                        sala=sala, efectos=ListaEnlazada(),
                        inventario=inventario, mensajes=ListaEnlazada())


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Menú: el jugador elige la única cripta disponible
    criptas = ListaEnlazada()
    criptas.agregar_al_final(CriptaVisible(id="c1", nombre="La Entrada", salas=5, dificultad=1))
    vista.mostrar_menu(criptas)
    assert isinstance(vista._pantalla_actual, PantallaMenu)
    vista.actualizar()
    vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("jugar", ("c1",))

    # 2. El Controlador reacciona mostrando el primer estado de la partida
    vista.mostrar_estado(_estado_de_prueba())
    assert isinstance(vista._pantalla_actual, PantallaJuego)
    vista.actualizar()
    pantalla_juego = vista._pantalla_actual
    pantalla_juego.on_key_press(arcade.key.A, 0)       # atacar
    pantalla_juego.on_key_press(arcade.key.ENTER, 0)   # al único enemigo
    assert vista.pedir_comando() == Comando("atacar", ("Rata gigante #1",))
    vista.actualizar()

    # 3. La partida termina: victoria
    resultado = ResultadoFinVisible(resultado="victoria", acciones=5,
                                     enemigos_derrotados=1, tiempo_final=20)
    vista.mostrar_fin(resultado)
    assert isinstance(vista._pantalla_actual, PantallaFin)
    vista.actualizar()
    vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")

    # 4. El Controlador vuelve al Menú (misma cripta sigue disponible)
    vista.mostrar_menu(criptas)
    assert isinstance(vista._pantalla_actual, PantallaMenu)
    assert vista._pantalla_actual.indice_seleccionado == 0   # arranca de cero otra vez
    vista.actualizar()
    vista._pantalla_actual.on_key_press(arcade.key.P, 0)
    assert vista.pedir_comando() == Comando("ver_puntajes")

    # 5. Puntajes, con el resultado recién jugado adentro
    puntajes = ListaEnlazada()
    puntajes.agregar_al_final(PuntajeVisible(
        nombre="Diego", id_cripta="c1", version_cripta="v1", acciones=5,
        enemigos_derrotados=1, tiempo_final=20, resultado="victoria"))
    vista.mostrar_puntajes(puntajes)
    assert isinstance(vista._pantalla_actual, PantallaPuntajes)
    vista.actualizar()
    vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
    assert vista.pedir_comando() == Comando("volver")

    # 6. De vuelta al Menú, una vez más
    vista.mostrar_menu(criptas)
    assert isinstance(vista._pantalla_actual, PantallaMenu)
    vista.actualizar()

    # 7. mostrar_mensajes/mostrar_error no rompen el ciclo en ningún punto
    vista.mostrar_mensajes(ListaEnlazada())
    vista.mostrar_error("prueba de error")
    assert isinstance(vista._pantalla_actual, PantallaMenu)
finally:
    vista.cerrar()

print("Sección vista_9 (integración completa de Vista) OK")