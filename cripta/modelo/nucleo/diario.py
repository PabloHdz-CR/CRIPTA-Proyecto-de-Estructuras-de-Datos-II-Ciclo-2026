"""Diario de retroceso (§2.11): guarda cada mutación dentro de UN intervalo
(una acción del jugador) y permite deshacer el intervalo más reciente, hasta
TAMANO_HISTORIAL intervalos atrás.

Se engancha al Mutador por el protocolo que ya documenta mutador.py:
Partida llama abrir_intervalo()/cerrar_intervalo() alrededor de cada acción
aceptada, y cada mutación avisa con registrar(tipo, objetivo, detalle,
anterior, nuevo). Diario no sabe nada de reglas del juego: solo aplica el
inverso de cada tipo de mutación, uno por uno, en el orden CONTRARIO al que
ocurrieron.
"""
from __future__ import annotations

from ..estructuras.pila import Pila
from ..estructuras.pilaAcotada import PilaAcotada
from . import mutador as m

TAMANO_HISTORIAL = 5  # como máximo 5 acciones de retroceso (§2.11)


class Diario:
    """Pila acotada de intervalos; cada intervalo es, a su vez, una Pila de
    registros (tipo, objetivo, detalle, anterior, nuevo).

    DECISIÓN: una Pila (no una ListaEnlazada) para los registros de un
    intervalo: el propio docstring de Pila ya dice para qué sirve ("deshacer
    los cambios de una acción en orden inverso al que se hicieron"):
    apilarlos en el orden en que ocurren y recorrerlos da automáticamente el
    orden inverso, sin tener que invertir nada a mano.
    """

    def __init__(self, tamano: int = TAMANO_HISTORIAL) -> None:
        self._intervalos = PilaAcotada(tamano)
        self._actual = None  # Pila del intervalo abierto, o None

    def abrir_intervalo(self, partida) -> None:
        self._actual = Pila()

    def registrar(self, tipo, objetivo, detalle, anterior, nuevo) -> None:
        self._actual.apilar((tipo, objetivo, detalle, anterior, nuevo))

    def cerrar_intervalo(self) -> None:
        # DECISIÓN: un intervalo sin registros (una acción aceptada que no
        # disparó ninguna mutación, como Esperar si no hay nada programado
        # detrás) no se apila: no hay nada que deshacer ahí, y ocuparía un
        # lugar de los 5 sin necesidad.
        if not self._actual.esta_vacia():
            self._intervalos.apilar(self._actual)
        self._actual = None

    def hay_cambios(self) -> bool:
        return not self._intervalos.esta_vacia()

    def deshacer(self, partida) -> bool:
        """Deshace el intervalo más reciente. Devuelve False si no hay nada
        que deshacer (nunca lanza error en ese caso)."""
        if self._intervalos.esta_vacia():
            return False
        intervalo = self._intervalos.desapilar()
        for registro in intervalo:  # la Pila ya recorre del tope al fondo
            self._revertir(partida, registro)
        return True

    # ------------------------------------------------------------------
    # El inverso de cada mutación (mismo protocolo que documenta mutador.py)
    # ------------------------------------------------------------------

    def _revertir(self, partida, registro) -> None:
        tipo, objetivo, detalle, anterior, nuevo = registro

        if tipo == m.ATRIBUTO:
            setattr(objetivo, detalle, anterior)

        elif tipo == m.AGENDA_PROGRAMAR:
            # DECISIÓN: cancelar (no hay 'quitar' en Agenda): la cancelación
            # perezosa ya documentada en agenda.py hace que el evento se
            # ignore como si nunca se hubiera programado.
            partida.agenda.cancelar(objetivo)
        elif tipo == m.AGENDA_EXTRAER:
            partida.agenda.reinsertar(objetivo)
        elif tipo == m.AGENDA_CANCELAR:
            partida.agenda.reactivar(objetivo)

        elif tipo == m.SUELO_AGREGAR:
        elif tipo == m.SUELO_QUITAR:
            objetivo.suelo.agregar_al_final(anterior)

        elif tipo == m.INVENTARIO_AGREGAR:
            objetivo.inventario.quitar(nuevo)
        elif tipo == m.INVENTARIO_QUITAR:
            objeto, posicion, estaba_equipado = anterior
            objetivo.inventario.insertar_en(posicion, objeto)
            if estaba_equipado:
                objetivo.equipo.equipar(objeto)
        elif tipo == m.INVENTARIO_EQUIPAR:
            objeto, posicion, reemplazado = anterior
            objetivo.inventario.mover_a_posicion(objeto, posicion)
            if reemplazado is not None:
                objetivo.equipo.equipar(reemplazado)
            else:
                objetivo.equipo.desequipar(objeto)

        elif tipo == m.ENEMIGO_ACTIVAR:
            objetivo.activos.eliminar_nodo(objetivo.activos.buscar(nuevo))
            objetivo.dormidos.agregar_al_final(nuevo)
            nuevo.activo = False
        elif tipo == m.ENEMIGO_MOVER:
            origen, destino = anterior, nuevo
            destino.activos.eliminar_nodo(destino.activos.buscar(objetivo))
            origen.activos.agregar_al_final(objetivo)
            objetivo.sala = origen.id
        elif tipo == m.ENEMIGO_QUITAR:
            objetivo.activos.agregar_al_final(anterior)

        elif tipo == m.EFECTO_AGREGAR:
            objetivo.efectos.eliminar_nodo(objetivo.efectos.buscar(nuevo))
        elif tipo == m.EFECTO_QUITAR:
            objetivo.efectos.agregar_al_final(anterior)

        else:
            raise ValueError(f"Tipo de mutación desconocido en el diario: {tipo!r}")