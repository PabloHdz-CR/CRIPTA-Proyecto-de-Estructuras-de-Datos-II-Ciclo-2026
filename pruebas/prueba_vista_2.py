"""Prueba de VistaJuego (ABC), VistaNula y Etiquetador (§6).

VistaJuego es el contrato: no se puede instanciar directo (le faltan
implementaciones), pero cualquier clase que implemente los 7 métodos sí.
VistaNula es la implementación vacía real que usan --replay/--bench.
Etiquetador lleva el conteo de "Rata gigante #1", "#2"... por tipo.
"""
import dataclasses

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import CriptaVisible, PuntajeVisible, ResultadoFinVisible
from cripta.vista.etiquetador import Etiquetador
from cripta.vista.vistaJuego import VistaJuego
from cripta.vista.vistaNula import VistaNula


def debe_fallar(error, funcion, *argumentos):
    try:
        funcion(*argumentos)
    except error:
        return
    raise AssertionError(f"debió lanzar {error.__name__}")


# 1. VistaJuego no se puede instanciar directo: es abstracta
debe_fallar(TypeError, VistaJuego)


# 1b. Una implementación mínima sí puede instanciarse, y solo si cubre los 7
class _VistaMinima(VistaJuego):
    def mostrar_estado(self, estado):
        pass

    def mostrar_mensajes(self, mensajes):
        pass

    def pedir_comando(self):
        return Comando("esperar")

    def mostrar_menu(self, criptas):
        pass

    def mostrar_puntajes(self, puntajes):
        pass

    def mostrar_fin(self, resultado):
        pass

    def mostrar_error(self, mensaje):
        pass

    def actualizar(self):
        pass


minima = _VistaMinima()
assert minima.pedir_comando() == Comando("esperar")

# 1c. Si falta un método, Python se niega a instanciarla (sigue siendo abstracta)
class _VistaIncompleta(VistaJuego):
    def mostrar_estado(self, estado):
        pass
    # le faltan los otros 6

debe_fallar(TypeError, _VistaIncompleta)

# 2. VistaNula: nunca bloquea y no hace nada, solo recuerda lo último recibido
nula = VistaNula()
assert nula.pedir_comando() is None        # ni siquiera con estado ya mostrado

nula.mostrar_estado("foto-1")
assert nula.ultimo_estado == "foto-1"
assert nula.pedir_comando() is None        # sigue sin bloquear ni inventar nada

mensajes = ListaEnlazada()
mensajes.agregar_al_final("Entras a Entrada.")
nula.mostrar_mensajes(mensajes)
assert nula.ultimos_mensajes is mensajes

criptas = ListaEnlazada()
criptas.agregar_al_final(CriptaVisible(id="c1", nombre="La Cripta", salas=10, dificultad=2))
nula.mostrar_menu(criptas)
assert nula.ultimo_menu is criptas
assert nula.ultimo_menu.ver_primero().nombre == "La Cripta"

puntajes = ListaEnlazada()
puntajes.agregar_al_final(
    PuntajeVisible(nombre="Ana", id_cripta="c1", version_cripta="v1",
                   acciones=40, enemigos_derrotados=5, tiempo_final=300,
                   resultado="victoria"))
nula.mostrar_puntajes(puntajes)
assert nula.ultimos_puntajes is puntajes

fin = ResultadoFinVisible(resultado="derrota", acciones=12, enemigos_derrotados=1, tiempo_final=90)
nula.mostrar_fin(fin)
assert nula.ultimo_fin is fin

nula.mostrar_error("no se pudo reproducir fielmente")
assert nula.ultimo_error == "no se pudo reproducir fielmente"

assert nula.actualizar() is None       # no hay ventana que bombear, no revienta

# 3. Etiquetador: contadores independientes por nombre_base, empiezan en #1
etq = Etiquetador()
assert etq.etiqueta("Rata gigante") == "Rata gigante #1"
assert etq.etiqueta("Rata gigante") == "Rata gigante #2"
assert etq.etiqueta("Esqueleto") == "Esqueleto #1"        # cuenta aparte
assert etq.etiqueta("Rata gigante") == "Rata gigante #3"
assert etq.etiqueta("Esqueleto") == "Esqueleto #2"

# 3b. reiniciar() vuelve todo a cero (nueva cripta)
etq.reiniciar()
assert etq.etiqueta("Rata gigante") == "Rata gigante #1"
assert etq.etiqueta("Esqueleto") == "Esqueleto #1"

# 3c. Dos Etiquetador son independientes entre sí
otro = Etiquetador()
assert otro.etiqueta("Rata gigante") == "Rata gigante #1"
assert etq.etiqueta("Rata gigante") == "Rata gigante #2"   # el primero no se vio afectado

print("Sección vista_2 (VistaJuego, VistaNula, Etiquetador) OK")