from cripta.modelo.nucleo.mutador import Mutador
from cripta.modelo.nucleo.diario import Diario
from cripta.modelo.reloj.agenda import Agenda
from cripta.modelo.reloj.evento import Evento
from cripta.modelo.mundo.sala import Sala
from cripta.modelo.objetos.inventario import Inventario
from cripta.modelo.objetos.equipo import Equipo
from cripta.modelo.actores.actor import Actor


class EventoFalso(Evento):
    def ejecutar(self, partida):
        pass


class ObjetoFalso:
    def __init__(self, id_instancia, clase="llave"):
        self.id_instancia = id_instancia
        self.clase = clase
        self.nombre = f"obj-{id_instancia}"

    class _Ficha:
        id = "itm_x"
    ficha = _Ficha()


class PartidaFalsa:
    """Solo necesita .agenda para que Diario revierta la agenda."""
    def __init__(self, agenda):
        self.agenda = agenda


# ---------------------------------------------------------------------
# 1) ATRIBUTO
# ---------------------------------------------------------------------
m = Mutador()
d = Diario()
m.diario = d

class Caja:
    def __init__(self):
        self.vida = 30

caja = Caja()
d.abrir_intervalo(None)
m.asignar(caja, "vida", 10)
d.cerrar_intervalo()
assert caja.vida == 10
assert d.hay_cambios()
assert d.deshacer(None) is True
assert caja.vida == 30, "ATRIBUTO no se revirtió"
assert not d.hay_cambios()
assert d.deshacer(None) is False   # nada más que deshacer
print("[OK] ATRIBUTO")

# ---------------------------------------------------------------------
# 2) AGENDA: programar, extraer, cancelar
# ---------------------------------------------------------------------
agenda = Agenda()
m = Mutador()
d = Diario()
m.diario = d
m.agenda = agenda
partida = PartidaFalsa(agenda)

e1 = EventoFalso(10)
d.abrir_intervalo(partida)
m.agenda_programar(e1)
d.cerrar_intervalo()
assert len(agenda) == 1
d.deshacer(partida)
assert agenda.ver_siguiente() is None, "AGENDA_PROGRAMAR no se revirtió (sigue visible)"
print("[OK] AGENDA_PROGRAMAR")

e2 = EventoFalso(5)
agenda.programar(e2)   # sin mutador, ya estaba antes del intervalo
d.abrir_intervalo(partida)
extraido = m.agenda_extraer()
d.cerrar_intervalo()
assert extraido is e2
assert agenda.ver_siguiente() is None
d.deshacer(partida)
assert agenda.ver_siguiente() is e2, "AGENDA_EXTRAER no se revirtió"
print("[OK] AGENDA_EXTRAER")

d.abrir_intervalo(partida)
m.agenda_cancelar(e2)
d.cerrar_intervalo()
assert agenda.ver_siguiente() is None, "cancelar no tuvo efecto"
d.deshacer(partida)
assert agenda.ver_siguiente() is e2, "AGENDA_CANCELAR no se revirtió"
print("[OK] AGENDA_CANCELAR")

# ---------------------------------------------------------------------
# 3) SUELO
# ---------------------------------------------------------------------
m = Mutador()
d = Diario()
m.diario = d
datos_jugador = type("D", (), {"vida_max": 30, "ataque": 1, "defensa": 1, "velocidad": 1})()
sala = Sala(1, "Sala", (None, None, None, None))
objeto = ObjetoFalso("o1")

d.abrir_intervalo(None)
m.suelo_agregar(sala, objeto)
d.cerrar_intervalo()
assert sala.suelo.contiene(objeto)
d.deshacer(None)
assert not sala.suelo.contiene(objeto), "SUELO_AGREGAR no se revirtió"
print("[OK] SUELO_AGREGAR")

sala.suelo.agregar_al_final(objeto)   # ya estaba ahí, fuera del intervalo
d.abrir_intervalo(None)
m.suelo_quitar(sala, objeto)
d.cerrar_intervalo()
assert not sala.suelo.contiene(objeto)
d.deshacer(None)
assert sala.suelo.contiene(objeto), "SUELO_QUITAR no se revirtió"
print("[OK] SUELO_QUITAR")

# ---------------------------------------------------------------------
# 4) INVENTARIO Y EQUIPO (el más delicado)
# ---------------------------------------------------------------------
m = Mutador()
d = Diario()
m.diario = d


class JugadorFalso:
    def __init__(self):
        self.inventario = Inventario(10)
        self.equipo = Equipo()


jugador = JugadorFalso()
arma1 = ObjetoFalso("arma1", clase="arma")
arma2 = ObjetoFalso("arma2", clase="arma")

# Recoger dos armas
d.abrir_intervalo(None)
m.inventario_agregar(jugador, arma1)
d.cerrar_intervalo()
d.abrir_intervalo(None)
m.inventario_agregar(jugador, arma2)
d.cerrar_intervalo()
assert len(jugador.inventario) == 2

# Equipar arma1 (se mueve al frente, posición 0 -> 0, sin reemplazo)
assert jugador.inventario.indice_de(arma1) == 0
d.abrir_intervalo(None)
m.inventario_equipar(jugador, arma1)
d.cerrar_intervalo()
assert jugador.equipo.arma is arma1

# Equipar arma2 (estaba en posición 1; reemplaza a arma1, que SIGUE en inventario)
d.abrir_intervalo(None)
m.inventario_equipar(jugador, arma2)
d.cerrar_intervalo()
assert jugador.equipo.arma is arma2
assert jugador.inventario.indice_de(arma2) == 0
assert jugador.inventario.indice_de(arma1) == 1  # sigue en el inventario

# Deshacer el equipar de arma2: debe volver arma1 a estar equipada, y arma2
# debe regresar a la posición que tenía antes de moverse al frente.
d.deshacer(None)
assert jugador.equipo.arma is arma1, "no se restauró el arma reemplazada"
assert jugador.inventario.indice_de(arma1) == 0
assert jugador.inventario.indice_de(arma2) == 1, "INVENTARIO_EQUIPAR no revirtió la posición"
print("[OK] INVENTARIO_EQUIPAR (con reemplazo)")

# Deshacer el equipar de arma1 (primero): no reemplazaba nada, así que debe
# quedar desequipada.
d.deshacer(None)
assert jugador.equipo.arma is None, "no se desequipó al revertir el primer equipar"
print("[OK] INVENTARIO_EQUIPAR (sin reemplazo)")

# Deshacer el agregar de arma2 y luego el de arma1
d.deshacer(None)
assert len(jugador.inventario) == 1 and jugador.inventario.buscar is not None
d.deshacer(None)
assert len(jugador.inventario) == 0, "INVENTARIO_AGREGAR no se revirtió del todo"
print("[OK] INVENTARIO_AGREGAR (reversión completa)")

# Soltar con el objeto equipado: debe quedar re-equipado al deshacer
m2 = Mutador()
d2 = Diario()
m2.diario = d2
jugador2 = JugadorFalso()
arma3 = ObjetoFalso("arma3", clase="arma")
d2.abrir_intervalo(None)
m2.inventario_agregar(jugador2, arma3)
d2.cerrar_intervalo()
d2.abrir_intervalo(None)
m2.inventario_equipar(jugador2, arma3)
d2.cerrar_intervalo()
assert jugador2.equipo.arma is arma3
d2.abrir_intervalo(None)
m2.inventario_quitar(jugador2, arma3)
d2.cerrar_intervalo()
assert jugador2.equipo.arma is None and len(jugador2.inventario) == 0
d2.deshacer(None)
assert len(jugador2.inventario) == 1 and jugador2.equipo.arma is arma3, (
    "INVENTARIO_QUITAR no restauró el equipo")
print("[OK] INVENTARIO_QUITAR (estaba equipado)")

# ---------------------------------------------------------------------
# 5 bis) Historial de 5: el sexto deshacer no debe poder ir más atrás
# ---------------------------------------------------------------------
m = Mutador()
d = Diario()
m.diario = d
caja = Caja()
for i in range(7):
    d.abrir_intervalo(None)
    m.asignar(caja, "vida", i)
    d.cerrar_intervalo()
assert caja.vida == 6
deshechos = 0
while d.deshacer(None):
    deshechos += 1
assert deshechos == 5, f"debían poder deshacerse 5 acciones, se deshicieron {deshechos}"
print("[OK] Historial acotado a 5 (PilaAcotada descarta las más viejas)")

print("Sección 4.5 OK")