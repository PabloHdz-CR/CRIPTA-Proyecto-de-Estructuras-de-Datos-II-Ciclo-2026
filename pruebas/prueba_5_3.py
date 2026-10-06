import shutil
import tempfile
from pathlib import Path

from cripta.adaptadores.almacenLocalDisco import AlmacenLocalDisco
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.dto import (FichaAntidotoDTO, FichaArmaDTO,
                                       FichaEnemigoDTO, FichaLlaveDTO,
                                       FichaPocionDTO, FichaTrampaDTO)

carpeta = tempfile.mkdtemp(prefix="cripta_test_")
try:
    almacen = AlmacenLocalDisco(carpeta)

    # 1. No existe todavía
    assert almacen.cargar_ficha("itm_daga", "cat-1") is None
    assert not almacen.tiene_ficha("itm_daga", "cat-1")

    # 2. Guardar y recuperar cada clase, con sus campos exactos
    suelta = ListaEnlazada()
    suelta.agregar_todos(["itm_pocion_menor", "itm_oro"])
    rata = FichaEnemigoDTO(id="ent_rata", nombre="Rata gigante", vida_max=12,
                           ataque=5, defensa=1, velocidad=150,
                           comportamiento="rastreador", suelta=suelta)
    daga = FichaArmaDTO(id="itm_daga", nombre="Daga oxidada", peso=2, valor=15,
                        ataque_bonus=3)
    trampa = FichaTrampaDTO(id="trp_dardos", nombre="Dardos", dano=4, rearme=300)
    trampa_sin_rearme = FichaTrampaDTO(id="trp_fuego", nombre="Fuego", dano=6)
    pocion = FichaPocionDTO(id="itm_pocion", nombre="Poción", peso=1, valor=10, cura=8)
    antidoto = FichaAntidotoDTO(id="itm_antidoto", nombre="Antídoto", peso=1, valor=5)
    llave = FichaLlaveDTO(id="itm_llave", nombre="Llave negra", peso=1, valor=0,
                          abre="puerta_salida")

    for ficha in (rata, daga, trampa, trampa_sin_rearme, pocion, antidoto, llave):
        almacen.guardar_ficha(ficha, "cat-1")

    recuperada_rata = almacen.cargar_ficha("ent_rata", "cat-1")
    assert recuperada_rata.vida_max == 12 and recuperada_rata.comportamiento == "rastreador"
    assert recuperada_rata.clase == "enemigo"
    assert list(recuperada_rata.suelta) == ["itm_pocion_menor", "itm_oro"]

    recuperada_daga = almacen.cargar_ficha("itm_daga", "cat-1")
    assert recuperada_daga.ataque_bonus == 3 and recuperada_daga.peso == 2
    assert recuperada_daga.clase == "arma"

    recuperada_trampa = almacen.cargar_ficha("trp_dardos", "cat-1")
    assert recuperada_trampa.dano == 4 and recuperada_trampa.rearme == 300

    recuperada_sin_rearme = almacen.cargar_ficha("trp_fuego", "cat-1")
    assert recuperada_sin_rearme.rearme is None      # el None se conserva, no se pierde

    recuperada_pocion = almacen.cargar_ficha("itm_pocion", "cat-1")
    assert recuperada_pocion.cura == 8 and recuperada_pocion.modificador_velocidad is None

    recuperada_llave = almacen.cargar_ficha("itm_llave", "cat-1")
    assert recuperada_llave.abre == "puerta_salida"

    assert almacen.tiene_ficha("itm_daga", "cat-1")

    # 3. Versión distinta: se trata como "no encontrada", no como error
    assert almacen.cargar_ficha("itm_daga", "cat-2") is None
    assert not almacen.tiene_ficha("itm_daga", "cat-2")

    # 4. Sobrescribir: la versión nueva reemplaza a la vieja
    daga_mejorada = FichaArmaDTO(id="itm_daga", nombre="Daga oxidada", peso=2,
                                 valor=15, ataque_bonus=99)
    almacen.guardar_ficha(daga_mejorada, "cat-2")
    assert almacen.cargar_ficha("itm_daga", "cat-1") is None      # la vieja ya no cuenta
    assert almacen.cargar_ficha("itm_daga", "cat-2").ataque_bonus == 99

    # 5. Sobrevive a "cerrar y volver a abrir" (otro AlmacenLocalDisco, misma carpeta)
    otro = AlmacenLocalDisco(carpeta)
    assert otro.cargar_ficha("itm_daga", "cat-2").ataque_bonus == 99
    assert otro.cargar_ficha("ent_rata", "cat-1").vida_max == 12

    # 6. Un archivo corrupto no hace caer el programa: se trata como "no está"
    ruta_corrupta = Path(carpeta) / "itm_corrupta.json"
    ruta_corrupta.write_text("esto no es json válido {{{", encoding="utf-8")
    assert almacen.cargar_ficha("itm_corrupta", "cat-1") is None

    # 7. Ids con caracteres raros no rompen el nombre de archivo
    rara = FichaAntidotoDTO(id="itm/raro:especial", nombre="Rara", peso=1, valor=1)
    almacen.guardar_ficha(rara, "cat-1")
    assert almacen.cargar_ficha("itm/raro:especial", "cat-1").nombre == "Rara"

    # 8. Una carpeta que no existe se crea sola
    carpeta_nueva = str(Path(carpeta) / "subcarpeta" / "mas_profundo")
    assert not Path(carpeta_nueva).exists()
    AlmacenLocalDisco(carpeta_nueva)
    assert Path(carpeta_nueva).exists()

    print("Sección 5.3 OK")
finally:
    shutil.rmtree(carpeta, ignore_errors=True)