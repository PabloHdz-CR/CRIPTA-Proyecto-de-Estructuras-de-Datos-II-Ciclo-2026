from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.puertos.errores import DatosInvalidos, ErrorDeRed
from ..modelo.puertos.dto import (
    DIRECCIONES,
    ResumenCriptaDTO, JugadorDTO, DatosCriptaDTO,
    SalidaDTO, SalaDTO, PaginaSalasDTO,
    EnemigoInstanciaDTO, TrampaInstanciaDTO, ContenidoSalaDTO,
    FichaEnemigoDTO, FichaTrampaDTO, FichaArmaDTO, FichaArmaduraDTO,
    FichaPocionDTO, FichaAntidotoDTO, FichaLlaveDTO, FichaAntorchaDTO,
    FichaPergaminoRetrocesoDTO,
    UbicacionLlaveDTO,
)

CLASES_OBJETO = ("arma", "armadura", "pocion", "antidoto", "llave", "antorcha", "pergamino_retroceso")

def _requerido(datos, campo, operacion):
    if campo not in datos:
        raise ErrorDeRed(operacion, f"la respuesta no trae el campo '{campo}'")
    return datos[campo]

def resumen_criptas_desde_json(datos):
    operacion = "listar criptas"
    resultado = ListaEnlazada()
    for item in _requerido(datos, "criptas", operacion):
        resultado.agregar_al_final(ResumenCriptaDTO(
            id=_requerido(item, "id", operacion),
            nombre=_requerido(item, "nombre", operacion),
            salas=_requerido(item, "salas", operacion),
            dificultad=_requerido(item, "dificultad", operacion),
        ))
    return resultado

def datos_cripta_desde_json(datos):
    operacion = "obtener los datos generales de la cripta"
    jugador_json = _requerido(datos, "jugador", operacion)
    jugador = JugadorDTO(
        vida_max=_requerido(jugador_json, "vida_max", operacion),
        ataque=_requerido(jugador_json, "ataque", operacion),
        defensa=_requerido(jugador_json, "defensa", operacion),
        velocidad=_requerido(jugador_json, "velocidad", operacion),
    )
    return DatosCriptaDTO(
        id=_requerido(datos, "id", operacion),
        version=_requerido(datos, "version", operacion),
        salas_total=_requerido(datos, "salas_total", operacion),
        paginas=_requerido(datos, "paginas", operacion),
        salas_por_pagina=_requerido(datos, "salas_por_pagina", operacion),
        sala_inicial=_requerido(datos, "sala_inicial", operacion),
        sala_salida=_requerido(datos, "sala_salida", operacion),
        llave_salida=_requerido(datos, "llave_salida", operacion),
        presupuesto_solicitudes=_requerido(datos, "presupuesto_solicitudes", operacion),
        inventario_max=_requerido(datos, "inventario_max", operacion),
        jugador=jugador,
    )

def _costo_desde_json(id_sala, direccion, datos):
    """El costo declarado de una salida, o None si no lo declara (FR-001).

    Ausente o null equivalen a no declarado, igual que llave y
    cierre_automatico (FR-003). Si viene un valor, debe ser un entero >= 1:
    se rechazan bool, 0, negativos, decimales y texto. Un valor inválido
    nunca se sustituye en silencio: es un error de datos que nombra la sala
    y la dirección.
    """
    costo = datos.get("costo")
    if costo is None:
        return None
    # DECISIÓN: type(...) is int y no isinstance: True y False son int en
    # Python, y un bool en el JSON es un error de datos, no un costo 1 o 0.
    if type(costo) is not int or costo < 1:
        raise DatosInvalidos(
            f"La salida {direccion} de la sala {id_sala} declara un costo inválido "
            f"({costo!r}): debe ser un entero mayor o igual que 1")
    return costo

def _salida_desde_json(id_sala, direccion, datos, operacion):
    return SalidaDTO(
        direccion=direccion,
        sala=_requerido(datos, "sala", operacion),
        cerrada=bool(datos.get("cerrada", False)),
        llave=datos.get("llave"),
        cierre_automatico=datos.get("cierre_automatico"),
        costo=_costo_desde_json(id_sala, direccion, datos),
    )

def _sala_desde_json(datos, operacion):
    id_sala = _requerido(datos, "id", operacion)
    salidas_json = _requerido(datos, "salidas", operacion)
    for clave in salidas_json:
        if clave not in DIRECCIONES:
            raise ErrorDeRed(operacion, f"dirección desconocida '{clave}'")
    salidas = ListaEnlazada()
    for direccion in DIRECCIONES:
        if direccion in salidas_json:
            salidas.agregar_al_final(
                _salida_desde_json(id_sala, direccion, salidas_json[direccion], operacion))
    return SalaDTO(
        id=id_sala,
        nombre=_requerido(datos, "nombre", operacion),
        salidas=salidas,
    )

def pagina_salas_desde_json(datos):
    operacion = "descargar una página del esqueleto"
    salas = ListaEnlazada()
    for item in _requerido(datos, "salas", operacion):
        salas.agregar_al_final(_sala_desde_json(item, operacion))
    return PaginaSalasDTO(
        pagina=_requerido(datos, "pagina", operacion),
        total_paginas=_requerido(datos, "total_paginas", operacion),
        salas=salas,
    )

def contenido_desde_json(datos):
    operacion = "descargar el contenido de las salas"
    resultado = ListaEnlazada()
    for item in _requerido(datos, "contenido", operacion):
        enemigos = ListaEnlazada()
        for e in item.get("enemigos", ()):
            enemigos.agregar_al_final(EnemigoInstanciaDTO(
                instancia=_requerido(e, "instancia", operacion),
                tipo=_requerido(e, "tipo", operacion),
                vida=e.get("vida"),
            ))
        objetos = ListaEnlazada()
        objetos.agregar_todos(item.get("objetos", ()))
        trampas = ListaEnlazada()
        for t in item.get("trampas", ()):
            trampas.agregar_al_final(TrampaInstanciaDTO(
                instancia=_requerido(t, "instancia", operacion),
                tipo=_requerido(t, "tipo", operacion),
            ))
        resultado.agregar_al_final(ContenidoSalaDTO(
            sala=_requerido(item, "sala", operacion),
            enemigos=enemigos,
            objetos=objetos,
            trampas=trampas,
        ))
    return resultado

# Prefijo con que se reconoce al cazador, igual que crear_comportamiento
# (en minúsculas y por prefijo, como "guard" o "rastread").
PREFIJO_CAZADOR = "cazad"

def _rango_desde_json(id_ficha, comportamiento, datos):
    """El rango de una ficha de enemigo (FR-009, FR-020).

    Si el comportamiento es cazador, el rango es obligatorio: entero >= 0. Si
    falta, es null o no lo cumple (bool, negativo, decimal, texto), es un
    error de datos que nombra la ficha. A diferencia del costo de una
    salida, null no equivale a un valor por omisión. En los demás
    comportamientos el rango se ignora (queda None).
    """
    if not str(comportamiento).lower().startswith(PREFIJO_CAZADOR):
        return None
    rango = datos.get("rango")
    if rango is None:
        raise DatosInvalidos(
            f"La ficha '{id_ficha}' es de un cazador y no declara su rango "
            "(entero mayor o igual que 0)")
    # DECISIÓN: type(...) is int, igual que en el costo: True y False no son rangos.
    if type(rango) is not int or rango < 0:
        raise DatosInvalidos(
            f"La ficha '{id_ficha}' declara un rango inválido ({rango!r}): debe "
            "ser un entero mayor o igual que 0")
    return rango

def _ficha_desde_json(datos, operacion):
    id_ = _requerido(datos, "id", operacion)
    nombre = _requerido(datos, "nombre", operacion)
    clase = _requerido(datos, "clase", operacion)

    if clase == "enemigo":
        suelta = ListaEnlazada()
        suelta.agregar_todos(datos.get("suelta", ()))
        comportamiento = _requerido(datos, "comportamiento", operacion)
        return FichaEnemigoDTO(
            id=id_, nombre=nombre,
            vida_max=_requerido(datos, "vida_max", operacion),
            ataque=_requerido(datos, "ataque", operacion),
            defensa=_requerido(datos, "defensa", operacion),
            velocidad=_requerido(datos, "velocidad", operacion),
            comportamiento=comportamiento,
            suelta=suelta,
            rango=_rango_desde_json(id_, comportamiento, datos),
        )
    if clase == "trampa":
        return FichaTrampaDTO(
            id=id_, nombre=nombre,
            dano=_requerido(datos, "daño", operacion),
            rearme=datos.get("rearme"),
        )

    if clase not in CLASES_OBJETO:
        raise ErrorDeRed(operacion, f"clase de ficha desconocida '{clase}'")
    peso = _requerido(datos, "peso", operacion)
    valor = _requerido(datos, "valor", operacion)

    if clase == "arma":
        return FichaArmaDTO(
            id=id_, nombre=nombre, peso=peso, valor=valor,
            ataque_bonus=_requerido(datos, "ataque_bonus", operacion))
    if clase == "armadura":
        return FichaArmaduraDTO(
            id=id_, nombre=nombre, peso=peso, valor=valor,
            defensa_bonus=_requerido(datos, "defensa_bonus", operacion))
    if clase == "pocion":
        return FichaPocionDTO(
            id=id_, nombre=nombre, peso=peso, valor=valor,
            cura=datos.get("cura"),
            modificador_velocidad=datos.get("modificador_velocidad"),
            duracion=datos.get("duracion"))
    if clase == "antidoto":
        return FichaAntidotoDTO(id=id_, nombre=nombre, peso=peso, valor=valor)
    if clase == "llave":
        return FichaLlaveDTO(
            id=id_, nombre=nombre, peso=peso, valor=valor,
            abre=_requerido(datos, "abre", operacion))
    if clase == "antorcha":
        return FichaAntorchaDTO(
            id=id_, nombre=nombre, peso=peso, valor=valor,
            duracion=_requerido(datos, "duracion", operacion))
    # Ya solo puede ser "pergamino_retroceso"
    return FichaPergaminoRetrocesoDTO(id=id_, nombre=nombre, peso=peso, valor=valor)


def fichas_desde_json(datos):
    operacion = "descargar fichas del catálogo"
    resultado = ListaEnlazada()
    for item in _requerido(datos, "entidades", operacion):
        resultado.agregar_al_final(_ficha_desde_json(item, operacion))
    return resultado

def version_desde_json(datos, operacion):
    return _requerido(datos, "version", operacion)

def llaves_desde_json(datos):
    """Respuesta de GET /criptas/{id}/llaves (003-resolubilidad, FR-025,
    contracts/datos-llaves.md) -> ListaEnlazada de UbicacionLlaveDTO.

    Reglas (FR-030): la raíz es un objeto con "llaves" de tipo lista; cada
    entrada es un objeto con "id" (texto no vacío), "sala" (entero, no bool)
    y opcionalmente "enemigo" (texto, o null = en el suelo). Los campos extra
    se ignoran y un id repetido es otra ubicación de la misma llave (FR-016).
    Cualquier otra cosa es DatosInvalidos con el índice de la entrada y el
    campo: nunca se descarta una entrada en silencio. Que la sala exista en
    el esqueleto se comprueba al armar el grafo, porque aquí no se conoce.

    DECISIÓN: isinstance(..., dict/list) solo LEE lo que entregó json; no crea
    diccionarios ni listas (igual que el resto de este módulo).
    """
    if not isinstance(datos, dict) or not isinstance(datos.get("llaves"), list):
        raise DatosInvalidos(
            "La ubicación de llaves no es un objeto con el campo 'llaves' de tipo lista")
    resultado = ListaEnlazada()
    indice = 0
    for entrada in datos["llaves"]:
        prefijo = f"La entrada {indice} de la ubicación de llaves"
        if not isinstance(entrada, dict):
            raise DatosInvalidos(f"{prefijo} no es un objeto")
        id_llave = entrada.get("id")
        if type(id_llave) is not str or not id_llave:
            raise DatosInvalidos(f"{prefijo} no trae un 'id' de texto no vacío ({id_llave!r})")
        sala = entrada.get("sala")
        # DECISIÓN: type(...) is int, como en los costos: True y False son
        # int en Python, y un bool en el JSON es un error de datos.
        if type(sala) is not int:
            raise DatosInvalidos(f"{prefijo} ('{id_llave}') no trae una 'sala' entera ({sala!r})")
        enemigo = entrada.get("enemigo")
        if enemigo is not None and type(enemigo) is not str:
            raise DatosInvalidos(
                f"{prefijo} ('{id_llave}') trae un 'enemigo' que no es texto ({enemigo!r})")
        resultado.agregar_al_final(UbicacionLlaveDTO(id=id_llave, sala=sala, enemigo=enemigo))
        indice += 1
    return resultado
