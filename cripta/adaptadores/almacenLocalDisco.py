"""Adaptador de persistencia: implementa AlmacenLocal guardando fichas como
archivos JSON en una carpeta local.

Cada ficha se guarda en su propio archivo: <carpeta>/<id_ficha>.json, con la
forma {"version_catalogo": "...", "ficha": {...}}. Un archivo por ficha (en
vez de un único archivo grande) permite leer y escribir una ficha sin tocar
las demás, y sobrevive al cierre del programa porque es disco, no memoria.

Convierte DTO <-> JSON con las mismas reglas de clase que convertidorJson.py,
así el formato en disco es consistente con el que llega por red: la caché no
debe notar la diferencia.
"""
import json
from pathlib import Path

from ..modelo.puertos.almacenLocal import AlmacenLocal
from ..modelo.puertos.dto import (FichaArmaDTO, FichaArmaduraDTO,
                                   FichaAntidotoDTO, FichaAntorchaDTO,
                                   FichaEnemigoDTO, FichaLlaveDTO,
                                   FichaPergaminoRetrocesoDTO, FichaPocionDTO,
                                   FichaTrampaDTO)
from ..modelo.estructuras.listaEnlazada import ListaEnlazada


def _ficha_a_dict(ficha):
    """Convierte una ficha (subclase de FichaDTO) a un diccionario plano, listo
    para json.dump. Es el único lugar de este archivo donde se arma un dict y
    una lista de Python, porque es la forma natural de hablar con el módulo
    json de la biblioteca estándar (igual que clienteHttp con requests): no
    sustituye ninguna estructura propia del programa, solo empaqueta para
    escribir a disco."""
    base = {"id": ficha.id, "nombre": ficha.nombre, "clase": ficha.clase}
    if isinstance(ficha, FichaEnemigoDTO):
        suelta = []
        for id_objeto in ficha.suelta:
            suelta.append(id_objeto)
        base.update(vida_max=ficha.vida_max, ataque=ficha.ataque,
                    defensa=ficha.defensa, velocidad=ficha.velocidad,
                    comportamiento=ficha.comportamiento, suelta=suelta)
    elif isinstance(ficha, FichaTrampaDTO):
        base.update(dano=ficha.dano, rearme=ficha.rearme)
    else:   # toda subclase de FichaObjetoDTO comparte peso y valor
        base.update(peso=ficha.peso, valor=ficha.valor)
        if isinstance(ficha, FichaArmaDTO):
            base["ataque_bonus"] = ficha.ataque_bonus
        elif isinstance(ficha, FichaArmaduraDTO):
            base["defensa_bonus"] = ficha.defensa_bonus
        elif isinstance(ficha, FichaPocionDTO):
            base.update(cura=ficha.cura, modificador_velocidad=ficha.modificador_velocidad,
                        duracion=ficha.duracion)
        elif isinstance(ficha, FichaLlaveDTO):
            base["abre"] = ficha.abre
        elif isinstance(ficha, FichaAntorchaDTO):
            base["duracion"] = ficha.duracion
        elif isinstance(ficha, (FichaAntidotoDTO, FichaPergaminoRetrocesoDTO)):
            pass
        else:
            raise ValueError(f"No sé cómo guardar una ficha de tipo {type(ficha).__name__}")
    return base


def _dict_a_ficha(datos):
    """El inverso de _ficha_a_dict. Reutiliza la lógica de clase de dto.py por
    if/elif (§7: nada de dict como tabla de búsqueda)."""
    clase = datos["clase"]
    if clase == "enemigo":
        suelta = ListaEnlazada()
        suelta.agregar_todos(datos.get("suelta", ()))
        return FichaEnemigoDTO(id=datos["id"], nombre=datos["nombre"],
                               vida_max=datos["vida_max"], ataque=datos["ataque"],
                               defensa=datos["defensa"], velocidad=datos["velocidad"],
                               comportamiento=datos["comportamiento"], suelta=suelta)
    if clase == "trampa":
        return FichaTrampaDTO(id=datos["id"], nombre=datos["nombre"],
                              dano=datos["dano"], rearme=datos.get("rearme"))
    peso, valor = datos["peso"], datos["valor"]
    if clase == "arma":
        return FichaArmaDTO(id=datos["id"], nombre=datos["nombre"], peso=peso,
                            valor=valor, ataque_bonus=datos["ataque_bonus"])
    if clase == "armadura":
        return FichaArmaduraDTO(id=datos["id"], nombre=datos["nombre"], peso=peso,
                                valor=valor, defensa_bonus=datos["defensa_bonus"])
    if clase == "pocion":
        return FichaPocionDTO(id=datos["id"], nombre=datos["nombre"], peso=peso,
                              valor=valor, cura=datos.get("cura"),
                              modificador_velocidad=datos.get("modificador_velocidad"),
                              duracion=datos.get("duracion"))
    if clase == "antidoto":
        return FichaAntidotoDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor)
    if clase == "llave":
        return FichaLlaveDTO(id=datos["id"], nombre=datos["nombre"], peso=peso,
                             valor=valor, abre=datos["abre"])
    if clase == "antorcha":
        return FichaAntorchaDTO(id=datos["id"], nombre=datos["nombre"], peso=peso,
                                valor=valor, duracion=datos["duracion"])
    if clase == "pergamino_retroceso":
        return FichaPergaminoRetrocesoDTO(id=datos["id"], nombre=datos["nombre"],
                                          peso=peso, valor=valor)
    raise ValueError(f"Clase de ficha desconocida al leer de disco: '{clase}'")


def _nombre_de_archivo(id_ficha):
    """Un id de catálogo puede traer cualquier carácter en teoría; se reemplazan
    los que no son seguros en un nombre de archivo, para no depender de qué
    sistema operativo lo ejecuta."""
    seguro = ""
    for caracter in id_ficha:
        if caracter.isalnum() or caracter in "-_.":
            seguro += caracter
        else:
            seguro += "_"
    return seguro + ".json"


class AlmacenLocalDisco(AlmacenLocal):
    """Guarda fichas como archivos JSON bajo una carpeta. Crea la carpeta si no
    existe. Un archivo que no se puede leer (corrupto, de otro formato) se
    trata como si la ficha no existiera, en vez de hacer fallar al programa."""

    def __init__(self, carpeta):
        self._carpeta = Path(carpeta)
        self._carpeta.mkdir(parents=True, exist_ok=True)

    def guardar_ficha(self, ficha, version_catalogo):
        ruta = self._carpeta / _nombre_de_archivo(ficha.id)
        contenido = {"version_catalogo": version_catalogo, "ficha": _ficha_a_dict(ficha)}
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(contenido, archivo, ensure_ascii=False)

    def cargar_ficha(self, id_ficha, version_catalogo):
        ruta = self._carpeta / _nombre_de_archivo(id_ficha)
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = json.load(archivo)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if contenido.get("version_catalogo") != version_catalogo:
            return None         # versión vieja: se trata como "no encontrada" (§4.4)
        try:
            return _dict_a_ficha(contenido["ficha"])
        except (KeyError, ValueError):
            return None         # archivo corrupto o de otro formato: no se cae el programa

    def tiene_ficha(self, id_ficha, version_catalogo):
        return self.cargar_ficha(id_ficha, version_catalogo) is not None