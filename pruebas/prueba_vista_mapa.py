"""Mapa conocido en la vista (T012 y T034 de specs/002-niebla-guerra/tasks.md).

Cubre FR-002, FR-014, FR-015, FR-016, FR-017 y SC-002 (escenarios 4 y 5 de
US1). T034 agrega el cursor del panel, saltar las avistadas y Enter (FR-035).

Cripta de la prueba (ids no consecutivos, para el orden numérico de FR-016):
         9
         │N
   100 ─O─ 10 ─E─ 2 ─E─ 7
         │S
         55
La inicial es la 10. Las salas tienen nombres marca "MARCA-<id>".
"""
import arcade

from cripta.modelo.mundo.conocimiento import EXPLORADA
from cripta.vista.comando import Comando
from cripta.vista.vistaArcade import VistaArcade

from pruebas.apoyo_niebla import (
    ANTORCHA, cerrar_fuentes, con_contenido, controlador_sobre, dar_objeto, doble, sala_n,
    PINCHOS, RATA)


def cripta():
    a_n, b_n = doble(10, "N", 9)
    a_s, b_s = doble(10, "S", 55)
    a_e, b_e = doble(10, "E", 2)
    a_o, b_o = doble(10, "O", 100)
    c_e, d_e = doble(2, "E", 7)
    salas = (sala_n(10, a_n, a_s, a_e, a_o, nombre="MARCA-10"),
             sala_n(9, b_n, nombre="MARCA-9"),
             sala_n(55, b_s, nombre="MARCA-55"),
             sala_n(2, b_e, c_e, nombre="MARCA-2"),
             sala_n(100, b_o, nombre="MARCA-100"),
             sala_n(7, d_e, nombre="MARCA-7"))
    salas = con_contenido(salas, 2, enemigos=(("r1", RATA),))
    return con_contenido(salas, 7, trampas=(("t1", PINCHOS),))


def abrir_mapa(controlador, vista):
    controlador.procesar(Comando("alternar_mapa"))
    mapa = vista.ultimo_estado.mapa
    assert mapa is not None, "FR-016: alternar_mapa abre el panel"
    return mapa


def caso_us1_e4_nada_desconocido():
    """US1 escenario 4 (FR-002, FR-014, FR-015, SC-002): ningún dato de salas no
    exploradas llega a la vista, aunque el programa ya las tenga."""
    controlador, vista, _ = controlador_sobre(cripta(), sala_inicial=10)
    controlador.procesar(Comando("mover", ("E",)))      # a la 2 (explorada); 7 avistada
    mapa = abrir_mapa(controlador, vista)
    partida = controlador.partida
    controlador._servicio.asegurar_contenido(7)        # el contenido de la 7 ya está en el programa
    texto = repr(vista.ultimo_estado)
    for s in partida.mundo:
        if s.conocimiento != EXPLORADA:
            assert f"MARCA-{s.id}" not in texto, (
                f"FR-014/SC-002: el nombre de la sala {s.id} llegó a la vista")
    assert "Pinchos" not in texto and "pinchos" not in texto, "FR-015: contenido de la 7"
    for visible in mapa.salas:
        if not visible.explorada:
            assert visible.nombre is None, f"FR-002: avistada {visible.id} con nombre"
            assert visible.salidas == (), f"FR-002: avistada {visible.id} con salidas"
    assert mapa.cantidad_exploradas == 2 and mapa.cantidad_avistadas == 4, (
        mapa.cantidad_exploradas, mapa.cantidad_avistadas)


def caso_us1_e5_mapa_sin_tiempo():
    """US1 escenario 5 (FR-016, FR-017): abrir y cerrar el mapa no gasta reloj,
    no va al log y no agrega intervalos al Diario."""
    controlador, vista, registro = controlador_sobre(cripta(), sala_inicial=10)
    partida = controlador.partida
    reloj = partida.reloj
    abrir_mapa(controlador, vista)
    controlador.procesar(Comando("alternar_mapa"))
    assert vista.ultimo_estado.mapa is None, "FR-016: alternar_mapa cierra el panel"
    assert partida.reloj == reloj, "FR-017: el mapa no consume tiempo"
    assert registro.acciones() == [], "FR-017: el mapa no va a partida.log"
    assert not partida.diario.hay_cambios(), "FR-017: el mapa no es una acción reversible"


def caso_orden_por_id():
    """FR-016: salas por id numérico; salidas en N, S, E, O; avistadas solo con id."""
    controlador, vista, _ = controlador_sobre(cripta(), sala_inicial=10)
    mapa = abrir_mapa(controlador, vista)
    assert [s.id for s in mapa.salas] == [2, 9, 10, 55, 100], (
        f"FR-016: orden numérico: {[s.id for s in mapa.salas]}")
    inicial = [s for s in mapa.salas if s.id == 10][0]
    assert inicial.explorada and inicial.actual and inicial.nombre == "MARCA-10"
    assert [x.direccion for x in inicial.salidas] == ["N", "S", "E", "O"], "FR-016: N, S, E, O"
    assert [x.destino for x in inicial.salidas] == [9, 55, 2, 100]
    assert all(x.costo == 100 for x in inicial.salidas), "FR-016: costo (100 sin declarar)"


def caso_tecla_m():
    """FR-017: en la partida, M solo encola alternar_mapa y ninguna otra letra lo hace."""
    controlador, vista_registro, _ = controlador_sobre(cripta(), sala_inicial=10)
    estado = vista_registro.ultimo_estado
    vista = VistaArcade(ancho=400, alto=300, titulo="prueba", visible=False)
    try:
        for codigo in range(arcade.key.A, arcade.key.Z + 1):
            vista.cerrar_historia()     # 004: H abre la consulta, que se traga las demás teclas
            vista.mostrar_estado(estado)
            _comandos(vista)        # lo que dejaron los eventos reales de la ventana
            vista._pantalla_actual.on_key_press(codigo, 0)
            encolados = []
            while True:
                comando = vista.pedir_comando()
                if comando is None:
                    break
                encolados.append(comando)
            if codigo == arcade.key.M:
                assert encolados == [Comando("alternar_mapa")], f"FR-017: M encoló {encolados}"
            else:
                assert Comando("alternar_mapa") not in encolados, (
                    f"FR-017: la tecla {chr(codigo).upper()} también abre el mapa")
    finally:
        vista.cerrar()


def caso_panel_se_dibuja():
    """FR-016: con el mapa abierto, la pantalla de juego arma el panel con una
    fila por sala y por salida, y RePág/AvPág no encolan comandos."""
    controlador, vista_registro, _ = controlador_sobre(cripta(), sala_inicial=10)
    controlador.procesar(Comando("alternar_mapa"))
    estado = vista_registro.ultimo_estado
    vista = VistaArcade(ancho=1024, alto=720, titulo="prueba", visible=False)
    try:
        vista.mostrar_estado(estado)
        vista.actualizar()
        pantalla = vista._pantalla_actual
        filas = list(pantalla._hud.filas_mapa)
        texto = " | ".join(filas)
        assert "MARCA-10" in texto and "(actual)" in texto, f"FR-016: {texto}"
        assert "(avistada)" in texto and "MARCA-9" not in texto, f"FR-002: {texto}"
        assert len(filas) >= 5 + 4, f"FR-016: una fila por sala y por salida: {filas}"
        _comandos(vista)            # actualizar() pudo dejar comandos de la ventana real
        pantalla.on_key_press(arcade.key.PAGEDOWN, 0)
        assert _comandos(vista) == [], "RePág/AvPág no son comandos"
    finally:
        vista.cerrar()


def _comandos(vista):
    """Saca y devuelve todo lo que hay en la cola de comandos. Se llama justo
    antes de cada tecla para que la prueba mire solo lo que ella encola, como
    vaciar() en prueba_vista_10 (los eventos reales de la ventana pueden dejar
    comandos)."""
    salida = []
    while True:
        comando = vista.pedir_comando()
        if comando is None:
            return salida
        salida.append(comando)


def caso_t034_cursor_y_enter():
    """T034 (FR-035): con el panel abierto, el cursor recorre solo las salas
    exploradas (salta las avistadas), las flechas no mueven al jugador y Enter
    encola ir_a con la sala bajo el cursor; sobre la sala actual, el
    Controlador responde con el rechazo de FR-018."""
    controlador, vista_registro, _ = controlador_sobre(cripta(), sala_inicial=10)
    controlador.procesar(Comando("mover", ("E",)))       # exploradas: 2 y 10
    controlador.procesar(Comando("alternar_mapa"))       # lista: 2, 7, 9, 10, 55, 100
    estado = vista_registro.ultimo_estado
    vista = VistaArcade(ancho=1024, alto=720, titulo="prueba", visible=False)
    try:
        def tecla(codigo):
            vista.mostrar_estado(estado)
            _comandos(vista)        # solo cuenta lo que encola esta tecla
            vista._pantalla_actual.on_key_press(codigo, 0)
            return _comandos(vista)

        assert tecla(arcade.key.ENTER) == [Comando("ir_a", (2,))], "FR-035: cursor en la primera explorada"
        assert tecla(arcade.key.DOWN) == [], "FR-035: las flechas no mueven al jugador"
        assert vista.cursor_mapa == 10, f"FR-035: salta 7 y 9 (avistadas): {vista.cursor_mapa}"
        assert tecla(arcade.key.DOWN) == [] and vista.cursor_mapa == 10, "FR-035: se queda en la última"
        assert tecla(arcade.key.UP) == [] and vista.cursor_mapa == 2
        assert tecla(arcade.key.LEFT) == [] and tecla(arcade.key.RIGHT) == [], (
            "FR-035: con el panel abierto, ninguna flecha mueve al jugador")
        comandos = tecla(arcade.key.ENTER)
        assert comandos == [Comando("ir_a", (2,))], f"FR-035: {comandos}"
        assert "> " in " ".join(vista._pantalla_actual._hud.filas_mapa), "FR-035: marca del cursor"
        controlador.procesar(comandos[0])
        assert vista_registro.ultimo_error == "Ya estás en esa sala.", (
            f"FR-018: {vista_registro.ultimo_error}")
        assert tecla(arcade.key.I) == [Comando("interrumpir")], "FR-028: I encola interrumpir"
    finally:
        vista.cerrar()


def _se_encima(a, b):
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def caso_controles_sin_encimarse():
    """FR-017 (las teclas M e I se documentan en la partida): el panel de
    Controles muestra todas sus filas sin encimarse y dentro del panel, a
    1280x720 y a la ventana por defecto del juego (1024x720)."""
    controlador, vista_registro, _ = controlador_sobre(cripta(), sala_inicial=10)
    estado = vista_registro.ultimo_estado
    for ancho, alto in ((1280, 720), (1024, 720)):
        vista = VistaArcade(ancho=ancho, alto=alto, titulo="prueba", visible=False)
        try:
            vista.mostrar_estado(estado)
            vista.actualizar()
            hud = vista._pantalla_actual._hud
            cajas = list(hud.cajas_controles)
            teclas = [t for t, _ in hud.controles_mostrados]
            assert "M" in teclas and "I" in teclas and "ESC" in teclas, f"FR-017: {teclas}"
            assert len(cajas) == len(hud.controles_mostrados), "una caja por control"
            textos = " ".join(x.text for x in hud._textos)
            assert "…" not in textos.split("Controles")[-1], (
                f"{ancho}x{alto}: hay descripciones recortadas en Controles")
            izq, der, abajo, arriba = hud.panel_controles
            for i, caja in enumerate(cajas):
                assert izq <= caja[0] and caja[1] <= der and abajo <= caja[2] and caja[3] <= arriba, (
                    f"{ancho}x{alto}: '{teclas[i]}' se sale del panel: {caja} fuera de "
                    f"{(izq, der, abajo, arriba)}")
                for j in range(i + 1, len(cajas)):
                    assert not _se_encima(caja, cajas[j]), (
                        f"{ancho}x{alto}: '{teclas[i]}' se encima con '{teclas[j]}'")
        finally:
            vista.cerrar()


def _llevar_al_controlador(vista, controlador):
    """Lo que la Vista encoló, procesado por el Controlador (una vuelta del bucle)."""
    for comando in _comandos(vista):
        controlador.procesar(comando)


def caso_us1_e6_seleccion_cierra_el_mapa():
    """US1 escenario 6 (FR-037): con el mapa abierto, S, U y Q cierran el mapa y
    abren solo su selección, con un único cursor; ESC la cancela y el mapa
    sigue cerrado."""
    for tecla, verbo in ((arcade.key.S, "soltar"), (arcade.key.U, "usar"),
                         (arcade.key.Q, "equipar")):
        vista = VistaArcade(ancho=1024, alto=720, titulo="prueba", visible=False)
        try:
            controlador, _, _ = controlador_sobre(cripta(), sala_inicial=10, vista=vista)
            dar_objeto(controlador.partida, ANTORCHA)
            controlador.procesar(Comando("alternar_mapa"))
            assert vista._pantalla_actual._estado.mapa is not None, "el mapa está abierto"
            _comandos(vista)
            vista._pantalla_actual.on_key_press(tecla, 0)
            _llevar_al_controlador(vista, controlador)
            pantalla = vista._pantalla_actual
            assert pantalla._estado.mapa is None, f"FR-037: {verbo} cerró el mapa"
            assert pantalla.modo == "objetivo" and pantalla.verbo_objetivo == verbo, (
                f"FR-037: se abrió la selección de {verbo}: {pantalla.modo}, {pantalla.verbo_objetivo}")
            assert len(pantalla._hud.filas_mapa) == 0, "FR-037: un solo cursor (sin panel del mapa)"
            _comandos(vista)
            pantalla.on_key_press(arcade.key.ESCAPE, 0)
            _llevar_al_controlador(vista, controlador)
            pantalla = vista._pantalla_actual
            assert pantalla.modo == "normal", "ESC cancela la selección"
            assert pantalla._estado.mapa is None and not controlador._mapa_abierto, (
                "FR-037: cancelar no vuelve a abrir el mapa")
        finally:
            vista.cerrar()
            cerrar_fuentes()


CASOS = (caso_us1_e4_nada_desconocido, caso_us1_e5_mapa_sin_tiempo, caso_orden_por_id,
         caso_tecla_m, caso_panel_se_dibuja, caso_t034_cursor_y_enter,
         caso_controles_sin_encimarse, caso_us1_e6_seleccion_cierra_el_mapa)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
        finally:
            cerrar_fuentes()
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_vista_mapa OK ({len(CASOS)} casos)")


main()
