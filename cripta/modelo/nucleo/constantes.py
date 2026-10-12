"""Constantes de las reglas del juego (§2). Son reglas fijas del enunciado, no
datos de una cripta: ids, cantidades de salas y presupuestos NUNCA van aquí."""
from __future__ import annotations

COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_ABRIR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25
COSTO_PRIMERA_ACCION_ENEMIGO = 100

ESCALA_VELOCIDAD = 100        # velocidad 100 = ritmo normal
DANO_AZAR_MAX = 4             # daño = max(1, ataque + randint(0, 4) - defensa)

INTERVALO_VENENO = 80
DURACION_VENENO = 400
DANO_VENENO = 1               # SUPUESTO: el enunciado dado no fija el daño por pulso
INTERVALO_REGENERACION = 200
CURA_REGENERACION = 1         # SUPUESTO: igual que el daño del veneno
REARME_TRAMPA = 300           # salvo que la ficha traiga otro valor
VIGENCIA_RASTRO = 400         # un rastro de 400 o más unidades ya no cuenta
MAX_RETROCESO = 5
TAMANO_BITACORA = 20

ID_JUGADOR = "jugador"
ESTADO_VICTORIA = "victoria"
ESTADO_DERROTA = "derrota"


def calcular_intervalo(costo: int, velocidad: int) -> int:
    """Tiempo hasta la siguiente acción: max(1, costo * 100 // velocidad)."""
    return max(1, costo * ESCALA_VELOCIDAD // velocidad)


def reescalar_restante(restante: int, velocidad_anterior: int, velocidad_nueva: int) -> int:
    """Tiempo restante tras un cambio de velocidad (§2.3)."""
    return max(1, restante * velocidad_anterior // velocidad_nueva)