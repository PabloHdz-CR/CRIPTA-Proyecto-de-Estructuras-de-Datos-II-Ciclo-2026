"""T008 (004-linea-tiempo, FR-001, FR-004): límite del bucle de eventos.

aplicar_accion(accion, limite=t) ejecuta la acción y después solo los eventos
con tiempo ≤ t (todos los de un mismo instante); sin límite, nada cambia.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py -m pruebas.prueba_limite_eventos
"""
import random

from cripta.adaptadores.partidaBinaria import CopiadorBinario
from pruebas.apoyo_linea import accion_al_azar, cripta_linea, huella_partida, partida_con_linea
from pruebas.apoyo_niebla import cerrar_fuentes


def caso_sin_limite_igual():
    """Sin límite (limite=None) el resultado es idéntico al de siempre, en
    200 acciones al azar."""
    descripcion = cripta_linea(7)
    a = partida_con_linea(descripcion, semilla=5, con_linea=False)
    b = partida_con_linea(descripcion, semilla=5, con_linea=False)
    azar = random.Random(11)
    for paso in range(200):
        accion = accion_al_azar(a, azar, con_pergaminos=False)
        ra = a.aplicar_accion(accion)
        rb = b.aplicar_accion(accion, limite=None)
        assert ra.aceptada == rb.aceptada, paso
        assert huella_partida(a) == huella_partida(b), f"paso {paso}: sin límite cambió el estado"


def caso_limite():
    """FR-001, FR-004: con límite t, después de la acción quedan ejecutados
    todos los eventos con tiempo ≤ t (también los de un mismo instante) y
    ninguno con tiempo > t; si la próxima decisión es ≤ t, el estado es el
    mismo que sin límite."""
    descripcion = cripta_linea(3)
    real = partida_con_linea(descripcion, semilla=9, con_linea=False)
    copiador = CopiadorBinario()
    azar = random.Random(21)
    probados = 0
    for paso in range(150):
        accion = accion_al_azar(real, azar, con_pergaminos=False)
        decision = real.jugador.evento_accion.tiempo
        copia = copiador.restaurar(copiador.tomar(real), real.servicio)
        t = decision + azar.randint(0, 150)
        resultado = copia.aplicar_accion(accion, limite=t)
        real.aplicar_accion(accion)
        if not resultado.aceptada or copia.terminada():
            continue
        probados += 1
        siguiente = copia.agenda.ver_siguiente()
        assert siguiente is not None, paso
        if siguiente is not copia.jugador.evento_accion:
            assert siguiente.tiempo > t, (
                f"FR-001/FR-004 paso {paso}: quedó un evento en {siguiente.tiempo} ≤ {t}")
        assert copia.reloj <= max(t, decision), f"paso {paso}: el reloj pasó el límite"
        if not real.terminada() and real.jugador.evento_accion.tiempo <= t:
            assert huella_partida(copia) == huella_partida(real), (
                f"paso {paso}: con la próxima decisión ≤ t debe ser el mismo estado")
    assert probados > 50, probados


CASOS = (caso_sin_limite_igual, caso_limite)

if __name__ == "__main__":
    try:
        for caso in CASOS:
            caso()
            print(f"[OK   ] {caso.__name__}")
    finally:
        cerrar_fuentes()
    print(f"prueba_limite_eventos OK ({len(CASOS)} casos)")
