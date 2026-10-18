"""Prueba de las teclas nuevas de la Vista (§10.2): nombre en el menú (N,
escribir, BACKSPACE, ENTER/ESC; mientras se escribe, las letras NO son
atajos), B en el menú (R ya no: el replay se elige en puntajes), la tabla
de puntajes (cursor y R solo en filas con replay), controles del replay en
PantallaJuego, R en la pantalla de fin y la pantalla de benchmark (ESC
vuelve, no sale).
"""
import arcade

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    BenchmarkVisible, CriptaVisible, EstadoVista, InfoReplay, InventarioVisible,
    JugadorVisible, PuntajeVisible, ResultadoFinVisible, SalaVisible)
from cripta.vista.pantallaBenchmark import PantallaBenchmark
from cripta.vista.vistaArcade import VistaArcade


def lista(*elementos):
    l = ListaEnlazada()
    for e in elementos:
        l.agregar_al_final(e)
    return l


def estado(replay=None):
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
                       nombre_jugador="Ana", replay=replay)


def vaciar(vista):
    """Descarta lo que haya en la cola (p. ej. un evento real de la ventana
    que actualizar() bombeó), para que cada assert mire solo lo que produjo
    la tecla que se está probando."""
    comandos(vista)


def comandos(vista):
    salida = []
    while True:
        c = vista.pedir_comando()
        if c is None:
            return salida
        salida.append(c)


vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
try:
    # 0. Pantalla de título: ENTER entra al menú, ESC sale, el resto nada
    from cripta.vista.pantallaTitulo import FRASES, PantallaTitulo
    vista.mostrar_titulo()
    titulo = vista._pantalla_actual
    assert isinstance(titulo, PantallaTitulo)
    vista.actualizar()
    vaciar(vista)
    assert titulo.frase_actual.strip("\u201c\u201d") in FRASES
    for tecla in (arcade.key.A, arcade.key.SPACE, arcade.key.UP, arcade.key.R):
        titulo.on_key_press(tecla, 0)
    assert comandos(vista) == []
    titulo.on_key_press(arcade.key.ENTER, 0)
    assert comandos(vista) == [Comando("entrar")]
    titulo.on_key_press(arcade.key.ESCAPE, 0)
    assert comandos(vista) == [Comando("salir")]

    criptas = lista(CriptaVisible("c1", "Primera", 6, 1), CriptaVisible("c2", "Segunda", 9, 3))
    vista.mostrar_nombre_jugador("Jugador")
    vista.mostrar_menu(criptas)
    menu = vista._pantalla_actual
    vista.actualizar()

    # 1. N abre la edición; la "n" de la propia tecla no se escribe; las
    #    letras no son atajos (P no pide puntajes); BACKSPACE borra; ENTER confirma.
    vaciar(vista)
    menu.on_key_press(arcade.key.N, 0)
    assert menu.editando_nombre
    menu.on_text("n")                          # el eco de la tecla N
    menu.on_text("Pepa")
    menu.on_key_press(arcade.key.P, 0)         # letra de "Pepa": no es atajo
    menu.on_key_press(arcade.key.BACKSPACE, 0)
    menu.on_text("x")
    assert comandos(vista) == []               # escribir no produce comandos
    vista.actualizar()
    menu.on_key_press(arcade.key.ENTER, 0)
    assert not menu.editando_nombre
    assert comandos(vista) == [Comando("cambiar_nombre", ("Pepx",))]

    # 2. ESC mientras se escribe cancela (no sale del juego)
    menu.on_key_press(arcade.key.N, 0)
    menu.on_text("zzz")
    menu.on_key_press(arcade.key.ESCAPE, 0)
    assert not menu.editando_nombre and comandos(vista) == []

    #    una "n" que NO es el eco (llega después de otra tecla) sí se escribe
    menu.on_key_press(arcade.key.N, 0)
    menu.on_text("n")                          # eco: se descarta
    menu.on_key_press(arcade.key.A, 0)         # otra tecla...
    menu.on_text("a")
    menu.on_key_press(arcade.key.N, 0)         # ...y la N de "Ana" es letra, no eco
    menu.on_text("n")
    menu.on_key_press(arcade.key.A, 0)
    menu.on_text("a")
    menu.on_key_press(arcade.key.ENTER, 0)
    assert comandos(vista) == [Comando("cambiar_nombre", ("ana",))]

    # 2b. Skins: la predeterminada es el tigre; flecha derecha/izquierda la
    #     cambian (dando la vuelta) sin encolar comandos (es presentación)
    from cripta.vista import texturas
    assert vista.skin == "tigre" == texturas.SKIN_POR_DEFECTO
    vaciar(vista)
    menu.on_key_press(arcade.key.RIGHT, 0)
    assert vista.skin == "caballero" and comandos(vista) == []
    menu.on_key_press(arcade.key.LEFT, 0)
    menu.on_key_press(arcade.key.LEFT, 0)
    assert vista.skin == texturas.SKINS[-1][0], "desde el primero, izquierda va al último"
    vista.actualizar()
    menu.on_key_press(arcade.key.RIGHT, 0)
    assert vista.skin == "tigre"
    for clave, _, _ in texturas.SKINS:         # todas tienen 4 cuadros de reposo y golpe
        for t in (0.0, 0.2, 0.4, 0.6):
            assert texturas.heroe(clave, t, False).width == 16
        assert texturas.heroe(clave, 0.0, True).height == 28
    reposo = [texturas.heroe("tigre", t, False) for t in (0.0, 0.2, 0.4, 0.6)]
    assert len({id(c) for c in reposo}) == 4, "el tigre tiene 4 cuadros distintos"

    # 2c. X pide partida nueva de la cripta elegida (aunque haya guardado)
    vaciar(vista)
    menu.on_key_press(arcade.key.X, 0)
    assert comandos(vista) == [Comando("jugar", ("c1", "nueva"))]
    menu.on_key_press(arcade.key.ENTER, 0)     # ENTER sigue pidiendo "jugar" sin modo
    assert comandos(vista) == [Comando("jugar", ("c1",))]

    # 3. R ya no hace nada en el menú; B pide el benchmark
    vaciar(vista)
    menu.on_key_press(arcade.key.R, 0)
    assert comandos(vista) == []
    vista.mostrar_error("aviso de prueba")     # el menú también muestra avisos
    vista.actualizar()
    vaciar(vista)
    menu.on_key_press(arcade.key.B, 0)
    assert comandos(vista) == [Comando("benchmark")]

    # 3b. Puntajes: el cursor elige la fila; R pide el replay de ESA partida,
    #     solo si tiene log; las flechas no se salen de la tabla
    puntajes = lista(
        PuntajeVisible("Ana", "c1", "v", 5, 1, 300, "victoria", id_partida="p-ana",
                       tiene_replay=True),
        PuntajeVisible("Viejo", "c1", "v", 2, 0, 90, "derrota"),
        PuntajeVisible("Beto", "c2", "v", 9, 2, 700, "derrota", id_partida="p-beto",
                       tiene_replay=True))
    vista.mostrar_puntajes(puntajes)
    tabla = vista._pantalla_actual
    vista.actualizar()
    vaciar(vista)
    assert tabla.cursor == 0
    tabla.on_key_press(arcade.key.R, 0)
    assert comandos(vista) == [Comando("ver_replay_partida", ("p-ana",))]
    tabla.on_key_press(arcade.key.DOWN, 0)
    tabla.on_key_press(arcade.key.R, 0)                # "Viejo": sin replay, solo avisa
    vista.actualizar()
    assert tabla.cursor == 1 and comandos(vista) == []
    for _ in range(5):
        tabla.on_key_press(arcade.key.DOWN, 0)
    assert tabla.cursor == 2, "no pasa de la última fila"
    tabla.on_key_press(arcade.key.R, 0)
    assert comandos(vista) == [Comando("ver_replay_partida", ("p-beto",))]
    tabla.on_key_press(arcade.key.ENTER, 0)
    assert comandos(vista) == [Comando("volver")]

    # 4. PantallaJuego en replay: sus teclas; las de juego no hacen nada
    vista.mostrar_estado(estado(InfoReplay(paso=1, total=4, pausado=False, velocidad=1,
                                           titulo="Ana · c1 · victoria · tiempo 300")))
    juego = vista._pantalla_actual
    vista.actualizar()
    vaciar(vista)
    for tecla in (arcade.key.SPACE, arcade.key.RIGHT, arcade.key.LEFT, arcade.key.UP,
                  arcade.key.DOWN, arcade.key.A, arcade.key.G):
        juego.on_key_press(tecla, 0)
    assert comandos(vista) == [Comando("replay_pausa"),
                               Comando("replay_paso"),             # derecha: adelante
                               Comando("replay_atras"),            # izquierda: atrás
                               Comando("replay_velocidad", ("+",)),  # arriba: más rápido
                               Comando("replay_velocidad", ("-",))]  # abajo: más lento
    for tecla in (arcade.key.PLUS, arcade.key.MINUS):     # +/- siguen sirviendo
        juego.on_key_press(tecla, 0)
    assert comandos(vista) == [Comando("replay_velocidad", ("+",)),
                               Comando("replay_velocidad", ("-",))]
    juego.on_key_press(arcade.key.ESCAPE, 0)
    assert comandos(vista) == [Comando("salir")]

    #    y fuera del replay, Espacio vuelve a ser "esperar"
    vista.mostrar_estado(estado())
    vista.actualizar()
    vaciar(vista)
    vista._pantalla_actual.on_key_press(arcade.key.SPACE, 0)
    assert comandos(vista) == [Comando("esperar")]

    # 5. Pantalla de fin: R solo si hay replay
    vista.mostrar_fin(ResultadoFinVisible("derrota", 3, 0, 120, puede_ver_replay=True))
    vista.actualizar()
    vaciar(vista)
    vista._pantalla_actual.on_key_press(arcade.key.R, 0)
    recibidos = comandos(vista)
    assert recibidos == [Comando("ver_replay")], recibidos
    vista.mostrar_fin(ResultadoFinVisible("victoria", 3, 1, 90, es_replay=True, coincide=True))
    vista.actualizar()
    vaciar(vista)
    vista._pantalla_actual.on_key_press(arcade.key.R, 0)
    assert comandos(vista) == []

    # 6. Benchmark: desplaza sin salirse del rango; ESC vuelve (no sale)
    filas = ListaEnlazada()
    for i in range(60):
        filas.agregar_al_final((str(i), "1.0"))
    vista.mostrar_espera("midiendo")
    vista.actualizar()
    vista.mostrar_benchmark(BenchmarkVisible(tablas=lista(("T", ("n", "us"), filas)),
                                             notas=lista("una nota " * 30), segundos=1.0,
                                             rapido=True))
    bench = vista._pantalla_actual
    assert isinstance(bench, PantallaBenchmark)
    vista.actualizar()
    bench.on_key_press(arcade.key.UP, 0)
    assert bench.desplazamiento == 0
    for _ in range(200):
        bench.on_key_press(arcade.key.DOWN, 0)
    maximo = bench.desplazamiento
    assert maximo > 0
    bench.on_key_press(arcade.key.PAGEDOWN, 0)
    assert bench.desplazamiento == maximo, "no pasa del final"
    vista.actualizar()
    vaciar(vista)
    bench.on_key_press(arcade.key.ESCAPE, 0)
    assert comandos(vista) == [Comando("volver")]
finally:
    vista.cerrar()

print("Sección vista_10 (teclas nuevas) OK")
