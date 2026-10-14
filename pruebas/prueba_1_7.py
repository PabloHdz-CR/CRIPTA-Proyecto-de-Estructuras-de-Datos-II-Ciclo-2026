import json
import os
import shutil

from cripta.adaptadores.fuenteOffline import FuenteOffline
from cripta.modelo.puertos.errores import ErrorDeRed, LoteInvalido

CARPETA = "paquete_prueba_offline"
shutil.rmtree(CARPETA, ignore_errors=True)


def escribir(ruta, contenido):
    ruta_completa = os.path.join(CARPETA, ruta)
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    with open(ruta_completa, "w", encoding="utf-8") as f:
        json.dump(contenido, f, ensure_ascii=False)


escribir("criptas.json", {"criptas": [
    {"id": "cripta-01", "nombre": "Osario menor", "salas": 20, "dificultad": 1}]})

escribir("criptas/cripta-01/general.json", {
    "id": "cripta-01", "version": "a3f91c", "salas_total": 20, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 19,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9,
    "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})

escribir("criptas/cripta-01/version.json", {"version": "a3f91c"})

escribir("criptas/cripta-01/esqueleto/pagina_1.json", {
    "pagina": 1, "total_paginas": 1,
    "salas": [
        {"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo de las urnas", "salidas": {
            "E": {"sala": 7, "cerrada": True, "llave": "itm_llave_bronce",
                  "cierre_automatico": 500},
            "S": {"sala": 1}, "N": {"sala": 3}}},
    ]})

escribir("criptas/cripta-01/contenido/2.json", {
    "sala": 2,
    "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 12}],
    "objetos": ["itm_daga_oxidada"],
    "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]})

escribir("catalogo/version.json", {"version": "k7"})
escribir("catalogo/ent_rata_gigante.json", {
    "id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante",
    "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
    "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]})
escribir("catalogo/itm_daga_oxidada.json", {
    "id": "itm_daga_oxidada", "clase": "arma", "nombre": "Daga oxidada",
    "peso": 2, "valor": 15, "ataque_bonus": 3})

fuente = FuenteOffline(CARPETA)

criptas = fuente.listar_criptas()
assert criptas.obtener(0).nombre == "Osario menor"

datos = fuente.datos_generales("cripta-01")
assert datos.presupuesto_solicitudes == 9 and datos.jugador.velocidad == 100

pagina = fuente.esqueleto("cripta-01", 1)
sala2 = pagina.salas.obtener(1)
direcciones = []
for salida in sala2.salidas:
    direcciones.append(salida.direccion)
assert direcciones == ["N", "S", "E"], direcciones

ids_salas = []
ids_salas.append(2)
contenido = fuente.contenido("cripta-01", ids_salas)
assert contenido.obtener(0).enemigos.obtener(0).tipo == "ent_rata_gigante"
assert contenido.obtener(0).objetos.obtener(0) == "itm_daga_oxidada"

ids_fichas = []
ids_fichas.append("ent_rata_gigante")
ids_fichas.append("itm_daga_oxidada")
fichas = fuente.catalogo(ids_fichas)
assert fichas.obtener(0).nombre == "Rata gigante"
assert fichas.obtener(1).ataque_bonus == 3

assert fuente.version_cripta("cripta-01") == "a3f91c"
assert fuente.version_catalogo() == "k7"

assert fuente.solicitudes_realizadas() == 0
assert fuente.presupuesto() is None
fuente.reiniciar_conteo()   # no debe fallar ni hacer nada

# Lote inválido: debe comportarse igual que ClienteHttp
try:
    fuente.catalogo([])
    assert False, "debía lanzar LoteInvalido"
except LoteInvalido:
    pass

try:
    fuente.contenido("cripta-01", [])
    assert False, "debía lanzar LoteInvalido"
except LoteInvalido:
    pass

# Archivo faltante: error legible, no caída silenciosa ni traceback crudo
try:
    fuente.datos_generales("cripta-no-existe")
    assert False, "debía lanzar ErrorDeRed"
except ErrorDeRed as error:
    assert "no se encontró" in str(error)

# Archivo corrupto: también debe traducirse a ErrorDeRed
ruta_mala = os.path.join(CARPETA, "catalogo", "itm_roto.json")
with open(ruta_mala, "w", encoding="utf-8") as f:
    f.write("{esto no es json valido")
try:
    fuente.catalogo(["itm_roto"])
    assert False, "debía lanzar ErrorDeRed con el archivo dañado"
except ErrorDeRed as error:
    assert "dañado" in str(error)

shutil.rmtree(CARPETA, ignore_errors=True)
print("Sección 1.7 OK")