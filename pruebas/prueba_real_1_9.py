"""Escenario contra el servicio REAL (necesita internet).

Uso (desde la carpeta que contiene 'cripta' y 'pruebas'):
    python -m pruebas.real_1_9

Gasta unas 8 solicitudes del API. Sirve para comprobar que los DTO coinciden
con las respuestas reales y para medir cuánto tarda la precarga. No forma
parte de ejecutar_pruebas.py porque depende de internet.
"""
import sys
import time

from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.errores import ErrorCripta

BASE_URL_REAL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
LOTES_DE_CONTENIDO = 2          # 2 lotes de 10 salas = 20 salas
SOLICITUDES_NECESARIAS = 8      # menú (2) + esqueleto (1) + contenido (2) + catálogo (1) + versiones (2)


def agregar_si_falta(lista, dato, limite):
    if len(lista) < limite and not lista.contiene(dato):
        lista.agregar_al_final(dato)


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL_REAL
    contador = ContadorSolicitudes()
    cliente = ClienteHttp(base_url, contador)
    asinc = FuenteAsincrona(cliente)
    try:
        inicio = time.perf_counter()
        primera = cliente.listar_criptas().obtener(0)
        datos = cliente.datos_generales(primera.id)
        print(f"Cripta: {primera.id} ({primera.nombre}), {primera.salas} salas")
        print(f"Presupuesto de solicitudes: {datos.presupuesto_solicitudes}")
        if datos.presupuesto_solicitudes < SOLICITUDES_NECESARIAS:
            print("El presupuesto es menor a lo que necesita esta prueba: me detengo.")
            return

        # Esqueleto: página 1
        esqueleto = asinc.enviar_esqueleto(primera.id, 1)
        esqueleto.esperar()
        asinc.recoger_listas()
        ids_salas = ListaEnlazada()
        for sala in esqueleto.resultado().salas:
            if len(ids_salas) < 10 * LOTES_DE_CONTENIDO:
                ids_salas.agregar_al_final(sala.id)
        print(f"Esqueleto: {len(ids_salas)} salas para precargar")

        # Contenido: se envían todos los lotes seguidos, sin esperar entre ellos
        lote = ListaEnlazada()
        ultimo = None
        inicio_envio = time.perf_counter()
        for id_sala in ids_salas:
            lote.agregar_al_final(id_sala)
            if len(lote) == 10:
                ultimo = asinc.enviar_contenido(primera.id, lote)
                lote = ListaEnlazada()
        if not lote.esta_vacia():
            ultimo = asinc.enviar_contenido(primera.id, lote)
        tiempo_envio = time.perf_counter() - inicio_envio
        ultimo.esperar()
        tiempo_total = time.perf_counter() - inicio_envio

        ids_catalogo = ListaEnlazada()
        salas_recibidas = 0
        for solicitud in asinc.recoger_listas():
            for contenido in solicitud.resultado():
                salas_recibidas += 1
                assert solicitud.pedido.contiene(contenido.sala)
                for enemigo in contenido.enemigos:
                    agregar_si_falta(ids_catalogo, enemigo.tipo, 10)
                for objeto in contenido.objetos:
                    agregar_si_falta(ids_catalogo, objeto, 10)
                for trampa in contenido.trampas:
                    agregar_si_falta(ids_catalogo, trampa.tipo, 10)
        print(f"Contenido: {salas_recibidas} salas recibidas")
        print(f"  Enviar los lotes tardó {tiempo_envio * 1000:.1f} ms (el juego no espera)")
        print(f"  Recibir todo tardó {tiempo_total * 1000:.0f} ms")

        # Catálogo
        if not ids_catalogo.esta_vacia():
            fichas = asinc.enviar_catalogo(ids_catalogo)
            fichas.esperar()
            asinc.recoger_listas()
            for ficha in fichas.resultado():
                print(f"  ficha: {ficha.id} | {ficha.clase} | {ficha.nombre}")

        print(f"Versión de la cripta: {cliente.version_cripta(primera.id)}")
        print(f"Versión del catálogo: {cliente.version_catalogo()}")
        print(f"Solicitudes realizadas: {cliente.solicitudes_realizadas()} "
              f"de {cliente.presupuesto()} "
              f"(quedan {contador.restantes()})")
        print(f"Tiempo total de la prueba: {time.perf_counter() - inicio:.1f} s")
    except ErrorCripta as error:
        print("La prueba se detuvo por un error del proyecto:")
        print(" ", error)
    finally:
        asinc.cerrar()
        cliente.cerrar()


main()