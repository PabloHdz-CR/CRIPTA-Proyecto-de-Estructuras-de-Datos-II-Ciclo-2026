
import struct

FORMATO_INT64 = "<q"
FORMATO_UINT32 = "<I"
FORMATO_INT32 = "<i"
FORMATO_FLOAT64 = "<d"
FORMATO_BOOL = "<B"


class EscritorBinario:

    def __init__(self) -> None:
        self._partes = bytearray()

    def bytes(self) -> bytes:
        return bytes(self._partes)

    def __len__(self) -> int:
        return len(self._partes)

    def entero(self, valor: int) -> None:
        self._partes += struct.pack(FORMATO_INT64, valor)

    def entero32(self, valor: int) -> None:
        self._partes += struct.pack(FORMATO_INT32, valor)

    def uentero32(self, valor: int) -> None:
        self._partes += struct.pack(FORMATO_UINT32, valor)

    def flotante(self, valor: float) -> None:
        self._partes += struct.pack(FORMATO_FLOAT64, valor)

    def booleano(self, valor: bool) -> None:
        self._partes += struct.pack(FORMATO_BOOL, 1 if valor else 0)

    def texto(self, valor: str) -> None:
        """None se escribe como longitud -1 (sin bytes de texto detrás)."""
        if valor is None:
            self.entero32(-1)
            return
        datos = valor.encode("utf-8")
        self.entero32(len(datos))
        self._partes += datos

    def entero_opcional(self, valor) -> None:
        if valor is None:
            self.booleano(False)
        else:
            self.booleano(True)
            self.entero(valor)

    def flotante_opcional(self, valor) -> None:
        if valor is None:
            self.booleano(False)
        else:
            self.booleano(True)
            self.flotante(valor)

    def crudo(self, datos: bytes) -> None:
        self._partes += datos

    def sobrescribir_entero(self, posicion: int, valor: int) -> None:
        self._partes[posicion:posicion + 8] = struct.pack(FORMATO_INT64, valor)


class LectorBinario:

    def __init__(self, datos: bytes, posicion: int = 0) -> None:
        self._datos = datos
        self._posicion = posicion

    @property
    def posicion(self) -> int:
        return self._posicion

    def _leer(self, formato: str):
        tamano = struct.calcsize(formato)
        fin = self._posicion + tamano
        (valor,) = struct.unpack(formato, self._datos[self._posicion:fin])
        self._posicion = fin
        return valor

    def entero(self) -> int:
        return self._leer(FORMATO_INT64)

    def entero32(self) -> int:
        return self._leer(FORMATO_INT32)

    def uentero32(self) -> int:
        return self._leer(FORMATO_UINT32)

    def flotante(self) -> float:
        return self._leer(FORMATO_FLOAT64)

    def booleano(self) -> bool:
        return self._leer(FORMATO_BOOL) != 0

    def texto(self):
        longitud = self.entero32()
        if longitud < 0:
            return None
        fin = self._posicion + longitud
        valor = self._datos[self._posicion:fin].decode("utf-8")
        self._posicion = fin
        return valor

    def entero_opcional(self):
        if self.booleano():
            return self.entero()
        return None

    def flotante_opcional(self):
        if self.booleano():
            return self.flotante()
        return None

    def crudo(self, cantidad: int) -> bytes:
        fin = self._posicion + cantidad
        valor = self._datos[self._posicion:fin]
        self._posicion = fin
        return valor