from abc import ABC, abstractmethod


class AlmacenLocal(ABC):
    """Puerto de persistencia en disco para fichas del catálogo (§4.4).

    Por ahora SOLO guarda fichas individuales, etiquetadas con la versión del
    catálogo bajo la que se descargaron. El esqueleto y el contenido de una
    cripta se resolverán en el Paso 6, junto con el guardado binario de la
    partida, para no definir dos formatos de persistencia distintos.

    Una ficha guardada bajo una versión de catálogo que YA NO coincide con la
    versión actual se considera "no encontrada" (no un error): el enunciado
    dice que solo se vuelve a pedir por red una ficha que nunca se persistió
    o cuya versión ya no coincide (§4.4), así que cargar_ficha devuelve None
    en ambos casos, y quien llama decide pedirla de nuevo.
    """

    @abstractmethod
    def guardar_ficha(self, ficha, version_catalogo):
        """Persiste 'ficha' (una subclase de FichaDTO) bajo la versión actual
        del catálogo. Sobrescribe lo que hubiera guardado con ese mismo id."""

    @abstractmethod
    def cargar_ficha(self, id_ficha, version_catalogo):
        """Devuelve la ficha guardada con ese id, o None si no existe o si fue
        guardada bajo una versión de catálogo distinta a 'version_catalogo'."""

    # ------------------------------------------------------------------
    # Ubicación de llaves (003-resolubilidad, FR-027, FR-028)
    # ------------------------------------------------------------------
    # DECISIÓN: no son abstractos, como los métodos opcionales de VistaJuego:
    # un almacén que no los implemente simplemente no guarda llaves y el
    # servicio las vuelve a pedir (cuenta en el presupuesto, pero nunca da un
    # dato equivocado).

    def guardar_llaves(self, id_cripta, version_cripta, ubicaciones):
        """Persiste la ubicación de llaves (ListaEnlazada de UbicacionLlaveDTO)
        de esa cripta bajo su versión. Sobrescribe lo guardado antes."""

    def cargar_llaves(self, id_cripta, version_cripta):
        """La ubicación guardada, o None si no existe, si se guardó con otra
        versión de cripta o si el archivo está dañado. Con otra versión es
        "no encontrada", igual que una ficha de otro catálogo (§4.4): así lo
        persistido por la primera parte se invalida solo (FR-028)."""
        return None

    @abstractmethod
    def tiene_ficha(self, id_ficha, version_catalogo):
        """True si hay una ficha persistida con ese id Y bajo esa versión.
        Para consultar sin pagar el costo de reconstruir el objeto completo."""