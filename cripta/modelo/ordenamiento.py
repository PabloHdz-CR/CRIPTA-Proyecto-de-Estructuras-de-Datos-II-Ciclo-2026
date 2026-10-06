"""Ordenamiento del proyecto (§4.9): dos algoritmos con características
distintas, implementados sobre nuestras propias estructuras (sin list.sort()
ni sorted(), prohibidos por el enunciado), más un selector automático que
elige entre ellos según el tamaño y el grado de orden de los datos.

Los elementos se ordenan usando SOLO el operador < (__lt__), igual que en
MonticuloMinimo: no se pasan funciones de comparación por parámetro (el
equipo decidió no usar funciones como valores todavía). Para ordenar por una
clave calculada (peso, valor, nombre, puntaje...) se envuelve cada elemento
en ClaveOrden, que compara solo por 'clave' y guarda el original en 'valor'.

Ninguna de las dos funciones de ordenamiento modifica la lista que recibe:
ambas devuelven una ListaEnlazada NUEVA.
"""
from .estructuras.listaEnlazada import ListaEnlazada
from .estructuras.nodo import Nodo

UMBRAL_TAMANO = 32                # bajo este tamaño, inserción
PROPORCION_CASI_ORDENADA = 0.1    # <=10% de pares adyacentes fuera de orden


class ClaveOrden:
    """Envoltorio genérico para ordenar por una clave calculada, sin pasar
    funciones como parámetro ni usar dict: compara solo por 'clave' (con <),
    y 'valor' es el objeto original, para recuperarlo después de ordenar."""

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor

    def __lt__(self, otro):
        return self.clave < otro.clave

    def __repr__(self):
        return f"ClaveOrden({self.clave!r})"


# ---------------------------------------------------------------------------
# Medición del grado de orden (para el selector)
# ---------------------------------------------------------------------------

def inversiones_adyacentes(lista):
    """Cuenta en O(n) cuántos pares CONSECUTIVOS están fuera de orden
    (elemento[i] > elemento[i+1]). No es el conteo completo de inversiones
    (eso sería O(n²)): es una medida barata y suficiente de qué tan "casi
    ordenada" está la lista, calculable en una sola pasada."""
    cuenta = 0
    anterior = None
    hay_anterior = False
    for dato in lista:
        if hay_anterior and dato < anterior:
            cuenta += 1
        anterior = dato
        hay_anterior = True
    return cuenta


def casi_ordenada(lista):
    """True si, proporcionalmente, hay pocos pares adyacentes fuera de orden."""
    n = len(lista)
    if n <= 1:
        return True
    return inversiones_adyacentes(lista) / n <= PROPORCION_CASI_ORDENADA


def seleccionar_algoritmo(lista):
    """Devuelve 'insercion' o 'mezcla' según propiedades MEDIBLES de los datos
    (§8: no basta con "usamos X porque es O(log n)"):
      - listas pequeñas (<= UMBRAL_TAMANO): inserción, porque su sobrecarga es
        mínima y no justifica dividir y fusionar.
      - listas grandes pero CASI ORDENADAS: inserción también, porque su
        costo real se acerca a O(n) cuando hay pocas inversiones adyacentes
        (el bucle interno casi no avanza).
      - cualquier otro caso: mezcla, que garantiza O(n log n) sin depender
        del orden de entrada.
    """
    if len(lista) <= UMBRAL_TAMANO or casi_ordenada(lista):
        return "insercion"
    return "mezcla"


def ordenar(lista):
    """Ordena 'lista' (ascendente, por <) eligiendo el algoritmo automáticamente.
    Devuelve una ListaEnlazada nueva; no modifica la original."""
    if seleccionar_algoritmo(lista) == "insercion":
        return insercion(lista)
    return mezcla(lista)


# ---------------------------------------------------------------------------
# Inserción: O(n) en el mejor caso (ya ordenada), O(n²) en el peor. Estable.
# ---------------------------------------------------------------------------

def insercion(lista):
    cabeza = _copiar_a_nodos(lista)
    cabeza = _insercion_nodos(cabeza)
    return _nodos_a_lista(cabeza)


def _insercion_nodos(cabeza):
    ordenada = None
    actual = cabeza
    while actual is not None:
        siguiente = actual.siguiente
        ordenada = _insertar_en_orden(ordenada, actual)
        actual = siguiente
    return ordenada


def _insertar_en_orden(cabeza, nodo):
    """Inserta 'nodo' (ya desenlazado de la lista) en su lugar dentro de la
    cadena ya ordenada que empieza en 'cabeza'. Si hay empate, el nodo nuevo
    queda DESPUÉS de los iguales (eso es lo que hace estable al algoritmo)."""
    if cabeza is None or nodo.dato < cabeza.dato:
        nodo.siguiente = cabeza
        return nodo
    actual = cabeza
    while actual.siguiente is not None and not (nodo.dato < actual.siguiente.dato):
        actual = actual.siguiente
    nodo.siguiente = actual.siguiente
    actual.siguiente = nodo
    return cabeza


# ---------------------------------------------------------------------------
# Mezcla (merge sort): O(n log n) siempre. Estable.
# ---------------------------------------------------------------------------

def mezcla(lista):
    cabeza = _copiar_a_nodos(lista)
    cabeza = _mezcla_nodos(cabeza)
    return _nodos_a_lista(cabeza)


def _mezcla_nodos(cabeza):
    if cabeza is None or cabeza.siguiente is None:
        return cabeza
    mitad = _dividir(cabeza)
    izquierda = _mezcla_nodos(cabeza)
    derecha = _mezcla_nodos(mitad)
    return _fusionar(izquierda, derecha)


def _dividir(cabeza):
    """Parte la cadena en dos (técnica del paso lento/paso rápido) y devuelve
    la cabeza de la segunda mitad, dejando la primera mitad terminada en None."""
    lento = cabeza
    rapido = cabeza.siguiente
    while rapido is not None and rapido.siguiente is not None:
        lento = lento.siguiente
        rapido = rapido.siguiente.siguiente
    mitad = lento.siguiente
    lento.siguiente = None
    return mitad


def _fusionar(a, b):
    """Fusiona dos cadenas YA ordenadas en una sola ordenada. En un empate se
    toma primero el nodo de 'a' (la mitad izquierda), lo que hace estable la
    fusión: conserva el orden relativo de los iguales."""
    relleno = Nodo(None)
    cola = relleno
    while a is not None and b is not None:
        if b.dato < a.dato:
            cola.siguiente = b
            b = b.siguiente
        else:
            cola.siguiente = a
            a = a.siguiente
        cola = cola.siguiente
    cola.siguiente = a if a is not None else b
    return relleno.siguiente


# ---------------------------------------------------------------------------
# Internos compartidos
# ---------------------------------------------------------------------------

def _copiar_a_nodos(lista):
    """Copia los datos de una ListaEnlazada a una cadena de Nodo suelta (no
    envuelta en ListaEnlazada), para no mutar la lista original."""
    cabeza = None
    cola = None
    for dato in lista:
        nuevo = Nodo(dato)
        if cabeza is None:
            cabeza = nuevo
        else:
            cola.siguiente = nuevo
        cola = nuevo
    return cabeza


def _nodos_a_lista(cabeza):
    resultado = ListaEnlazada()
    nodo = cabeza
    while nodo is not None:
        resultado.agregar_al_final(nodo.dato)
        nodo = nodo.siguiente
    return resultado