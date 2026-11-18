"""T028 (004-linea-tiempo, US5): la consulta de la línea de tiempo en la
ventana, con la tecla H.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_vista_historia
"""
import dataclasses

import arcade

from cripta.vista.comando import Comando
from cripta.vista.estadoVista import ViajeVisible
from cripta.vista.vistaArcade import VistaArcade
from pruebas.apoyo_niebla import cerrar_fuentes, controlador_sobre, pasillo_n

TITULO = "Historia: instante (120) o acción (#3) - Enter consulta, ESC vuelve"


def _comandos(vista):
    """Saca y devuelve lo que hay en la cola de comandos (como en prueba_vista_mapa)."""
    salida = []
    while True:
        comando = vista.pedir_comando()
        if comando is None:
            return salida
        salida.append(comando)


def _llevar(vista, controlador):
    """Lo que encoló la Vista, procesado por el Controlador."""
    comandos = _comandos(vista)
    for comando in comandos:
        controlador.procesar(comando)
    return comandos


def _escribir(vista, texto):
    for caracter in texto:
        vista._pantalla_actual.on_text(caracter)


def _tecla(vista, codigo, modificadores=0):
    _comandos(vista)            # solo cuenta lo que encola esta tecla
    vista._pantalla_actual.on_key_press(codigo, modificadores)
    return _comandos(vista)


def _partida_con_ventana():
    """Ventana real oculta, Controlador real y tres movimientos (reloj ≥ 300)."""
    vista = VistaArcade(ancho=1024, alto=720, titulo="prueba", visible=False)
    controlador, _, registro = controlador_sobre(pasillo_n(6), vista=vista)
    for _ in range(3):
        controlador.procesar(Comando("mover", ("E",)))
    return vista, controlador, registro


def caso_e1_instante_y_esc():
    """US5 escenario 1 (FR-017, FR-018): H, "120", Enter encola historia 120 y
    el panel muestra el resumen; ESC vuelve y el reloj no cambió."""
    vista, controlador, registro = _partida_con_ventana()
    try:
        reloj = controlador.partida.reloj
        acciones_log = len(registro.acciones())
        assert _tecla(vista, arcade.key.H) == [], "FR-017: H solo abre la consulta"
        assert vista.historia_abierta, "FR-017: H abre la consulta"
        assert TITULO in vista._pantalla_actual._hud.texto_historia, vista._pantalla_actual._hud.texto_historia
        _escribir(vista, "120")
        assert vista.texto_historia == "120"
        vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
        comandos = _llevar(vista, controlador)
        assert comandos == [Comando("historia", ("120",))], f"FR-017: {comandos}"
        filas = " | ".join(vista._pantalla_actual._hud.filas_historia)
        assert "Instante 120" in filas and "Mapa conocido" in filas, f"FR-017: {filas}"
        vista._pantalla_actual.on_key_press(arcade.key.ESCAPE, 0)
        comandos = _llevar(vista, controlador)
        assert comandos == [Comando("cerrar_historia")], f"ESC: {comandos}"
        assert not vista.historia_abierta and vista._pantalla_actual._estado.historia is None
        assert len(vista._pantalla_actual._hud.filas_historia) == 0, "ESC cierra el panel"
        assert controlador.partida.reloj == reloj, "FR-018: el reloj no cambió"
        assert len(registro.acciones()) == acciones_log, "FR-005: nada al log"
    finally:
        vista.cerrar()


def caso_e2_numero_de_accion():
    """US5 escenario 2 (FR-017): "#3" y Enter; Retroceso borra."""
    vista, controlador, _ = _partida_con_ventana()
    try:
        _tecla(vista, arcade.key.H)
        _escribir(vista, "#39")
        assert _tecla(vista, arcade.key.BACKSPACE) == [] and vista.texto_historia == "#3"
        vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
        comandos = _llevar(vista, controlador)
        assert comandos == [Comando("historia", ("#3",))], f"FR-017: {comandos}"
        filas = " | ".join(vista._pantalla_actual._hud.filas_historia)
        assert "Antes de la acción #3" in filas, filas
    finally:
        vista.cerrar()


def caso_e3_invalido_sigue_abierta():
    """US5 escenario 3 (FR-003, FR-017): un valor inválido muestra el motivo y
    la consulta sigue abierta."""
    vista, controlador, _ = _partida_con_ventana()
    try:
        _tecla(vista, arcade.key.H)
        _escribir(vista, "999999")
        vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
        _llevar(vista, controlador)
        aviso = vista._pantalla_actual._aviso or ""
        assert "posterior al reloj actual" in aviso, f"FR-003: {aviso}"
        _sin_recortes_ni_cartel(vista, aviso)
        # El mensaje largo de la prueba manual: «… se puede consultar de #1 a #n+1».
        for _ in range(6):
            vista._pantalla_actual.on_key_press(arcade.key.BACKSPACE, 0)
        _escribir(vista, "#99999")
        vista._pantalla_actual.on_key_press(arcade.key.ENTER, 0)
        _llevar(vista, controlador)
        aviso = vista._pantalla_actual._aviso or ""
        assert "se puede consultar de #1 a #" in aviso, f"FR-003: {aviso}"
        _sin_recortes_ni_cartel(vista, aviso)
        for _ in range(6):
            vista._pantalla_actual.on_key_press(arcade.key.BACKSPACE, 0)
        _escribir(vista, "999999")
        assert vista.historia_abierta, "FR-017: la consulta sigue abierta"
        assert _tecla(vista, arcade.key.ENTER) == [Comando("historia", ("999999",))], (
            "se puede corregir y volver a consultar")
    finally:
        vista.cerrar()


def _sin_recortes_ni_cartel(vista, aviso):
    """T041: con la consulta abierta, el motivo se lee completo dentro del
    panel, sin "…", y no hay cartel encima del título."""
    for ancho, alto in ((1024, 720), (1280, 720)):
        vista.ventana.set_size(ancho, alto)
        pantalla = vista._pantalla_actual
        pantalla._armar_textos()
        hud = pantalla._hud
        filas = list(hud.filas_aviso_historia)
        assert filas, f"{ancho}x{alto}: el motivo no está en el panel"
        unidas = " ".join(fila.strip() for fila in filas)
        assert unidas.split() == aviso.split(), f"{ancho}x{alto}: {filas} contra {aviso!r}"
        assert not any("…" in fila for fila in filas), f"{ancho}x{alto}: recortado: {filas}"
        assert hud._cartel is None, f"{ancho}x{alto}: el cartel tapa el título del panel"


def caso_e4_las_demas_teclas_no_hacen_nada():
    """US5 escenario 4 (FR-018): con la consulta abierta, letras y flechas no
    encolan acciones ni abren selecciones, y las letras no se escriben."""
    vista, controlador, _ = _partida_con_ventana()
    try:
        _tecla(vista, arcade.key.H)
        for codigo in list(range(arcade.key.A, arcade.key.Z + 1)) + [
                arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT,
                arcade.key.SPACE, arcade.key.TAB]:
            assert _tecla(vista, codigo) == [], f"FR-018: la tecla {codigo} encoló algo"
            assert vista._pantalla_actual.modo == "normal", "FR-018: no abre selecciones"
        _escribir(vista, "abc")
        assert vista.texto_historia == "", "solo dígitos y #"
        assert _tecla(vista, arcade.key.ENTER) == [], "Enter sin texto no consulta"
        assert vista.historia_abierta
    finally:
        vista.cerrar()


def caso_h_detiene_el_viaje_y_cierra_el_mapa():
    """Contrato de la ventana (FR-017): con un viaje en curso, H encola primero
    interrumpir; con el mapa abierto, lo cierra antes de abrir la consulta."""
    vista, controlador, _ = _partida_con_ventana()
    try:
        estado = vista._pantalla_actual._estado
        vista.mostrar_estado(dataclasses.replace(estado, viaje=ViajeVisible(6, "Sala 6", 2)))
        assert _tecla(vista, arcade.key.H) == [Comando("interrumpir")], "H detiene el viaje"
        assert vista.historia_abierta
        vista._pantalla_actual.on_key_press(arcade.key.ESCAPE, 0)
        _llevar(vista, controlador)
        controlador.procesar(Comando("alternar_mapa"))
        assert vista._pantalla_actual._estado.mapa is not None
        assert _tecla(vista, arcade.key.H) == [Comando("alternar_mapa")], "H cierra el mapa"
        assert vista.historia_abierta
    finally:
        vista.cerrar()


def caso_controles_muestran_h():
    """FR-017: el panel de Controles muestra H sin encimarse (la prueba de
    prueba_vista_mapa lo comprueba para todas las filas)."""
    vista, controlador, _ = _partida_con_ventana()
    try:
        vista.actualizar()
        teclas = [t for t, _ in vista._pantalla_actual._hud.controles_mostrados]
        assert "H" in teclas, f"FR-017: {teclas}"
    finally:
        vista.cerrar()


CASOS = (caso_e1_instante_y_esc, caso_e2_numero_de_accion, caso_e3_invalido_sigue_abierta,
         caso_e4_las_demas_teclas_no_hacen_nada, caso_h_detiene_el_viaje_y_cierra_el_mapa,
         caso_controles_muestran_h)


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
    print(f"prueba_vista_historia OK ({len(CASOS)} casos)")


main()
