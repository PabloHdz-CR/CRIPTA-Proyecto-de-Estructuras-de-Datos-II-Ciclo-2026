"""Bitácora de partida y reproducción (§4.11): archivo de texto de SOLO
anexado. La primera línea es el encabezado (id de cripta, versión de cripta,
versión de catálogo, semilla); cada línea siguiente es una acción del
jugador, en el mismo formato que ya produce Accion.texto() (el propio
accion.py dice que ese texto está pensado exactamente para esto: "así el log
de partida basta para reproducirla").

registrar_accion() abre en modo 'a' y nunca relee lo anterior: cumple la
restricción de "solo anexado" del enunciado. La comprobación de si la
versión del log sigue siendo compatible con los datos disponibles NO es
trabajo de esta clase: eso lo decide quien use --replay (comparando
encabezado.version_cripta/version_catalogo contra lo que reporte el
servicio de datos), porque solo ServicioDatos sabe qué versión hay
disponible ahora.
"""
from __future__ import annotations

from pathlib import Path

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.nucleo.accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar,
    UsarPergamino)
from ..modelo.puertos.errores import ErrorCripta

PREFIJO_ENCABEZADO = "CRIPTA "


class EncabezadoPartida:
    """id de cripta, versión de cripta, versión de catálogo y semilla:
    el mínimo que exige §4.11 para poder reproducir la partida."""

    def __init__(self, id_cripta, version_cripta, version_catalogo, semilla: int):
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.semilla = semilla

    def texto(self) -> str:
        return (f"{PREFIJO_ENCABEZADO}{self.id_cripta} {self.version_cripta} "
                f"{self.version_catalogo} {self.semilla}")

    @staticmethod
    def desde_texto(linea: str) -> "EncabezadoPartida":
        if not linea.startswith(PREFIJO_ENCABEZADO):
            raise ErrorCripta(
                "El archivo de partida no tiene un encabezado válido (falta 'CRIPTA ')")
        # DECISIÓN: .split() arma un contenedor de Python de vida muy corta, igual
        # que leer un dict de response.json(): se usa una sola vez para separar los
        # cuatro campos de una línea de texto y se descarta de inmediato; no
        # sustituye ninguna estructura del programa (nada se guarda en él).
        partes = linea[len(PREFIJO_ENCABEZADO):].split(" ")
        if len(partes) != 4:
            raise ErrorCripta(
                f"El encabezado de la partida debe tener 4 campos, trae {len(partes)}")
        id_cripta, version_cripta, version_catalogo, semilla_texto = partes
        try:
            semilla = int(semilla_texto)
        except ValueError as error:
            raise ErrorCripta(
                f"La semilla del encabezado no es un entero: '{semilla_texto}'") from error
        return EncabezadoPartida(id_cripta, version_cripta, version_catalogo, semilla)


def _accion_desde_texto(linea: str):
    partes = linea.split(" ")
    nombre = partes[0]
    if nombre == "MOVER":
        return Mover(direccion=partes[1])
    if nombre == "ABRIR":
        return AbrirPuerta(direccion=partes[1])
    if nombre == "ATACAR":
        return Atacar(objetivo=partes[1])
    if nombre == "ESPERAR":
        return Esperar()
    if nombre == "RECOGER":
        return Recoger(id_objeto=int(partes[1]))
    if nombre == "SOLTAR":
        return Soltar(id_objeto=int(partes[1]))
    if nombre == "USAR":
        return Usar(id_objeto=int(partes[1]))
    if nombre == "EQUIPAR":
        return Equipar(id_objeto=int(partes[1]))
    if nombre == "PERGAMINO":
        return UsarPergamino()
    raise ErrorCripta(f"Acción desconocida en el log de partida: '{nombre}'")


class RegistroArchivo:
    """Escribe y lee el log de una partida (texto plano, solo anexado)."""

    def __init__(self, ruta):
        self._ruta = Path(ruta)

    def iniciar(self, encabezado: EncabezadoPartida) -> None:
        """Crea el archivo (lo trunca si ya existía de una partida anterior
        con el mismo nombre) y escribe el encabezado como primera línea."""
        with open(self._ruta, "w", encoding="utf-8") as archivo:
            archivo.write(encabezado.texto())
            archivo.write("\n")

    def registrar_accion(self, accion) -> None:
        """Anexa una línea por cada acción ACEPTADA del jugador. Abre en modo
        'a': nunca relee ni reescribe lo que ya estaba (§4.11)."""
        with open(self._ruta, "a", encoding="utf-8") as archivo:
            archivo.write(accion.texto())
            archivo.write("\n")

    def leer(self):
        """Devuelve (EncabezadoPartida, ListaEnlazada de acciones), leyendo el
        archivo línea por línea (nunca se materializa en una lista de Python
        de por medio)."""
        encabezado = None
        acciones = ListaEnlazada()
        with open(self._ruta, "r", encoding="utf-8") as archivo:
            for numero, linea_cruda in enumerate(archivo):
                linea = linea_cruda.rstrip("\n")
                if numero == 0:
                    encabezado = EncabezadoPartida.desde_texto(linea)
                elif linea:
                    acciones.agregar_al_final(_accion_desde_texto(linea))
        if encabezado is None:
            raise ErrorCripta("El archivo de partida está vacío")
        return encabezado, acciones