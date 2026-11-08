import json
from pathlib import Path

from . import convertidorJson
from ..modelo.puertos.errores import DatosInvalidos

from ..modelo.puertos.almacenLocal import AlmacenLocal
from ..modelo.puertos.dto import (FichaArmaDTO, FichaArmaduraDTO, FichaAntidotoDTO, FichaAntorchaDTO, FichaEnemigoDTO, FichaLlaveDTO, FichaPergaminoRetrocesoDTO, FichaPocionDTO, FichaTrampaDTO)
from ..modelo.estructuras.listaEnlazada import ListaEnlazada


def _ficha_a_dict(ficha):
    base = {"id": ficha.id, "nombre": ficha.nombre, "clase": ficha.clase}
    if isinstance(ficha, FichaEnemigoDTO):
        suelta = []
        for id_objeto in ficha.suelta:
            suelta.append(id_objeto)
        base.update(vida_max=ficha.vida_max, ataque=ficha.ataque,
                    defensa=ficha.defensa, velocidad=ficha.velocidad,
                    comportamiento=ficha.comportamiento, suelta=suelta,
                    rango=ficha.rango)                 # FR-020: None si no es cazador
    elif isinstance(ficha, FichaTrampaDTO):
        base.update(dano=ficha.dano, rearme=ficha.rearme)
    else:
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
    clase = datos["clase"]

    if clase == "enemigo":
        suelta = ListaEnlazada()
        suelta.agregar_todos(datos.get("suelta", ()))
        return FichaEnemigoDTO(id=datos["id"], nombre=datos["nombre"],vida_max=datos["vida_max"], ataque=datos["ataque"],
                               defensa=datos["defensa"], velocidad=datos["velocidad"],comportamiento=datos["comportamiento"], suelta=suelta,
                               rango=datos.get("rango"))   # FR-020; .get: cachés de antes no lo traen
    if clase == "trampa":
        return FichaTrampaDTO(id=datos["id"], nombre=datos["nombre"], dano=datos["dano"], rearme=datos.get("rearme"))

    peso, valor = datos["peso"], datos["valor"]
    if clase == "arma":
        return FichaArmaDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor, ataque_bonus=datos["ataque_bonus"])

    if clase == "armadura":
        return FichaArmaduraDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor, defensa_bonus=datos["defensa_bonus"])

    if clase == "pocion":
        return FichaPocionDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor,
                              cura=datos.get("cura"), modificador_velocidad=datos.get("modificador_velocidad"), duracion=datos.get("duracion"))
    if clase == "antidoto":
        return FichaAntidotoDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor)

    if clase == "llave":
        return FichaLlaveDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor, abre=datos["abre"])
    if clase == "antorcha":
        return FichaAntorchaDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor, duracion=datos["duracion"])
    if clase == "pergamino_retroceso":
        return FichaPergaminoRetrocesoDTO(id=datos["id"], nombre=datos["nombre"], peso=peso, valor=valor)
    raise ValueError(f"Clase de ficha desconocida al leer de disco: '{clase}'")


def _nombre_de_archivo(id_ficha):
    seguro = ""
    for caracter in id_ficha:
        if caracter.isalnum() or caracter in "-_.":
            seguro += caracter
        else:
            seguro += "_"
    return seguro + ".json"


class AlmacenLocalDisco(AlmacenLocal):

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

    # ------------------------------------------------------------------
    # Ubicación de llaves (003-resolubilidad, contracts/datos-llaves.md)
    # ------------------------------------------------------------------

    def _ruta_llaves(self, id_cripta):
        return self._carpeta / "llaves" / _nombre_de_archivo(str(id_cripta))

    def guardar_llaves(self, id_cripta, version_cripta, ubicaciones):
        """<carpeta>/llaves/<id_cripta>.json con la versión de la cripta y las
        entradas en el mismo formato que la respuesta del API."""
        entradas = []
        for ubicacion in ubicaciones:
            entrada = {"id": ubicacion.id, "sala": ubicacion.sala}
            if ubicacion.enemigo is not None:
                entrada["enemigo"] = ubicacion.enemigo
            entradas.append(entrada)
        ruta = self._ruta_llaves(id_cripta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump({"version_cripta": version_cripta, "llaves": entradas}, archivo,
                      ensure_ascii=False)

    def cargar_llaves(self, id_cripta, version_cripta):
        try:
            with open(self._ruta_llaves(id_cripta), "r", encoding="utf-8") as archivo:
                contenido = json.load(archivo)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if not isinstance(contenido, dict) or contenido.get("version_cripta") != version_cripta:
            return None         # otra versión (p. ej. de la primera parte): no encontrada
        try:
            return convertidorJson.llaves_desde_json(contenido)
        except DatosInvalidos:
            return None         # dañado: se vuelve a pedir, nunca se usa a medias

    def tiene_ficha(self, id_ficha, version_catalogo):
        return self.cargar_ficha(id_ficha, version_catalogo) is not None