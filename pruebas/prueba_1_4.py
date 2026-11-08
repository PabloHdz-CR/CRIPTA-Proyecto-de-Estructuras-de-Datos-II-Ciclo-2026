from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.errores import LoteInvalido
from cripta.modelo.puertos.fuenteDatos import FuenteDatos, validar_lote, LIMITE_LOTE

# 1. La interfaz no se puede instanciar
try:
    FuenteDatos()
    assert False, "debió lanzar TypeError"
except TypeError:
    pass


# 2. Una clase incompleta tampoco
class Incompleta(FuenteDatos):
    def listar_criptas(self):
        return None


try:
    Incompleta()
    assert False, "debió lanzar TypeError"
except TypeError as error:
    print("Error esperado:", error)


# 3. Una clase que implementa todo sí se puede crear
class Falsa(FuenteDatos):
    def listar_criptas(self):
        return ListaEnlazada()

    def datos_generales(self, id_cripta):
        return None

    def esqueleto(self, id_cripta, pagina):
        return None

    def contenido(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        return ListaEnlazada()

    def catalogo(self, ids):
        validar_lote("catalogo", ids)
        return ListaEnlazada()

    def llaves(self, id_cripta):
        # 003-resolubilidad (FR-025): esta fuente no usa la ubicación de llaves.
        return ListaEnlazada()

    def version_cripta(self, id_cripta):
        return "v1"

    def version_catalogo(self):
        return "cat-1"

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass

fuente = Falsa()
assert isinstance(fuente, FuenteDatos)
assert fuente.solicitudes_realizadas() == 0
assert fuente.presupuesto() is None


# 4. Validación de lotes
def lote_de(cantidad):
    lote = ListaEnlazada()
    for numero in range(cantidad):
        lote.agregar_al_final(numero)
    return lote


fuente.contenido("cripta-01", lote_de(1))            # mínimo válido
fuente.contenido("cripta-01", lote_de(LIMITE_LOTE))  # máximo válido

for tamano in (0, LIMITE_LOTE + 1):
    try:
        fuente.catalogo(lote_de(tamano))
        assert False, "debió lanzar LoteInvalido"
    except LoteInvalido as error:
        print("Error esperado:", error)
        assert error.cantidad == tamano

print("Sección 1.4 OK")