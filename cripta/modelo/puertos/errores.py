class ErrorCripta(Exception):
    """Base de todos los errores propios del proyecto."""


class ErrorDeRed(ErrorCripta):
    def __init__(self, operacion, causa, codigo_http=None):
        self.operacion = operacion
        self.causa = causa
        self.codigo_http = codigo_http
        mensaje = f"Falló la operación '{operacion}': {causa}"
        if codigo_http is not None:
            mensaje += f" (HTTP {codigo_http})"
        super().__init__(mensaje)


class PresupuestoAgotado(ErrorCripta):
    def __init__(self, operacion, usadas, presupuesto):
        self.operacion = operacion
        self.usadas = usadas
        self.presupuesto = presupuesto
        super().__init__(
            f"Presupuesto de solicitudes agotado antes de '{operacion}': "
            f"{usadas} de {presupuesto} usadas."
        )


class VersionIncompatible(ErrorCripta):
    def __init__(self, elemento, esperada, encontrada):
        self.elemento = elemento
        self.esperada = esperada
        self.encontrada = encontrada
        super().__init__(
            f"Versión incompatible de {elemento}: "
            f"se esperaba {esperada} y se encontró {encontrada}."
        )

class LoteInvalido(ErrorCripta):
    def __init__(self, operacion, cantidad, limite):
        self.operacion = operacion
        self.cantidad = cantidad
        self.limite = limite
        super().__init__(
            f"Lote inválido en '{operacion}': {cantidad} elementos "
            f"(debe haber entre 1 y {limite})."
        )