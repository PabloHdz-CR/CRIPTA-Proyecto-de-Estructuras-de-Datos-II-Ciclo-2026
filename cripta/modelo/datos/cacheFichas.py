from ..estructuras.listaDoble import ListaDoble


class _EntradaCache:
    """Lo que guarda cada nodo de la lista: el id, la ficha, y cuántas
    referencias activas la tienen fijada (>0 significa "en uso": no se
    desaloja). Varias instancias pueden compartir la misma ficha a la vez
    (dos ratas con la misma ficha de catálogo), por eso es un contador y no
    una bandera."""

    def __init__(self, id_ficha, ficha):
        self.id_ficha = id_ficha
        self.ficha = ficha
        self.fijaciones = 0

    def en_uso(self):
        return self.fijaciones > 0


class CacheFichas:
    """Caché de fichas del catálogo en memoria, con tope de capacidad y
    desalojo LRU (§4.4).

    - El FRENTE de la lista es lo usado más recientemente; el FONDO es lo más
      antiguo. Cada acierto mueve la entrada al frente: O(1), porque ya
      conocemos el método de ListaDoble para esto (es el mismo que usa
      "equipar" en el inventario).
    - Buscar si un id está en caché recorre la lista desde el frente: O(capacidad).
      Es una decisión deliberada del equipo (no usar dict ni como índice),
      documentada y medida, válida porque la capacidad es pequeña (25 por
      defecto) frente al costo real del sistema (red, disco).
    - Las fichas "en uso" (fijadas al menos una vez) nunca se desalojan,
      aunque estén en el fondo: el desalojo busca desde el fondo saltando las
      que están en uso.
    - Si todas las fichas están en uso y hay que insertar una más, la caché
      crece temporalmente por encima de su capacidad: perder una ficha que
      un actor vivo todavía necesita sería un error peor que exceder el tope
      por un momento. Se documenta como límite conocido.
    """

    CAPACIDAD_POR_DEFECTO = 25

    def __init__(self, capacidad=CAPACIDAD_POR_DEFECTO):
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._entradas = ListaDoble()      # nodos con _EntradaCache
        self.aciertos = 0
        self.fallos = 0

    @property
    def capacidad(self):
        return self._capacidad

    def __len__(self):
        return len(self._entradas)

    # ------------------------------------------------------------------
    # Consulta (la operación más frecuente, según el enunciado)
    # ------------------------------------------------------------------

    def obtener(self, id_ficha):
        """Devuelve la ficha si está en memoria (y la marca como recién usada);
        si no, cuenta un fallo y devuelve None. O(capacidad)."""
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self._entradas.mover_al_inicio(nodo)     # O(1): pasa a ser lo más reciente
        return nodo.dato.ficha

    def contiene(self, id_ficha):
        """Como obtener(), pero sin contar acierto/fallo ni reordenar. Para
        comprobar sin alterar las estadísticas ni el orden LRU."""
        return self._buscar_nodo(id_ficha) is not None

    # ------------------------------------------------------------------
    # Inserción y desalojo
    # ------------------------------------------------------------------

    def insertar(self, id_ficha, ficha):
        """Agrega (o reemplaza) una ficha, al frente (recién usada).

        Si la caché está llena, desaloja primero la entrada LRU que no esté en
        uso. Si ya existe un id igual, se reemplaza su ficha sin tocar sus
        fijaciones. Devuelve el id desalojado, o None si no se desalojó nada.
        """
        existente = self._buscar_nodo(id_ficha)
        if existente is not None:
            existente.dato.ficha = ficha
            self._entradas.mover_al_inicio(existente)
            return None

        desalojado = None
        if len(self._entradas) >= self._capacidad:
            desalojado = self._desalojar_uno()

        self._entradas.agregar_al_inicio(_EntradaCache(id_ficha, ficha))
        return desalojado

    def _desalojar_uno(self):
        """Busca desde el fondo (lo más antiguo) la primera entrada que no esté
        en uso y la elimina. Devuelve su id, o None si todas están en uso."""
        nodo = self._entradas.ultimo()
        while nodo is not None:
            if not nodo.dato.en_uso():
                id_desalojado = nodo.dato.id_ficha
                self._entradas.eliminar_nodo(nodo)
                return id_desalojado
            nodo = self._entradas.anterior_de(nodo)
        return None     # todas en uso: la caché crecerá por encima del tope

    # ------------------------------------------------------------------
    # Fijar / soltar referencias ("en uso")
    # ------------------------------------------------------------------

    def fijar(self, id_ficha):
        """Marca una referencia activa a esa ficha (no se podrá desalojar
        mientras tenga al menos una). Debe estar en caché; si no, ValueError."""
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            raise ValueError(f"'{id_ficha}' no está en la caché: no se puede fijar")
        nodo.dato.fijaciones += 1

    def soltar_referencia(self, id_ficha):
        """Quita una referencia activa. Si llega a 0, vuelve a ser candidata al
        desalojo (pero no se saca de inmediato: solo cuando haga falta espacio)."""
        nodo = self._buscar_nodo(id_ficha)
        if nodo is None:
            raise ValueError(f"'{id_ficha}' no está en la caché: no se puede soltar")
        if nodo.dato.fijaciones == 0:
            raise ValueError(f"'{id_ficha}' no tiene ninguna referencia fijada")
        nodo.dato.fijaciones -= 1

    def esta_en_uso(self, id_ficha):
        nodo = self._buscar_nodo(id_ficha)
        return nodo is not None and nodo.dato.en_uso()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _buscar_nodo(self, id_ficha):
        """Recorre desde el frente. O(capacidad): no usa dict (política del
        equipo), válido porque la capacidad es pequeña frente al costo de red."""
        nodo = self._entradas.primero()
        while nodo is not None:
            if nodo.dato.id_ficha == id_ficha:
                return nodo
            nodo = self._entradas.siguiente_de(nodo)
        return None

    def ver(self, id_ficha):
        """Como obtener(), pero sin contar acierto/fallo ni reordenar: una
        consulta "silenciosa". La usa ServicioDatos para leer una ficha que
        ACABA de insertar en esta misma llamada (porque llegó por disco o por
        red), sin que eso se contabilice como un acierto de caché: contar eso
        como acierto inflaría artificialmente la estadística que pide §4.4."""
        nodo = self._buscar_nodo(id_ficha)
        return nodo.dato.ficha if nodo is not None else None