from dataclasses import FrozenInstanceError

from cripta.adaptadores import convertidorJson as cj
from cripta.modelo.puertos.errores import ErrorDeRed

# --- Lista de criptas y datos generales ---
criptas = cj.resumen_criptas_desde_json(
    {"criptas": [{"id": "cripta-01", "nombre": "Osario menor", "salas": 20, "dificultad": 1}]})
assert criptas.obtener(0).nombre == "Osario menor"

datos = cj.datos_cripta_desde_json({
    "id": "cripta-01", "version": "a3f91c", "salas_total": 20, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 19,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9,
    "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})
assert datos.presupuesto_solicitudes == 9
assert datos.jugador.velocidad == 100

# --- Esqueleto: las salidas salen siempre en orden N, S, E, O ---
pagina = cj.pagina_salas_desde_json({
    "pagina": 1, "total_paginas": 1,
    "salas": [
        {"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo de las urnas", "salidas": {
            "E": {"sala": 7, "cerrada": True, "llave": "itm_llave_bronce",
                  "cierre_automatico": 500},
            "S": {"sala": 1},
            "N": {"sala": 3}}},
    ]})
sala2 = pagina.salas.obtener(1)
direcciones = []
for salida in sala2.salidas:
    direcciones.append(salida.direccion)
assert direcciones == ["N", "S", "E"]
salida_e = sala2.salidas.obtener(2)
assert salida_e.cerrada is True
assert salida_e.llave == "itm_llave_bronce"
assert salida_e.cierre_automatico == 500
salida_n_sala1 = pagina.salas.obtener(0).salidas.obtener(0)
assert salida_n_sala1.cerrada is False and salida_n_sala1.llave is None

# --- Contenido ---
contenido = cj.contenido_desde_json({"contenido": [{
    "sala": 2,
    "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 12}],
    "objetos": ["itm_daga_oxidada"],
    "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]}]})
sala = contenido.obtener(0)
assert sala.enemigos.obtener(0).tipo == "ent_rata_gigante"
assert sala.objetos.obtener(0) == "itm_daga_oxidada"
assert sala.trampas.obtener(0).instancia == "t-17"

# --- Catálogo: cada clase produce su subclase ---
fichas = cj.fichas_desde_json({"entidades": [
    {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante",
     "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
     "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]},
    {"id": "itm_daga_oxidada", "clase": "arma", "nombre": "Daga oxidada",
     "peso": 2, "valor": 15, "ataque_bonus": 3},
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
     "peso": 1, "valor": 5, "duracion": 2000},
    {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos en la pared",
     "daño": 4, "rearme": 300},
    {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor",
     "peso": 1, "valor": 10, "cura": 8},
]})
rata = fichas.obtener(0)
assert rata.clase == "enemigo" and rata.velocidad == 150
assert rata.suelta.obtener(0) == "itm_pocion_menor"
assert fichas.obtener(1).ataque_bonus == 3
assert fichas.obtener(2).duracion == 2000
assert fichas.obtener(3).dano == 4
assert fichas.obtener(4).cura == 8
assert fichas.obtener(4).modificador_velocidad is None

# --- Inmutabilidad ---
try:
    rata.nombre = "Otra"
    assert False, "debió lanzar FrozenInstanceError"
except FrozenInstanceError:
    pass

# --- Errores con contexto ---
try:
    cj.fichas_desde_json({"entidades": [{"id": "x", "nombre": "x", "clase": "dragon"}]})
    assert False, "debió lanzar ErrorDeRed"
except ErrorDeRed as error:
    print("Error esperado:", error)

try:
    cj.datos_cripta_desde_json({"id": "x"})
    assert False, "debió lanzar ErrorDeRed"
except ErrorDeRed as error:
    print("Error esperado:", error)

print("Sección 1.3 OK")

# --- Campos ausentes en el JSON (los valores por defecto)
contenido = cj.contenido_desde_json({"contenido": [{"sala": 4}]})
sala_vacia = contenido.obtener(0)
assert sala_vacia.sala == 4
assert sala_vacia.enemigos.esta_vacia() and sala_vacia.objetos.esta_vacia()
assert sala_vacia.trampas.esta_vacia()
fichas = cj.fichas_desde_json({"entidades": [
    {"id": "e", "clase": "enemigo", "nombre": "E", "vida_max": 5, "ataque": 1,
     "defensa": 0, "velocidad": 100, "comportamiento": "errante"}]})
assert fichas.obtener(0).suelta.esta_vacia()