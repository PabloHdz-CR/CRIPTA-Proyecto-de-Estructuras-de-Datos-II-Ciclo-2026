import os
import shutil

from cripta.adaptadores.registroArchivo import EncabezadoPartida, RegistroArchivo
from cripta.modelo.nucleo.accion import (
    AbrirPuerta, Atacar, Equipar, Esperar, Mover, Recoger, Soltar, Usar,
    UsarPergamino)
from cripta.modelo.puertos.errores import ErrorCripta

CARPETA = "paquete_prueba_6_4"
shutil.rmtree(CARPETA, ignore_errors=True)
os.makedirs(CARPETA, exist_ok=True)

ruta_log = os.path.join(CARPETA, "partida.log")
registro = RegistroArchivo(ruta_log)
encabezado = EncabezadoPartida("cripta-01", "a3f91c", "cat-2026-08-01", semilla=12345)
registro.iniciar(encabezado)

acciones_originales = [
    Mover("N"), AbrirPuerta("E"), Atacar("e-201"), Recoger(7), Equipar(7),
    Usar(9), Soltar(3), UsarPergamino(), Esperar(),
]
for accion in acciones_originales:
    registro.registrar_accion(accion)

encabezado_leido, acciones_leidas = registro.leer()
assert encabezado_leido.id_cripta == "cripta-01"
assert encabezado_leido.version_cripta == "a3f91c"
assert encabezado_leido.version_catalogo == "cat-2026-08-01"
assert encabezado_leido.semilla == 12345

leidas = []
for a in acciones_leidas:
    leidas.append(a)
assert len(leidas) == len(acciones_originales)
for original, leida in zip(acciones_originales, leidas):
    assert type(original) is type(leida), (original, leida)
    assert original == leida, f"no quedó igual: {original!r} -> {leida!r}"

registro.registrar_accion(Mover("S"))
_, acciones_mas = registro.leer()
contador = 0
for _ in acciones_mas:
    contador += 1
assert contador == len(acciones_originales) + 1, "registrar_accion no anexó, reescribió"

ruta_mala = os.path.join(CARPETA, "vacio.log")
open(ruta_mala, "w").close()
try:
    RegistroArchivo(ruta_mala).leer()
    assert False, "debía fallar con archivo vacío"
except ErrorCripta:
    pass

ruta_sin_encabezado = os.path.join(CARPETA, "sin_encabezado.log")
with open(ruta_sin_encabezado, "w", encoding="utf-8") as f:
    f.write("MOVER N\n")
try:
    RegistroArchivo(ruta_sin_encabezado).leer()
    assert False, "debía fallar sin el prefijo CRIPTA"
except ErrorCripta:
    pass

shutil.rmtree(CARPETA, ignore_errors=True)
print("Sección 6.4 OK")