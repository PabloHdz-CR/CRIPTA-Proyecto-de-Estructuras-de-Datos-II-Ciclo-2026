"""Tab / Shift+Tab en el inventario: el cursor da la vuelta en los extremos y,
con una vista ordenada (tecla O), sigue el orden que se ve en pantalla.

Ejecutar desde la carpeta que contiene 'cripta' y 'pruebas':
    py pruebas/prueba_cursor_inventario.py
"""
from cripta.controlador.controladorJuego import ControladorJuego
from cripta.modelo.objetos.inventario import Inventario


class Ficha:
    def __init__(self, nombre, peso, valor):
        self.id = f"itm_{nombre}"
        self.nombre = nombre
        self.peso = peso
        self.valor = valor


class Objeto:
    def __init__(self, nombre, peso, valor):
        self.ficha = Ficha(nombre, peso, valor)
        self.id_objeto = nombre


A, B, C = Objeto("a", 3, 10), Objeto("b", 1, 30), Objeto("c", 2, 20)

# 1. Modelo, orden real A, B, C: da la vuelta en los dos sentidos
inventario = Inventario(10)
for objeto in (A, B, C):
    inventario.recoger(objeto)
assert inventario.actual() is A
assert inventario.siguiente() is B and inventario.siguiente() is C
assert inventario.siguiente() is A, "después del último vuelve al primero"
assert inventario.anterior() is C, "antes del primero viene el último"
assert inventario.anterior() is B

# Un solo objeto: Tab y Shift+Tab lo dejan donde está. Vacío: None.
uno = Inventario(10)
uno.recoger(A)
assert uno.siguiente() is A and uno.anterior() is A
assert Inventario(10).siguiente() is None and Inventario(10).anterior() is None


# 2. Controlador: con una vista ordenada, Tab sigue el orden de la pantalla
class Jugador:
    def __init__(self, inventario):
        self.inventario = inventario


class Partida:
    def __init__(self, inventario):
        self.jugador = Jugador(inventario)


class ControladorFalso:
    """Solo lo que usa _mover_cursor_inventario."""

    def __init__(self, inventario, criterio):
        self.partida = Partida(inventario)
        self._criterio_orden = criterio
        self.mostrados = 0

    def _mostrar_estado_actual(self):
        self.mostrados += 1


mover = ControladorJuego._mover_cursor_inventario
inventario.enfocar(A)
falso = ControladorFalso(inventario, "peso")          # en pantalla: B (1), C (2), A (3)
mover(falso, 1)
assert inventario.actual() is B, "A es el último de la vista: Tab vuelve al primero (B)"
mover(falso, 1)
assert inventario.actual() is C
mover(falso, -1)
assert inventario.actual() is B
mover(falso, -1)
assert inventario.actual() is A, "Shift+Tab desde el primero va al último de la vista"
assert falso.mostrados == 4

# El orden real no cambia por recorrer la vista ordenada
reales = []
for objeto in inventario:
    reales.append(objeto)
assert reales == [A, B, C]

# Sin criterio (orden real) usa la ListaDoble y también da la vuelta
falso = ControladorFalso(inventario, None)
inventario.enfocar(C)
mover(falso, 1)
assert inventario.actual() is A

print("Sección cursor del inventario OK")
