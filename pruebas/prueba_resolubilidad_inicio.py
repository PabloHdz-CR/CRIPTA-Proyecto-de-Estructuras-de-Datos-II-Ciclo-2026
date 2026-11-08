"""Inicio de partida según la resolubilidad (003-resolubilidad, T029).

FR-018 a FR-021, FR-031, contracts/registro.md. Escenarios H2.E1 (Apéndice
B) a H2.E4, el encabezado del log con las palabras de marca, el replay fiel
y el guardado idéntico antes y después de la tecla V en una partida cargada.

Usa ControladorMenu sobre el paquete pruebas/datos/resolubilidad, sin
ventana (VistaNula) y con carpetas temporales.

Uso: py -m pruebas.prueba_resolubilidad_inicio
"""
import os
import tempfile
from pathlib import Path

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.adaptadores.registroArchivo import CarpetaRegistros, RegistroArchivo
from cripta.controlador.bench.reporte import Reporte
from cripta.controlador.controladorMenu import ControladorMenu
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.modoReplay import ModoReplay
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.controlador.textoResolubilidad import AVISO_RESOLUBLE, AVISO_SIN_REPORTE
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.puertos.errores import ErrorCripta
from cripta.modelo.puertos.registroAcciones import EncabezadoPartida
from cripta.modelo.resolubilidad.resultadoResolubilidad import (
    NO_RESOLUBLE, NO_VERIFICADA, RESOLUBLE)
from cripta.vista.comando import Comando
from cripta.vista.vistaNula import VistaNula

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "pruebas" / "datos" / "resolubilidad"
FUENTES = []


class FuenteContada(FuenteOffline):
    """FuenteOffline que cuenta las consultas de llaves."""

    def __init__(self, carpeta):
        super().__init__(carpeta)
        self.llamadas_llaves = 0

    def llaves(self, id_cripta):
        self.llamadas_llaves += 1
        return super().llaves(id_cripta)


class Juego:
    """Un ControladorMenu completo sobre el paquete, con su propia carpeta
    temporal (o la que se pase, para continuar un guardado)."""

    def __init__(self, forzar=False, carpeta=None):
        self.carpeta = carpeta or Path(tempfile.mkdtemp(prefix="prueba_resolubilidad_inicio_"))
        self.fuente = FuenteContada(PAQUETE)
        asincrona = FuenteAsincrona(self.fuente)
        FUENTES.append(asincrona)
        # Caché de llaves y fichas propia de cada Juego: así el contador de
        # llaves mide lo que pide ESTE servicio.
        fichas = Path(tempfile.mkdtemp(prefix="prueba_resolubilidad_fichas_"))
        self.servicio = ServicioDatos(self.fuente, asincrona, CacheFichas(25),
                                      AlmacenLocalDisco(fichas))
        self.vista = VistaNula()
        self.menu = ControladorMenu(
            self.servicio, self.vista,
            GestorGuardado(AlmacenPartidaDisco(self.carpeta / "guardados")),
            PuntajesArchivo(self.carpeta / "puntajes.jsonl"),
            CarpetaRegistros(self.carpeta / "partidas"),
            ReporteFinal(Reporte(imprimir=False)), semilla_fija=7, forzar=forzar)
        self.menu.iniciar()

    def enviar(self, verbo, *argumentos):
        self.menu.procesar(Comando(verbo, tuple(argumentos)))

    def log(self, id_cripta):
        return self.carpeta / "partidas" / f"{id_cripta}.log"

    def encabezado(self, id_cripta):
        return self.log(id_cripta).read_text(encoding="utf-8").split("\n")[0]

    def mensajes(self):
        return list(self.vista.ultimo_estado.mensajes)


def prueba_h2_e1_no_resoluble_sin_forzar():
    # H2.E1 (FR-018, FR-019; Apéndice B): la partida no inicia, no hay log y
    # se muestra el reporte; "volver" regresa al menú.
    juego = Juego()
    juego.enviar("jugar", "res-autociclo")
    reporte = juego.vista.ultima_resolubilidad
    assert reporte is not None and reporte.veredicto == NO_RESOLUBLE
    assert not reporte.puede_continuar
    assert list(reporte.lineas)[0] == "Cripta res-autociclo (versión v1): NO RESOLUBLE"
    assert juego.menu._juego is None
    assert not juego.log("res-autociclo").exists()
    juego.vista.ultimo_menu = None
    juego.enviar("aceptar_resolubilidad")         # sin --forzar no inicia
    assert juego.menu._juego is None
    juego.enviar("volver")
    assert juego.vista.ultimo_menu is not None
    assert juego.menu._juego is None and not juego.log("res-autociclo").exists()


def prueba_h2_e2_no_resoluble_con_forzar():
    # H2.E2 (FR-018, FR-020): con --forzar se muestra la pantalla con
    # puede_continuar; al aceptar, la partida inicia y el log lo anota.
    juego = Juego(forzar=True)
    juego.enviar("jugar", "res-autociclo")
    assert juego.vista.ultima_resolubilidad.puede_continuar
    assert juego.menu._juego is None
    juego.enviar("aceptar_resolubilidad")
    assert juego.menu._juego is not None
    assert juego.encabezado("res-autociclo").endswith(" FORZADA NO_RESOLUBLE"), \
        juego.encabezado("res-autociclo")
    # El reporte sigue disponible con V (EstadoVista.resolubilidad).
    assert juego.vista.ultimo_estado.resolubilidad.veredicto == NO_RESOLUBLE


def prueba_h2_e3_resoluble():
    # H2.E3 (FR-018, FR-019): la partida inicia sin pantalla, con el aviso
    # corto y el reporte completo en EstadoVista para la tecla V. Con
    # --forzar es igual: sin pantalla y sin palabras de marca.
    for forzar in (False, True):
        juego = Juego(forzar=forzar)
        juego.enviar("jugar", "res-cadena")
        assert juego.vista.ultima_resolubilidad is None
        assert juego.menu._juego is not None
        assert AVISO_RESOLUBLE in juego.mensajes(), juego.mensajes()
        reporte = juego.vista.ultimo_estado.resolubilidad
        assert reporte.veredicto == RESOLUBLE
        assert list(reporte.lineas) == [
            "Cripta res-cadena (versión v1): RESOLUBLE",
            "Orden de obtención de llaves (3):",
            "  1. itm_res_a: sala 1",
            "  2. itm_res_b: sala 2",
            "  3. itm_res_salida: sala 3",
        ]
        assert len(juego.encabezado("res-cadena").split(" ")) == 5   # CRIPTA + 4 campos


def prueba_h2_e4_replay_de_partida_forzada():
    # H2.E4 (FR-021): --replay reproduce una partida forzada sin bloquearla.
    juego = Juego(forzar=True)
    juego.enviar("jugar", "res-autociclo")
    juego.enviar("aceptar_resolubilidad")
    juego.enviar("esperar")
    juego.enviar("esperar")
    servicio = Juego().servicio
    modo = ModoReplay(servicio, VistaNula(), ReporteFinal(Reporte(imprimir=False)),
                      Reporte(imprimir=False))
    assert modo.ejecutar(RegistroArchivo(juego.log("res-autociclo")))
    assert modo.partida.reloj == juego.menu._juego.partida.reloj


def prueba_sin_llaves_no_verificada():
    # FR-031: NO_VERIFICADA bloquea sin --forzar y deja iniciar con él.
    juego = Juego()
    juego.enviar("jugar", "res-sin-llaves")
    assert juego.vista.ultima_resolubilidad.veredicto == NO_VERIFICADA
    assert juego.menu._juego is None
    forzado = Juego(forzar=True)
    forzado.enviar("jugar", "res-sin-llaves")
    forzado.enviar("aceptar_resolubilidad")
    assert forzado.menu._juego is not None
    assert forzado.encabezado("res-sin-llaves").endswith(" FORZADA NO_VERIFICADA")


def partida_guardada():
    """Una partida de res-cadena guardada y vuelta al menú."""
    juego = Juego()
    juego.enviar("jugar", "res-cadena")
    juego.enviar("esperar")
    juego.enviar("guardar")
    juego.enviar("salir")
    return juego.carpeta


def prueba_cargada_no_verifica_y_v_avisa():
    # FR-021: continuar una partida guardada no consulta llaves ni muestra
    # reporte; V (ver_resolubilidad) avisa en la bitácora, sin tocar el log.
    carpeta = partida_guardada()
    juego = Juego(carpeta=carpeta)
    juego.enviar("jugar", "res-cadena")
    assert juego.menu._juego is not None
    assert juego.fuente.llamadas_llaves == 0
    assert juego.vista.ultima_resolubilidad is None
    assert juego.vista.ultimo_estado.resolubilidad is None
    lineas_antes = juego.log("res-cadena").read_text(encoding="utf-8")
    juego.enviar("ver_resolubilidad")
    assert juego.mensajes()[-1] == AVISO_SIN_REPORTE, juego.mensajes()
    assert juego.log("res-cadena").read_text(encoding="utf-8") == lineas_antes


def prueba_guardado_identico_tras_v():
    # FR-021 (T029): en una partida cargada, el binario guardado antes y
    # después de V es idéntico byte a byte.
    carpeta = partida_guardada()
    juego = Juego(carpeta=carpeta)
    juego.enviar("jugar", "res-cadena")
    antes = juego.carpeta / "antes.bin"
    despues = juego.carpeta / "despues.bin"
    PartidaBinaria.guardar(juego.menu._juego.partida, antes)
    juego.enviar("ver_resolubilidad")
    PartidaBinaria.guardar(juego.menu._juego.partida, despues)
    assert antes.read_bytes() == despues.read_bytes(), \
        "el aviso de V cambió el estado serializado: parar y decidir (tasks.md T029)"


def prueba_replay_fiel_de_partida_resoluble():
    # FR-018, FR-021: verificar no cambia la partida. Una partida corta en una
    # cripta resoluble, reproducida desde su log, llega al mismo estado.
    juego = Juego()
    juego.enviar("jugar", "res-cadena")
    for _ in range(3):
        juego.enviar("esperar")
    original = juego.carpeta / "original.bin"
    PartidaBinaria.guardar(juego.menu._juego.partida, original)
    modo = ModoReplay(Juego().servicio, VistaNula(), ReporteFinal(Reporte(imprimir=False)),
                      Reporte(imprimir=False))
    assert modo.ejecutar(RegistroArchivo(juego.log("res-cadena")))
    reproducida = juego.carpeta / "reproducida.bin"
    PartidaBinaria.guardar(modo.partida, reproducida)
    assert original.read_bytes() == reproducida.read_bytes()


def escribir_log(texto):
    ruta = Path(tempfile.mkdtemp(prefix="prueba_resolubilidad_log_")) / "x.log"
    ruta.write_text(texto + "\n", encoding="utf-8")
    return RegistroArchivo(ruta)


def prueba_encabezado_palabras_de_marca():
    # contracts/registro.md (FR-020, FR-021).
    encabezado, _ = escribir_log("CRIPTA c v cat 5").leer()
    assert not encabezado.forzada and encabezado.veredicto_forzado is None
    for marcas, veredicto in (("FORZADA NO_RESOLUBLE", NO_RESOLUBLE),
                              ("NO_VERIFICADA FORZADA", NO_VERIFICADA)):
        encabezado, _ = escribir_log(f"CRIPTA c v cat 5 {marcas}").leer()
        assert encabezado.forzada and encabezado.veredicto_forzado == veredicto, marcas
    for malas in ("OTRA", "FORZADA", "NO_RESOLUBLE", "FORZADA FORZADA NO_RESOLUBLE",
                  "FORZADA NO_RESOLUBLE NO_VERIFICADA"):
        try:
            escribir_log(f"CRIPTA c v cat 5 {malas}").leer()
        except ErrorCripta:
            pass
        else:
            raise AssertionError(f"el encabezado con '{malas}' debía rechazarse")
    # Ida y vuelta: lo que se escribe se lee igual.
    ruta = Path(tempfile.mkdtemp(prefix="prueba_resolubilidad_log_")) / "y.log"
    registro = RegistroArchivo(ruta)
    registro.iniciar(EncabezadoPartida("c", "v", "cat", 5, forzada=True,
                                       veredicto_forzado=NO_VERIFICADA))
    assert ruta.read_text(encoding="utf-8").split("\n")[0] == "CRIPTA c v cat 5 FORZADA NO_VERIFICADA"
    leido, _ = registro.leer()
    assert leido.forzada and leido.veredicto_forzado == NO_VERIFICADA


def main():
    # Los ControladorMenu escriben fichas y logs en carpetas temporales; el
    # directorio de trabajo también, por si algo usa rutas relativas.
    os.chdir(tempfile.mkdtemp(prefix="prueba_resolubilidad_inicio_cwd_"))
    pruebas = [valor for nombre, valor in sorted(globals().items())
               if nombre.startswith("prueba_") and callable(valor)]
    try:
        for prueba in pruebas:
            prueba()
            print(f"  ok  {prueba.__name__}")
    finally:
        while FUENTES:
            FUENTES.pop().cerrar()
    print(f"prueba_resolubilidad_inicio: {len(pruebas)} casos OK")


if __name__ == "__main__":
    main()
