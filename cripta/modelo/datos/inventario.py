"""El inventario del jugador (§2.7, §4.5).

Está montado sobre ListaDoble: recorrer en ambos sentidos, soltar el objeto
que se está viendo sin que el costo dependa de su posición, y equipar (mover
al frente) son operaciones O(1), que es justo lo que exige §4.5.

Cada objeto recogido FIJA su ficha en la CacheFichas (D31/D32): mientras esté
en el inventario, su ficha no puede desalojarse. Al soltarlo o usarlo (se
consume), se suelta esa referencia. Por eso 'recoger' exige que la ficha ya
esté en la caché (normalmente, resuelta antes con ServicioDatos.resolver_fichas);
si no, CacheFichas.fijar lanza ValueError.
"""
from ..estructuras.listaDoble import ListaDoble
from ..estructuras.listaEnlazada import ListaEnlazada

CRITERIOS_ORDEN = ("peso", "valor", "nombre")


class ObjetoInventario:
    """Una instancia de objeto dentro del inventario: su propio id de
    instancia más la ficha de catálogo que comparte con otras instancias del
    mismo tipo (§2.7: "la ficha técnica se comparte; la pertenencia al
    inventario o al suelo corresponde a la instancia")."""

    def __init__(self, id_instancia, ficha):
        self.id_instancia = id_instancia
        self.ficha = ficha

    def __repr__(self):
        return f"ObjetoInventario(#{self.id_instancia}, {self.ficha.id})"


class Inventario:

    def __init__(self, capacidad, cache):
        self._capacidad = capacidad
        self._cache = cache
        self._objetos = ListaDoble()
        self._actual = None          # NodoDoble, o None si está vacío
        self._nodo_arma = None       # NodoDoble equipado como arma, o None
        self._nodo_armadura = None   # NodoDoble equipado como armadura, o None
        self._siguiente_instancia = 1

    @property
    def capacidad(self):
        return self._capacidad

    def __len__(self):
        return len(self._objetos)

    def esta_vacio(self):
        return self._objetos.esta_vacia()

    def esta_lleno(self):
        return len(self._objetos) >= self._capacidad

    # ------------------------------------------------------------------
    # Recoger / soltar / usar
    # ------------------------------------------------------------------

    def recoger(self, ficha):
        """Agrega un objeto nuevo (al final, sin mover el cursor si ya había
        algo). Si está lleno, no agrega nada y devuelve None — el llamador
        (Partida) es quien decide que eso significa que la acción se rechaza
        sin consumir tiempo (Ap. B). Fija la ficha en la caché."""
        if self.esta_lleno():
            return None
        objeto = ObjetoInventario(self._siguiente_instancia, ficha)
        self._siguiente_instancia += 1
        nodo = self._objetos.agregar_al_final(objeto)
        self._cache.fijar(ficha.id)
        if self._actual is None:
            self._actual = nodo
        return objeto

    def soltar_actual(self):
        """Quita el objeto que se está viendo (el cursor pasa al vecino) y
        suelta su referencia en caché. O(1), sin importar la posición (§4.5)."""
        if self._actual is None:
            raise IndexError("El inventario está vacío")
        return self._quitar_nodo(self._actual)

    def usar_actual(self):
        """Igual que soltar_actual, para un objeto que se consume al usarlo
        (una poción, un antídoto, un pergamino). El efecto del objeto lo
        aplica quien llama; esto solo lo retira del inventario."""
        if self._actual is None:
            raise IndexError("El inventario está vacío")
        return self._quitar_nodo(self._actual)

    def _quitar_nodo(self, nodo):
        if nodo is self._actual:
            vecino = self._objetos.siguiente_de(nodo)
            if vecino is None:
                vecino = self._objetos.anterior_de(nodo)
            self._actual = vecino            # puede quedar en None si era el único
        if nodo is self._nodo_arma:
            self._nodo_arma = None
        if nodo is self._nodo_armadura:
            self._nodo_armadura = None
        objeto = self._objetos.eliminar_nodo(nodo)
        self._cache.soltar_referencia(objeto.ficha.id)
        return objeto

    # ------------------------------------------------------------------
    # Navegación (ambos sentidos) y equipar
    # ------------------------------------------------------------------

    def actual(self):
        return self._actual.dato if self._actual is not None else None

    def siguiente(self):
        if self._actual is not None:
            vecino = self._objetos.siguiente_de(self._actual)
            if vecino is not None:
                self._actual = vecino
        return self.actual()

    def anterior(self):
        if self._actual is not None:
            vecino = self._objetos.anterior_de(self._actual)
            if vecino is not None:
                self._actual = vecino
        return self.actual()

    def equipar_actual(self):
        """Equipa el objeto que se está viendo (debe ser arma o armadura) y lo
        mueve al frente del orden real (§2.7). Si ya había algo equipado de
        la misma clase, deja de estar marcado como equipado, PERO SIGUE en
        el inventario — no se elimina."""
        if self._actual is None:
            raise IndexError("El inventario está vacío")
        objeto = self._actual.dato
        clase = objeto.ficha.clase
        if clase == "arma":
            self._nodo_arma = self._actual
        elif clase == "armadura":
            self._nodo_armadura = self._actual
        else:
            raise ValueError(f"No se puede equipar un objeto de clase '{clase}'")
        self._objetos.mover_al_inicio(self._actual)
        return objeto

    def arma_equipada(self):
        return self._nodo_arma.dato if self._nodo_arma is not None else None

    def armadura_equipada(self):
        return self._nodo_armadura.dato if self._nodo_armadura is not None else None

    def cantidad_pergaminos(self):
        cantidad = 0
        for objeto in self._objetos:
            if objeto.ficha.clase == "pergamino_retroceso":
                cantidad += 1
        return cantidad

    # ------------------------------------------------------------------
    # Vista ordenada (§4.5): NO altera el orden real
    # ------------------------------------------------------------------

    def vista_ordenada(self, criterio):
        """Devuelve una ListaEnlazada NUEVA con los objetos ordenados por
        'peso', 'valor' o 'nombre', sin tocar el orden real del inventario."""
        if criterio not in CRITERIOS_ORDEN:
            raise ValueError(f"Criterio de orden desconocido: '{criterio}'")
        copia = ListaEnlazada()
        for objeto in self._objetos:
            copia.agregar_al_final(objeto)
        return self._ordenar_insercion(copia, criterio)

    def _clave(self, objeto, criterio):
        if criterio == "peso":
            return objeto.ficha.peso
        if criterio == "valor":
            return objeto.ficha.valor
        return objeto.ficha.nombre          # "nombre"

    def _ordenar_insercion(self, lista, criterio):
        """ORDENACIÓN TEMPORAL por inserción. Se reemplaza en el Paso 6 por
        Ordenamiento (§4.9), que elige entre al menos dos algoritmos según el
        tamaño y el orden de los datos. Con inventario_max acotado (unas
        decenas de objetos), el costo es insignificante mientras tanto."""
        n = len(lista)
        for i in range(1, n):
            valor_actual = lista.obtener(i)
            clave_actual = self._clave(valor_actual, criterio)
            j = i - 1
            while j >= 0 and self._clave(lista.obtener(j), criterio) > clave_actual:
                lista.establecer(j + 1, lista.obtener(j))
                j -= 1
            lista.establecer(j + 1, valor_actual)
        return lista

    def __iter__(self):
        """Los objetos en el orden REAL (el que ve 'actual'/'siguiente'/'anterior')."""
        return iter(self._objetos)