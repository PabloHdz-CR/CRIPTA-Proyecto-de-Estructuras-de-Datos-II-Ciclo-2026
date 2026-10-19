"""Mediciones del rastro del jugador (§4.7): un solo campo por sala con
caducidad detectada al consultar, contra la alternativa descartada de guardar
el recorrido del jugador como una lista de visitas (sala, instante) y buscar
en ella la visita más fresca de cada vecina.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchRastro            (completo)
    python -m cripta.controlador.bench.benchRastro --rapido   (versión corta)

La cripta sintética es un pasillo de n salas (cada una con salida E y O). El
jugador camina L pasos por el pasillo y termina junto al rastreador, que está
en la sala del medio: sus dos vecinas tienen rastro fresco.
"""
import sys

from ...modelo.actores.comportamientos import Rastreador
from ...modelo.nucleo.accion import Esperar
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.mundo.sala import Sala
from ...modelo.mundo.salida import Salida
from ...modelo.nucleo.constantes import VIGENCIA_RASTRO
from .medidor import Medidor
from .reporte import Reporte

DECISIONES = 2000              # decisiones por medición del campo único
DECISIONES_LISTA = 20          # la lista de visitas es mucho más lenta
PASO = 10                      # unidades de tiempo por paso del jugador
PRESUPUESTO_CICLO_MS = 20      # §5.2


class _Mundo:
    def __init__(self, salas):
        self._salas = salas                    # tupla: id de sala -> Sala

    def sala(self, id_sala):
        return self._salas[id_sala]


class _Partida:
    """Lo único que el Rastreador consulta: el mundo y el reloj."""

    def __init__(self, mundo, reloj):
        self.mundo = mundo
        self.reloj = reloj


class _Enemigo:
    def __init__(self, sala):
        self.sala = sala


def _pasillo(n):
    def salidas(i):
        este = Salida("E", i + 1) if i + 1 < n else None
        oeste = Salida("O", i - 1) if i > 0 else None
        return (None, None, este, oeste)
    return tuple(Sala(i, f"Sala {i}", salidas(i)) for i in range(n))


def _recorrer(salas, pasos, visitas=None):
    """El jugador camina `pasos` pasos de ida y vuelta por el pasillo y termina
    en la vecina este del medio. Devuelve el reloj final."""
    n = len(salas)
    reloj = 0
    for paso in range(pasos):
        vuelta = paso % (2 * n - 2) if n > 1 else 0
        id_sala = vuelta if vuelta < n else 2 * n - 2 - vuelta
        reloj = paso * PASO
        salas[id_sala].rastro = reloj
        if visitas is not None:
            visitas.agregar_al_final((id_sala, reloj))
    reloj += PASO
    final = n // 2 + 1
    salas[final].rastro = reloj
    if visitas is not None:
        visitas.agregar_al_final((final, reloj))
    return reloj


class EscenarioCampo:
    """La decisión: el Rastreador real sobre Sala.rastro (O(salidas))."""

    def __init__(self, pasos):
        self._pasos = pasos
        self._partida = None
        self._enemigo = None

    def preparar(self, n):
        salas = _pasillo(n)
        reloj = _recorrer(salas, self._pasos)
        self._partida = _Partida(_Mundo(salas), reloj)
        self._enemigo = _Enemigo(n // 2)

    def ejecutar(self):
        rastreador, enemigo, partida = Rastreador(), self._enemigo, self._partida
        for _ in range(DECISIONES):
            rastreador.decidir_sin_jugador(enemigo, partida)


def decidir_con_visitas(sala, visitas, reloj):
    """La alternativa descartada: para cada vecina abierta, busca su última
    visita recorriendo TODO el recorrido. O(salidas x L)."""
    mejor_salida = None
    mejor_rastro = None
    for salida in sala.vecinas_abiertas():
        ultima = None
        for id_sala, instante in visitas:
            if id_sala == salida.destino:
                ultima = instante
        if ultima is None or reloj - ultima >= VIGENCIA_RASTRO:
            continue
        if (mejor_rastro is None or ultima > mejor_rastro
                or (ultima == mejor_rastro and salida.destino < mejor_salida.destino)):
            mejor_salida = salida
            mejor_rastro = ultima
    return mejor_salida


class EscenarioVisitas:
    def __init__(self, pasos):
        self._pasos = pasos
        self._sala = None
        self._visitas = None
        self._reloj = 0

    def preparar(self, n):
        salas = _pasillo(n)
        self._visitas = ListaEnlazada()
        self._reloj = _recorrer(salas, self._pasos, self._visitas)
        self._sala = salas[n // 2]

    def ejecutar(self):
        for _ in range(DECISIONES_LISTA):
            decidir_con_visitas(self._sala, self._visitas, self._reloj)


class EscenarioVarios:
    """k rastreadores, cada uno en su sala, deciden en el mismo ciclo."""

    def __init__(self):
        self._partida = None
        self._enemigos = None

    def preparar(self, k):
        n = 2 * k + 3
        salas = _pasillo(n)
        reloj = _recorrer(salas, n)
        self._partida = _Partida(_Mundo(salas), reloj)
        self._enemigos = ListaEnlazada()
        for numero in range(k):
            self._enemigos.agregar_al_final(_Enemigo(1 + 2 * numero))

    def ejecutar(self):
        rastreador, partida = Rastreador(), self._partida
        for _ in range(DECISIONES // 20):
            for enemigo in self._enemigos:
                rastreador.decidir_sin_jugador(enemigo, partida)


def verificar_reglas():
    """Las reglas de §2.9 y §4.7 que la medición da por buenas: va al rastro
    más fresco, empata hacia el menor id y un rastro de 400 ya no cuenta."""
    salas = _pasillo(5)
    mundo = _Mundo(salas)
    rastreador, enemigo = Rastreador(), _Enemigo(2)
    salas[1].rastro, salas[3].rastro = 100, 120
    if rastreador.decidir_sin_jugador(enemigo, _Partida(mundo, 130)).direccion != "E":
        raise RuntimeError("El rastreador no siguió el rastro más fresco")
    salas[1].rastro = 120
    if rastreador.decidir_sin_jugador(enemigo, _Partida(mundo, 130)).direccion != "O":
        raise RuntimeError("El empate no fue hacia el menor id de sala")
    vencido = rastreador.decidir_sin_jugador(enemigo, _Partida(mundo, 120 + VIGENCIA_RASTRO))
    if not isinstance(vencido, Esperar):
        raise RuntimeError("Un rastro de 400 unidades todavía se siguió")


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    tamanos = (50, 500) if rapido else (50, 500, 5000)
    recorridos = (100, 2000) if rapido else (100, 2000, 20000)
    rastreadores = (1, 10, 100) if rapido else (1, 10, 100, 1000)

    reporte.titulo("Rastro del jugador: mediciones (§4.7)")
    verificar_reglas()
    reporte.nota("Verificación: sigue el rastro más fresco, empata al menor id y "
                 f"descarta rastros de {VIGENCIA_RASTRO} o más unidades.")

    filas = ListaEnlazada()
    for n in tamanos:
        for pasos in recorridos:
            campo = medidor.medir(EscenarioCampo(pasos), n).minimo / DECISIONES * 1e6
            visitas = medidor.medir(EscenarioVisitas(pasos), n).minimo / DECISIONES_LISTA * 1e6
            filas.agregar_al_final((str(n), str(pasos), f"{campo:.2f}", f"{visitas:.1f}",
                                    f"{visitas / campo:.0f}x"))
    reporte.tabla("Costo de UNA decisión del rastreador, en microsegundos",
                  ("salas n", "pasos L", "campo único µs", "lista de visitas µs",
                   "lista / campo"), filas)

    filas = ListaEnlazada()
    ciclos = DECISIONES // 20
    for k in rastreadores:
        total = medidor.medir(EscenarioVarios(), k).minimo / ciclos * 1e6
        porcentaje = total / (PRESUPUESTO_CICLO_MS * 1000) * 100
        filas.agregar_al_final((str(k), f"{total:.1f}", f"{total / k:.2f}",
                                f"{porcentaje:.2f} %"))
    reporte.tabla("Varios rastreadores en un ciclo, en microsegundos",
                  ("rastreadores k", "ciclo µs", "por rastreador µs",
                   f"ciclo / {PRESUPUESTO_CICLO_MS} ms"), filas)
    reporte.nota("")
    reporte.nota("El campo único no depende de n ni de L (solo de las salidas, 2 aquí) y "
                 "el ciclo crece lineal con k. La lista de visitas crece con L.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
