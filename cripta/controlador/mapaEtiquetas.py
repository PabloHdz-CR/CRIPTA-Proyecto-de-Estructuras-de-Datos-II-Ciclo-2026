"""MapaEtiquetas: asocia cada id de instancia de enemigo con su etiqueta
visible ("Rata gigante #1", "Rata gigante #2"...) de forma ESTABLE a lo
largo de la partida (§2.6, §10.2). Lo comparten ConstructorEstadoVista
(id -> etiqueta) y TraductorComandos (etiqueta -> id).

Problema que resuelve: Etiquetador (vista/etiquetador.py) SOLO sabe generar
una etiqueta nueva cada vez que se le pregunta. Si se llamara una vez por
turno, "Rata gigante #1" pasaría a ser "#2" en el turno siguiente. Además,
Vista nunca ve el id de instancia real (ActorVisible solo trae la etiqueta):
cuando el jugador elige "atacar Rata gigante #1" (D46), Controlador tiene
que volver de la etiqueta al id real para construir Atacar(objetivo=...).

DECISIÓN (D47): ListaEnlazada de pares (id_instancia, etiqueta) con búsqueda
lineal en ambos sentidos.
  - etiqueta_de y resolver: O(k) en tiempo, k = enemigos etiquetados en la
    partida; memoria O(k).
  - Alternativas descartadas:
      * dict id -> etiqueta: prohibido como tabla de búsqueda (§7).
      * Tabla hash propia: O(1) promedio, pero k son decenas de enemigos por
        cripta y la tabla necesitaría DOS índices (uno por id y otro por
        etiqueta); con k tan pequeño la constante de hashear supera a
        recorrer la lista (mismo criterio que D32).
      * Recalcular con Etiquetador en cada turno: O(e) pero las etiquetas
        cambian entre turnos y el ataque apuntaría al enemigo equivocado.
  - Límite conocido: si una cripta tuviera miles de enemigos visibles a la
    vez, conviene cambiar a una tabla hash propia con dos índices.

DECISIÓN: se usa Etiquetador de la Vista porque es la regla de nombrado que
la Vista ya definió (§2.6); no dibuja nada ni importa arcade, así que el
Controlador no queda atado a una vista concreta.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..vista.etiquetador import Etiquetador

if TYPE_CHECKING:
    from ..modelo.actores.enemigo import Enemigo


class MapaEtiquetas:

    def __init__(self) -> None:
        self._etiquetador: Etiquetador = Etiquetador()
        self._pares: ListaEnlazada = ListaEnlazada()      # (id_instancia, etiqueta)

    def reiniciar(self) -> None:
        """Una cripta nueva (o cargada) empieza de cero. O(1)."""
        self._etiquetador.reiniciar()
        self._pares = ListaEnlazada()

    def etiqueta_de(self, enemigo: "Enemigo") -> str:
        """Etiqueta estable: se asigna la primera vez y se recuerda, incluso
        si el enemigo cambia de sala. O(k)."""
        existente = self._buscar_por_instancia(enemigo.id_instancia)
        if existente is not None:
            return existente
        etiqueta = self._etiquetador.etiqueta(enemigo.nombre)
        self._pares.agregar_al_final((enemigo.id_instancia, etiqueta))
        return etiqueta

    def resolver(self, etiqueta: str) -> Optional[str]:
        """El id de instancia de esa etiqueta, o None. O(k)."""
        for id_instancia, etiqueta_guardada in self._pares:
            if etiqueta_guardada == etiqueta:
                return id_instancia
        return None

    def _buscar_por_instancia(self, id_instancia: str) -> Optional[str]:
        for id_guardado, etiqueta in self._pares:
            if id_guardado == id_instancia:
                return etiqueta
        return None
