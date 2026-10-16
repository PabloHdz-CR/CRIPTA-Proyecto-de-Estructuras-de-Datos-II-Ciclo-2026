"""EstadoVista: foto de solo lectura con todo lo que la Vista necesita
mostrar (§6, §10.2).

Lo arma el Controlador (ConstructorEstadoVista, todavía por construir del
lado de Controlador) a partir del modelo real (Partida, Jugador, Sala...).
Vista NUNCA ve esas clases: solo recibe este paquete de datos planos, ya
traducido. Por eso nada aquí importa cripta.modelo.nucleo, .actores, etc. --
solo ListaEnlazada (es infraestructura, no reglas del juego) y tipos nativos.

Todo son dataclasses congeladas (frozen): una foto, no algo que la Vista
pueda mutar y que se desincronice con el modelo real.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..modelo.estructuras.listaEnlazada import ListaEnlazada

# Los tres estados posibles de una salida, tal como los pide la guía
# ("abierta, cerrada o con llave").
SALIDA_ABIERTA = "abierta"
SALIDA_CERRADA_CON_LLAVE = "cerrada_con_llave"
SALIDA_SIN_SALIDA = "sin_salida"


@dataclass(frozen=True)
class SalidaVisible:
    direccion: str                  # "N", "S", "E" u "O"
    estado: str                     # una de las constantes SALIDA_*


@dataclass(frozen=True)
class ActorVisible:
    """Un enemigo tal como lo ve el jugador: ya etiquetado ("Rata gigante
    #1"), no por su id_instancia interno."""
    etiqueta: str
    vida: int
    vida_max: int


@dataclass(frozen=True)
class ObjetoVisible:
    id_objeto: int                  # el id_instancia real: lo necesita
                                     # TraductorComandos para armar Recoger/
                                     # Soltar/Usar/Equipar sin adivinar
    nombre: str
    clase: str                      # "arma", "armadura", "pocion", ...
    peso: int
    valor: int
    equipado: bool = False


@dataclass(frozen=True)
class EfectoVisible:
    tipo: str                       # "veneno", "velocidad", "antorcha", "regeneracion"
    descripcion: str                # texto ya armado por el Controlador


@dataclass(frozen=True)
class SalaVisible:
    nombre: str
    salidas: tuple                  # 4 SalidaVisible, orden N, S, E, O (como Sala.salidas)
    enemigos: ListaEnlazada         # de ActorVisible
    objetos: ListaEnlazada          # de ObjetoVisible (lo que hay en el suelo)


@dataclass(frozen=True)
class JugadorVisible:
    vida: int
    vida_max: int
    ataque_efectivo: int
    defensa_efectiva: int
    velocidad: int
    antorcha_encendida: bool
    acciones: int
    enemigos_derrotados: int


@dataclass(frozen=True)
class InventarioVisible:
    objetos: ListaEnlazada          # de ObjetoVisible, en el orden real (el del cursor)
    indice_actual: int              # -1 si está vacío
    capacidad: int
    cantidad_pergaminos: int
    criterio_orden: str = None      # None = solo orden real
    vista_ordenada: ListaEnlazada = None


@dataclass(frozen=True)
class EstadoVista:
    """Lo que necesita UNA pantalla de juego para dibujarse completa."""
    id_cripta: str
    version_cripta: str
    reloj: int
    terminada: bool
    resultado: str                  # None, "victoria" o "derrota"
    jugador: JugadorVisible
    sala: SalaVisible
    efectos: ListaEnlazada          # de EfectoVisible (los del jugador)
    inventario: InventarioVisible
    mensajes: ListaEnlazada         # últimos 20 (los entrega Bitacora)


@dataclass(frozen=True)
class CriptaVisible:
    """Una fila del menú de selección de cripta (mostrar_menu). Es el mismo
    contenido que ResumenCriptaDTO en el modelo, pero Vista no importa ese
    módulo: el Controlador lo traduce al armar la lista."""
    id: str
    nombre: str
    salas: int
    dificultad: int


@dataclass(frozen=True)
class PuntajeVisible:
    """Una fila de la tabla de puntajes (mostrar_puntajes), ya traducida de
    RegistroPuntaje."""
    nombre: str
    id_cripta: str
    version_cripta: str
    acciones: int
    enemigos_derrotados: int
    tiempo_final: int
    resultado: str                  # "victoria" o "derrota"


@dataclass(frozen=True)
class ResultadoFinVisible:
    """Lo que necesita la pantalla de Fin: el mismo contenido de un
    PuntajeVisible, sin repetir la cripta (ya se sabe cuál se estaba
    jugando) -- se arma aparte porque llega en el momento en que termina la
    partida, no desde la tabla de puntajes guardada."""
    resultado: str                  # "victoria" o "derrota"
    acciones: int
    enemigos_derrotados: int
    tiempo_final: int
    # Resumen de red y caché (§5.1), el mismo que ReporteFinal imprime en la
    # terminal. Opcional: --replay arma el resultado sin estos datos.
    solicitudes_realizadas: Optional[int] = None
    presupuesto: Optional[int] = None       # None = --offline (sin red)
    aciertos_cache: Optional[int] = None
    fallos_cache: Optional[int] = None