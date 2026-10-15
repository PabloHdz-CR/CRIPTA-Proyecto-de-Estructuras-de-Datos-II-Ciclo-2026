"""Prueba del contrato compartido de Vista: Comando y EstadoVista (§6, §10.2).

Son dataclasses congeladas (foto de solo lectura): esta prueba confirma que
se arman bien, que son inmutables (si alguien las muta por error, revienta
en el acto y no deja el estado mostrado desincronizado), y que las
colecciones usan ListaEnlazada y no list/dict de Python (ya lo cubre
prueba_reglas.py de forma general, pero aquí se confirma el comportamiento
real de las clases).
"""
import dataclasses

from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.vista.comando import Comando
from cripta.vista.estadoVista import (
    SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE, SALIDA_SIN_SALIDA,
    ActorVisible, EfectoVisible, EstadoVista, InventarioVisible,
    JugadorVisible, ObjetoVisible, SalaVisible, SalidaVisible)

# 1. Comando: verbo + argumentos, inmutable
c = Comando("mover", ("N",))
assert c.verbo == "mover" and c.argumentos == ("N",)
try:
    c.verbo = "atacar"
    raise AssertionError("Comando debería ser inmutable (frozen)")
except dataclasses.FrozenInstanceError:
    pass

# Comando sin argumentos (p. ej. "esperar")
c2 = Comando("esperar")
assert c2.argumentos == ()

# Dos comandos con los mismos datos son iguales (dataclass, no identidad)
assert Comando("mover", ("N",)) == Comando("mover", ("N",))
assert Comando("mover", ("N",)) != Comando("mover", ("S",))

# 2. EstadoVista: se arma completo y es de solo lectura
enemigos = ListaEnlazada()
enemigos.agregar_al_final(ActorVisible("Rata gigante #1", 15, 20))
enemigos.agregar_al_final(ActorVisible("Rata gigante #2", 20, 20))

objetos_suelo = ListaEnlazada()
objetos_suelo.agregar_al_final(ObjetoVisible(100, "Espada", "arma", 3, 10))

sala = SalaVisible(
    nombre="Entrada",
    salidas=(
        SalidaVisible("N", SALIDA_CERRADA_CON_LLAVE),
        SalidaVisible("S", SALIDA_SIN_SALIDA),
        SalidaVisible("E", SALIDA_ABIERTA),
        None,
    ),
    enemigos=enemigos,
    objetos=objetos_suelo,
)

jugador = JugadorVisible(
    vida=18, vida_max=30, ataque_efectivo=14, defensa_efectiva=3,
    velocidad=100, antorcha_encendida=False, acciones=7, enemigos_derrotados=1,
)

inventario_objetos = ListaEnlazada()
inventario_objetos.agregar_al_final(ObjetoVisible(1, "Escudo", "armadura", 4, 8, equipado=True))
inventario_objetos.agregar_al_final(ObjetoVisible(2, "Espada", "arma", 3, 10, equipado=True))
inventario_objetos.agregar_al_final(ObjetoVisible(3, "Llave roja", "llave", 1, 1))

inventario = InventarioVisible(
    objetos=inventario_objetos, indice_actual=2, capacidad=8, cantidad_pergaminos=0,
)

efectos = ListaEnlazada()
efectos.agregar_al_final(EfectoVisible("veneno", "Envenenado (3 pulsos restantes)"))

mensajes = ListaEnlazada()
mensajes.agregar_al_final("Entras a Entrada.")
mensajes.agregar_al_final("¡Pincho! Recibes 5 de daño.")

estado = EstadoVista(
    id_cripta="cripta-01", version_cripta="v3", reloj=450,
    terminada=False, resultado=None, jugador=jugador, sala=sala,
    efectos=efectos, inventario=inventario, mensajes=mensajes,
)

assert estado.sala.nombre == "Entrada"
assert estado.sala.salidas[0].estado == SALIDA_CERRADA_CON_LLAVE
assert estado.sala.salidas[3] is None
assert len(estado.sala.enemigos) == 2
assert estado.sala.enemigos.ver_primero().etiqueta == "Rata gigante #1"
assert estado.jugador.vida == 18
assert estado.inventario.indice_actual == 2
assert len(estado.inventario.objetos) == 3
assert estado.efectos.ver_primero().tipo == "veneno"
assert len(estado.mensajes) == 2
assert estado.terminada is False and estado.resultado is None

try:
    estado.reloj = 999
    raise AssertionError("EstadoVista debería ser inmutable (frozen)")
except dataclasses.FrozenInstanceError:
    pass

# 3. EstadoVista de una partida terminada (victoria), sin inventar campos
estado_fin = dataclasses.replace(estado, terminada=True, resultado="victoria")
assert estado_fin.terminada is True and estado_fin.resultado == "victoria"
assert estado_fin.jugador is estado.jugador    # replace() no reconstruye lo que no cambia

print("Sección vista_1 (Comando y EstadoVista) OK")