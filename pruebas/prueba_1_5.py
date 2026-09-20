import threading

from cripta.adaptadores.contadorSolicitudes import ContadorSolicitudes
from cripta.modelo.puertos.errores import PresupuestoAgotado


def trabajar(contador, bloqueados, indice):
    """Cada hilo intenta 50 solicitudes y cuenta cuántas le bloquearon."""
    for _ in range(50):
        try:
            contador.registrar_intento("prueba")
        except PresupuestoAgotado:
            bloqueados[indice] += 1


# 1. Sin presupuesto conocido no hay límite, pero se cuenta
contador = ContadorSolicitudes()
for _ in range(3):
    contador.registrar_intento("listar criptas")
assert contador.solicitudes_realizadas() == 3
assert contador.presupuesto() is None
assert contador.restantes() is None

# 2. Con presupuesto: se puede gastar hasta el límite y no más
contador.establecer_presupuesto(5)
assert contador.restantes() == 2
contador.registrar_intento("a")
contador.registrar_intento("b")
assert contador.restantes() == 0
try:
    contador.registrar_intento("solicitud de más")
    assert False, "debió lanzar PresupuestoAgotado"
except PresupuestoAgotado as error:
    print("Error esperado:", error)
    assert error.usadas == 5 and error.presupuesto == 5
assert contador.solicitudes_realizadas() == 5   # el intento bloqueado NO suma

# 3. Un presupuesto negativo se rechaza
try:
    contador.establecer_presupuesto(-1)
    assert False, "debió lanzar ValueError"
except ValueError:
    pass

# 4. Si el presupuesto llega menor a lo ya gastado, restantes nunca es negativo
contador.establecer_presupuesto(2)
assert contador.restantes() == 0

# 5. Reiniciar deja todo como al inicio
contador.reiniciar()
assert contador.solicitudes_realizadas() == 0
assert contador.presupuesto() is None

# 6. Varios hilos a la vez: nunca se pasa del presupuesto
contador = ContadorSolicitudes()
contador.establecer_presupuesto(100)
bloqueados = [0] * 8
hilos = []
for numero in range(8):
    hilo = threading.Thread(target=trabajar, args=(contador, bloqueados, numero))
    hilos.append(hilo)
    hilo.start()
for hilo in hilos:
    hilo.join()
assert contador.solicitudes_realizadas() == 100   # exacto: ni una más
assert sum(bloqueados) == 8 * 50 - 100            # el resto fue bloqueado

print("Sección 1.5 OK")