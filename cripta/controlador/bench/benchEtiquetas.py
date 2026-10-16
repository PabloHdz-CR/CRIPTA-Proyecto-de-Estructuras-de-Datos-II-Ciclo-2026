"""Mediciones de MapaEtiquetas (D47): etiquetas estables con búsqueda lineal
sobre una ListaEnlazada, contra la alternativa descartada de recalcular las
etiquetas con un Etiquetador nuevo en cada turno (más barata, pero inestable:
"Rata #1" puede cambiar de dueño entre turnos).

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchEtiquetas            (completo)
    python -m cripta.controlador.bench.benchEtiquetas --rapido   (versión corta)

Un "turno" es lo que hace el Controlador entre dos decisiones del jugador:
etiquetar los ENEMIGOS_EN_SALA enemigos visibles (ConstructorEstadoVista) y
resolver una etiqueta para atacar (TraductorComandos). Peor caso: los
enemigos de la sala son los últimos etiquetados (al final de la lista).
"""
import sys

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...vista.etiquetador import Etiquetador
from ..mapaEtiquetas import MapaEtiquetas
from .medidor import Medidor
from .reporte import Reporte

ENEMIGOS_EN_SALA = 5
TURNOS = 2000
PRESUPUESTO_CICLO_MS = 20          # §5.2


class _EnemigoSintetico:
    def __init__(self, numero):
        self.id_instancia = f"e-{numero}"
        self.nombre = f"Tipo {numero % 7}"


class EscenarioMapa:
    """La decisión: MapaEtiquetas con k enemigos ya etiquetados."""

    def __init__(self):
        self._mapa = None
        self._sala = None

    def preparar(self, k):
        self._mapa = MapaEtiquetas()
        todos = ListaEnlazada()
        for numero in range(k):
            enemigo = _EnemigoSintetico(numero)
            todos.agregar_al_final(enemigo)
            self._mapa.etiqueta_de(enemigo)
        self._sala = ListaEnlazada()
        for numero in range(max(0, k - ENEMIGOS_EN_SALA), k):
            self._sala.agregar_al_final(_EnemigoSintetico(numero))

    def ejecutar(self):
        mapa = self._mapa
        for _ in range(TURNOS):
            ultima = None
            for enemigo in self._sala:
                ultima = mapa.etiqueta_de(enemigo)
            mapa.resolver(ultima)


class EscenarioRecalcular:
    """La alternativa descartada: un Etiquetador nuevo por turno, solo con
    los enemigos de la sala (no depende de k)."""

    def __init__(self):
        self._sala = None

    def preparar(self, k):
        self._sala = ListaEnlazada()
        for numero in range(max(0, k - ENEMIGOS_EN_SALA), k):
            self._sala.agregar_al_final(_EnemigoSintetico(numero))

    def ejecutar(self):
        for _ in range(TURNOS):
            etiquetador = Etiquetador()
            for enemigo in self._sala:
                etiquetador.etiqueta(enemigo.nombre)


def verificar_estabilidad():
    """La razón de la decisión: con MapaEtiquetas la etiqueta no cambia
    aunque cambie el orden o el grupo de enemigos visibles."""
    mapa = MapaEtiquetas()
    a, b = _EnemigoSintetico(0), _EnemigoSintetico(7)       # mismo tipo
    primera = mapa.etiqueta_de(a)
    mapa.etiqueta_de(b)
    if mapa.etiqueta_de(a) != primera or mapa.resolver(primera) != a.id_instancia:
        raise RuntimeError("MapaEtiquetas no conserva la etiqueta")


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    tamanos = (10, 50, 200) if rapido else (10, 50, 200, 1000)

    reporte.titulo("Etiquetas de enemigos: mediciones (D47)")
    verificar_estabilidad()
    reporte.nota("Verificación: MapaEtiquetas conserva la etiqueta de cada instancia.")

    filas = ListaEnlazada()
    for k in tamanos:
        mapa = medidor.medir(EscenarioMapa(), k).minimo / TURNOS * 1e6
        recalcular = medidor.medir(EscenarioRecalcular(), k).minimo / TURNOS * 1e6
        porcentaje = mapa / (PRESUPUESTO_CICLO_MS * 1000) * 100
        filas.agregar_al_final((str(k), f"{mapa:.1f}", f"{recalcular:.1f}",
                                f"{porcentaje:.2f} %"))
    reporte.tabla(f"Costo por turno ({ENEMIGOS_EN_SALA} enemigos en sala + 1 resolver), "
                  "en microsegundos",
                  ("etiquetados k", "MapaEtiquetas µs", "recalcular µs",
                   f"mapa / {PRESUPUESTO_CICLO_MS} ms"), filas)
    reporte.nota("")
    reporte.nota("Recalcular no depende de k pero da etiquetas inestables (el ataque "
                 "podría ir al enemigo equivocado). MapaEtiquetas crece lineal con k; "
                 "la columna derecha muestra qué parte del presupuesto de §5.2 consume.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()
