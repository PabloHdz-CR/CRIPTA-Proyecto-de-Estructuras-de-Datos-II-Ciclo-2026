"""Integración del Paso 1: ClienteHttp + ContadorSolicitudes + convertidor +
FuenteAsincrona, contra un servidor local que imita el API real.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    python -m pruebas.prueba_1_9_integracion
"""
from cripta.adaptadores.clienteHttp import ClienteHttp
from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.errores import ErrorDeRed, PresupuestoAgotado
from pruebas.prueba_falso_1_6 import ServidorFalso


def uno(dato):
    lista = ListaEnlazada()
    lista.agregar_al_final(dato)
    return lista


def agregar_si_falta(lista, dato):
    if not lista.contiene(dato):
        lista.agregar_al_final(dato)


def armar_lotes(ids_salas, tamano):
    """Parte una ListaEnlazada de ids en lotes de 'tamano' (el último puede ser menor)."""
    lotes = ListaEnlazada()
    lote = ListaEnlazada()
    for id_sala in ids_salas:
        lote.agregar_al_final(id_sala)
        if len(lote) == tamano:
            lotes.agregar_al_final(lote)
            lote = ListaEnlazada()
    if not lote.esta_vacia():
        lotes.agregar_al_final(lote)
    return lotes


def escenario_partida(latencia):
    """Una partida completa de datos: menú, esqueleto, precarga, catálogo en
    cadena, un 429 recuperable y el presupuesto agotado.

    Devuelve un resumen observable para compararlo entre ejecuciones.
    """
    servidor = ServidorFalso(latencia=latencia)          # 25 salas, presupuesto 12
    contador = ContadorSolicitudes()
    cliente = ClienteHttp(servidor.base_url, contador, margen_espera=0)
    asinc = FuenteAsincrona(cliente)
    orden_recogido = []
    try:
        # 1. Menú (síncrono): lista de criptas y datos generales -> 2 solicitudes
        criptas = cliente.listar_criptas()
        id_cripta = criptas.obtener(0).id
        datos = cliente.datos_generales(id_cripta)
        assert cliente.presupuesto() == 12
        assert datos.paginas == 3
        assert cliente.solicitudes_realizadas() == 2 == servidor.total_recibidas()

        # 2. Esqueleto por páginas (asíncrono) -> 3 solicitudes
        ultimo = None
        for pagina in range(1, datos.paginas + 1):
            ultimo = asinc.enviar_esqueleto(id_cripta, pagina)
        if latencia > 0:
            # El envío no bloqueó: el trabajo de las 3 páginas sigue en curso
            assert not ultimo.lista()
        ultimo.esperar()
        ids_salas = ListaEnlazada()
        for solicitud in asinc.recoger_listas():
            orden_recogido.append(solicitud.numero)
            for sala in solicitud.resultado().salas:
                ids_salas.agregar_al_final(sala.id)
        assert len(ids_salas) == 25
        assert ids_salas.obtener(0) == 1 and ids_salas.obtener(24) == 25
        assert orden_recogido == [1, 2, 3]

        # 3. Contenido en lotes de 10 (asíncrono) -> 3 solicitudes
        ultimo = None
        for lote in armar_lotes(ids_salas, 10):
            ultimo = asinc.enviar_contenido(id_cripta, lote)
        ultimo.esperar()
        vistas = ListaEnlazada()
        ids_catalogo = ListaEnlazada()
        primer_lote = True
        for solicitud in asinc.recoger_listas():
            orden_recogido.append(solicitud.numero)
            resultado = solicitud.resultado()
            if primer_lote:
                # El servidor responde en orden inverso: se empareja por 'sala'
                assert resultado.obtener(0).sala == 10
                primer_lote = False
            for contenido in resultado:
                assert solicitud.pedido.contiene(contenido.sala)   # respondió lo pedido
                assert not vistas.contiene(contenido.sala)         # sin repetidas
                vistas.agregar_al_final(contenido.sala)
                for enemigo in contenido.enemigos:
                    agregar_si_falta(ids_catalogo, enemigo.tipo)
                for objeto in contenido.objetos:
                    agregar_si_falta(ids_catalogo, objeto)
                for trampa in contenido.trampas:
                    agregar_si_falta(ids_catalogo, trampa.tipo)
        assert len(vistas) == 25
        assert len(ids_catalogo) == 3

        # 4. Catálogo en cadena -> 2 solicitudes: la rata "suelta" una poción que
        #    solo se descubre al leer la ficha de la rata
        solicitud = asinc.enviar_catalogo(ids_catalogo)
        solicitud.esperar()
        nuevos = ListaEnlazada()
        for hecha in asinc.recoger_listas():
            orden_recogido.append(hecha.numero)
        for ficha in solicitud.resultado():
            if ficha.clase == "enemigo":
                for suelto in ficha.suelta:
                    if not ids_catalogo.contiene(suelto):
                        agregar_si_falta(nuevos, suelto)
        assert len(nuevos) == 1 and nuevos.obtener(0) == "itm_pocion"
        segunda = asinc.enviar_catalogo(nuevos)
        segunda.esperar()
        for hecha in asinc.recoger_listas():
            orden_recogido.append(hecha.numero)
        pocion = segunda.resultado().obtener(0)
        assert pocion.clase == "pocion" and pocion.cura == 8
        assert cliente.solicitudes_realizadas() == 10 == servidor.total_recibidas()
        assert contador.restantes() == 2

        # 5. Un 429 recuperable: gasta 2 solicitudes (el 429 y el reintento)
        servidor.inyectar_429(1)
        con_429 = asinc.enviar_catalogo(uno("itm_daga"))
        con_429.esperar()
        for hecha in asinc.recoger_listas():
            orden_recogido.append(hecha.numero)
        assert con_429.resultado().obtener(0).id == "itm_daga"
        assert cliente.solicitudes_realizadas() == 12 == servidor.total_recibidas()
        assert contador.restantes() == 0

        # 6. Presupuesto agotado: la solicitud NO llega al servidor
        de_mas = asinc.enviar_catalogo(uno("ent_rata"))
        de_mas.esperar()
        for hecha in asinc.recoger_listas():
            orden_recogido.append(hecha.numero)
        assert isinstance(de_mas.fallo(), PresupuestoAgotado)
        assert servidor.total_recibidas() == 12
        assert cliente.solicitudes_realizadas() == 12

        # 7. El mismo identificador de cliente en TODAS las solicitudes
        vistos = servidor.ids_de_cliente_vistos()
        assert len(vistos) == 1 and vistos[0] == cliente.id_cliente()

        # 8. Nueva partida: el conteo vuelve a 0 y el presupuesto se olvida
        rutas = servidor.rutas_recibidas()
        cliente.reiniciar_conteo()
        assert cliente.solicitudes_realizadas() == 0 and cliente.presupuesto() is None
        assert cliente.version_catalogo() == "cat-test-1"
        assert cliente.solicitudes_realizadas() == 1

        return rutas, orden_recogido, 12
    finally:
        asinc.cerrar()
        cliente.cerrar()
        servidor.cerrar()


def escenario_429_persistente():
    """Un servicio que limita sin parar: 1 intento + 3 reintentos, luego error."""
    servidor = ServidorFalso(presupuesto=6)
    contador = ContadorSolicitudes()
    cliente = ClienteHttp(servidor.base_url, contador, margen_espera=0)
    asinc = FuenteAsincrona(cliente)
    try:
        id_cripta = cliente.listar_criptas().obtener(0).id
        cliente.datos_generales(id_cripta)
        assert cliente.solicitudes_realizadas() == 2
        servidor.inyectar_429(100)
        solicitud = asinc.enviar_catalogo(uno("ent_rata"))
        solicitud.esperar()
        error = solicitud.fallo()
        print("Error esperado:", error)
        assert isinstance(error, ErrorDeRed) and error.codigo_http == 429
        # 2 del menú + 4 intentos (1 + 3 reintentos): el conteo coincide con el servidor
        assert cliente.solicitudes_realizadas() == 6 == servidor.total_recibidas()
        assert contador.restantes() == 0
    finally:
        asinc.cerrar()
        cliente.cerrar()
        servidor.cerrar()


# --- Ejecución --------------------------------------------------------------

lenta = escenario_partida(latencia=0.05)
rapida = escenario_partida(latencia=0.0)

# La latencia real NO debe cambiar lo que se pide, en qué orden ni lo que se gasta
assert lenta[0] == rapida[0], "las rutas pedidas cambiaron con la latencia"
assert lenta[1] == rapida[1], "el orden de recolección cambió con la latencia"
assert lenta[2] == rapida[2]
assert len(lenta[0]) == 12

escenario_429_persistente()

print("Sección 1.9 OK: 12 solicitudes idénticas con latencia de 50 ms y de 0 ms")