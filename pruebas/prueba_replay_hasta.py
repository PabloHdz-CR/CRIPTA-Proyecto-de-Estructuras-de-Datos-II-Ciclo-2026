"""T022 (004-linea-tiempo, US3): --replay partida.log --hasta t.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_replay_hasta
"""
import random
import tempfile
from pathlib import Path

from cripta.adaptadores.partidaBinaria import CopiadorBinario
from cripta.adaptadores.registroArchivo import RegistroArchivo
from cripta.controlador.bench.reporte import Reporte
from cripta.controlador.constructorResumen import ConstructorResumen
from cripta.controlador.fabricaAplicacion import FabricaAplicacion
from cripta.controlador.modoReplay import ModoReplay
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.vista.comando import Comando
from cripta.vista.vistaNula import VistaNula
from pruebas.apoyo_linea import cripta_linea
from pruebas.apoyo_niebla import PERGAMINO, cerrar_fuentes, con_contenido, controlador_sobre, servicio_niebla

TERMINO_ANTES = "La partida terminó antes"


def cripta(semilla, pergaminos=2, lado=5):
    """cripta_linea con pergaminos en el suelo de la sala inicial: se recogen
    con acciones que van al log, así la reproducción los tiene."""
    return con_contenido(cripta_linea(semilla, lado=lado), 1, objetos=[PERGAMINO] * pergaminos)


def grabar(descripcion, semilla, acciones=40):
    """Juega una partida con el Controlador real y un log en disco: primero
    recoge lo que hay en la sala inicial. Devuelve (controlador, ruta)."""
    ruta = Path(tempfile.mkdtemp(prefix="replay_hasta_")) / "partida.log"
    controlador, _, _ = controlador_sobre(descripcion, semilla=semilla, vida_jugador=10 ** 9,
                                          registro=RegistroArchivo(ruta))
    for objeto in [o for o in controlador.partida.mundo.sala(1).suelo]:
        controlador.procesar(Comando("recoger", (objeto.id_instancia,)))
    azar = random.Random(semilla)
    for _ in range(acciones):
        partida = controlador.partida
        sala = partida.mundo.sala(partida.jugador.sala)
        direcciones = [s.direccion for s in sala.salidas if s is not None and s.transitable()]
        if partida.puede_retroceder() and partida.jugador.inventario.primer_pergamino() is not None \
                and azar.random() < 0.1:
            controlador.procesar(Comando("pergamino"))
        elif direcciones and azar.random() < 0.7:
            controlador.procesar(Comando("mover", (azar.choice(direcciones),)))
        else:
            controlador.procesar(Comando("esperar"))
    return controlador, ruta


def replay_hasta(descripcion, ruta, t):
    """Reproduce el log con --hasta t sobre un servicio nuevo. Devuelve
    (ok, notas del reporte)."""
    reporte = Reporte(imprimir=False)
    modo = ModoReplay(servicio_niebla(descripcion, vida_jugador=10 ** 9), VistaNula(), ReporteFinal(),
                      reporte=reporte, copiador_estado=CopiadorBinario())
    ok = modo.ejecutar(RegistroArchivo(ruta), hasta=t)
    return ok, [nota for nota in reporte.notas]


def texto_historia(controlador, t):
    partida = controlador.partida
    copia = partida.linea.reconstruir_instante(t, partida)
    return [linea for linea in ConstructorResumen().construir(copia, str(t), t).lineas]


def caso_e1_t_posterior_al_final():
    """US3 escenario 1 (FR-013; Apéndice B 5): t mayor que el final → estado
    final y el aviso de que la partida terminó antes, en qué instante."""
    descripcion = cripta(51)
    controlador, ruta = grabar(descripcion, 51, acciones=25)
    final = controlador.partida.reloj
    ok, notas = replay_hasta(descripcion, ruta, final + 10_000)
    assert ok, notas
    avisos = [n for n in notas if n.startswith(TERMINO_ANTES)]
    assert avisos and str(final) in avisos[0], f"FR-013: {notas}"


def caso_e2_e3_igual_que_historia():
    """US3 escenarios 2 y 3 (FR-013, FR-014, FR-007): el resumen de --hasta t
    es el mismo texto que «historia <t>» al final de la partida original,
    también con pergaminos en el log."""
    descripcion = cripta(52, pergaminos=3)
    controlador, ruta = grabar(descripcion, 52, acciones=40)
    assert "PERGAMINO" in ruta.read_text(encoding="utf-8"), "la prueba necesita pergaminos en el log"
    azar = random.Random(5)
    for _ in range(6):
        t = azar.randint(0, controlador.partida.reloj)
        ok, notas = replay_hasta(descripcion, ruta, t)
        assert ok, notas
        esperado = texto_historia(controlador, t)
        assert notas[-len(esperado):] == esperado, f"FR-014: instante {t}\n{notas}\n{esperado}"


def caso_e4_uso_incorrecto():
    """US3 escenario 4 (FR-015) y FR-022: --hasta sin --replay, t inválido y
    --checkpoint-cada inválido terminan con código 2 sin abrir la ventana."""
    for argumentos in (("--hasta", "5"), ("--replay", "x.log", "--hasta", "abc"),
                       ("--replay", "x.log", "--hasta", "-4"), ("--checkpoint-cada", "0"),
                       ("--checkpoint-cada", "-2"), ("--checkpoint-cada", "x")):
        try:
            FabricaAplicacion(argumentos).ejecutar()
            raise AssertionError(f"FR-015/FR-022: {argumentos} debió terminar con error")
        except SystemExit as salida:
            assert salida.code == 2, f"{argumentos}: código {salida.code}"


def caso_e5_version_no_disponible():
    """US3 escenario 5 (FR-016): con una versión que ya no está, se informa
    como --replay y no se imprime ningún resumen."""
    descripcion = cripta(53, pergaminos=0)
    _, ruta = grabar(descripcion, 53, acciones=10)
    texto = ruta.read_text(encoding="utf-8").split("\n")
    partes = texto[0].split(" ")
    partes[2] = "version-vieja"
    texto[0] = " ".join(partes)
    ruta.write_text("\n".join(texto), encoding="utf-8")
    ok, notas = replay_hasta(descripcion, ruta, 50)
    assert not ok, "FR-016: debió fallar"
    assert any("reproducción fiel" in n for n in notas), notas
    assert not any(n.startswith("Instante") for n in notas), "FR-016: no debe imprimir resumen"


def caso_sc006_veinte_partidas():
    """SC-006: 20 partidas grabadas, 10 instantes cada una: --hasta igual a
    «historia» al final de la partida original."""
    for numero in range(20):
        descripcion = cripta(60 + numero, lado=4)
        controlador, ruta = grabar(descripcion, 60 + numero, acciones=20)
        azar = random.Random(numero)
        for _ in range(10):
            t = azar.randint(0, controlador.partida.reloj)
            ok, notas = replay_hasta(descripcion, ruta, t)
            assert ok, notas
            esperado = texto_historia(controlador, t)
            assert notas[-len(esperado):] == esperado, f"SC-006 partida {numero}, instante {t}"


CASOS = (caso_e1_t_posterior_al_final, caso_e2_e3_igual_que_historia, caso_e4_uso_incorrecto,
         caso_e5_version_no_disponible, caso_sc006_veinte_partidas)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}", flush=True)
    finally:
        cerrar_fuentes()
    print(f"prueba_replay_hasta OK ({len(CASOS)} casos)")
