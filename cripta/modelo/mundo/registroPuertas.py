"""RegistroPuertas: versión del estado de las puertas de un Mundo (FR-017,
research R2)."""
from __future__ import annotations


class RegistroPuertas:
    """Contador que avanza cada vez que cambia el estado abierto/cerrado de
    cualquier salida del Mundo. Hay uno por Mundo, compartido por todas sus
    salidas; el *setter* de Salida.cerrada llama a avisar_cambio().

    El mapa de distancias del cazador guarda la versión con la que se
    calculó: si la versión cambió, el mapa ya no vale y se recalcula. Así su
    decisión es la misma que calculando desde cero (FR-017).

    No es estado reversible (principio V): deshacer una acción la
    INCREMENTA en lugar de restaurarla, porque lo único que importa es que
    cambie. Invalidar de más solo cuesta un recálculo y nunca cambia una
    decisión; restaurarla podría dar por bueno un mapa calculado con otras
    puertas.
    """

    def __init__(self) -> None:
        self._version = 0

    @property
    def version(self) -> int:
        """Versión actual: arranca en 0 y solo crece."""
        return self._version

    def avisar_cambio(self) -> None:
        """Una salida cambió de abierta a cerrada o al revés."""
        self._version += 1
