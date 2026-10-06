"""Decide qué salas conviene pedir por adelantado, para que el jugador nunca
quede esperando ~400 ms parado frente a una puerta (§4.2).

Recorre el esqueleto en anchura (BFS) desde la sala donde está el jugador,
siguiendo solo salidas abiertas, y junta hasta un lote de 'limite' salas que
todavía no se hayan solicitado. El recorrido es determinista: la Cola procesa
en FIFO y las salidas de cada sala siempre se visitan en el orden N, S, E, O
(fijado por EsqueletoCripta.vecinas_abiertas), así que la latencia real de la
red nunca puede cambiar qué salas se eligen (§2.4).
"""
from ..estructuras.cola import Cola
from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.fuenteDatos import LIMITE_LOTE


class PlanificadorPrecarga:

    def siguiente_lote(self, esqueleto, id_sala_actual, limite=LIMITE_LOTE):
        """Devuelve una ListaEnlazada de hasta 'limite' ids de sala que conviene
        pedir ahora: las más cercanas a id_sala_actual que aún no se han
        solicitado. Marca esas salas como 'solicitada' de inmediato (antes de
        que ServicioDatos de verdad las pida), para que una segunda llamada
        seguida no proponga las mismas."""
        candidatos = ListaEnlazada()
        visitadas = ListaEnlazada()
        pendientes = Cola()
        pendientes.encolar(id_sala_actual)
        visitadas.agregar_al_final(id_sala_actual)

        while not pendientes.esta_vacia() and len(candidatos) < limite:
            actual = pendientes.desencolar()
            for id_vecina in esqueleto.vecinas_abiertas(actual):
                if visitadas.contiene(id_vecina):
                    continue
                visitadas.agregar_al_final(id_vecina)
                pendientes.encolar(id_vecina)
                entrada_vecina = esqueleto.buscar(id_vecina)
                ya_lista = entrada_vecina is not None and entrada_vecina.solicitada
                if not ya_lista and len(candidatos) < limite:
                    candidatos.agregar_al_final(id_vecina)
                    if entrada_vecina is not None:
                        entrada_vecina.solicitada = True
        return candidatos