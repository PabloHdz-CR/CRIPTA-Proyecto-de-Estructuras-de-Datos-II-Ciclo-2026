"""Sala del mundo (§2.1, §2.4, §2.9)."""
from __future__ import annotations

from ..actores.actor import clave_instancia
from ..estructuras.listaDoble import ListaDoble
from ..estructuras.listaEnlazada import ListaEnlazada
from ..nucleo.constantes import VIGENCIA_RASTRO
from ..puertos.dto import DIRECCIONES


class Sala:
    """Una sala: 4 salidas, enemigos dormidos y activos, objetos del suelo,
    trampas y el rastro del jugador.

    Rastro: guarda el instante de la última presencia del jugador (un solo
    campo por sala). Su caducidad se detecta al consultarlo, sin eventos de
    limpieza: consultar cuesta O(1) y decidir un rastreador, O(salidas).
    """

    def __init__(self, id_sala: int, nombre: str, salidas: tuple) -> None:
        self.id = id_sala
        self.nombre = nombre
        # DECISIÓN: tupla de 4 (N, S, E, O) y no una colección: acceso O(1) por
        # dirección y orden fijo, que da determinismo al errante y al rastreador.
        self.salidas = salidas                    # tupla de 4: N, S, E, O (o None)
        # DECISIÓN: ListaDoble para dormidos, activos y suelo: quitar un nodo ya
        # conocido es O(1) (eliminar_nodo) y agregar al final también.
        self.dormidos = ListaDoble()              # Enemigo, por id de instancia ascendente
        self.activos = ListaDoble()               # Enemigo en acción
        self.suelo = ListaDoble()                 # Objeto
        self.trampas = ListaEnlazada()            # Trampa
        # DECISIÓN: UN solo campo de rastro por sala (no una lista de visitas): basta
        # para decidir en O(salidas) y ocupa memoria constante por sala (§4.7).
        self.rastro = None                        # instante de la última presencia
        self.contenido_cargado = False

    # ------------------------------------------------------------------
    # Salidas
    # ------------------------------------------------------------------

    def salida(self, direccion: str):
        """La Salida en esa dirección, o None si no existe. O(1)."""
        return self.salidas[DIRECCIONES.index(direccion)]

    def vecinas_abiertas(self) -> ListaEnlazada:
        """Salidas transitables, en el orden fijo N, S, E, O (determinismo)."""
        abiertas = ListaEnlazada()
        for salida in self.salidas:
            if salida is not None and salida.transitable():
                abiertas.agregar_al_final(salida)
        return abiertas

    # ------------------------------------------------------------------
    # Rastro
    # ------------------------------------------------------------------

    def rastro_fresco(self, reloj: int):
        """El instante del rastro si tiene menos de 400 unidades, o None."""
        # DECISIÓN: la caducidad se detecta AL CONSULTAR; no hay eventos de limpieza
        # (alternativa descartada de §4.7: costaría un evento por sala visitada).
        if self.rastro is None or reloj - self.rastro >= VIGENCIA_RASTRO:
            return None
        return self.rastro

    # ------------------------------------------------------------------
    # Enemigos
    # ------------------------------------------------------------------

    def agregar_dormido(self, enemigo) -> None:
        """Inserta en orden ascendente de id de instancia. O(k), k dormidos."""
        # DECISIÓN: se ordena al CARGAR (pocos enemigos por sala) y no al activar:
        # así activar_enemigos() es un simple vaciado en orden, sin ordenar nada.
        nodo = self.dormidos.primero()
        while nodo is not None:
            if enemigo.clave_id < nodo.dato.clave_id:
                self.dormidos.insertar_antes_de(nodo, enemigo)
                return
            nodo = self.dormidos.siguiente_de(nodo)
        self.dormidos.agregar_al_final(enemigo)

    def activar_enemigos(self, partida) -> None:
        """Activa todos los dormidos, por id ascendente (así la agenda les
        asigna secuencias crecientes y el desempate es determinista)."""
        while not self.dormidos.esta_vacia():
            self.dormidos.ver_primero().activar(partida)

    def buscar_enemigo(self, id_instancia: str):
        for enemigo in self.activos:
            if enemigo.id_instancia == id_instancia:
                return enemigo
        return None

    def buscar_objeto(self, id_objeto: int):
        for objeto in self.suelo:
            if objeto.id_instancia == id_objeto:
                return objeto
        return None

    # ------------------------------------------------------------------
    # Trampas
    # ------------------------------------------------------------------

    def disparar_trampas(self, partida) -> None:
        for trampa in self.trampas:
            if not partida.jugador.vivo:
                return
            trampa.activar(partida)