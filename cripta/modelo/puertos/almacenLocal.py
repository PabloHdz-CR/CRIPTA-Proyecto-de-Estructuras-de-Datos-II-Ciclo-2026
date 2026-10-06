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

    @abstractmethod
    def tiene_ficha(self, id_ficha, version_catalogo):
        """True si hay una ficha persistida con ese id Y bajo esa versión.
        Para consultar sin pagar el costo de reconstruir el objeto completo."""