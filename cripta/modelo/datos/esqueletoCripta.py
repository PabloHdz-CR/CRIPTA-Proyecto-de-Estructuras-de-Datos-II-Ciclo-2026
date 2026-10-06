"""Guarda el esqueleto de una cripta (las salas y sus salidas, §3.2) a medida
que se van descargando por páginas, y permite consultarlo.

Importante sobre complejidad: buscar una sala por id es O(salas_conocidas),
igual que la búsqueda en CacheFichas (D32): el equipo decidió no usar dict
como índice en ningún punto del programa. Con las decenas o pocos cientos de
salas de una cripta esto es aceptable; se documenta y se mide (5.7).
"""
from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.dto import DIRECCIONES


class EntradaSala:
    """Una sala del esqueleto, más el estado mutable que necesita la precarga:
    si ya se pidió su contenido (para no repetir la misma solicitud) y si el
    contenido ya llegó. La SalaDTO en sí (sala.id, sala.nombre, sala.salidas)
    es inmutable, por eso este envoltorio aparte."""

    def __init__(self, sala_dto):
        self.sala = sala_dto
        self.solicitada = False       # ya se envió una solicitud de contenido
        self.contenido = None         # None hasta que llega la respuesta


class EsqueletoCripta:
    """Colección de EntradaSala, en el orden en que llegaron las páginas."""

    def __init__(self):
        self._entradas = ListaEnlazada()
        self._total_paginas = None

    def agregar_pagina(self, pagina_dto):
        """Vuelca una PaginaSalasDTO. Si una sala ya estaba (una página se pidió
        dos veces), se ignora la repetida en vez de duplicarla."""
        self._total_paginas = pagina_dto.total_paginas
        for sala in pagina_dto.salas:
            if self.buscar(sala.id) is None:
                self._entradas.agregar_al_final(EntradaSala(sala))

    def paginas_completas(self, paginas_descargadas):
        """True si ya se descargaron todas las páginas del esqueleto."""
        return self._total_paginas is not None and paginas_descargadas >= self._total_paginas

    def __len__(self):
        return len(self._entradas)

    def buscar(self, id_sala):
        """Devuelve la EntradaSala con ese id, o None. O(salas conocidas)."""
        for entrada in self._entradas:
            if entrada.sala.id == id_sala:
                return entrada
        return None

    def vecinas_abiertas(self, id_sala):
        """Ids de las salas alcanzables desde id_sala por una salida ABIERTA,
        en el orden fijo N, S, E, O (determinismo: §2.9 y §4.7)."""
        resultado = ListaEnlazada()
        entrada = self.buscar(id_sala)
        if entrada is None:
            return resultado
        for direccion in DIRECCIONES:
            for salida in entrada.sala.salidas:
                if salida.direccion == direccion and not salida.cerrada:
                    resultado.agregar_al_final(salida.sala)
        return resultado

    def __iter__(self):
        return iter(self._entradas)