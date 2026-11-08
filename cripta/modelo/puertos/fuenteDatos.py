from abc import ABC, abstractmethod

from .errores import LoteInvalido

# Máximo de elementos por consulta de contenido o de catálogo (§3.4).
# Es una regla del servicio, no de cada cripta.
LIMITE_LOTE = 10


def validar_lote(operacion, elementos):
    """Comprueba que el lote tenga entre 1 y LIMITE_LOTE elementos.

    Los adaptadores lo llaman ANTES de enviar la solicitud. Sirve para
    cualquier objeto con len(), como una ListaEnlazada.
    Lanza LoteInvalido si la cantidad está fuera de rango.
    """
    cantidad = len(elementos)
    if cantidad < 1 or cantidad > LIMITE_LOTE:
        raise LoteInvalido(operacion, cantidad, LIMITE_LOTE)


class FuenteDatos(ABC):
    """Puerto de acceso a los datos de las criptas y del catálogo.

    Es el único contrato que el modelo conoce para obtener datos. Lo
    implementan ClienteHttp (red) y FuenteOffline (archivos en disco), y el
    modelo no debe notar la diferencia (§3.4).

    Reglas comunes a todos los métodos de consulta:
      - Devuelven DTO (ver dto.py), nunca diccionarios de JSON.
      - Las colecciones de entrada y salida son ListaEnlazada.
      - Pueden lanzar ErrorDeRed o PresupuestoAgotado.
      - Son síncronos: bloquean hasta tener la respuesta.
    """

    @abstractmethod
    def listar_criptas(self):
        """Devuelve una ListaEnlazada de ResumenCriptaDTO."""

    @abstractmethod
    def datos_generales(self, id_cripta):
        """Devuelve el DatosCriptaDTO de la cripta indicada."""

    @abstractmethod
    def esqueleto(self, id_cripta, pagina):
        """Devuelve la PaginaSalasDTO número 'pagina' (se cuenta desde 1)."""

    @abstractmethod
    def contenido(self, id_cripta, ids_salas):
        """Devuelve una ListaEnlazada de ContenidoSalaDTO.

        ids_salas: ListaEnlazada de enteros, con 1 a LIMITE_LOTE elementos.
        Lanza LoteInvalido si el tamaño está fuera de rango.
        El orden de la respuesta puede no coincidir con el de ids_salas:
        quien llama debe emparejar por el campo 'sala'.
        """

    @abstractmethod
    def catalogo(self, ids):
        """Devuelve una ListaEnlazada de fichas (subclases de FichaDTO).

        ids: ListaEnlazada de textos, con 1 a LIMITE_LOTE elementos.
        Lanza LoteInvalido si el tamaño está fuera de rango.
        El orden de la respuesta puede no coincidir con el de ids:
        quien llama debe emparejar por el campo 'id'.
        """

    @abstractmethod
    def llaves(self, id_cripta):
        """Devuelve una ListaEnlazada de UbicacionLlaveDTO: GET
        /criptas/{id}/llaves (003-resolubilidad, FR-025). Cuenta como una
        solicitud más dentro del presupuesto (FR-026). Lanza DatosInvalidos si
        la respuesta está mal formada (FR-030); ErrorDeRed si no se pudo
        obtener (sin conexión: si falta el archivo, FR-029)."""

    @abstractmethod
    def version_cripta(self, id_cripta):
        """Devuelve la versión actual de la cripta (texto)."""

    @abstractmethod
    def version_catalogo(self):
        """Devuelve la versión global del catálogo (texto)."""

    @abstractmethod
    def solicitudes_realizadas(self):
        """Devuelve cuántas solicitudes de red se han hecho en esta ejecución.

        Cuenta los reintentos. Una fuente que no usa la red (offline) devuelve 0.
        """

    @abstractmethod
    def presupuesto(self):
        """Devuelve el presupuesto_solicitudes de la cripta actual.

        Devuelve None mientras no se conozca (antes de pedir los datos
        generales) o si la fuente no usa la red.
        """

    @abstractmethod
    def reiniciar_conteo(self):
        """Empieza una partida nueva: el conteo de solicitudes vuelve a 0 y
        se olvida el presupuesto. Una fuente que no usa la red no hace nada."""