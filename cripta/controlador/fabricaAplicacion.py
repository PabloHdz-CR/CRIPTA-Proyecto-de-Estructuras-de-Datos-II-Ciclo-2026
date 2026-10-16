"""FabricaAplicacion: lee --offline, --replay, --bench y --cache-size, elige
los adaptadores e inyecta dependencias (§6). Es la raíz de composición: el
ÚNICO lugar del Controlador que conoce clases concretas de adaptadores y
donde se decide HTTP u offline (sin propagar un if por el modelo, §6).

    --offline[=CARPETA]   paquete de respuestas en disco (datos_offline/)
    --replay ARCHIVO.log  reproduce sin vista interactiva; sale con 1 si falla
    --bench [--rapido]    mediciones de §5.3
    --cache-size N        tope de fichas en memoria (25 por defecto, §4.4)

DECISIÓN: ninguna ruta, id ni presupuesto de una cripta concreta está aquí
(§9): solo carpetas por defecto del programa y la URL base del API.
"""
from __future__ import annotations

import sys
import time
from typing import Optional

from ..adaptadores.almacenLocalDisco import AlmacenLocalDisco
from ..adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from ..adaptadores.clienteHttp import ClienteHttp
from ..adaptadores.contadorSolicitudes import ContadorSolicitudes
from ..adaptadores.fuenteOffline import FuenteOffline
from ..adaptadores.puntajesArchivo import PuntajesArchivo
from ..adaptadores.registroArchivo import CarpetaRegistros, RegistroArchivo
from ..modelo.datos.cacheFichas import CacheFichas
from ..modelo.datos.fuenteAsincrona import FuenteAsincrona
from ..modelo.datos.servicioDatos import ServicioDatos
from ..vista.vistaNula import VistaNula
from .controladorMenu import ControladorMenu
from .gestorGuardado import GestorGuardado
from .modoBench import ModoBench
from .modoReplay import ModoReplay
from .reporteFinal import ReporteFinal

BASE_URL_POR_DEFECTO = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
CARPETA_OFFLINE_POR_DEFECTO = "datos_offline"
CARPETA_FICHAS_POR_DEFECTO = "fichas_guardadas"
CARPETA_GUARDADOS_POR_DEFECTO = "guardados"
CARPETA_LOGS_POR_DEFECTO = "partidas"
ARCHIVO_PUNTAJES_POR_DEFECTO = "puntajes.jsonl"
RITMO_SEGUNDOS = 1 / 60     # ritmo de cuadro: evita usar 100 % de un núcleo


class FabricaAplicacion:

    def __init__(self, argumentos: Optional[tuple] = None) -> None:
        # DECISIÓN: sys.argv es la lista que entrega el intérprete; se copia a
        # una tupla inmutable y solo se lee (no es almacenamiento del programa).
        self._argumentos = tuple(argumentos) if argumentos is not None else tuple(sys.argv[1:])

    def ejecutar(self) -> None:
        offline, carpeta_offline = self._leer_offline()
        ruta_replay = self._leer_opcion_con_valor("--replay")
        modo_bench = "--bench" in self._argumentos
        modo_rapido = "--rapido" in self._argumentos
        tamano_cache = self._leer_cache_size()

        if modo_bench:
            # --bench usa cargas sintéticas: no necesita red, caché ni vista.
            ModoBench().ejecutar(modo_rapido)
            return

        servicio = self._armar_servicio(offline, carpeta_offline, tamano_cache)
        reporte_final = ReporteFinal()

        if ruta_replay is not None:
            modo = ModoReplay(servicio, VistaNula(), reporte_final)
            if not modo.ejecutar(RegistroArchivo(ruta_replay)):
                sys.exit(1)       # código de salida distinto de 0: útil en revisión
            return

        self._correr_interactivo(servicio, reporte_final)

    def _armar_servicio(self, offline: bool, carpeta_offline: Optional[str],
                        tamano_cache: int) -> ServicioDatos:
        # DECISIÓN: --offline cambia SOLO la fuente síncrona; ServicioDatos y
        # el modelo usan el mismo puerto FuenteDatos en ambos casos (§3.4).
        if offline:
            sincrona = FuenteOffline(carpeta_offline)
        else:
            sincrona = ClienteHttp(BASE_URL_POR_DEFECTO, ContadorSolicitudes())
        asincrona = FuenteAsincrona(sincrona)
        cache = CacheFichas(tamano_cache)
        almacen = AlmacenLocalDisco(CARPETA_FICHAS_POR_DEFECTO)
        return ServicioDatos(sincrona, asincrona, cache, almacen)

    def _correr_interactivo(self, servicio: ServicioDatos, reporte_final: ReporteFinal) -> None:
        # DECISIÓN: VistaArcade se importa AQUÍ: --replay y --bench corren sin
        # que pyarcade/pyglet siquiera se importen (§6). Verificado.
        from ..vista.vistaArcade import VistaArcade

        vista = VistaArcade(ancho=800, alto=600, titulo="Cripta")
        controlador = ControladorMenu(
            servicio, vista,
            GestorGuardado(AlmacenPartidaDisco(CARPETA_GUARDADOS_POR_DEFECTO)),
            PuntajesArchivo(ARCHIVO_PUNTAJES_POR_DEFECTO),
            CarpetaRegistros(CARPETA_LOGS_POR_DEFECTO),
            reporte_final)
        controlador.iniciar()
        try:
            # DECISIÓN (D44): el Controlador es el dueño del bucle; nunca se
            # llama arcade.run(). Cada vuelta es O(1) más lo que cueste el
            # comando recibido.
            while not controlador.terminado():
                vista.actualizar()                  # no bloquea (D44)
                comando = vista.pedir_comando()      # None si no hay nada (D43)
                controlador.procesar(comando)
                time.sleep(RITMO_SEGUNDOS)
        finally:
            vista.cerrar()

    # ------------------------------------------------------------------
    # Lectura de flags
    # ------------------------------------------------------------------
    # DECISIÓN: recorrido lineal O(a) sobre los argumentos en vez de argparse:
    # son 4 flags simples y argparse guarda sus opciones en dicts internos.

    def _leer_offline(self) -> "tuple[bool, Optional[str]]":
        for argumento in self._argumentos:
            if argumento == "--offline":
                return True, CARPETA_OFFLINE_POR_DEFECTO
            if argumento.startswith("--offline="):
                return True, argumento[len("--offline="):]
        return False, None

    def _leer_opcion_con_valor(self, nombre: str) -> Optional[str]:
        for indice, argumento in enumerate(self._argumentos):
            if argumento == nombre and indice + 1 < len(self._argumentos):
                return self._argumentos[indice + 1]
        return None

    def _leer_cache_size(self) -> int:
        valor = self._leer_opcion_con_valor("--cache-size")
        if valor is None:
            return CacheFichas.CAPACIDAD_POR_DEFECTO
        try:
            return int(valor)
        except ValueError as error:
            raise ValueError(f"--cache-size necesita un entero, recibí '{valor}'") from error
