"""Ayudas compartidas por las pruebas de 001-terreno-cazador (T005).

No es una prueba y no va en ejecutar_pruebas.py: lo importan las pruebas de
FR-004 a FR-028. Como vive en pruebas/, puede usar estructuras de Python; lo
que se entrega al modelo (DTOs, salas) usa las estructuras propias.

Contenido:
  - Descripciones de mundos sintéticos: pasillo, malla n×n, la ruta "menos
    salas pero más cara" (H2.E5) y criptas pequeñas al azar con
    random.Random(semilla) para la equivalencia con el oráculo (T022).
  - salas_dto() y mundo_desde(): convierten una descripción en SalaDTO y en un
    Mundo enlazado.
  - FuenteMemoria y partida_minima(): una Partida real sobre una fuente falsa
    en memoria, sin disco ni red.
  - servicio_terreno(): ServicioDatos sin conexión sobre el paquete de prueba
    pruebas/datos/terreno_cazador (T004).
  - VistaRegistradora: guarda cada llamada a mostrar_error, mostrar_estado y
    mostrar_fin.

Descripción de un mundo: una tupla de salas (id, salidas), donde cada salida
es (direccion, destino, costo, cerrada). costo None = no declarado.
"""
from __future__ import annotations

import random
import tempfile
from pathlib import Path

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.mundo.mundo import Mundo
from cripta.modelo.nucleo.partida import Partida
from cripta.modelo.puertos.dto import (
    DIRECCIONES, ContenidoSalaDTO, DatosCriptaDTO, EnemigoInstanciaDTO,
    FichaEnemigoDTO, JugadorDTO, PaginaSalasDTO, ResumenCriptaDTO, SalaDTO,
    SalidaDTO)
from cripta.modelo.puertos.errores import ErrorDeRed
from cripta.modelo.puertos.fuenteDatos import FuenteDatos, validar_lote
from cripta.vista.vistaNula import VistaNula

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_TERRENO = RAIZ / "pruebas" / "datos" / "terreno_cazador"

OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}
COSTOS_AL_AZAR = (1, 50, 100, 250, 300)

ID_CRIPTA = "c-sintetica"
VERSION_CRIPTA = "v1"
VERSION_CATALOGO = "cat-sintetico"


def le(*elementos) -> ListaEnlazada:
    """ListaEnlazada con los elementos dados, en orden."""
    lista = ListaEnlazada()
    for elemento in elementos:
        lista.agregar_al_final(elemento)
    return lista


def a_lista(iterable) -> list:
    """Copia a una lista de Python (solo para comparar en las pruebas)."""
    return [x for x in iterable]


# ---------------------------------------------------------------------------
# Descripciones de mundos sintéticos
# ---------------------------------------------------------------------------

def salida(direccion: str, destino: int, costo=None, cerrada: bool = False) -> tuple:
    """Una salida de la descripción."""
    return (direccion, destino, costo, cerrada)


def pasillo(n: int, costo=None) -> tuple:
    """Salas 1..n en línea, de oeste a este, con puertas en los dos sentidos."""
    salas = []
    for i in range(1, n + 1):
        salidas = []
        if i < n:
            salidas.append(salida("E", i + 1, costo))
        if i > 1:
            salidas.append(salida("O", i - 1, costo))
        salas.append((i, tuple(salidas)))
    return tuple(salas)


def id_malla(n: int, fila: int, columna: int) -> int:
    """Id de la sala (fila, columna) de una malla n×n, desde 1."""
    return fila * n + columna + 1


def malla(n: int, costo=None) -> tuple:
    """Malla n×n con puertas abiertas en los dos sentidos. La fila 0 está al norte."""
    salas = []
    for fila in range(n):
        for columna in range(n):
            salidas = []
            if fila > 0:
                salidas.append(salida("N", id_malla(n, fila - 1, columna), costo))
            if fila < n - 1:
                salidas.append(salida("S", id_malla(n, fila + 1, columna), costo))
            if columna < n - 1:
                salidas.append(salida("E", id_malla(n, fila, columna + 1), costo))
            if columna > 0:
                salidas.append(salida("O", id_malla(n, fila, columna - 1), costo))
            salas.append((id_malla(n, fila, columna), tuple(salidas)))
    return tuple(salas)


def ruta_corta_cara() -> tuple:
    """H2.E5: de la sala 1 a la 2 hay una ruta de 1 salida que cuesta 500
    (1 E→2) y otra de 3 salidas que suma 300 (1 N→3, 3 E→4 y 4 S→2, de 100
    cada una). Con el cazador en 1 y el jugador en 2, debe salir por el N con
    costo 100."""
    return (
        (1, (salida("N", 3, 100), salida("E", 2, 500))),
        (2, (salida("N", 4, 100), salida("O", 1, 500))),
        (3, (salida("S", 1, 100), salida("E", 4, 100))),
        (4, (salida("S", 2, 100), salida("O", 3, 100))),
    )


def cripta_al_azar(azar: random.Random, salas_min: int = 4, salas_max: int = 12,
                   prob_un_sentido: float = 0.2, prob_cerrada: float = 0.2,
                   prob_una_cara: float = 0.3, prob_duplicada: float = 0.25) -> tuple:
    """Cripta pequeña al azar para la equivalencia con el oráculo (T022).

    - Costos al azar en COSTOS_AL_AZAR o sin declarar.
    - Puertas de doble sentido con costos coherentes entre caras (las dos
      iguales, o solo una declarada: FR-027), y salidas de un solo sentido.
    - Cada cara se cierra al azar por su cuenta (puertas direccionales).
    - Con frecuencia fija (prob_duplicada), una segunda puerta entre las mismas
      dos salas, en otra dirección y con el mismo costo, para ejercitar el
      desempate N, S, E, O de FR-014.

    Usa solo el Random que recibe (determinismo). No garantiza que el grafo
    sea conexo: "sin ruta" también es un caso que se prueba.
    """
    n = azar.randint(salas_min, salas_max)
    libres = {i: list(DIRECCIONES) for i in range(1, n + 1)}
    salidas = {i: [] for i in range(1, n + 1)}

    def direccion_libre(a, b):
        """Una dirección libre en a cuya opuesta esté libre en b, o None."""
        candidatas = [d for d in libres[a] if OPUESTA[d] in libres[b]]
        return azar.choice(candidatas) if candidatas else None

    def conectar(a, b, d, costo, un_sentido):
        libres[a].remove(d)
        salidas[a].append(salida(d, b, costo, azar.random() < prob_cerrada))
        if un_sentido:
            return
        libres[b].remove(OPUESTA[d])
        costo_vuelta = costo
        if costo is not None and azar.random() < prob_una_cara:
            costo_vuelta = None                     # solo una cara declara
        salidas[b].append(salida(OPUESTA[d], a, costo_vuelta, azar.random() < prob_cerrada))

    intentos = azar.randint(n, 2 * n)
    for _ in range(intentos):
        a = azar.randint(1, n)
        b = azar.randint(1, n)
        if a == b:
            continue
        d = direccion_libre(a, b)
        if d is None:
            continue
        costo = azar.choice(COSTOS_AL_AZAR + (None,))
        un_sentido = azar.random() < prob_un_sentido
        conectar(a, b, d, costo, un_sentido)
        if azar.random() < prob_duplicada:
            d2 = direccion_libre(a, b)
            if d2 is not None:
                conectar(a, b, d2, costo, un_sentido)

    return tuple((i, tuple(sorted(salidas[i], key=lambda s: DIRECCIONES.index(s[0]))))
                 for i in range(1, n + 1))


def suma_de_costos(descripcion) -> int:
    """Suma de los costos de todas las salidas (100 si no se declara): cota
    superior de cualquier ruta, para elegir rangos al azar (T022)."""
    return sum(100 if s[2] is None else s[2] for _, salidas in descripcion for s in salidas)


def validar_descripcion(descripcion) -> None:
    """Revisa que la descripción sea un esqueleto válido: ids únicos, una salida
    por dirección, destinos existentes y caras de una misma puerta con costos
    coherentes (las dos iguales o solo una declarada, FR-027)."""
    ids = [id_sala for id_sala, _ in descripcion]
    assert len(ids) == len(set(ids)), f"ids repetidos: {ids}"
    por_id = dict(descripcion)
    for id_sala, salidas in descripcion:
        direcciones = [s[0] for s in salidas]
        assert len(direcciones) == len(set(direcciones)), f"sala {id_sala}: {direcciones}"
        for d, destino, costo, _ in salidas:
            assert destino in por_id, f"sala {id_sala} {d} → {destino} no existe"
            assert costo is None or (type(costo) is int and costo >= 1), (id_sala, d, costo)
            for d2, destino2, costo2, _ in por_id[destino]:
                if d2 == OPUESTA[d] and destino2 == id_sala:
                    assert costo is None or costo2 is None or costo == costo2, (
                        f"caras distintas entre {id_sala} y {destino}: {costo} y {costo2}")


# ---------------------------------------------------------------------------
# De la descripción al modelo
# ---------------------------------------------------------------------------

def salas_dto(descripcion) -> ListaEnlazada:
    """ListaEnlazada de SalaDTO, con las salidas en orden N, S, E, O."""
    resultado = ListaEnlazada()
    for id_sala, salidas in descripcion:
        ordenadas = sorted(salidas, key=lambda s: DIRECCIONES.index(s[0]))
        dtos = ListaEnlazada()
        for d, destino, costo, cerrada in ordenadas:
            dtos.agregar_al_final(SalidaDTO(direccion=d, sala=destino, cerrada=cerrada,
                                            costo=costo))
        resultado.agregar_al_final(SalaDTO(id=id_sala, nombre=f"Sala {id_sala}", salidas=dtos))
    return resultado


def datos_cripta(descripcion, sala_inicial: int = 1, velocidad_jugador: int = 100,
                 vida_jugador: int = 100) -> DatosCriptaDTO:
    """Datos generales de una cripta sintética. La sala de salida es la de id
    mayor, para que la partida no termine por llegar a ella sin querer."""
    ultima = max(id_sala for id_sala, _ in descripcion)
    return DatosCriptaDTO(
        id=ID_CRIPTA, version=VERSION_CRIPTA, salas_total=len(descripcion), paginas=1,
        salas_por_pagina=max(1, len(descripcion)), sala_inicial=sala_inicial,
        sala_salida=ultima, llave_salida="itm_llave_sintetica",
        presupuesto_solicitudes=10 ** 6, inventario_max=10,
        jugador=JugadorDTO(vida_max=vida_jugador, ataque=1, defensa=0,
                           velocidad=velocidad_jugador))


def mundo_desde(descripcion, enlazar: bool = True) -> Mundo:
    """Mundo con el esqueleto de la descripción. Si enlazar es True, llama a
    Mundo.enlazar() (costos efectivos y entrantes, T016)."""
    mundo = Mundo(datos_cripta(descripcion))
    mundo.agregar_esqueleto(salas_dto(descripcion))
    if enlazar:
        mundo.enlazar()
    return mundo


def ficha_enemigo(id_ficha: str, comportamiento: str, velocidad: int = 100,
                  rango=None, vida_max: int = 10, ataque: int = 1,
                  defensa: int = 0) -> FichaEnemigoDTO:
    """Ficha de enemigo para una FuenteMemoria (rango solo si es cazador)."""
    return FichaEnemigoDTO(id=id_ficha, nombre=id_ficha, vida_max=vida_max, ataque=ataque,
                           defensa=defensa, velocidad=velocidad,
                           comportamiento=comportamiento, suelta=ListaEnlazada(),
                           rango=rango)


def enemigo(sala: int, instancia: str, tipo: str, vida=None) -> tuple:
    """Un enemigo colocado en una sala: (sala, EnemigoInstanciaDTO)."""
    return (sala, EnemigoInstanciaDTO(instancia=instancia, tipo=tipo, vida=vida))


class FuenteMemoria(FuenteDatos):
    """FuenteDatos en memoria para una cripta sintética: sin disco ni red.
    No cuenta solicitudes (como FuenteOffline)."""

    def __init__(self, descripcion, enemigos=(), fichas=(), sala_inicial: int = 1,
                 velocidad_jugador: int = 100, vida_jugador: int = 100) -> None:
        validar_descripcion(descripcion)
        self._descripcion = descripcion
        self._datos = datos_cripta(descripcion, sala_inicial, velocidad_jugador, vida_jugador)
        self._enemigos = tuple(enemigos)
        self._fichas = tuple(fichas)

    def listar_criptas(self):
        return le(ResumenCriptaDTO(id=ID_CRIPTA, nombre="Sintética",
                                   salas=len(self._descripcion), dificultad=1))

    def datos_generales(self, id_cripta):
        return self._datos

    def esqueleto(self, id_cripta, pagina):
        return PaginaSalasDTO(pagina=1, total_paginas=1, salas=salas_dto(self._descripcion))

    def contenido(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        resultado = ListaEnlazada()
        for id_sala in ids_salas:
            enemigos = ListaEnlazada()
            for sala, dto in self._enemigos:
                if sala == id_sala:
                    enemigos.agregar_al_final(dto)
            resultado.agregar_al_final(ContenidoSalaDTO(
                sala=id_sala, enemigos=enemigos, objetos=ListaEnlazada(),
                trampas=ListaEnlazada()))
        return resultado

    def catalogo(self, ids):
        validar_lote("catalogo", ids)
        resultado = ListaEnlazada()
        for id_ficha in ids:
            encontrada = None
            for ficha in self._fichas:
                if ficha.id == id_ficha:
                    encontrada = ficha
            if encontrada is None:
                raise ErrorDeRed("catalogo", f"la ficha {id_ficha} no existe")
            resultado.agregar_al_final(encontrada)
        return resultado

    def version_cripta(self, id_cripta):
        return VERSION_CRIPTA

    def version_catalogo(self):
        return VERSION_CATALOGO

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass


def servicio_sobre(fuente: FuenteDatos) -> ServicioDatos:
    """ServicioDatos real sobre la fuente dada, con la caché de fichas en una
    carpeta temporal (nunca en la del juego)."""
    carpeta = Path(tempfile.mkdtemp(prefix="apoyo_terreno_"))
    return ServicioDatos(fuente, FuenteAsincrona(fuente), CacheFichas(25),
                         AlmacenLocalDisco(carpeta))


def servicio_terreno() -> ServicioDatos:
    """ServicioDatos sin conexión sobre el paquete pruebas/datos/terreno_cazador."""
    return servicio_sobre(FuenteOffline(CARPETA_TERRENO))


def partida_minima(descripcion, sala_inicial: int = 1, enemigos=(), fichas=(),
                   semilla: int = 1, velocidad_jugador: int = 100,
                   vida_jugador: int = 100, diario=None) -> Partida:
    """Partida real e iniciada sobre una FuenteMemoria. Los enemigos de la sala
    inicial se activan al iniciar; para los de otras salas, ver activar_sala().
    Si se pasa un Diario, se conecta antes de iniciar (como el Controlador)."""
    fuente = FuenteMemoria(descripcion, enemigos, fichas, sala_inicial,
                           velocidad_jugador, vida_jugador)
    servicio = servicio_sobre(fuente)
    servicio.iniciar_cripta(ID_CRIPTA)
    partida = Partida(servicio)
    if diario is not None:
        partida.conectar_diario(diario)
    partida.iniciar(semilla)
    return partida


def activar_sala(partida: Partida, id_sala: int) -> None:
    """Carga el contenido de la sala (si falta) y activa a sus enemigos, como
    cuando el jugador entra en ella."""
    partida._asegurar_contenido(id_sala)
    partida.mundo.sala(id_sala).activar_enemigos(partida)


def buscar_enemigo(partida: Partida, id_instancia: str):
    """El enemigo con ese id de instancia, activo o dormido, en cualquier sala."""
    for sala in partida.mundo:
        for grupo in (sala.activos, sala.dormidos):
            for actor in grupo:
                if actor.id_instancia == id_instancia:
                    return actor
    raise AssertionError(f"no hay ningún enemigo '{id_instancia}'")


# ---------------------------------------------------------------------------
# Vista
# ---------------------------------------------------------------------------

class VistaRegistradora(VistaNula):
    """VistaNula que guarda cada llamada para que las pruebas la revisen."""

    def __init__(self) -> None:
        super().__init__()
        self.errores = []
        self.estados = []
        self.fines = []

    def mostrar_error(self, mensaje: str) -> None:
        self.errores.append(mensaje)

    def mostrar_estado(self, estado) -> None:
        self.estados.append(estado)

    def mostrar_fin(self, resultado) -> None:
        self.fines.append(resultado)

    @property
    def ultimo_estado(self):
        """El último estado mostrado, o None."""
        return self.estados[-1] if self.estados else None


if __name__ == "__main__":
    # Autocomprobación de las descripciones (no usa el modelo): las criptas al
    # azar son esqueletos válidos, reproducibles con la misma semilla, y una
    # parte tiene dos salidas hacia la misma vecina (FR-014).
    for constructor in (pasillo(5), pasillo(3, costo=250), malla(4), malla(3, costo=50),
                        ruta_corta_cara()):
        validar_descripcion(constructor)
    assert len(malla(32)) == 1024
    con_duplicadas = 0
    for semilla in range(300):
        primera = cripta_al_azar(random.Random(semilla))
        assert primera == cripta_al_azar(random.Random(semilla)), semilla
        validar_descripcion(primera)
        assert 4 <= len(primera) <= 12
        for _, salidas in primera:
            destinos = [s[1] for s in salidas]
            if len(destinos) != len(set(destinos)):
                con_duplicadas += 1
                break
    assert con_duplicadas > 30, f"pocas criptas con salidas duplicadas: {con_duplicadas}"
    print(f"apoyo_terreno OK ({con_duplicadas} de 300 criptas con dos salidas a la misma vecina)")
