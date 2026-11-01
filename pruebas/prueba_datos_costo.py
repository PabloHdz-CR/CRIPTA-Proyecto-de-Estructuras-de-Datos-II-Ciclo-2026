"""Validación de los datos de costo (001-terreno-cazador, Historia 1).

Requisitos que ejerce: FR-001 (el campo costo es opcional; sin él vale 100),
FR-002 (mismo costo en los dos sentidos, enlace idempotente), FR-003 (un
costo que no es entero ≥ 1 es un error de datos que nombra sala y salida),
FR-019 (el esqueleto acepta el campo costo), FR-027 (caras de una puerta con
costos distintos: la cripta se rechaza; una sola cara declarada vale para las
dos), FR-009 y FR-020 (la ficha de un cazador trae un rango entero >= 0
obligatorio; en los demás comportamientos se ignora).

Escenarios de aceptación: H1.E7 y H1.E8 (cada caso lleva su marca).

Ejecutar desde la raíz del proyecto:
    py -m pruebas.prueba_datos_costo
"""
import tempfile
from pathlib import Path

from cripta.adaptadores import convertidorJson
from cripta.adaptadores.almacenPartidaDisco import AlmacenPartidaDisco
from cripta.adaptadores.puntajesArchivo import PuntajesArchivo
from cripta.adaptadores.registroArchivo import CarpetaRegistros
from cripta.controlador.controladorMenu import ControladorMenu
from cripta.controlador.gestorGuardado import GestorGuardado
from cripta.controlador.reporteFinal import ReporteFinal
from cripta.modelo.mundo.mundo import Mundo
from cripta.modelo.puertos.errores import DatosInvalidos, ErrorCripta
from cripta.vista.comando import Comando
from pruebas.apoyo_terreno import (
    VistaRegistradora, a_lista, datos_cripta, mundo_desde, pasillo, salida,
    servicio_terreno)


def pagina_json(salidas_de_la_sala_7):
    """Una página de esqueleto con la sala 7 (las salidas dadas) y la 8."""
    return {"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 7, "nombre": "Siete", "salidas": salidas_de_la_sala_7},
        {"id": 8, "nombre": "Ocho", "salidas": {"S": {"sala": 7}}}]}


def salidas_dto(pagina, id_sala):
    for sala in pagina.salas:
        if sala.id == id_sala:
            return a_lista(sala.salidas)
    raise AssertionError(f"no está la sala {id_sala}")


# ---------------------------------------------------------------------------
# Convertidor: lectura y validación del campo costo (FR-001, FR-003, FR-019)
# ---------------------------------------------------------------------------

def caso_convertidor_lee_costo():
    """FR-019, FR-001: el convertidor lee 'costo'; si falta, queda None (no
    declarado), no 100, para que la regla de las dos caras lo distinga."""
    pagina = convertidorJson.pagina_salas_desde_json(pagina_json(
        {"N": {"sala": 8, "costo": 300}, "E": {"sala": 8}, "S": {"sala": 8, "costo": 1}}))
    por_direccion = {s.direccion: s.costo for s in salidas_dto(pagina, 7)}
    assert por_direccion == {"N": 300, "S": 1, "E": None}, por_direccion


def caso_convertidor_rechaza_costos_invalidos():
    """FR-003: 0, negativos, decimales, texto y bool son un error de datos de la
    jerarquía ErrorCripta que nombra la sala y la dirección; nunca se
    sustituyen en silencio. (null no está aquí: equivale a no declarado.)"""
    for invalido in (0, -5, 2.5, "100", True, False, 100.0):
        try:
            convertidorJson.pagina_salas_desde_json(
                pagina_json({"E": {"sala": 8, "costo": invalido}}))
        except ErrorCripta as error:
            texto = str(error)
            assert "7" in texto and "E" in texto, f"{invalido!r}: {texto}"
            assert repr(invalido) in texto or str(invalido) in texto, f"{invalido!r}: {texto}"
        else:
            raise AssertionError(f"el costo {invalido!r} debía rechazarse")


def caso_convertidor_costo_null():
    """FR-003, FR-001: "costo": null equivale a no declararlo, igual que un campo
    ausente (como llave y cierre_automatico): el DTO queda con None y, tras el
    enlace, vale 100, o el de la otra cara si esa sí lo declara (FR-027)."""
    pagina = convertidorJson.pagina_salas_desde_json(pagina_json(
        {"N": {"sala": 8, "costo": None}, "E": {"sala": 8}}))
    por_direccion = {s.direccion: s.costo for s in salidas_dto(pagina, 7)}
    assert por_direccion == {"N": None, "E": None}, por_direccion
    salas = convertidorJson.pagina_salas_desde_json({"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 1, "nombre": "Uno", "salidas": {"E": {"sala": 2, "costo": None},
                                                "N": {"sala": 3, "costo": None}}},
        {"id": 2, "nombre": "Dos", "salidas": {"O": {"sala": 1, "costo": 250}}},
        {"id": 3, "nombre": "Tres", "salidas": {"S": {"sala": 1, "costo": None}}}]}).salas
    mundo = Mundo(datos_cripta(((1, ()), (2, ()), (3, ()))))
    mundo.agregar_esqueleto(salas)
    mundo.enlazar()
    assert costos(mundo) == {(1, "E"): 250, (2, "O"): 250, (1, "N"): 100, (3, "S"): 100}


# ---------------------------------------------------------------------------
# Mundo.enlazar(): las dos caras de una puerta (FR-002, FR-027)
# ---------------------------------------------------------------------------

def costos(mundo):
    """{(sala, dirección): costo efectivo} de todas las salidas."""
    resultado = {}
    for sala in mundo:
        for s in sala.salidas:
            if s is not None:
                resultado[(sala.id, s.direccion)] = s.costo
    return resultado


def caso_h1_e7_caras_distintas():
    """H1.E7 (FR-027): A→B declara 300 y B→A declara 200 → la cripta se rechaza
    con DatosInvalidos; el mensaje nombra las dos salas y los dos costos."""
    descripcion = ((1, (salida("E", 2, 300),)), (2, (salida("O", 1, 200),)))
    try:
        mundo_desde(descripcion)
    except DatosInvalidos as error:
        texto = str(error)
        for parte in ("sala 1", "sala 2", "300", "200", "costos distintos"):
            assert parte in texto, f"falta '{parte}' en: {texto}"
    else:
        raise AssertionError("las caras con costos distintos debían rechazarse")


def caso_h1_e8_una_sola_cara():
    """H1.E8 (FR-027, FR-002): solo A→B declara 300 → 300 en los dos sentidos.
    Vale igual si la que declara es la otra cara."""
    for descripcion in (((1, (salida("E", 2, 300),)), (2, (salida("O", 1),))),
                        ((1, (salida("E", 2),)), (2, (salida("O", 1, 300),)))):
        assert costos(mundo_desde(descripcion)) == {(1, "E"): 300, (2, "O"): 300}


def caso_tabla_del_contrato():
    """FR-001, FR-002, FR-027: el resto de la tabla de contracts/datos-entrada.md.
    Sin costo en ninguna cara → 100; iguales → ese valor; un solo sentido → el
    declarado, o 100 si no declara."""
    assert costos(mundo_desde(pasillo(2))) == {(1, "E"): 100, (2, "O"): 100}
    assert costos(mundo_desde(pasillo(2, costo=50))) == {(1, "E"): 50, (2, "O"): 50}
    un_sentido = ((1, (salida("E", 2, 250), salida("N", 3))), (2, ()), (3, ()))
    assert costos(mundo_desde(un_sentido)) == {(1, "E"): 250, (1, "N"): 100}


def caso_contraparte_por_direccion_opuesta():
    """FR-002 (research R8): la contraparte de A —E→ B es B —O→, si conduce a A.
    Una salida de B hacia A en otra dirección no es su contraparte."""
    descripcion = ((1, (salida("E", 2, 300),)), (2, (salida("N", 1, 200),)))
    assert costos(mundo_desde(descripcion)) == {(1, "E"): 300, (2, "N"): 200}


def caso_enlazar_idempotente():
    """FR-002: llamar dos veces a enlazar() deja las mismas entrantes en cada
    sala (misma cantidad, sin duplicados), los mismos costos efectivos y un
    solo registro de puertas por salida."""
    descripcion = ((1, (salida("N", 2, 50), salida("E", 3))),
                   (2, (salida("S", 1), salida("E", 3, 250))),
                   (3, (salida("O", 1), salida("N", 2, 250))))
    mundo = mundo_desde(descripcion)
    entrantes_1 = {sala.id: sorted((s.origen.id, s.direccion) for s in sala.entrantes)
                   for sala in mundo}
    costos_1 = costos(mundo)
    mundo.enlazar()
    entrantes_2 = {sala.id: sorted((s.origen.id, s.direccion) for s in sala.entrantes)
                   for sala in mundo}
    assert entrantes_1 == entrantes_2, (entrantes_1, entrantes_2)
    assert costos(mundo) == costos_1
    for lista in entrantes_2.values():
        assert len(lista) == len(set(lista)), f"entrantes duplicadas: {lista}"
    assert entrantes_2 == {1: [(2, "S"), (3, "O")], 2: [(1, "N"), (3, "N")],
                           3: [(1, "E"), (2, "E")]}, entrantes_2
    # Referencias directas: origen y sala_destino son las salas del mundo.
    for sala in mundo:
        for s in sala.salidas:
            if s is not None:
                assert s.origen is sala and s.sala_destino is mundo.sala(s.destino)
    # Un solo registro: cambiar una puerta avanza la versión exactamente 1.
    version = mundo.registro_puertas.version
    mundo.sala(1).salida("N").cerrada = True
    assert mundo.registro_puertas.version == version + 1
    mundo.sala(1).salida("N").cerrada = False
    assert mundo.registro_puertas.version == version + 2


# ---------------------------------------------------------------------------
# Controlador: el error de datos llega a la Vista y la partida no empieza
# ---------------------------------------------------------------------------

def nuevo_menu(vista):
    carpeta = Path(tempfile.mkdtemp(prefix="prueba_datos_costo_"))
    return ControladorMenu(
        servicio_terreno(), vista,
        GestorGuardado(AlmacenPartidaDisco(carpeta / "guardados")),
        PuntajesArchivo(carpeta / "puntajes.jsonl"),
        CarpetaRegistros(carpeta / "partidas"), ReporteFinal(), semilla_fija=1)


def caso_controlador_caras_distintas():
    """FR-027 (H1.E7 de punta a punta): ControladorMenu sobre el paquete
    pruebas/datos/terreno_cazador inicia terreno-caras-distintas → captura
    DatosInvalidos, llama una sola vez a mostrar_error con "No se pudo iniciar
    la cripta", las dos salas y los dos costos, y la partida no empieza."""
    vista = VistaRegistradora()
    menu = nuevo_menu(vista)
    menu.iniciar()
    menu.procesar(Comando("jugar", ("terreno-caras-distintas",)))
    assert len(vista.errores) == 1, vista.errores
    texto = vista.errores[0]
    for parte in ("No se pudo iniciar la cripta", "sala 1", "sala 2", "300", "200"):
        assert parte in texto, f"falta '{parte}' en: {texto}"
    assert menu._juego is None, "la partida no debía empezar"


def caso_controlador_terreno_valido():
    """FR-019: la cripta terreno-a, con costos coherentes, sí empieza."""
    vista = VistaRegistradora()
    menu = nuevo_menu(vista)
    menu.iniciar()
    menu.procesar(Comando("jugar", ("terreno-a",)))
    assert vista.errores == [], vista.errores
    assert menu._juego is not None


# ---------------------------------------------------------------------------
# Rango de las fichas de cazador (FR-009, FR-020)
# ---------------------------------------------------------------------------

def ficha_json(comportamiento, **extra):
    datos = {"id": "ent_prueba", "nombre": "Prueba", "clase": "enemigo", "vida_max": 10,
             "ataque": 2, "defensa": 1, "velocidad": 100, "comportamiento": comportamiento,
             "suelta": []}
    datos.update(extra)
    return datos


def una_ficha(datos):
    fichas = a_lista(convertidorJson.fichas_desde_json({"entidades": [datos]}))
    assert len(fichas) == 1
    return fichas[0]


def caso_rango_de_cazador():
    """FR-009, FR-020: la ficha de un cazador trae su rango; 0 es válido."""
    assert una_ficha(ficha_json("cazador", rango=400)).rango == 400
    assert una_ficha(ficha_json("cazador", rango=0)).rango == 0
    assert una_ficha(ficha_json("Cazadora", rango=7)).rango == 7     # prefijo, sin mayúsculas


def caso_rango_invalido_o_ausente():
    """FR-009: un cazador sin rango, o con un rango que no es entero >= 0
    (incluidos null, bool, decimales y texto), es un error de datos que nombra
    la ficha. A diferencia del costo, null no vale como "no declarado"."""
    casos = [ficha_json("cazador")] + [ficha_json("cazador", rango=valor)
                                       for valor in (-1, True, False, 2.5, None, "400")]
    for datos in casos:
        try:
            una_ficha(datos)
        except ErrorCripta as error:
            assert "ent_prueba" in str(error), str(error)
        else:
            raise AssertionError(f"la ficha {datos} debía rechazarse")


def caso_rango_ignorado_en_otros():
    """FR-009: en los demás comportamientos el rango se ignora (aunque sea raro)."""
    for comportamiento in ("errante", "rastreador", "guardián"):
        for extra in ({}, {"rango": 300}, {"rango": "x"}):
            assert una_ficha(ficha_json(comportamiento, **extra)).rango is None


def caso_controlador_sin_rango():
    """FR-009 de punta a punta: terreno-sin-rango (su cazador sin rango está en
    la sala inicial) no puede iniciarse; el Controlador lo informa con
    mostrar_error, nombrando la ficha, y la partida no empieza."""
    vista = VistaRegistradora()
    menu = nuevo_menu(vista)
    menu.iniciar()
    menu.procesar(Comando("jugar", ("terreno-sin-rango",)))
    assert len(vista.errores) == 1, vista.errores
    texto = vista.errores[0]
    assert "No se pudo iniciar la cripta" in texto and "ent_cazador_sin_rango" in texto, texto
    assert menu._juego is None


CASOS = (
    caso_convertidor_lee_costo,
    caso_convertidor_rechaza_costos_invalidos,
    caso_convertidor_costo_null,
    caso_h1_e7_caras_distintas,
    caso_h1_e8_una_sola_cara,
    caso_tabla_del_contrato,
    caso_contraparte_por_direccion_opuesta,
    caso_enlazar_idempotente,
    caso_controlador_caras_distintas,
    caso_controlador_terreno_valido,
    caso_rango_de_cazador,
    caso_rango_invalido_o_ausente,
    caso_rango_ignorado_en_otros,
    caso_controlador_sin_rango,
)


def main():
    fallidos = []
    for caso in CASOS:
        try:
            caso()
            print(f"[OK   ] {caso.__name__}")
        except Exception as error:                  # se reportan todos los casos
            fallidos.append(caso.__name__)
            print(f"[FALLÓ] {caso.__name__}: {type(error).__name__}: {error}")
    if fallidos:
        raise SystemExit(f"Fallaron {len(fallidos)} de {len(CASOS)} casos: {', '.join(fallidos)}")
    print(f"prueba_datos_costo OK ({len(CASOS)} casos)")


main()
