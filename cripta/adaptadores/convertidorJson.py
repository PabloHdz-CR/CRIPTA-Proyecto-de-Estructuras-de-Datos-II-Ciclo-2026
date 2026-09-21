from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.puertos.errores import ErrorDeRed
from ..modelo.puertos.dto import (
    DIRECCIONES,
    ResumenCriptaDTO, JugadorDTO, DatosCriptaDTO,
    SalidaDTO, SalaDTO, PaginaSalasDTO,
    EnemigoInstanciaDTO, TrampaInstanciaDTO, ContenidoSalaDTO,
    FichaEnemigoDTO, FichaTrampaDTO, FichaArmaDTO, FichaArmaduraDTO,
    FichaPocionDTO, FichaAntidotoDTO, FichaLlaveDTO, FichaAntorchaDTO,
    FichaPergaminoRetrocesoDTO,
)

# Clases de catálogo que son objetos (comparten peso y valor).
CLASES_OBJETO = ("arma", "armadura", "pocion", "antidoto", "llave",
                 "antorcha", "pergamino_retroceso")


def _requerido(datos, campo, operacion):
    """Devuelve datos[campo]. Si falta, lanza ErrorDeRed con contexto."""
    if campo not in datos:
        raise ErrorDeRed(operacion, f"la respuesta no trae el campo '{campo}'")
    return datos[campo]


# ---------------------------------------------------------------------------
# Lista de criptas y datos generales
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Esqueleto
# ---------------------------------------------------------------------------

def _salida_desde_json(direccion, datos, operacion):
    return SalidaDTO(
        direccion=direccion,
        sala=_requerido(datos, "sala", operacion),
        cerrada=bool(datos.get("cerrada", False)),
        llave=datos.get("llave"),
        cierre_automatico=datos.get("cierre_automatico"),
    )


def _sala_desde_json(datos, operacion):
    salidas_json = _requerido(datos, "salidas", operacion)
    # Rechazar direcciones que no conocemos, en lugar de ignorarlas.
    for clave in salidas_json:
        if clave not in DIRECCIONES:
            raise ErrorDeRed(operacion, f"dirección desconocida '{clave}'")
    # Se recorren en el orden fijo N, S, E, O, sin importar el del JSON.
    salidas = ListaEnlazada()
    for direccion in DIRECCIONES:
        if direccion in salidas_json:
            salidas.agregar_al_final(
                _salida_desde_json(direccion, salidas_json[direccion], operacion))
    return SalaDTO(
        id=_requerido(datos, "id", operacion),
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


# ---------------------------------------------------------------------------
# Contenido de las salas
# ---------------------------------------------------------------------------

def contenido_desde_json(datos):
    """Devuelve una ListaEnlazada de ContenidoSalaDTO."""
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


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

def _ficha_desde_json(datos, operacion):
    id_ = _requerido(datos, "id", operacion)
    nombre = _requerido(datos, "nombre", operacion)
    clase = _requerido(datos, "clase", operacion)

    # Se usa if/elif y no un diccionario de funciones, porque §7 prohíbe
    # usar dict como tabla de búsqueda.
    if clase == "enemigo":
        suelta = ListaEnlazada()
        suelta.agregar_todos(datos.get("suelta", ()))
        return FichaEnemigoDTO(
            id=id_, nombre=nombre,
            vida_max=_requerido(datos, "vida_max", operacion),
            ataque=_requerido(datos, "ataque", operacion),
            defensa=_requerido(datos, "defensa", operacion),
            velocidad=_requerido(datos, "velocidad", operacion),
            comportamiento=_requerido(datos, "comportamiento", operacion),
            suelta=suelta,
        )
    if clase == "trampa":
        return FichaTrampaDTO(
            id=id_, nombre=nombre,
            dano=_requerido(datos, "daño", operacion),
            rearme=datos.get("rearme"),
        )

    if clase not in CLASES_OBJETO:
        raise ErrorDeRed(operacion, f"clase de ficha desconocida '{clase}'")
    # Desde aquí todas son objetos: comparten peso y valor.
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
    """Devuelve una ListaEnlazada de fichas (subclases de FichaDTO)."""
    operacion = "descargar fichas del catálogo"
    resultado = ListaEnlazada()
    for item in _requerido(datos, "entidades", operacion):
        resultado.agregar_al_final(_ficha_desde_json(item, operacion))
    return resultado


# ---------------------------------------------------------------------------
# Versiones
# ---------------------------------------------------------------------------

def version_desde_json(datos, operacion):
    """Sirve para las dos consultas de versión (cripta y catálogo)."""
    return _requerido(datos, "version", operacion)