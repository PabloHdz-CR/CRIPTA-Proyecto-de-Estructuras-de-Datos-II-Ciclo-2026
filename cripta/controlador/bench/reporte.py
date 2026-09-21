from ...modelo.estructuras.listaEnlazada import ListaEnlazada


class Reporte:
    """Junta las tablas de resultados y las imprime con las columnas alineadas.

    También guarda las tablas y las notas en memoria (atributos 'tablas' y
    'notas', ListaEnlazada) para poder revisarlas desde las pruebas.
    """

    def __init__(self, imprimir=True):
        self._imprimir = imprimir
        self.tablas = ListaEnlazada()   # cada una: (titulo, encabezados, filas)
        self.notas = ListaEnlazada()

    def _escribir(self, texto=""):
        if self._imprimir:
            print(texto)

    def titulo(self, texto):
        self._escribir()
        self._escribir("=" * len(texto))
        self._escribir(texto)
        self._escribir("=" * len(texto))

    def nota(self, texto):
        self.notas.agregar_al_final(texto)
        self._escribir(texto)

    def tabla(self, titulo, encabezados, filas):
        """encabezados: tupla de textos. filas: ListaEnlazada de tuplas de textos."""
        self.tablas.agregar_al_final((titulo, encabezados, filas))
        anchos = ListaEnlazada()
        for columna in range(len(encabezados)):
            ancho = len(encabezados[columna])
            for fila in filas:
                if len(fila[columna]) > ancho:
                    ancho = len(fila[columna])
            anchos.agregar_al_final(ancho)
        self._escribir()
        self._escribir(titulo)
        self._escribir(self._linea(encabezados, anchos))
        self._escribir(self._separador(anchos))
        for fila in filas:
            self._escribir(self._linea(fila, anchos))

    def _separador(self, anchos):
        texto = ""
        primero = True
        for ancho in anchos:
            if not primero:
                texto += "-+-"
            texto += "-" * ancho
            primero = False
        return texto

    def _linea(self, celdas, anchos):
        texto = ""
        columna = 0
        for ancho in anchos:
            if columna > 0:
                texto += " | "
            if columna == 0:
                texto += celdas[columna].ljust(ancho)
            else:
                texto += celdas[columna].rjust(ancho)
            columna += 1
        return texto