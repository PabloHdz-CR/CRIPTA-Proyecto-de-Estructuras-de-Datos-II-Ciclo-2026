"""Tabla de puntajes local, persistida en disco (§2.12).

Un archivo de texto de solo anexado, un registro JSON por línea (JSON Lines):
agregar() nunca relee ni reescribe lo que ya había, solo añade una línea.
cargar() reconstruye la TablaPuntajes completa leyendo todas las líneas.

Igual que AlmacenLocalDisco con las fichas: el único lugar de este archivo
donde se arma un dict es para hablar con el módulo json de la biblioteca
estándar (empaquetar un RegistroPuntaje para escribirlo a disco), no para
sustituir ninguna estructura propia del programa.
"""
import json
from pathlib import Path

from ..modelo.nucleo.puntajes import RegistroPuntaje, TablaPuntajes
from ..modelo.puertos.almacenPuntajes import AlmacenPuntajes


class PuntajesArchivo(AlmacenPuntajes):

    def __init__(self, ruta):
        self._ruta = Path(ruta)

    def agregar(self, registro: RegistroPuntaje) -> None:
        linea = {
            "nombre": registro.nombre,
            "id_cripta": registro.id_cripta,
            "version_cripta": registro.version_cripta,
            "acciones": registro.acciones,
            "enemigos_derrotados": registro.enemigos_derrotados,
            "tiempo_final": registro.tiempo_final,
            "resultado": registro.resultado,
        }
        with open(self._ruta, "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(linea, ensure_ascii=False))
            archivo.write("\n")

    def cargar(self) -> TablaPuntajes:
        """Lee todos los puntajes guardados. Una línea corrupta o de otro
        formato se ignora (no hace caer el programa), igual que un archivo
        de ficha corrupto en AlmacenLocalDisco."""
        tabla = TablaPuntajes()
        if not self._ruta.exists():
            return tabla
        with open(self._ruta, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    datos = json.loads(linea)
                    registro = RegistroPuntaje(
                        nombre=datos["nombre"],
                        id_cripta=datos["id_cripta"],
                        version_cripta=datos["version_cripta"],
                        acciones=datos["acciones"],
                        enemigos_derrotados=datos["enemigos_derrotados"],
                        tiempo_final=datos["tiempo_final"],
                        resultado=datos["resultado"],
                    )
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
                tabla.agregar(registro)
        return tabla