import os
import shutil

from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.modelo.nucleo.puntajes import RegistroPuntaje

CARPETA = "paquete_prueba_6_5"
shutil.rmtree(CARPETA, ignore_errors=True)
os.makedirs(CARPETA, exist_ok=True)

ruta_puntajes = os.path.join(CARPETA, "puntajes.jsonl")
archivo = PuntajesArchivo(ruta_puntajes)

tabla_vacia = archivo.cargar()
assert len(tabla_vacia) == 0, "un archivo que no existe debe dar una tabla vacía"

r1 = RegistroPuntaje("Diego", "cripta-01", "v1", acciones=40, enemigos_derrotados=3,
                      tiempo_final=5200, resultado="victoria")
r2 = RegistroPuntaje("Ana", "cripta-01", "v1", acciones=55, enemigos_derrotados=1,
                      tiempo_final=6100, resultado="derrota")
archivo.agregar(r1)
archivo.agregar(r2)

tabla = archivo.cargar()
assert len(tabla) == 2
nombres = []
for registro in tabla:
    nombres.append(registro.nombre)
assert nombres == ["Diego", "Ana"], nombres

mejores = tabla.vista_ordenada("tiempo")
primero = mejores.obtener(0)
assert primero.nombre == "Diego", "la vista ordenada por tiempo no sirvió"

with open(ruta_puntajes, "a", encoding="utf-8") as f:
    f.write("esto no es json\n")
    f.write('{"nombre": "Incompleto"}\n')
tabla2 = archivo.cargar()
assert len(tabla2) == 2, "las líneas corruptas debieron ignorarse, no tumbar la carga"

shutil.rmtree(CARPETA, ignore_errors=True)
print("Sección 6.5 OK")