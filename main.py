"""Bootstrap de Cripta: arma la Vista real (pyarcade) y corre el bucle
principal (§10.2). El Controlador sigue siendo el dueño del bucle -- nunca
se llama arcade.run() (ver DECISIONES.md, D44).

Este archivo es el único lugar donde Vista y Controlador se conocen: Vista
no importa nada de Controlador/Modelo, y viceversa -- main.py es quien los
junta. Por eso vive en la raíz del proyecto, junto a cripta/ y pruebas/, no
dentro de ningún paquete.

TODO (Controlador, pendiente): reemplazar _DemoControlador por las clases
reales (ControladorMenu, ControladorJuego, TraductorComandos, GestorGuardado)
apenas estén listas. Mientras tanto, este demo deja correr la Vista de
punta a punta (Menú -> Juego -> Puntajes -> Menú -> salir) con datos de
mentira, para probar que todo el cableado funciona antes de que exista el
Controlador real.
"""
from __future__ import annotations

import time

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.estadoVista import (
    ActorVisible, CriptaVisible, EstadoVista, InventarioVisible,
    JugadorVisible, PuntajeVisible, SalaVisible)
from cripta.vista.vistaArcade import VistaArcade

_RITMO_SEGUNDOS = 1 / 60    # ritmo de cuadro habitual de pyarcade; evita que
                            # el bucle use 100% de un núcleo sin necesidad


class _DemoControlador:
    """Reemplazar por el Controlador real. Reacciona a los Comando que
    arma Vista (vocabulario completo en DECISIONES.md D45/D46) y decide
    qué mostrar_* llamar después -- exactamente el trabajo que harán
    ControladorMenu/ControladorJuego/TraductorComandos."""

    def __init__(self, vista):
        self._vista = vista
        self._terminado = False
        self._en_partida = False

    def iniciar(self) -> None:
        self._mostrar_menu()

    def terminado(self) -> bool:
        return self._terminado

    def procesar(self, comando) -> None:
        if comando is None:
            return
        if comando.verbo == "salir":
            self._terminado = True
        elif comando.verbo == "jugar":
            self._en_partida = True
            self._vista.mostrar_estado(self._estado_de_mentira())
        elif comando.verbo in ("mover", "esperar", "atacar", "usar", "equipar", "soltar"):
            # Acá va TraductorComandos (arma la Accion real) + Partida.ejecutar();
            # el demo solo vuelve a mostrar el mismo estado para no romper el bucle.
            if self._en_partida:
                self._vista.mostrar_estado(self._estado_de_mentira())
        elif comando.verbo == "ver_puntajes":
            self._vista.mostrar_puntajes(self._puntajes_de_mentira())
        elif comando.verbo == "volver":
            self._en_partida = False
            self._mostrar_menu()

    def _mostrar_menu(self) -> None:
        criptas = ListaEnlazada()
        criptas.agregar_al_final(
            CriptaVisible(id="demo", nombre="Cripta de prueba", salas=5, dificultad=1))
        self._vista.mostrar_menu(criptas)

    def _estado_de_mentira(self) -> EstadoVista:
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
        return EstadoVista(id_cripta="demo", version_cripta="v1", reloj=0,
                            terminada=False, resultado=None, jugador=jugador,
                            sala=sala, efectos=ListaEnlazada(),
                            inventario=inventario, mensajes=ListaEnlazada())

    def _puntajes_de_mentira(self) -> ListaEnlazada:
        puntajes = ListaEnlazada()
        puntajes.agregar_al_final(PuntajeVisible(
            nombre="Jugador de prueba", id_cripta="demo", version_cripta="v1",
            acciones=10, enemigos_derrotados=1, tiempo_final=50,
            resultado="victoria"))
        return puntajes


def ejecutar() -> None:
    vista = VistaArcade(ancho=800, alto=600, titulo="Cripta")
    controlador = _DemoControlador(vista)
    controlador.iniciar()
    try:
        # Cerrar la ventana con el botón del sistema operativo todavía no
        # está manejado -- por ahora, ESCAPE es la forma de salir.
        while not controlador.terminado():
            vista.actualizar()                  # bombea eventos, no bloquea (D44)
            comando = vista.pedir_comando()      # None si no hay nada todavía (D43)
            controlador.procesar(comando)
            time.sleep(_RITMO_SEGUNDOS)
    finally:
        vista.cerrar()


if __name__ == "__main__":
    ejecutar()