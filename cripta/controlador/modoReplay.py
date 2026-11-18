"""ModoReplay: `--replay partida.log` (§4.11). Valida versión de cripta y
de catálogo antes de reproducir: si no coinciden, lo REPORTA y no reproduce
(Apéndice B). Corre con VistaNula, sin vista interactiva (§6).

Complejidad: O(A · C) en tiempo, A acciones del log y C el costo de un ciclo
de eventos (< 20 ms por §5.2). Memoria O(A) para las acciones leídas.

DECISIÓN: el log llega como puerto RegistroAcciones ya construido por
FabricaAplicacion: ModoReplay no abre archivos ni conoce el formato.

DECISIÓN: se reproduce desde el inicio con la semilla del encabezado y la
MISMA Partida.aplicar_accion que usa el juego interactivo. Alternativa
descartada: guardar estados intermedios en el log, que es una copia del
estado (prohibido en §4.6) y dejaría de probar el determinismo.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..modelo.nucleo.diario import Diario
from ..modelo.nucleo.lineaTiempo import K_POR_OMISION, LineaTiempo
from ..modelo.nucleo.partida import Partida
from ..modelo.puertos.errores import ErrorCripta
from ..vista.estadoVista import ResultadoFinVisible
from .bench.reporte import Reporte
from .constructorEstadoVista import ConstructorEstadoVista
from .constructorResumen import ConstructorResumen
from .mapaEtiquetas import MapaEtiquetas

if TYPE_CHECKING:
    from ..modelo.datos.servicioDatos import ServicioDatos
    from ..modelo.puertos.dto import DatosCriptaDTO
    from ..modelo.puertos.registroAcciones import EncabezadoPartida, RegistroAcciones
    from ..vista.vistaJuego import VistaJuego
    from .reporteFinal import ReporteFinal


class ModoReplay:

    def __init__(self, servicio: "ServicioDatos", vista: "VistaJuego",
                 reporte_final: "ReporteFinal", reporte: Optional[Reporte] = None,
                 copiador_estado=None, k_linea: int = K_POR_OMISION) -> None:
        self._servicio = servicio
        self._vista = vista
        self._reporte_final = reporte_final
        # DECISIÓN: los errores también van a un Reporte: con VistaNula,
        # mostrar_error no muestra nada, y el Apéndice B prohíbe fallar en
        # silencio. Reporte es el formateador de --bench (ver ReporteFinal).
        self._reporte = reporte if reporte is not None else Reporte()
        self._constructor = ConstructorEstadoVista(MapaEtiquetas())
        self.partida: Optional[Partida] = None
        # 004-linea-tiempo (research R8): la misma línea de tiempo que en la
        # partida en vivo, alimentada por las acciones y pergaminos del log.
        self._copiador_estado = copiador_estado
        self._k_linea = k_linea

    def ejecutar(self, registro: "RegistroAcciones", hasta: Optional[int] = None) -> bool:
        """True si se reprodujo completa; False si no (ya reportado).

        hasta (004-linea-tiempo, FR-013, FR-014): al terminar el log imprime el
        resumen del instante 'hasta' de la historia tal como quedó, el mismo
        que daría «historia <hasta>» al final de la partida original."""
        try:
            encabezado, acciones = registro.leer()
            datos = self._servicio.iniciar_cripta(encabezado.id_cripta)
        except (OSError, ErrorCripta) as error:
            return self._fallar(f"No se pudo leer el log o iniciar la cripta: {error}")

        motivo = self._version_incompatible(datos, encabezado)
        if motivo is not None:
            return self._fallar(f"No se puede garantizar una reproducción fiel: {motivo}")

        self.partida = Partida(self._servicio)
        self.partida.conectar_diario(Diario())        # el log puede traer PERGAMINO
        numero = 0
        try:
            self.partida.iniciar(encabezado.semilla)
            if self._copiador_estado is not None:
                self.partida.conectar_linea(LineaTiempo(self._k_linea, self._copiador_estado))
            for accion in acciones:
                numero += 1
                if self.partida.terminada():
                    break
                resultado = self.partida.aplicar_accion(accion)
                if not resultado.aceptada:
                    # Un rechazo nunca se anexa al log: si aparece uno, el log
                    # no corresponde a estos datos. Se reporta y se detiene.
                    return self._fallar(
                        f"La acción #{numero} del log ({accion.texto()}) fue rechazada "
                        f"al reproducir: {resultado.motivo}. El log no corresponde a "
                        f"estos datos o a esta versión del programa.")
        except ErrorCripta as error:
            return self._fallar(f"Error durante la reproducción: {error}")

        self._vista.mostrar_estado(self._constructor.construir(self.partida))
        self._reporte.titulo("Reproducción completa")
        self._reporte.nota(f"Acciones reproducidas: {numero}")
        self._reporte.nota(f"Reloj virtual final:   {self.partida.reloj}")
        estado = self.partida.fin if self.partida.fin is not None else "en curso"
        self._reporte.nota(f"Estado final:          {estado}")
        if self.partida.terminada():
            self._vista.mostrar_fin(self._resultado_visible())
        if hasta is not None and not self._imprimir_hasta(hasta):
            return False
        self._reporte_final.imprimir(self._servicio)
        return True

    def _imprimir_hasta(self, t: int) -> bool:
        """El resumen del instante t (contracts/cli.md). Si t es posterior al
        final, el estado final y el aviso de que la partida terminó antes."""
        partida = self.partida
        linea = partida.linea
        if linea is None:
            return self._fallar("Esta reproducción no tiene línea de tiempo.")
        final = partida.reloj
        try:
            if t > final:
                copia = linea.reconstruir_accion(linea.acciones + 1, partida)
                resumen = ConstructorResumen().construir(
                    copia, str(t), final, aviso=f"La partida terminó antes, en el instante {final}.")
            else:
                copia = linea.reconstruir_instante(t, partida)
                resumen = ConstructorResumen().construir(copia, str(t), t)
        except ErrorCripta as error:
            return self._fallar(f"No se pudo consultar el instante {t}: {error}")
        self._reporte.titulo(f"Estado en el instante {t}")
        for texto in resumen.lineas:
            self._reporte.nota(texto)
        return True

    def _fallar(self, mensaje: str) -> bool:
        self._vista.mostrar_error(mensaje)
        self._reporte.titulo("Reproducción NO realizada")
        self._reporte.nota(mensaje)
        return False

    def _version_incompatible(self, datos: "DatosCriptaDTO",
                              encabezado: "EncabezadoPartida") -> Optional[str]:
        return motivo_version_incompatible(self._servicio, datos, encabezado)

    def _resultado_visible(self) -> ResultadoFinVisible:
        registro = self.partida.resultado("replay")
        return ResultadoFinVisible(
            resultado=registro.resultado, acciones=registro.acciones,
            enemigos_derrotados=registro.enemigos_derrotados,
            tiempo_final=registro.tiempo_final)


def motivo_version_incompatible(servicio: "ServicioDatos", datos: "DatosCriptaDTO",
                                encabezado: "EncabezadoPartida") -> Optional[str]:
    """El motivo por el que el log no se puede reproducir fielmente, o None
    si se puede. O(1). La comparten --replay (ModoReplay) y el replay en la
    ventana (ControladorReplay): la regla vive en un solo lugar."""
    if datos.version != encabezado.version_cripta:
        return (f"la cripta '{encabezado.id_cripta}' está en la versión "
                f"'{datos.version}' y el log se grabó con '{encabezado.version_cripta}'")
    actual = servicio.version_catalogo()
    grabada = encabezado.version_catalogo
    # DECISIÓN: "None" en el log = se grabó sin conocer la versión del
    # catálogo (modo offline sin versión); actual None = hoy no se puede
    # consultar. En ambos casos no hay con qué comparar y se reproduce: la
    # versión de la cripta ya coincidió.
    if grabada not in (None, "None") and actual is not None and actual != grabada:
        return (f"el catálogo está en la versión '{actual}' y el log se "
                f"grabó con '{grabada}'")
    return None
