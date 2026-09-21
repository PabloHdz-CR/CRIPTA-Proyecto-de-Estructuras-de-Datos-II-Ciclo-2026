"""Mediciones de la agenda de eventos (§4.1): evidencia para el Documento de
Decisiones.

Se puede ejecutar directamente (desde la carpeta que contiene 'cripta'):
    python -m cripta.controlador.bench.benchAgenda            (completo)
    python -m cripta.controlador.bench.benchAgenda --rapido   (versión corta)

Más adelante el modo --bench del programa llamará a ejecutar().

Mide cuatro cosas:
  1. Que todas las agendas entreguen los eventos en el MISMO orden.
  2. Cuánto cuesta un ciclo "sacar el próximo evento y programar otro" con
     100 a 10 000 eventos pendientes (comparando la decisión y las alternativas).
  3. Cuántas comparaciones hace cada estructura por ciclo.
  4. Cancelación perezosa (la decisión) contra cancelación inmediata.
"""
import random
import sys

from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from .alternativasAgenda import (CLAVES_AGENDA, EventoBench, EventoContado,
                                 crear_agenda)
from .medidor import Medidor
from .reporte import Reporte

SEMILLA = 2026
LIMITE_CICLO_MS = 20   # §5.2: un ciclo completo entre decisiones < 20 ms


def listas_iguales(a, b):
    """True si dos ListaEnlazada tienen los mismos elementos en el mismo orden."""
    if len(a) != len(b):
        return False
    recorrido_b = iter(b)
    for elemento in a:
        if elemento != next(recorrido_b):
            return False
    return True


def elegir_al_azar(elementos, cantidad, azar):
    """Elige EXACTAMENTE 'cantidad' elementos al azar recorriendo la lista una sola vez.

    Es el "muestreo por selección" (algoritmo S de Knuth): cada elemento se toma
    con probabilidad (los que faltan por tomar) / (los que quedan por ver).
    Al final quedan justo 'cantidad' elegidos, todos con la misma probabilidad,
    y con la misma semilla siempre salen los mismos. Solo recorre en orden, así
    que sirve para una lista enlazada.
    """
    elegidos = ListaEnlazada()
    por_ver = len(elementos)
    faltan = cantidad
    for elemento in elementos:
        if faltan > 0 and azar.random() * por_ver < faltan:
            elegidos.agregar_al_final(elemento)
            faltan -= 1
        por_ver -= 1
    return elegidos


class EscenarioCiclos:
    """N eventos pendientes; después, 'ciclos' veces: sacar el próximo evento y
    programar otro un poco más adelante. Es el trabajo típico de la agenda."""

    def __init__(self, clave, ciclos, clase_evento=EventoBench):
        self._clave = clave
        self._ciclos = ciclos
        self._clase_evento = clase_evento
        self._agenda = None
        self._azar = None
        self._secuencia = 0

    def preparar(self, n):
        self._azar = random.Random(SEMILLA)
        self._agenda = crear_agenda(self._clave)
        self._secuencia = 0
        for _ in range(n):
            self._secuencia += 1
            evento = self._clase_evento(self._azar.randint(0, 1000), self._secuencia)
            self._agenda.programar(evento)

    def ejecutar(self):
        agenda = self._agenda
        azar = self._azar
        for _ in range(self._ciclos):
            evento = agenda.siguiente()
            self._secuencia += 1
            agenda.programar(self._clase_evento(
                evento.tiempo + azar.randint(1, 500), self._secuencia))

    def ejecutar_y_registrar(self):
        """Igual que ejecutar(), pero devuelve (en una ListaEnlazada) el orden de
        los eventos sacados."""
        agenda = self._agenda
        azar = self._azar
        orden = ListaEnlazada()
        for _ in range(self._ciclos):
            evento = agenda.siguiente()
            orden.agregar_al_final((evento.tiempo, evento.secuencia))
            self._secuencia += 1
            agenda.programar(self._clase_evento(
                evento.tiempo + azar.randint(1, 500), self._secuencia))
        return orden


class EscenarioCancelacion:
    """N eventos pendientes; se cancela una fracción al azar y luego se vacía la
    agenda. Mide el costo total de cancelar y de sacar todos los eventos vivos."""

    def __init__(self, clave, fraccion):
        self._clave = clave
        self._fraccion = fraccion
        self._agenda = None
        self._por_cancelar = ListaEnlazada()
        self._n = 0

    def preparar(self, n):
        self._n = n
        azar = random.Random(SEMILLA)
        self._agenda = crear_agenda(self._clave)
        eventos = ListaEnlazada()
        for secuencia in range(1, n + 1):
            evento = EventoBench(azar.randint(0, 1000), secuencia)
            eventos.agregar_al_final(evento)
            self._agenda.programar(evento)
        self._por_cancelar = elegir_al_azar(eventos, int(n * self._fraccion), azar)

    def ejecutar(self):
        for evento in self._por_cancelar:
            self._agenda.cancelar(evento)
        # Tope de seguridad: una agenda con errores podría no vaciarse nunca
        for _ in range(self._n + 1):
            if self._agenda.siguiente() is None:
                return
        raise RuntimeError("La agenda no se vació: entregó más eventos de los que tenía")

    def ejecutar_y_registrar(self):
        for evento in self._por_cancelar:
            self._agenda.cancelar(evento)
        orden = ListaEnlazada()
        for _ in range(self._n + 1):
            evento = self._agenda.siguiente()
            if evento is None:
                return orden
            orden.agregar_al_final((evento.tiempo, evento.secuencia))
        raise RuntimeError("La agenda no se vació: entregó más eventos de los que tenía")

    def cancelados(self):
        return len(self._por_cancelar)


def ciclos_para(n, rapido):
    """Con muchos eventos las alternativas lentas tardan mucho: se hacen menos ciclos."""
    if rapido:
        return 100
    if n <= 1000:
        return 500
    return 100


def verificar_mismo_orden(rapido):
    """Todas las agendas deben sacar los eventos exactamente en el mismo orden."""
    n = 100 if rapido else 300
    referencia = None
    for clave in CLAVES_AGENDA:
        escenario = EscenarioCiclos(clave, 200)
        escenario.preparar(n)
        orden = escenario.ejecutar_y_registrar()
        if referencia is None:
            referencia = orden
        elif not listas_iguales(orden, referencia):
            raise RuntimeError(f"La agenda '{clave}' sacó los eventos en otro orden")
    # La cancelación perezosa y la inmediata también deben coincidir
    for fraccion in (0.1, 0.5, 0.9):
        perezosa = EscenarioCancelacion("monticulo_enlazado", fraccion)
        inmediata = EscenarioCancelacion("reconstruida", fraccion)
        perezosa.preparar(100)
        inmediata.preparar(100)
        if not listas_iguales(perezosa.ejecutar_y_registrar(),
                              inmediata.ejecutar_y_registrar()):
            raise RuntimeError("La cancelación inmediata difiere de la perezosa")


def comparaciones_por_ciclo(clave, n, ciclos):
    escenario = EscenarioCiclos(clave, ciclos, EventoContado)
    escenario.preparar(n)
    EventoContado.comparaciones = 0     # no se cuentan las de preparar()
    escenario.ejecutar()
    return EventoContado.comparaciones / ciclos


def ejecutar(reporte=None, rapido=False):
    """Corre todas las mediciones. Devuelve el Reporte con las tablas."""
    if reporte is None:
        reporte = Reporte()
    repeticiones = 3 if rapido else 5
    medidor = Medidor(repeticiones)
    tamanos = (100, 300) if rapido else (100, 300, 1000, 3000, 10000)

    reporte.titulo("Agenda de eventos: mediciones (§4.1)")
    verificar_mismo_orden(rapido)
    reporte.nota("Verificación: todas las agendas sacan los eventos en el mismo orden.")

    # 1. Costo de un ciclo según la cantidad de eventos pendientes
    filas = ListaEnlazada()
    ultimo_tiempo_decision = 0.0
    for n in tamanos:
        ciclos = ciclos_para(n, rapido)
        mejor_tiempo = None
        mejor_nombre = ""
        tiempo_decision = None
        for clave in CLAVES_AGENDA:
            medicion = medidor.medir(EscenarioCiclos(clave, ciclos), n)
            por_ciclo = medicion.minimo / ciclos * 1e6            # microsegundos
            promedio = medicion.promedio / ciclos * 1e6
            nombre = crear_agenda(clave).nombre
            if clave == "monticulo_enlazado":
                tiempo_decision = por_ciclo
                ultimo_tiempo_decision = por_ciclo
            if mejor_tiempo is None or por_ciclo < mejor_tiempo:
                mejor_tiempo = por_ciclo
                mejor_nombre = nombre
            filas.agregar_al_final((str(n), nombre, f"{por_ciclo:.1f}", f"{promedio:.1f}",
                                    f"{por_ciclo / tiempo_decision:.1f}x"))
        reporte.nota(f"  Con {n} eventos la más rápida fue: {mejor_nombre}")
    reporte.tabla(
        "1. Tiempo por ciclo (sacar el próximo y programar otro), en microsegundos",
        ("eventos", "estructura", "mínimo µs", "promedio µs", "vs decisión"), filas)

    # 2. Comparaciones por ciclo
    filas = ListaEnlazada()
    tamanos_comp = (100, 300) if rapido else (300, 1000)
    for n in tamanos_comp:
        for clave in CLAVES_AGENDA:
            cantidad = comparaciones_por_ciclo(clave, n, 100)
            filas.agregar_al_final((str(n), crear_agenda(clave).nombre, f"{cantidad:.1f}"))
    reporte.tabla("2. Comparaciones por ciclo (cada comparación es una llamada a <)",
                  ("eventos", "estructura", "comparaciones"), filas)

    # 3. Cancelación perezosa contra cancelación inmediata
    n = 100 if rapido else 300
    filas = ListaEnlazada()
    for fraccion in (0.1, 0.5, 0.9):
        for clave in ("monticulo_enlazado", "reconstruida"):
            escenario = EscenarioCancelacion(clave, fraccion)
            medicion = medidor.medir(escenario, n)
            nombre = crear_agenda(clave).nombre
            filas.agregar_al_final((f"{int(fraccion * 100)}%", nombre,
                                    str(escenario.cancelados()),
                                    f"{medicion.minimo * 1000:.2f}"))
    reporte.tabla(f"3. Cancelar una fracción de {n} eventos y vaciar la agenda, en milisegundos",
                  ("cancelados", "estrategia", "eventos", "mínimo ms"), filas)

    # 4. Lectura frente al requisito de §5.2
    reporte.nota("")
    reporte.nota(f"Con la decisión (montículo de nodos) y {tamanos[len(tamanos) - 1]} eventos "
                 f"pendientes, un evento cuesta ~{ultimo_tiempo_decision:.1f} µs: en "
                 f"{LIMITE_CICLO_MS} ms caben ~{int(LIMITE_CICLO_MS * 1000 / ultimo_tiempo_decision)} "
                 f"eventos (§5.2).")
    return reporte


def main():
    rapido = "--rapido" in sys.argv
    ejecutar(Reporte(), rapido)


if __name__ == "__main__":
    main()