from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def agregar_si_falta(lista, dato, limite):
    """Agrega 'dato' a la lista si no está y aún no se llegó al límite."""
    if len(lista) < limite and not lista.contiene(dato):
        lista.agregar_al_final(dato)


contador = ContadorSolicitudes()
cliente = ClienteHttp(BASE_URL, contador)

criptas = cliente.listar_criptas()
primera = criptas.obtener(0)
print("Cripta:", primera.id, "-", primera.nombre, "-", primera.salas, "salas")

datos = cliente.datos_generales(primera.id)
print("Presupuesto de la cripta:", cliente.presupuesto())

pagina = cliente.esqueleto(primera.id, 1)
ids_salas = ListaEnlazada()
for sala in pagina.salas:
    agregar_si_falta(ids_salas, sala.id, 10)
print("Salas en la página 1:", len(pagina.salas), "| pedimos contenido de", len(ids_salas))

contenidos = cliente.contenido(primera.id, ids_salas)
ids_catalogo = ListaEnlazada()
for contenido in contenidos:
    for enemigo in contenido.enemigos:
        agregar_si_falta(ids_catalogo, enemigo.tipo, 10)
    for objeto in contenido.objetos:
        agregar_si_falta(ids_catalogo, objeto, 10)
    for trampa in contenido.trampas:
        agregar_si_falta(ids_catalogo, trampa.tipo, 10)

if not ids_catalogo.esta_vacia():
    for ficha in cliente.catalogo(ids_catalogo):
        print("  ficha:", ficha.id, "|", ficha.clase, "|", ficha.nombre)

print("Versión de la cripta:", cliente.version_cripta(primera.id))
print("Versión del catálogo:", cliente.version_catalogo())

print("Solicitudes realizadas:", cliente.solicitudes_realizadas(),
      "de", cliente.presupuesto())
cliente.cerrar()