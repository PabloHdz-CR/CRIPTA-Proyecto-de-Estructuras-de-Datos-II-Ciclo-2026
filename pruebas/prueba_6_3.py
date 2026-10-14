"""Prueba de PartidaBinaria (§6.3, guardado binario) contra las clases REALES
del modelo: Jugador, Mundo, Sala, Enemigo, Objeto, Trampa, Agenda, Evento y
Efecto. Arma una partida a mano (sin red, como hace esta suite con las demás
secciones), la guarda, la carga de vuelta y compara que el estado completo
sobreviva el viaje -- incluido el estado del random (determinismo, §2.12).
También prueba cargar_sala() (carga parcial, §4.10) y la detección de una
versión de formato incompatible.
"""
import os
import random
import shutil

from cripta.adaptadores.partidaBinaria import PartidaBinaria
from cripta.modelo.actores.comportamientos import crear_comportamiento
from cripta.modelo.actores.enemigo import Enemigo
from cripta.modelo.actores.jugador import Jugador
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.mundo.mundo import Mundo
from cripta.modelo.mundo.sala import Sala
from cripta.modelo.mundo.salida import Salida
from cripta.modelo.mundo.trampa import Trampa
from cripta.modelo.nucleo.mutador import Mutador
from cripta.modelo.nucleo.partida import Partida
from cripta.modelo.nucleo.fabricaEntidades import FabricaEntidades
from cripta.modelo.objetos.objeto import crear_objeto
from cripta.modelo.puertos.dto import (
    FichaArmaDTO, FichaArmaduraDTO, FichaEnemigoDTO, FichaLlaveDTO,
    FichaTrampaDTO, JugadorDTO)
from cripta.modelo.reloj.agenda import Agenda
from cripta.modelo.reloj.efecto import EfectoVelocidad, EfectoVeneno
from cripta.modelo.reloj.eventos import (
    EventoAccionActor, EventoCambioVelocidad, EventoCierrePuerta,
    EventoRearmeTrampa, EventoVeneno)

CARPETA = "paquete_prueba_6_3"
shutil.rmtree(CARPETA, ignore_errors=True)
os.makedirs(CARPETA, exist_ok=True)
RUTA = os.path.join(CARPETA, "partida.bin")

# ----------------------------------------------------------------------
# "Catálogo" de fichas y un servicio falso (sin red) que sabe resolverlas
# ----------------------------------------------------------------------

FICHA_RATA = FichaEnemigoDTO("rata", "Rata", 20, 5, 2, 90, "guardian", ListaEnlazada())
FICHA_ESPADA = FichaArmaDTO("espada", "Espada", 3, 10, 4)
FICHA_ESCUDO = FichaArmaduraDTO("escudo", "Escudo", 4, 8, 3)
FICHA_LLAVE = FichaLlaveDTO("llave-roja", "Llave roja", 1, 1, "puerta-roja")
FICHA_TRAMPA = FichaTrampaDTO("pincho", "Pincho", 5, None)
_SUELTA = ListaEnlazada()
_SUELTA.agregar_al_final("llave-roja")
FICHA_RATA_SUELTA = FichaEnemigoDTO("rata2", "Rata2", 15, 4, 1, 100, "errante", _SUELTA)

CATALOGO = [
    ("rata", FICHA_RATA), ("espada", FICHA_ESPADA), ("escudo", FICHA_ESCUDO),
    ("llave-roja", FICHA_LLAVE), ("pincho", FICHA_TRAMPA), ("rata2", FICHA_RATA_SUELTA),
]


class ServicioFalso:
    """Imita la única parte de ServicioDatos que PartidaBinaria usa al
    cargar: resolver_fichas(). No hay red ni disco de por medio."""

    def resolver_fichas(self, ids):
        resultado = ListaEnlazada()
        for id_pedido in ids:
            encontrada = None
            for id_guardado, ficha in CATALOGO:
                if id_guardado == id_pedido:
                    encontrada = ficha
                    break
            assert encontrada is not None, f"ficha no encontrada en la prueba: {id_pedido}"
            resultado.agregar_al_final(encontrada)
        return resultado


def construir_partida():
    """Arma una Partida completa a mano (sin Partida.iniciar(), que necesita
    red): llena cada rincón del estado que PartidaBinaria debe guardar --
    puerta con cierre automático pendiente, enemigo dormido y enemigo activo
    (con efecto de velocidad y su evento de fin), objeto en el suelo, trampa
    ya disparada con su rearme pendiente, inventario y equipo del jugador, y
    un efecto de veneno con su evento vivo."""
    servicio = ServicioFalso()
    partida = Partida.__new__(Partida)
    partida.servicio = servicio
    partida.mutador = Mutador()
    partida.datos = type("Datos", (), {"id": "cripta-01", "version": "v3"})()
    partida.version_catalogo = "cat-7"
    partida.semilla = 12345
    partida.azar = random.Random(12345)
    partida.azar.random()          # avanza el estado para que no sea el inicial
    partida.azar.random()
    partida.reloj = 450
    partida.fin = None
    partida.diario = None
    partida._mensajes = ListaEnlazada()

    partida.agenda = Agenda()
    partida.mutador.agenda = partida.agenda

    datos_mundo = type("D", (), {
        "sala_inicial": 1, "sala_salida": 2, "llave_salida": "puerta-roja",
        "inventario_max": 8, "jugador": JugadorDTO(30, 6, 3, 100)})()
    partida.mundo = Mundo(datos_mundo)

    salida_1a2 = Salida("N", 2, cerrada=True, llave="puerta-roja", cierre_automatico=200)
    salida_2a1 = Salida("S", 1)
    sala1 = Sala(1, "Entrada", (salida_1a2, None, None, None))
    sala2 = Sala(2, "Salida", (None, salida_2a1, None, None))
    sala1.rastro = 100
    sala1.contenido_cargado = True
    sala2.contenido_cargado = True
    partida.mundo._salas.agregar_al_final(sala1)
    partida.mundo._salas.agregar_al_final(sala2)

    evento_cierre = EventoCierrePuerta(600, salida_1a2)
    partida.agenda.programar(evento_cierre)
    salida_1a2.evento_cierre = evento_cierre

    dormido = Enemigo("e-1", FICHA_RATA, 20, 1, crear_comportamiento(FICHA_RATA.comportamiento))
    sala1.dormidos.agregar_al_final(dormido)

    activo = Enemigo("e-2", FICHA_RATA_SUELTA, 10, 2,
                      crear_comportamiento(FICHA_RATA_SUELTA.comportamiento))
    activo.activo = True
    activo.suelta.agregar_al_final(FICHA_LLAVE)
    efecto_vel = EfectoVelocidad(activo, 20, 150)
    activo.efectos.agregar_al_final(efecto_vel)
    evento_turno_enemigo = EventoAccionActor(partida.reloj + 50, activo)
    partida.agenda.programar(evento_turno_enemigo)
    activo.evento_accion = evento_turno_enemigo
    evento_fin_velocidad = EventoCambioVelocidad(partida.reloj + 30, activo, efecto_vel)
    partida.agenda.programar(evento_fin_velocidad)
    efecto_vel.evento = evento_fin_velocidad
    sala2.activos.agregar_al_final(activo)

    espada_suelo = crear_objeto(100, FICHA_ESPADA)
    sala1.suelo.agregar_al_final(espada_suelo)

    trampa = Trampa("t-1", FICHA_TRAMPA, 2)
    trampa.armada = False
    evento_rearme = EventoRearmeTrampa(partida.reloj + 300, trampa)
    partida.agenda.programar(evento_rearme)
    trampa.evento_rearme = evento_rearme
    sala2.trampas.agregar_al_final(trampa)

    jugador = Jugador(datos_mundo.jugador, 1, 8)
    jugador.vida = 18
    jugador.acciones = 7
    jugador.enemigos_derrotados = 1
    escudo = crear_objeto(1, FICHA_ESCUDO)
    espada = crear_objeto(2, FICHA_ESPADA)
    llave = crear_objeto(3, FICHA_LLAVE)
    jugador.inventario.recoger(escudo)
    jugador.inventario.recoger(espada)
    jugador.inventario.recoger(llave)
    jugador.equipo.equipar(espada)
    jugador.equipo.equipar(escudo)
    jugador.inventario.enfocar(llave)

    efecto_veneno = EfectoVeneno(jugador)
    jugador.efectos.agregar_al_final(efecto_veneno)
    evento_veneno = EventoVeneno(partida.reloj + 80, jugador, efecto_veneno, 3)
    partida.agenda.programar(evento_veneno)
    efecto_veneno.evento = evento_veneno

    evento_turno_jugador = EventoAccionActor(partida.reloj + 10, jugador)
    partida.agenda.programar(evento_turno_jugador)
    jugador.evento_accion = evento_turno_jugador

    partida.jugador = jugador
    partida._fabrica = FabricaEntidades(servicio)
    partida._fabrica._siguiente_id_objeto = 101   # el siguiente libre tras 'espada_suelo'=100

    return partida, servicio


def _resumen_agenda(agenda):
    """Vuelca todos los eventos de una agenda a una lista de tuplas
    comparables, dejando la agenda intacta (los reinserta)."""
    extraidos = []
    while True:
        evento = agenda.extraer_siguiente()
        if evento is None:
            break
        extraidos.append(evento)
    resumen = []
    for evento in extraidos:
        resumen.append((type(evento).__name__, evento.tiempo, evento.secuencia))
        agenda.reinsertar(evento)
    return resumen


def verificar(po, pc):
    """po = partida original, pc = partida recién cargada del archivo."""
    assert pc.semilla == po.semilla
    assert pc.reloj == po.reloj
    assert pc.fin == po.fin
    assert pc.datos.id == po.datos.id and pc.datos.version == po.datos.version
    assert pc.version_catalogo == po.version_catalogo
    assert pc.azar.getstate() == po.azar.getstate(), "el estado del random no sobrevivió"
    assert pc._fabrica._siguiente_id_objeto == po._fabrica._siguiente_id_objeto

    assert len(pc.mundo) == len(po.mundo)
    s1 = pc.mundo.sala(1)
    s2 = pc.mundo.sala(2)
    assert s1.nombre == "Entrada" and s2.nombre == "Salida"
    assert s1.rastro == 100
    assert s1.salidas[0].destino == 2 and s1.salidas[0].cerrada is True
    assert s1.salidas[0].llave == "puerta-roja"
    assert s1.salidas[0].cierre_automatico == 200
    assert s1.salidas[0].evento_cierre is not None
    assert s1.salidas[0].evento_cierre.tiempo == 600
    assert s2.salidas[1].destino == 1

    assert len(s1.dormidos) == 1
    dormido = s1.dormidos.ver_primero()
    assert dormido.id_instancia == "e-1" and dormido.ficha.id == "rata"
    assert dormido.vida == 20 and dormido.activo is False

    assert len(s2.activos) == 1
    activo = s2.activos.ver_primero()
    assert activo.id_instancia == "e-2" and activo.ficha.id == "rata2"
    assert activo.vida == 10 and activo.activo is True
    assert len(activo.suelta) == 1
    assert activo.suelta.ver_primero().id == "llave-roja"
    assert len(activo.efectos) == 1
    efecto_vel = activo.efectos.ver_primero()
    assert efecto_vel.TIPO == "velocidad" and efecto_vel.modificador == 20
    assert efecto_vel.evento is not None
    assert type(efecto_vel.evento).__name__ == "EventoCambioVelocidad"
    assert activo.evento_accion is not None and activo.evento_accion.tiempo == po.reloj + 50

    assert len(s1.suelo) == 1
    assert s1.suelo.ver_primero().id_instancia == 100
    assert s1.suelo.ver_primero().ficha.id == "espada"

    assert len(s2.trampas) == 1
    trampa = s2.trampas.ver_primero()
    assert trampa.id_instancia == "t-1" and trampa.armada is False
    assert trampa.evento_rearme is not None and trampa.evento_rearme.tiempo == po.reloj + 300

    jugador = pc.jugador
    assert jugador.vida == 18 and jugador.acciones == 7 and jugador.enemigos_derrotados == 1
    assert len(jugador.inventario) == 3
    assert jugador.equipo.arma is not None and jugador.equipo.arma.ficha.id == "espada"
    assert jugador.equipo.armadura is not None and jugador.equipo.armadura.ficha.id == "escudo"
    assert jugador.inventario.actual() is not None
    assert jugador.inventario.actual().ficha.id == "llave-roja"
    assert len(jugador.efectos) == 1
    efecto_ven = jugador.efectos.ver_primero()
    assert efecto_ven.TIPO == "veneno"
    assert efecto_ven.evento is not None and efecto_ven.evento.numero == 3
    assert jugador.evento_accion is not None and jugador.evento_accion.tiempo == po.reloj + 10

    resumen_original = _resumen_agenda(po.agenda)
    resumen_cargado = _resumen_agenda(pc.agenda)
    assert len(resumen_original) == len(resumen_cargado) == 6
    for elemento in resumen_original:
        assert elemento in resumen_cargado, f"falta en la agenda cargada: {elemento}"


partida, servicio = construir_partida()

# guardar() no debe alterar una partida que sigue en curso (p. ej. un
# autoguardado): se compara la agenda antes y después.
resumen_antes = _resumen_agenda(partida.agenda)
PartidaBinaria.guardar(partida, RUTA)
resumen_despues = _resumen_agenda(partida.agenda)
assert resumen_antes == resumen_despues, "guardar() alteró la partida original"

cargada = PartidaBinaria.cargar(RUTA, servicio)
verificar(partida, cargada)

# Carga parcial de una sola sala (§4.10), sin tocar el resto del archivo.
sala_parcial = PartidaBinaria.cargar_sala(RUTA, 2, servicio)
assert sala_parcial.nombre == "Salida"
assert len(sala_parcial.activos) == 1
assert sala_parcial.activos.ver_primero().id_instancia == "e-2"

# Detección de versión de formato incompatible (§4.10): se corrompe a mano
# el campo version_formato del encabezado fijo (bytes 4..8).
with open(RUTA, "rb") as archivo:
    contenido = bytearray(archivo.read())
contenido[4:8] = (99).to_bytes(4, "little")
ruta_corrupta = RUTA + ".version_mala"
with open(ruta_corrupta, "wb") as archivo:
    archivo.write(contenido)
fallo_detectado = False
try:
    PartidaBinaria.cargar(ruta_corrupta, servicio)
except Exception as error:
    fallo_detectado = True
    assert type(error).__name__ == "VersionIncompatible", (
        f"debió lanzar VersionIncompatible, lanzó {type(error).__name__}")
assert fallo_detectado, "debió rechazar una versión de formato incompatible, no reprodujo en silencio"

print("Sección 6.3 OK")