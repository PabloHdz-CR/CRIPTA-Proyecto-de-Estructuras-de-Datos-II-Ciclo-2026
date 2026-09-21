"""Alternativas descartadas para la agenda de eventos (§4.1), SOLO para medir.

El juego NO usa nada de este archivo. Existe para poder medir directamente lo
que se descartó (lo exige §8 del enunciado). Igual que el resto del programa,
todas están hechas con NUESTRAS estructuras (Nodo, ListaEnlazada,
MonticuloMinimo): no se usan las colecciones de Python.

Todas las agendas comparten la misma interfaz:
    programar(evento)   agrega un evento pendiente
    cancelar(evento)    lo marca para que no se ejecute
    siguiente()         devuelve el próximo evento NO cancelado, o None
"""
from ...modelo.estructuras.listaEnlazada import ListaEnlazada
from ...modelo.estructuras.heapMinimo import HeapMinimo
from ...modelo.estructuras.nodo import Nodo

CLAVES_AGENDA = (
    "monticulo_enlazado",       # la decisión: montículo de nodos enlazados
    "monticulo_sobre_lista",    # descartada: montículo con datos en una lista enlazada
    "busqueda_lineal",          # descartada: recorrer todo para hallar el menor
    "lista_ordenada",           # descartada: lista enlazada siempre ordenada
)


class EventoBench:
    """Evento mínimo para medir: (tiempo, secuencia) y la bandera cancelado."""

    def __init__(self, tiempo, secuencia):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.cancelado = False

    def __lt__(self, otro):
        if self.tiempo != otro.tiempo:
            return self.tiempo < otro.tiempo
        return self.secuencia < otro.secuencia


class EventoContado(EventoBench):
    """Igual que EventoBench, pero cuenta cuántas comparaciones se hacen."""

    comparaciones = 0

    def __lt__(self, otro):
        EventoContado.comparaciones += 1
        return EventoBench.__lt__(self, otro)


class MonticuloSobreLista:
    """Montículo de mínimo cuyos datos viven en una ListaEnlazada, por posiciones.

    Es la alternativa (b) de D23: hace los mismos pasos que el montículo de
    arreglo (padre de i: (i - 1) // 2; hijos: 2i + 1 y 2i + 2), pero llegar a
    la posición i en una lista enlazada cuesta O(i), así que cada operación
    pasa de O(log n) a O(n) o peor.
    """

    def __init__(self):
        self._datos = ListaEnlazada()

    def __len__(self):
        return len(self._datos)

    def esta_vacio(self):
        return self._datos.esta_vacia()

    def insertar(self, dato):
        datos = self._datos
        datos.agregar_al_final(dato)
        posicion = len(datos) - 1
        while posicion > 0:
            padre = (posicion - 1) // 2
            actual = datos.obtener(posicion)          # O(posicion)
            del_padre = datos.obtener(padre)          # O(padre)
            if actual < del_padre:
                datos.establecer(posicion, del_padre)
                datos.establecer(padre, actual)
                posicion = padre
            else:
                return

    def extraer_minimo(self):
        datos = self._datos
        if datos.esta_vacia():
            raise IndexError("El montículo está vacío")
        primero = datos.obtener(0)
        ultimo = datos.eliminar_ultimo()              # O(n) en una lista simple
        if not datos.esta_vacia():
            datos.establecer(0, ultimo)
            self._bajar()
        return primero

    def _bajar(self):
        datos = self._datos
        cantidad = len(datos)
        posicion = 0
        actual = datos.obtener(0)
        while True:
            menor = posicion
            dato_menor = actual
            izquierdo = 2 * posicion + 1
            derecho = izquierdo + 1
            if izquierdo < cantidad:
                dato_izquierdo = datos.obtener(izquierdo)
                if dato_izquierdo < dato_menor:
                    menor = izquierdo
                    dato_menor = dato_izquierdo
            if derecho < cantidad:
                dato_derecho = datos.obtener(derecho)
                if dato_derecho < dato_menor:
                    menor = derecho
                    dato_menor = dato_derecho
            if menor == posicion:
                return
            datos.establecer(posicion, dato_menor)
            datos.establecer(menor, actual)
            posicion = menor


class AgendaPerezosa:
    """Agenda con cancelación perezosa sobre cualquier montículo.

    Con MonticuloMinimo es la DECISIÓN; con MonticuloSobreLista, una alternativa.
    Cancelar solo enciende una bandera; el evento cancelado se descarta cuando
    llega a la raíz.
    """

    def __init__(self, estructura, nombre):
        self.nombre = nombre
        self._estructura = estructura
        self.descartados = 0      # eventos cancelados que salieron sin ejecutarse

    def programar(self, evento):
        self._estructura.insertar(evento)

    def cancelar(self, evento):
        evento.cancelado = True

    def siguiente(self):
        while not self._estructura.esta_vacio():
            evento = self._estructura.extraer_minimo()
            if not evento.cancelado:
                return evento
            self.descartados += 1
        return None


class AgendaBusquedaLineal:
    """Lista enlazada sin orden: programar es O(1), pero cada siguiente()
    recorre todos los eventos para encontrar el menor."""

    def __init__(self):
        self.nombre = "búsqueda lineal (lista enlazada)"
        self._eventos = ListaEnlazada()
        self.descartados = 0

    def programar(self, evento):
        self._eventos.agregar_al_final(evento)

    def cancelar(self, evento):
        evento.cancelado = True

    def siguiente(self):
        mejor = None
        posicion_mejor = -1
        posicion = 0
        for evento in self._eventos:
            if not evento.cancelado:
                if mejor is None or evento < mejor:
                    mejor = evento
                    posicion_mejor = posicion
            posicion += 1
        if mejor is None:
            return None
        self._eventos.eliminar_en(posicion_mejor)
        return mejor


class AgendaListaOrdenada:
    """Lista enlazada ordenada de MENOR a MAYOR: el próximo evento está en la cabeza.

    siguiente() es O(1), pero programar() busca su lugar recorriendo la lista
    desde la cabeza: O(n) comparaciones. Trabaja directamente con Nodo porque
    insertar en medio de una lista necesita el nodo anterior.
    """

    def __init__(self):
        self.nombre = "lista enlazada ordenada"
        self._cabeza = None
        self.descartados = 0

    def programar(self, evento):
        if self._cabeza is None or evento < self._cabeza.dato:
            self._cabeza = Nodo(evento, self._cabeza)
            return
        anterior = self._cabeza
        while anterior.siguiente is not None and anterior.siguiente.dato < evento:
            anterior = anterior.siguiente
        anterior.siguiente = Nodo(evento, anterior.siguiente)

    def cancelar(self, evento):
        evento.cancelado = True

    def siguiente(self):
        while self._cabeza is not None:
            evento = self._cabeza.dato
            self._cabeza = self._cabeza.siguiente
            if not evento.cancelado:
                return evento
            self.descartados += 1
        return None


class AgendaReconstruida:
    """Cancelación INMEDIATA: cancelar reconstruye el montículo sin ese evento.

    Es la alternativa a la cancelación perezosa: cada cancelación cuesta
    O(n log n), porque se vuelven a insertar todos los eventos restantes.
    """

    def __init__(self):
        self.nombre = "cancelación inmediata (reconstruir)"
        self._monticulo = HeapMinimo()
        self.descartados = 0

    def programar(self, evento):
        self._monticulo.insertar(evento)

    def cancelar(self, evento):
        nuevo = HeapMinimo()
        for otro in self._monticulo:
            if otro is not evento:
                nuevo.insertar(otro)
        self._monticulo = nuevo

    def siguiente(self):
        if self._monticulo.esta_vacio():
            return None
        return self._monticulo.extraer_minimo()


def crear_agenda(clave):
    """Crea una agenda nueva y vacía según su clave.

    Se usa if/elif y no un diccionario de funciones: §7 prohíbe dict como
    tabla de búsqueda.
    """
    if clave == "monticulo_enlazado":
        return AgendaPerezosa(HeapMinimo(), "montículo de nodos (decisión)")
    if clave == "monticulo_sobre_lista":
        return AgendaPerezosa(MonticuloSobreLista(), "montículo sobre lista enlazada")
    if clave == "busqueda_lineal":
        return AgendaBusquedaLineal()
    if clave == "lista_ordenada":
        return AgendaListaOrdenada()
    if clave == "reconstruida":
        return AgendaReconstruida()
    raise ValueError(f"Clave de agenda desconocida: {clave}")