import shutil
import tempfile
import threading

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.modelo.datos.cacheFichas import CacheFichas
from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.datos.servicioDatos import ServicioDatos
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.dto import (DatosCriptaDTO, EnemigoInstanciaDTO,
                                       ContenidoSalaDTO, FichaArmaDTO,
                                       FichaEnemigoDTO, FichaPocionDTO,
                                       JugadorDTO, PaginaSalasDTO,
                                       ResumenCriptaDTO, SalaDTO, SalidaDTO)
from cripta.modelo.puertos.errores import ErrorCripta, ErrorDeRed
from cripta.modelo.puertos.fuenteDatos import FuenteDatos, validar_lote


def le(*elementos):
    l = ListaEnlazada()
    l.agregar_todos(elementos)
    return l


def ids_de(lista_enlazada):
    r = []
    for d in lista_enlazada:
        r.append(d)
    return r


def salidas(*pares):
    lista = ListaEnlazada()
    for par in pares:
        lista.agregar_al_final(SalidaDTO(direccion=par[0], sala=par[1]))
    return lista


# --- Cripta de prueba: 5 salas en pasillo 1-2-3-4-5 ---
SALAS = (
    SalaDTO(id=1, nombre="S1", salidas=salidas(("N", 2))),
    SalaDTO(id=2, nombre="S2", salidas=salidas(("S", 1), ("N", 3))),
    SalaDTO(id=3, nombre="S3", salidas=salidas(("S", 2), ("N", 4))),
    SalaDTO(id=4, nombre="S4", salidas=salidas(("S", 3), ("N", 5))),
    SalaDTO(id=5, nombre="S5", salidas=salidas(("S", 4))),
)

CONTENIDO = {
    1: ContenidoSalaDTO(sala=1, enemigos=le(), objetos=le("itm_daga"), trampas=le()),
    2: ContenidoSalaDTO(sala=2, enemigos=le(EnemigoInstanciaDTO("e1", "ent_rata", 12)),
                        objetos=le(), trampas=le()),
    3: ContenidoSalaDTO(sala=3, enemigos=le(), objetos=le(), trampas=le()),
    4: ContenidoSalaDTO(sala=4, enemigos=le(), objetos=le(), trampas=le()),
    5: ContenidoSalaDTO(sala=5, enemigos=le(), objetos=le(), trampas=le()),
}

FICHAS = {
    "ent_rata": FichaEnemigoDTO(id="ent_rata", nombre="Rata", vida_max=12, ataque=5,
                                defensa=1, velocidad=150, comportamiento="rastreador",
                                suelta=le("itm_pocion")),
    "itm_daga": FichaArmaDTO(id="itm_daga", nombre="Daga", peso=2, valor=15, ataque_bonus=3),
    "itm_pocion": FichaPocionDTO(id="itm_pocion", nombre="Poción", peso=1, valor=10, cura=8),
}
# 12 ids extra, solo para probar que el catálogo se parte en lotes de 10
for n in range(1, 13):
    FICHAS[f"itm_extra{n}"] = FichaArmaDTO(id=f"itm_extra{n}", nombre=f"Extra {n}",
                                           peso=1, valor=1, ataque_bonus=0)

DATOS_CRIPTA = DatosCriptaDTO(
    id="c1", version="v1", salas_total=5, paginas=2, salas_por_pagina=3,
    sala_inicial=1, sala_salida=5, llave_salida="itm_llave",
    presupuesto_solicitudes=1000, inventario_max=10,
    jugador=JugadorDTO(vida_max=30, ataque=6, defensa=2, velocidad=100))


class FuenteFalsa(FuenteDatos):
    """FuenteDatos de mentira con la cripta de prueba. Cuenta solicitudes como
    lo haría ContadorSolicitudes, y puede bloquearse con un Event para probar
    que asegurar_contenido/precargar no se adelantan a la red."""

    def __init__(self):
        self._solicitudes = 0
        self._cerrojo = threading.Lock()
        self.bloqueo_contenido = None    # Event opcional: si existe, contenido() espera
        self.ids_catalogo_vistos = []    # para comprobar tamaño de lotes

    def _contar(self):
        with self._cerrojo:
            self._solicitudes += 1

    def listar_criptas(self):
        self._contar()
        return le(ResumenCriptaDTO(id="c1", nombre="Cripta", salas=5, dificultad=1))

    def datos_generales(self, id_cripta):
        self._contar()
        return DATOS_CRIPTA

    def esqueleto(self, id_cripta, pagina):
        self._contar()
        if pagina == 1:
            return PaginaSalasDTO(pagina=1, total_paginas=2, salas=le(SALAS[0], SALAS[1], SALAS[2]))
        return PaginaSalasDTO(pagina=2, total_paginas=2, salas=le(SALAS[3], SALAS[4]))

    def contenido(self, id_cripta, ids_salas):
        self._contar()
        validar_lote("contenido", ids_salas)
        if self.bloqueo_contenido is not None:
            self.bloqueo_contenido.wait(5)
        resultado = ListaEnlazada()
        for id_sala in ids_salas:
            resultado.agregar_al_final(CONTENIDO[id_sala])
        return resultado

    def catalogo(self, ids):
        self._contar()
        validar_lote("catalogo", ids)
        vistos = []
        for id_ficha in ids:
            vistos.append(id_ficha)
        self.ids_catalogo_vistos.append(vistos)
        resultado = ListaEnlazada()
        for id_ficha in ids:
            if id_ficha not in FICHAS:
                raise ErrorDeRed("catalogo", f"ficha {id_ficha} no existe")
            resultado.agregar_al_final(FICHAS[id_ficha])
        return resultado

    def llaves(self, id_cripta):
        # 003-resolubilidad (FR-025): esta fuente no usa la ubicación de llaves.
        return ListaEnlazada()

    def version_cripta(self, id_cripta):
        self._contar()
        return "v1"

    def version_catalogo(self):
        self._contar()
        return "cat-1"

    def solicitudes_realizadas(self):
        with self._cerrojo:
            return self._solicitudes

    def presupuesto(self):
        return DATOS_CRIPTA.presupuesto_solicitudes

    def reiniciar_conteo(self):
        with self._cerrojo:
            self._solicitudes = 0


def nuevo_servicio(fuente=None, carpeta=None, capacidad_cache=25):
    fuente = fuente if fuente is not None else FuenteFalsa()
    asincrona = FuenteAsincrona(fuente)
    cache = CacheFichas(capacidad_cache)
    almacen = AlmacenLocalDisco(carpeta) if carpeta is not None else None
    servicio = ServicioDatos(fuente, asincrona, cache, almacen)
    return servicio, fuente, asincrona


# ===================================================================
carpeta = tempfile.mkdtemp(prefix="cripta_5_5_")
try:
    # 1. iniciar_cripta: datos generales + todas las páginas del esqueleto
    servicio, fuente, asincrona = nuevo_servicio(carpeta=carpeta)
    try:
        datos = servicio.iniciar_cripta("c1")
        assert datos.salas_total == 5 and datos.paginas == 2
        assert len(servicio.esqueleto()) == 5
        assert servicio.esqueleto().buscar(3).sala.nombre == "S3"
        # datos generales (1) + version catálogo (1) + 2 páginas de esqueleto = 4
        assert fuente.solicitudes_realizadas() == 4

        # 2. Antes de precargar, nada está listo
        assert not servicio.contenido_listo(1)

        # 3. precargar() NO bloquea (se nota porque devuelve antes de que la red "responda")
        fuente.bloqueo_contenido = threading.Event()
        servicio.precargar(1)                      # desde la sala 1: pide la 2 (único vecino)
        assert not servicio.contenido_listo(2)      # la red sigue bloqueada: aún no llegó
        fuente.bloqueo_contenido.set()               # ahora sí "responde"

        # 4. asegurar_contenido bloquea hasta tenerlo, y no vuelve a pedir si ya está
        contenido_2 = servicio.asegurar_contenido(2)
        assert contenido_2.enemigos.obtener(0).tipo == "ent_rata"
        solicitudes_antes = fuente.solicitudes_realizadas()
        assert servicio.contenido_listo(2)
        otra_vez = servicio.asegurar_contenido(2)
        assert otra_vez is contenido_2               # mismo objeto: no se repitió la solicitud
        assert fuente.solicitudes_realizadas() == solicitudes_antes

        # 5. asegurar_contenido de una sala NO precargada también funciona (pide y espera)
        contenido_5 = servicio.asegurar_contenido(5)
        assert contenido_5.sala == 5

        # 6. Una sala que no existe en el esqueleto
        try:
            servicio.asegurar_contenido(999)
            assert False, "debió lanzar ErrorCripta"
        except ErrorCripta as error:
            print("Error esperado:", error)
    finally:
        asincrona.cerrar()

    # 7. resolver_fichas: orden de salida = orden de entrada, y resuelve en cascada
    servicio, fuente, asincrona = nuevo_servicio(carpeta=carpeta, capacidad_cache=25)
    try:
        fichas = servicio.resolver_fichas(le("itm_daga", "ent_rata"))
        assert ids_de(fichas)[0].id == "itm_daga" and ids_de(fichas)[1].id == "ent_rata"
        assert servicio.fallos_cache() == 2 and servicio.aciertos_cache() == 0

        # Volver a pedir las mismas: ahora son aciertos, no se vuelve a tocar la red
        solicitudes_antes = fuente.solicitudes_realizadas()
        servicio.resolver_fichas(le("itm_daga", "ent_rata"))
        assert fuente.solicitudes_realizadas() == solicitudes_antes
        assert servicio.aciertos_cache() == 2

        # Resolución en cadena: la rata "suelta" una poción no pedida explícitamente
        cadena = servicio.resolver_ficha_y_dependientes("ent_rata")
        ids_cadena = []
        for ficha in cadena:
            ids_cadena.append(ficha.id)
        assert ids_cadena == ["ent_rata", "itm_pocion"]

        # 8. Catálogo en lotes de hasta 10: 12 ids nuevos -> 2 solicitudes, ninguna > 10
        fuente.ids_catalogo_vistos = []
        ids_extra = ListaEnlazada()
        for n in range(1, 13):
            ids_extra.agregar_al_final(f"itm_extra{n}")
        resultado = servicio.resolver_fichas(ids_extra)
        assert len(resultado) == 12
        assert len(fuente.ids_catalogo_vistos) == 2
        for lote in fuente.ids_catalogo_vistos:
            assert len(lote) <= 10
        assert sum(len(lote) for lote in fuente.ids_catalogo_vistos) == 12
    finally:
        asincrona.cerrar()

    # 9. Persistencia: lo que se pide por red queda en disco, y una sesión nueva lo usa sin red
    fuente_a, fuente_b = FuenteFalsa(), FuenteFalsa()
    servicio_a, _, asincrona_a = nuevo_servicio(fuente=fuente_a, carpeta=carpeta, capacidad_cache=25)
    try:
        servicio_a.iniciar_cripta("c1")               # fija version_catalogo = "cat-1"
        servicio_a.resolver_fichas(le("itm_daga"))
    finally:
        asincrona_a.cerrar()

    servicio_b, _, asincrona_b = nuevo_servicio(fuente=fuente_b, carpeta=carpeta, capacidad_cache=25)
    try:
        servicio_b.iniciar_cripta("c1")                # misma version_catalogo: "cat-1"
        solicitudes_antes = fuente_b.solicitudes_realizadas()
        ficha = servicio_b.resolver_fichas(le("itm_daga")).obtener(0)
        assert ficha.ataque_bonus == 3
        assert fuente_b.solicitudes_realizadas() == solicitudes_antes    # vino de disco, no de red
    finally:
        asincrona_b.cerrar()

    # 10. Error de red al resolver una ficha que no existe en el catálogo
    servicio, fuente, asincrona = nuevo_servicio(carpeta=carpeta)
    try:
        try:
            servicio.resolver_fichas(le("itm_no_existe"))
            assert False, "debió lanzar ErrorDeRed"
        except ErrorDeRed as error:
            print("Error esperado:", error)
    finally:
        asincrona.cerrar()

    # 11. reiniciar_sesion: el conteo vuelve a 0, pero la caché sigue sirviendo
    servicio, fuente, asincrona = nuevo_servicio(carpeta=carpeta)
    try:
        servicio.iniciar_cripta("c1")
        servicio.resolver_fichas(le("itm_daga"))
        servicio.reiniciar_sesion()
        assert fuente.solicitudes_realizadas() == 0
        assert servicio.datos_cripta() is None and len(servicio.esqueleto()) == 0
        solicitudes_antes = fuente.solicitudes_realizadas()
        ficha = servicio.resolver_fichas(le("itm_daga")).obtener(0)      # sigue en caché
        assert ficha.ataque_bonus == 3
        assert fuente.solicitudes_realizadas() == solicitudes_antes
    finally:
        asincrona.cerrar()

    print("Sección 5.5 OK")
finally:
    shutil.rmtree(carpeta, ignore_errors=True)