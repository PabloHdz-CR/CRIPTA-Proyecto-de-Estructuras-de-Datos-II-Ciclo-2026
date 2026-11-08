"""verificar_cripta(servicio): la verificación de la cripta ya iniciada en el
servicio de datos (003-resolubilidad, research.md R6).

La comparten el juego (ControladorJuego.preparar_nueva), --verificar
(ModoVerificar) y las pruebas. Pide la ubicación de llaves al servicio
(caché por versión, presupuesto) y verifica con el esqueleto y los datos
generales que el servicio ya tiene (FR-017: sin contenido ni catálogo).

Cualquier ErrorCripta (red, presupuesto agotado, datos inválidos o ausentes)
da un resultado NO_VERIFICADA con el mensaje: nunca NO_RESOLUBLE (FR-031).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..estructuras.listaEnlazada import ListaEnlazada
from ..puertos.errores import ErrorCripta
from .resultadoResolubilidad import ResultadoResolubilidad, no_verificada
from .verificadorResolubilidad import verificar_resolubilidad

if TYPE_CHECKING:
    from ..datos.servicioDatos import ServicioDatos


def verificar_cripta(servicio: "ServicioDatos") -> ResultadoResolubilidad:
    """Requiere que servicio.iniciar_cripta() ya se haya llamado."""
    datos = servicio.datos_cripta()
    try:
        ubicaciones = servicio.ubicacion_llaves()
        salas = ListaEnlazada()
        for entrada in servicio.esqueleto():
            salas.agregar_al_final(entrada.sala)
        return verificar_resolubilidad(datos, salas, ubicaciones)
    except ErrorCripta as error:
        return no_verificada(datos.id, datos.version, datos.llave_salida,
                             datos.sala_salida, str(error))
