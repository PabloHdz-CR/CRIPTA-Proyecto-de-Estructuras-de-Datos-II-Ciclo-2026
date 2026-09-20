from dataclasses import dataclass

from ..estructuras.listaEnlazada import ListaEnlazada

# Direcciones válidas, en el orden fijo en que se guardan las salidas de una
# sala. Un orden fijo hace que las decisiones al azar sean reproducibles.
DIRECCIONES = ("N", "S", "E", "O")


# ---------------------------------------------------------------------------
# Lista de criptas y datos generales
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResumenCriptaDTO:
    """Una fila de GET /criptas."""
    id: str
    nombre: str
    salas: int
    dificultad: int


@dataclass(frozen=True)
class JugadorDTO:
    """Estadísticas iniciales del jugador (vienen en los datos de la cripta)."""
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int


@dataclass(frozen=True)
class DatosCriptaDTO:
    """Respuesta de GET /criptas/{id}."""
    id: str
    version: str
    salas_total: int
    paginas: int
    salas_por_pagina: int
    sala_inicial: int
    sala_salida: int
    llave_salida: str
    presupuesto_solicitudes: int
    inventario_max: int
    jugador: JugadorDTO


# ---------------------------------------------------------------------------
# Esqueleto
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SalidaDTO:
    """Una salida de una sala. Si el JSON no trae 'cerrada', está abierta."""
    direccion: str
    sala: int                    # id de la sala a la que conduce
    cerrada: bool = False
    llave: str = None            # id de la llave que la abre (si está cerrada)
    cierre_automatico: int = None  # None = no se cierra sola


@dataclass(frozen=True)
class SalaDTO:
    id: int
    nombre: str
    salidas: ListaEnlazada       # ListaEnlazada de SalidaDTO, en orden N, S, E, O


@dataclass(frozen=True)
class PaginaSalasDTO:
    """Respuesta de GET /criptas/{id}/salas?pagina=n."""
    pagina: int
    total_paginas: int
    salas: ListaEnlazada         # ListaEnlazada de SalaDTO


# ---------------------------------------------------------------------------
# Contenido de las salas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnemigoInstanciaDTO:
    instancia: str
    tipo: str                    # id de catálogo
    vida: int = None             # None = usa vida_max de la ficha


@dataclass(frozen=True)
class TrampaInstanciaDTO:
    instancia: str
    tipo: str                    # id de catálogo


@dataclass(frozen=True)
class ContenidoSalaDTO:
    sala: int
    enemigos: ListaEnlazada      # de EnemigoInstanciaDTO
    objetos: ListaEnlazada       # de str (ids de catálogo)
    trampas: ListaEnlazada       # de TrampaInstanciaDTO


# ---------------------------------------------------------------------------
# Fichas del catálogo (una clase base y una subclase por clase del catálogo)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FichaDTO:
    """Base de todas las fichas. Cada subclase declara su CLASE."""
    id: str
    nombre: str

    CLASE = None  # sin anotación: es una constante de clase, no un campo

    @property
    def clase(self):
        return self.CLASE


@dataclass(frozen=True)
class FichaEnemigoDTO(FichaDTO):
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    comportamiento: str          # llega tal cual: "guardián", "errante", ...
    suelta: ListaEnlazada        # de str (ids de catálogo)

    CLASE = "enemigo"


@dataclass(frozen=True)
class FichaTrampaDTO(FichaDTO):
    dano: int                    # en el JSON el campo se llama "daño"
    rearme: int = None           # None = usar el valor por defecto (300)

    CLASE = "trampa"


@dataclass(frozen=True)
class FichaObjetoDTO(FichaDTO):
    """Datos comunes de todos los objetos."""
    peso: int
    valor: int


@dataclass(frozen=True)
class FichaArmaDTO(FichaObjetoDTO):
    ataque_bonus: int

    CLASE = "arma"


@dataclass(frozen=True)
class FichaArmaduraDTO(FichaObjetoDTO):
    defensa_bonus: int

    CLASE = "armadura"


@dataclass(frozen=True)
class FichaPocionDTO(FichaObjetoDTO):
    cura: int = None                    # None si la poción no cura
    modificador_velocidad: int = None   # None si no cambia la velocidad
    duracion: int = None

    CLASE = "pocion"


@dataclass(frozen=True)
class FichaAntidotoDTO(FichaObjetoDTO):
    CLASE = "antidoto"


@dataclass(frozen=True)
class FichaLlaveDTO(FichaObjetoDTO):
    abre: str                    # id de la puerta/llave que abre

    CLASE = "llave"


@dataclass(frozen=True)
class FichaAntorchaDTO(FichaObjetoDTO):
    duracion: int

    CLASE = "antorcha"


@dataclass(frozen=True)
class FichaPergaminoRetrocesoDTO(FichaObjetoDTO):
    CLASE = "pergamino_retroceso"