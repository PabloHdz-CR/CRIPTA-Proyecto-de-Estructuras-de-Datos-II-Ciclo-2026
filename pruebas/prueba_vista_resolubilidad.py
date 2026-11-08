"""Vista de la resolubilidad (003-resolubilidad, T030).

FR-019, FR-020, FR-037; escenario H2.E3 (V abre y cierra el reporte),
contracts/vista.md:
  - la pantalla de reporte manda "volver" con ENTER y ESC si no se puede
    continuar, y "aceptar_resolubilidad" con ENTER (ESC sigue en "volver")
    con --forzar;
  - en la partida, V alterna el panel sin encolar comandos si hay reporte;
    sin reporte encola "ver_resolubilidad"; en el replay no hace nada;
  - V no hace nada en el menú, el fin ni los puntajes (no está asignada a
    otra acción);
  - el README documenta V en la tabla de la partida;
  - el texto largo no se pierde: partir_linea parte cada línea en filas que
    caben, con sangría de continuación y sin perder texto; el panel de V y
    la pantalla de reporte muestran una línea de 200 caracteres completa
    (la unión de sus filas es la línea original y ninguna fila supera el
    máximo), y con el panel abierto las flechas arriba/abajo y RePág/AvPág
    lo desplazan en vez de mover al jugador.

Sigue el estilo de prueba_vista_10 (ventana invisible).
"""
from pathlib import Path

import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    CriptaVisible, EstadoVista, InfoReplay, InventarioVisible, JugadorVisible,
    ReporteResolubilidadVisible, ResultadoFinVisible, SalaVisible)
from cripta.vista.pantallaResolubilidad import PantallaResolubilidad
from cripta.vista.partirLineas import SANGRIA_CONTINUACION, partir_linea, unir_filas
from cripta.vista.vistaArcade import VistaArcade

RAIZ = Path(__file__).resolve().parent.parent


def lista(*elementos):
    l = ListaEnlazada()
    for e in elementos:
        l.agregar_al_final(e)
    return l


def reporte(puede_continuar=False, veredicto="NO_RESOLUBLE"):
    return ReporteResolubilidadVisible(
        veredicto=veredicto,
        lineas=lista("Cripta c (versión v): NO RESOLUBLE", "Motivo: ..."),
        puede_continuar=puede_continuar)


def estado(resolubilidad=None, replay=None):
    jugador = JugadorVisible(vida=10, vida_max=10, ataque_efectivo=1, defensa_efectiva=1,
                             velocidad=100, antorcha_encendida=False, acciones=0,
                             enemigos_derrotados=0)
    sala = SalaVisible(nombre="Sala", salidas=(None, None, None, None),
                       enemigos=ListaEnlazada(), objetos=ListaEnlazada())
    inventario = InventarioVisible(objetos=ListaEnlazada(), indice_actual=-1, capacidad=5,
                                   cantidad_pergaminos=0)
    return EstadoVista(id_cripta="c", version_cripta="v", reloj=0, terminada=False,
                       resultado=None, jugador=jugador, sala=sala, efectos=ListaEnlazada(),
                       inventario=inventario, mensajes=ListaEnlazada(),
                       nombre_jugador="Ana", replay=replay, resolubilidad=resolubilidad)


def comandos(vista):
    salida = []
    while True:
        c = vista.pedir_comando()
        if c is None:
            return salida
        salida.append(c)


LINEA_LARGA = ("  1. itm_llave_hierro, encerrada por sala 12 E -> sala 24 (requiere "
               "itm_llave_negra) -> itm_llave_negra, encerrada por sala 7 E -> sala 22 "
               "(requiere itm_llave_hierro) -> itm_llave_hierro, fin del ciclo")[:200]
assert len(LINEA_LARGA) == 200, len(LINEA_LARGA)


def comprobar_filas(filas, maximo, original):
    """Ninguna fila supera el máximo y la unión sin la sangría es la línea."""
    filas = list(filas)
    assert all(len(fila) <= maximo for fila in filas), (maximo, filas)
    assert all(fila.startswith(SANGRIA_CONTINUACION) for fila in filas[1:]), filas
    assert unir_filas(filas) == original, filas
    return filas


def prueba_partir_linea():
    # Corta: una sola fila, igual a la original.
    assert list(partir_linea("Ciclos: ninguno.", 40)) == ["Ciclos: ninguno."]
    assert list(partir_linea("", 10)) == [""]
    # Larga con espacios: corta en espacios, sangría de continuación.
    filas = comprobar_filas(partir_linea(LINEA_LARGA, 60), 60, LINEA_LARGA)
    assert len(filas) >= 4
    for fila in filas[:-1]:
        assert fila.endswith(" "), fila          # el corte cayó en un espacio
    # Sin espacios: corta la palabra, sin perder caracteres.
    sin_espacios = "x" * 95
    filas = comprobar_filas(partir_linea(sin_espacios, 20), 20, sin_espacios)
    assert filas[0] == "x" * 20 and len(filas) == 6
    # La sangría propia del reporte ("  - ...") no es un lugar de corte.
    sangrada = "  " + "y" * 30
    comprobar_filas(partir_linea(sangrada, 12), 12, sangrada)
    # Exactamente en el límite: una fila.
    assert list(partir_linea("a" * 15, 15)) == ["a" * 15]


prueba_partir_linea()


def readme_tiene_v():
    """La tabla "Partida" del README tiene una fila cuya primera celda es V."""
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    inicio = texto.index("**Partida.**")
    fin = texto.index("**Fin de partida.**", inicio)
    for linea in texto[inicio:fin].split("\n"):
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if celdas and celdas[0] == "V":
            return True
    return False


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 1. Pantalla de reporte sin --forzar: ENTER y ESC vuelven al menú.
    vista.mostrar_resolubilidad(reporte(puede_continuar=False))
    pantalla = vista._pantalla_actual
    assert isinstance(pantalla, PantallaResolubilidad)
    vista.actualizar()
    comandos(vista)
    pantalla.on_key_press(arcade.key.ENTER, 0)
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert comandos(vista) == [Comando("volver"), Comando("volver")]
    for tecla in (arcade.key.UP, arcade.key.DOWN, arcade.key.PAGEUP, arcade.key.PAGEDOWN,
                  arcade.key.V):
        pantalla.on_key_press(tecla, 0)
    assert comandos(vista) == []

    # 2. Con --forzar: ENTER juega de todos modos, ESC vuelve.
    vista.mostrar_resolubilidad(reporte(puede_continuar=True))
    pantalla = vista._pantalla_actual
    pantalla.on_key_press(arcade.key.ENTER, 0)
    pantalla.on_key_press(arcade.key.ESCAPE, 0)
    assert comandos(vista) == [Comando("aceptar_resolubilidad"), Comando("volver")]

    # 3. H2.E3: en la partida, V abre y cierra el panel sin encolar comandos.
    vista.mostrar_estado(estado(resolubilidad=reporte(veredicto="RESOLUBLE")))
    juego = vista._pantalla_actual
    assert not vista.panel_resolubilidad
    juego.on_key_press(arcade.key.V, 0)
    assert vista.panel_resolubilidad
    assert comandos(vista) == []
    juego.on_key_press(arcade.key.V, 0)
    assert not vista.panel_resolubilidad
    assert comandos(vista) == []

    # 4. Sin reporte (partida cargada): V pide el aviso al Controlador.
    vista.mostrar_estado(estado(resolubilidad=None))
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)
    assert comandos(vista) == [Comando("ver_resolubilidad")]
    assert not vista.panel_resolubilidad

    # 5. En el replay, V no hace nada.
    vista.mostrar_estado(estado(replay=InfoReplay(paso=0, total=3, pausado=True, velocidad=1)))
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)
    assert comandos(vista) == [] and not vista.panel_resolubilidad

    # 6. V no está asignada en el menú, el fin ni los puntajes.
    vista.mostrar_menu(lista(CriptaVisible("c1", "Primera", 6, 1)))
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)
    assert comandos(vista) == []
    vista.mostrar_fin(ResultadoFinVisible(resultado="victoria", acciones=1,
                                          enemigos_derrotados=0, tiempo_final=10))
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)
    assert comandos(vista) == []
    vista.mostrar_puntajes(ListaEnlazada())
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)
    assert comandos(vista) == []

    # 7. Texto largo en la pantalla de reporte: completo y dentro del ancho.
    largo = ReporteResolubilidadVisible(veredicto="NO_RESOLUBLE", lineas=lista(
        "Cripta c (versión v): NO RESOLUBLE", LINEA_LARGA), puede_continuar=False)
    vista.mostrar_resolubilidad(largo)
    pantalla = vista._pantalla_actual
    vista.actualizar()
    filas = list(pantalla.filas)
    assert filas[0] == "Cripta c (versión v): NO RESOLUBLE"
    comprobar_filas(filas[1:], pantalla.maximo_caracteres, LINEA_LARGA)
    assert len(filas) > 2, "la línea larga debía partirse"

    # 8. Texto largo en el panel de V: completo, dentro del ancho y con
    # desplazamiento; las flechas no mueven al jugador mientras está abierto.
    vista.mostrar_estado(estado(resolubilidad=largo))
    juego = vista._pantalla_actual
    juego.on_key_press(arcade.key.V, 0)
    assert vista.panel_resolubilidad
    hud = juego._hud
    filas = list(hud.filas_resolubilidad)
    # La primera línea también puede partirse si el panel es angosto: sus
    # filas van primero y las de la línea larga, después.
    encabezado = "Cripta c (versión v): NO RESOLUBLE"
    cuantas = len(partir_linea(encabezado, hud.maximo_resolubilidad))
    comprobar_filas(filas[:cuantas], hud.maximo_resolubilidad, encabezado)
    comprobar_filas(filas[cuantas:], hud.maximo_resolubilidad, LINEA_LARGA)
    assert hud.visibles_resolubilidad >= 1
    if len(filas) > hud.visibles_resolubilidad:
        for _ in range(len(filas)):
            juego = vista._pantalla_actual
            juego.on_key_press(arcade.key.DOWN, 0)
        hud = vista._pantalla_actual._hud
        assert hud.desplazamiento_resolubilidad == len(filas) - hud.visibles_resolubilidad
        vista._pantalla_actual.on_key_press(arcade.key.PAGEUP, 0)
        vista._pantalla_actual.on_key_press(arcade.key.UP, 0)
    assert comandos(vista) == [], "con el panel abierto, las flechas no mueven al jugador"
    vista._pantalla_actual.on_key_press(arcade.key.V, 0)      # se cierra
    vista._pantalla_actual.on_key_press(arcade.key.UP, 0)     # y ahora sí mueve
    assert comandos(vista) == [Comando("mover", ("N",))]

    # 9. FR-037: el README documenta V.
    assert readme_tiene_v(), "falta la fila de V en la tabla Partida del README"
finally:
    vista.cerrar()

print("prueba_vista_resolubilidad OK")
