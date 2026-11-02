"""Equivalencia del cazador con un cálculo desde cero (001-terreno-cazador).

Requisitos que ejerce: FR-017 (la decisión de cada turno es idéntica a la que
se obtendría calculando la ruta desde cero; reutilizar el mapa no la cambia),
FR-018 (determinismo: misma semilla, misma secuencia), FR-022 (guardar y
cargar entre turnos no cambia la decisión) y SC-002 (al menos 1000
situaciones al azar, 100 % de coincidencia con un cálculo independiente).

Cada situación sale de random.Random(SEMILLA + i): una cripta de 4 a 12 salas
de apoyo_terreno.cripta_al_azar (costos en {1, 50, 100, 250, 300} o sin
declarar, puertas cerradas, salidas de un solo sentido y, en una minoría,
dos salidas hacia la misma vecina), un rango entre 0 y la suma de todos los
costos, y varios turnos encadenados con cambios entre ellos: el jugador se
mueve (aplicar_accion, y el cazador actúa por la agenda), una puerta se abre
o se cierra por el Mutador, se deshace la última acción con el Diario, o la
partida se guarda y se carga (PartidaBinaria, T051) y se sigue con la
cargada. En
cada turno, la acción y el costo del cazador deben ser idénticos a los del
oráculo Bellman-Ford de pruebas/oraculo_rutas.py. Si difieren se corrige el
código, nunca el oráculo.

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_cazador_equivalencia
"""
import random
import tempfile
from pathlib import Path

from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.modelo.nucleo.accion import Esperar, Mover
from cripta.modelo.nucleo.diario import Diario
from pruebas import oraculo_rutas
from pruebas.apoyo_terreno import (
    activar_sala, buscar_enemigo, cerrar_fuentes, cripta_al_azar, enemigo, ficha_enemigo,
    partida_minima, suma_de_costos)

SITUACIONES = 1000
SEMILLA = 20261101
FICHA = "ent_cazador"
ARCHIVO = Path(tempfile.mkdtemp(prefix="prueba_equivalencia_")) / "partida.bin"
CARGAS = [0]                     # cuántas veces se guardó y se cargó (T051)


def _salidas_abiertas(sala):
    return [s for s in sala.salidas if s is not None and not s.cerrada]


def _todas_las_salidas(partida):
    return [s for sala in partida.mundo for s in sala.salidas if s is not None]


def _guardar_y_cargar(partida):
    """Guarda la partida y devuelve la cargada (con un Diario nuevo, como el
    Controlador al continuar una partida). El servicio ya tiene la cripta."""
    PartidaBinaria.guardar(partida, ARCHIVO)
    cargada = PartidaBinaria.cargar(ARCHIVO, partida.servicio)
    CARGAS[0] += 1
    cargada.conectar_diario(Diario())
    return cargada


def _cambiar(partida, azar):
    """Un cambio entre dos turnos del cazador. Devuelve (descripción, partida):
    la partida es otra si se guardó y se cargó."""
    tipo = azar.choice(("mover", "mover", "puerta", "deshacer", "guardar"))
    if tipo == "guardar":
        return "guardar y cargar", _guardar_y_cargar(partida)
    if tipo == "deshacer":
        if partida.puede_retroceder():
            partida.deshacer()
            return "deshacer", partida
        tipo = "puerta"
    if tipo == "puerta":
        salida = azar.choice(_todas_las_salidas(partida))
        # Por el Mutador y dentro de un intervalo del Diario, como cualquier
        # cambio del juego: así también se puede deshacer después.
        partida.diario.abrir_intervalo(partida)
        partida.mutador.asignar(salida, "cerrada", not salida.cerrada)
        partida.diario.cerrar_intervalo()
        return f"puerta {salida.origen.id}{salida.direccion} cerrada={salida.cerrada}", partida
    abiertas = _salidas_abiertas(partida.mundo.sala(partida.jugador.sala))
    accion = Mover(azar.choice(abiertas).direccion) if abiertas else Esperar()
    resultado = partida.aplicar_accion(accion)
    assert resultado.aceptada, resultado.motivo
    return f"jugador {accion}", partida


def una_situacion(indice):
    """Corre la situación 'indice' y devuelve la secuencia de decisiones."""
    semilla = SEMILLA + indice
    azar = random.Random(semilla)
    descripcion = cripta_al_azar(azar)
    salas = [id_sala for id_sala, _ in descripcion]
    # Sala de salida aislada (la de id mayor): la partida no termina por llegar a ella.
    descripcion = descripcion + ((max(salas) + 1, ()),)
    rango = azar.randint(0, suma_de_costos(descripcion))
    sala_cazador = azar.choice(salas)
    sala_jugador = azar.choice(salas)
    turnos = azar.randint(3, 6)
    partida = partida_minima(descripcion, sala_inicial=sala_jugador, semilla=semilla,
                             enemigos=(enemigo(sala_cazador, "c-1", FICHA),),
                             fichas=(ficha_enemigo(FICHA, "cazador", rango=rango),),
                             diario=Diario())
    activar_sala(partida, sala_cazador)
    cazador = buscar_enemigo(partida, "c-1")
    secuencia = []
    historia = [f"semilla={semilla} rango={rango} cazador={sala_cazador} jugador={sala_jugador}",
                f"cripta={descripcion}"]
    for turno in range(turnos):
        if partida.terminada() or not cazador.vivo:
            break
        accion = cazador.comportamiento.decidir(cazador, partida)
        costo = partida.costo_de(cazador, accion)
        esperada = oraculo_rutas.decidir_en_partida(partida, cazador, rango)
        historia.append(f"turno {turno}: cazador en {cazador.sala}, jugador en "
                        f"{partida.jugador.sala} → {(accion, costo)}")
        if (accion, costo) != esperada:
            raise AssertionError(
                f"situación {indice} difiere en el turno {turno}: cazador {(accion, costo)}, "
                f"oráculo {esperada}\n  " + "\n  ".join(historia))
        secuencia.append((accion, costo))
        cambio, partida = _cambiar(partida, azar)
        historia.append("  cambio: " + cambio)
        cazador = buscar_enemigo(partida, "c-1")        # en la cargada, es otro objeto
    return tuple(secuencia)


def todas():
    """Las SITUACIONES situaciones, en orden. Devuelve (secuencias, decisiones)."""
    secuencias = []
    decisiones = 0
    for indice in range(SITUACIONES):
        secuencia = una_situacion(indice)
        secuencias.append(secuencia)
        decisiones += len(secuencia)
        if indice % 50 == 49:
            cerrar_fuentes()
    cerrar_fuentes()
    return secuencias, decisiones


def main():
    primera, decisiones = todas()
    cargas = CARGAS[0]
    assert decisiones >= SITUACIONES, decisiones
    assert cargas >= 100, f"pocas cargas entre turnos: {cargas}"
    tipos = {type(accion).__name__ for secuencia in primera for accion, _ in secuencia}
    assert tipos == {"Mover", "Esperar", "Atacar"}, f"faltan tipos de decisión: {tipos}"
    # FR-018: la misma semilla da exactamente la misma secuencia.
    segunda, _ = todas()
    assert primera == segunda, "dos pasadas con la misma semilla dieron secuencias distintas"
    print(f"prueba_cazador_equivalencia OK ({SITUACIONES} situaciones, {decisiones} "
          f"decisiones idénticas al oráculo, {cargas} guardados y cargas entre turnos, "
          f"dos pasadas iguales)")


main()
