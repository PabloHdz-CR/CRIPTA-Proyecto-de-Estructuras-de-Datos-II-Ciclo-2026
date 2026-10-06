"""Mediciones de la caché de fichas (§4.4): LRU (la decisión) contra FIFO
(D31), con un patrón de acceso DESIGUAL: el 20% de las fichas reciben el 80%
de las consultas (un enemigo común se consulta todo el tiempo; un objeto raro,
casi nunca). Es el escenario donde LRU debería distinguirse de verdad.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchCache            (completo)
    python -m cripta.controlador.bench.benchCache --rapido   (versión corta)
"""
import random
import sys

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .alternativasDatos import CLAVES_CACHE, crear_cache, nombre_cache
from .medidor import Medidor
from .reporte import Reporte

SEMILLA = 2026
FRACCION_POPULARES = 0.2     # el 20% de las fichas...
PROBABILIDAD_POPULAR = 0.8   # ...recibe el 80% de los accesos


def generar_patron(azar, total_fichas, accesos):
    """Genera, en una ListaEnlazada, 'accesos' ids de ficha (como texto),
    siguiendo el patrón 80/20. Los ids "populares" son los de menor número
    (f0, f1, ...), una convención interna de este generador, no del programa."""
    cantidad_populares = max(1, int(total_fichas * FRACCION_POPULARES))
    patron = ListaEnlazada()
    for _ in range(accesos):
        if azar.random() < PROBABILIDAD_POPULAR:
            numero = azar.randrange(cantidad_populares)
        else:
            numero = azar.randrange(cantidad_populares, total_fichas)
        patron.agregar_al_final(f"f{numero}")
    return patron


class EscenarioAccesoCache:
    """Recorre un patrón de accesos ya generado (fijo, para comparar caches en
    igualdad de condiciones) sobre una caché nueva de la clave indicada."""

    def __init__(self, clave, capacidad, patron):
        self._clave = clave
        self._capacidad = capacidad
        self._patron = patron
        self._cache = None

    def preparar(self, n):
        self._cache = crear_cache(self._clave, self._capacidad)

    def ejecutar(self):
        cache = self._cache
        for id_ficha in self._patron:
            ficha = cache.obtener(id_ficha)
            if ficha is None:
                cache.insertar(id_ficha, id_ficha)   # "ficha" de mentira: basta su id


def tasa_de_acierto(clave, capacidad, total_fichas, accesos, semilla=SEMILLA):
    """Ejecuta el patrón UNA vez y devuelve (aciertos, fallos) reales (no
    tiempos): es la evidencia principal, no depende de la velocidad de la
    máquina. El mismo patrón se genera siempre igual con la misma semilla,
    así que LRU y FIFO se comparan con EXACTAMENTE la misma secuencia."""
    azar = random.Random(semilla)
    patron = generar_patron(azar, total_fichas, accesos)
    cache = crear_cache(clave, capacidad)
    for id_ficha in patron:
        ficha = cache.obtener(id_ficha)
        if ficha is None:
            cache.insertar(id_ficha, id_ficha)
    return cache.aciertos, cache.fallos


def verificar_mismo_patron():
    """Ambas caches ven EXACTAMENTE la misma secuencia de accesos."""
    azar1 = random.Random(SEMILLA)
    azar2 = random.Random(SEMILLA)
    patron1 = generar_patron(azar1, 100, 500)
    patron2 = generar_patron(azar2, 100, 500)
    iter2 = iter(patron2)
    for id1 in patron1:
        if id1 != next(iter2):
            raise RuntimeError("El patrón de acceso no es reproducible con la misma semilla")


def ejecutar(reporte=None, rapido=False):
    if reporte is None:
        reporte = Reporte()
    medidor = Medidor(3 if rapido else 5)
    capacidad = 25                      # --cache-size por defecto
    total_fichas = 100                  # fichas distintas que existen en la cripta
    accesos_lista = (500, 2000) if rapido else (500, 2000, 10000, 50000)

    reporte.titulo("Caché de fichas: mediciones (§4.4)")
    verificar_mismo_patron()
    reporte.nota("Verificación: LRU y FIFO reciben exactamente el mismo patrón de accesos.")
    reporte.nota(f"Patrón: {int(FRACCION_POPULARES * 100)}% de las fichas reciben "
                 f"el {int(PROBABILIDAD_POPULAR * 100)}% de los accesos. "
                 f"Capacidad de la caché: {capacidad} de {total_fichas} fichas posibles.")

    # 1. Tasa de acierto (la evidencia principal, no depende de la máquina)
    filas = ListaEnlazada()
    for accesos in accesos_lista:
        for clave in CLAVES_CACHE:
            aciertos, fallos = tasa_de_acierto(clave, capacidad, total_fichas, accesos)
            porcentaje = aciertos / (aciertos + fallos) * 100
            filas.agregar_al_final((str(accesos), nombre_cache(clave),
                                    str(aciertos), str(fallos), f"{porcentaje:.1f}%"))
    reporte.tabla("1. Aciertos y fallos con patrón 80/20 (misma secuencia para ambas)",
                  ("accesos", "política", "aciertos", "fallos", "tasa de acierto"), filas)

    # 2. Tiempo por acceso (evidencia secundaria: confirma que no hay sorpresas de velocidad)
    filas = ListaEnlazada()
    for accesos in accesos_lista:
        azar = random.Random(SEMILLA)
        patron = generar_patron(azar, total_fichas, accesos)
        tiempo_decision = None
        for clave in CLAVES_CACHE:
            medicion = medidor.medir(EscenarioAccesoCache(clave, capacidad, patron), accesos)
            por_acceso = medicion.minimo / accesos * 1e6     # microsegundos
            if clave == "lru":
                tiempo_decision = por_acceso
            filas.agregar_al_final((str(accesos), nombre_cache(clave), f"{por_acceso:.2f}",
                                    f"{por_acceso / tiempo_decision:.1f}x"))
    reporte.tabla("2. Tiempo por acceso, en microsegundos",
                  ("accesos", "política", "mínimo µs", "vs decisión"), filas)

    reporte.nota("")
    reporte.nota("Con un patrón de acceso desigual, LRU conserva en memoria las fichas "
                 "populares aunque hayan entrado hace tiempo; FIFO las desaloja igual que "
                 "a cualquier otra si entraron antes, sin importar cuánto se sigan usando.")
    return reporte


def main():
    ejecutar(Reporte(), "--rapido" in sys.argv)


if __name__ == "__main__":
    main()