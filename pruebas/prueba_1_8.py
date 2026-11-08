import threading
import time

from cripta.modelo.datos.fuenteAsincrona import FuenteAsincrona
from cripta.modelo.estructuras.listaEnlazada import ListaEnlazada
from cripta.modelo.puertos.errores import ErrorDeRed, LoteInvalido
from cripta.modelo.puertos.fuenteDatos import FuenteDatos


def texto(elementos):
    partes = []
    for elemento in elementos:
        partes.append(str(elemento))
    return ",".join(partes)


def lote_de(cantidad):
    lote = ListaEnlazada()
    for numero in range(1, cantidad + 1):
        lote.agregar_al_final(numero)
    return lote


def uno(numero):
    lote = ListaEnlazada()
    lote.agregar_al_final(numero)
    return lote


def ids_de(textos):
    lote = ListaEnlazada()
    lote.agregar_todos(textos)
    return lote


class FuenteFalsa(FuenteDatos):
    """FuenteDatos de mentira: anota las llamadas y simula demoras y fallos."""

    def __init__(self):
        self.llamadas = []
        self.simultaneas = 0
        self.max_simultaneas = 0
        self.bloqueo = None        # Event: si existe, las llamadas esperan a que se active
        self.demora = 0
        self.empezo = threading.Event()
        self.fallar_con = None     # pedido para el que se lanza ErrorDeRed
        self.explotar_con = None   # pedido para el que se lanza ValueError
        self._cerrojo = threading.Lock()

    def _atender(self, operacion, pedido):
        with self._cerrojo:
            self.simultaneas += 1
            if self.simultaneas > self.max_simultaneas:
                self.max_simultaneas = self.simultaneas
            self.llamadas.append(operacion + ":" + pedido)
        self.empezo.set()
        try:
            if self.bloqueo is not None:
                self.bloqueo.wait(5)
            if self.demora:
                time.sleep(self.demora)
            if self.explotar_con == pedido:
                raise ValueError("boom")
            if self.fallar_con == pedido:
                raise ErrorDeRed(operacion, "falla simulada")
            return operacion + ":" + pedido
        finally:
            with self._cerrojo:
                self.simultaneas -= 1

    def contenido(self, id_cripta, ids_salas):
        return self._atender("contenido", texto(ids_salas))

    def catalogo(self, ids):
        return self._atender("catalogo", texto(ids))

    def esqueleto(self, id_cripta, pagina):
        return self._atender("esqueleto", str(pagina))

    def listar_criptas(self):
        return None

    def datos_generales(self, id_cripta):
        return None

    def llaves(self, id_cripta):
        # 003-resolubilidad (FR-025): esta fuente no usa la ubicación de llaves.
        return ListaEnlazada()

    def version_cripta(self, id_cripta):
        return "v1"

    def version_catalogo(self):
        return "cat-1"

    def solicitudes_realizadas(self):
        return 0

    def presupuesto(self):
        return None

    def reiniciar_conteo(self):
        pass


# 1. Números de envío, resultados y una sola solicitud a la vez
fake = FuenteFalsa()
fake.demora = 0.05
asinc = FuenteAsincrona(fake)
s1 = asinc.enviar_contenido("c1", lote_de(2))
s2 = asinc.enviar_catalogo(ids_de(["a", "b"]))
s3 = asinc.enviar_esqueleto("c1", 2)
assert (s1.numero, s2.numero, s3.numero) == (1, 2, 3)
assert s1.operacion == "contenido" and s3.pedido == 2
s3.esperar()
listas = asinc.recoger_listas()
numeros = []
for solicitud in listas:
    numeros.append(solicitud.numero)
assert numeros == [1, 2, 3]
assert s1.resultado() == "contenido:1,2"
assert s2.resultado() == "catalogo:a,b"
assert s3.resultado() == "esqueleto:2"
assert fake.llamadas == ["contenido:1,2", "catalogo:a,b", "esqueleto:2"]
assert fake.max_simultaneas == 1
assert asinc.sin_recoger() == 0 and asinc.pendientes() == 0
assert asinc.recoger_listas().esta_vacia()      # cada solicitud se entrega una sola vez
asinc.cerrar()

# 2. recoger_listas se detiene en la primera que no terminó
fake = FuenteFalsa()
fake.bloqueo = threading.Event()
asinc = FuenteAsincrona(fake)
a = asinc.enviar_contenido("c", uno(1))
b = asinc.enviar_contenido("c", uno(2))
fake.empezo.wait(2)
assert not a.lista() and not b.lista()
assert asinc.pendientes() == 2
assert asinc.recoger_listas().esta_vacia()
try:
    a.resultado()
    assert False, "debió lanzar RuntimeError"
except RuntimeError:
    pass
assert a.esperar(0.05) is False                 # se agota el tiempo máximo
fake.bloqueo.set()
b.esperar()
listas = asinc.recoger_listas()
assert len(listas) == 2
assert listas.obtener(0) is a and listas.obtener(1) is b
asinc.cerrar()

# 3. Un error no mata al hilo y se relanza en quien pide el resultado
fake = FuenteFalsa()
fake.fallar_con = "1"
asinc = FuenteAsincrona(fake)
mala = asinc.enviar_contenido("c", uno(1))
buena = asinc.enviar_contenido("c", lote_de(2))
buena.esperar()
try:
    mala.resultado()
    assert False, "debió lanzar ErrorDeRed"
except ErrorDeRed as error:
    print("Error esperado:", error)
    assert "falla simulada" in str(error)
assert isinstance(mala.fallo(), ErrorDeRed)
assert buena.fallo() is None
assert buena.resultado() == "contenido:1,2"
assert asinc.activa()
asinc.cerrar()

# 4. Un error inesperado también se convierte en ErrorDeRed
fake = FuenteFalsa()
fake.explotar_con = "1"
asinc = FuenteAsincrona(fake)
rara = asinc.enviar_contenido("c", uno(1))
rara.esperar()
try:
    rara.resultado()
    assert False, "debió lanzar ErrorDeRed"
except ErrorDeRed as error:
    print("Error esperado:", error)
    assert "error inesperado" in str(error)
assert asinc.activa()
asinc.cerrar()

# 5. Un lote inválido falla al instante y no se encola nada
fake = FuenteFalsa()
asinc = FuenteAsincrona(fake)
for tamano in (0, 11):
    try:
        asinc.enviar_contenido("c", lote_de(tamano))
        assert False, "debió lanzar LoteInvalido"
    except LoteInvalido:
        pass
try:
    asinc.enviar_catalogo(lote_de(11))
    assert False, "debió lanzar LoteInvalido"
except LoteInvalido:
    pass
assert asinc.sin_recoger() == 0
assert fake.llamadas == []
asinc.cerrar()

# 6. Copia defensiva: modificar el lote después de enviarlo no afecta el pedido
fake = FuenteFalsa()
fake.bloqueo = threading.Event()
asinc = FuenteAsincrona(fake)
asinc.enviar_contenido("c", uno(1))             # ocupa al hilo de fondo
fake.empezo.wait(2)
lote = lote_de(2)
b = asinc.enviar_contenido("c", lote)
lote.agregar_al_final(99)                       # se modifica DESPUÉS de enviar
fake.bloqueo.set()
b.esperar()
assert b.resultado() == "contenido:1,2"
asinc.cerrar()

# 7. 30 solicitudes seguidas: se atienden todas y en orden de envío
fake = FuenteFalsa()
asinc = FuenteAsincrona(fake)
enviadas = []
esperado = []
for numero in range(1, 31):
    enviadas.append(asinc.enviar_contenido("c", uno(numero)))
    esperado.append("contenido:" + str(numero))
enviadas[29].esperar()
assert fake.llamadas == esperado
assert fake.max_simultaneas == 1
listas = asinc.recoger_listas()
assert len(listas) == 30
for posicion in range(30):
    assert listas.obtener(posicion).numero == posicion + 1
asinc.cerrar()

# 8. cerrar(): termina la solicitud en curso y descarta las pendientes
fake = FuenteFalsa()
fake.demora = 0.3
asinc = FuenteAsincrona(fake)
a = asinc.enviar_contenido("c", uno(1))
fake.empezo.wait(2)                             # A ya está en curso
b = asinc.enviar_contenido("c", uno(2))
c = asinc.enviar_contenido("c", uno(3))
asinc.cerrar(espera_maxima=5)
assert not asinc.activa()
assert a.lista() and a.resultado() == "contenido:1"
for descartada in (b, c):
    assert descartada.lista()
    try:
        descartada.resultado()
        assert False, "debió lanzar ErrorDeRed"
    except ErrorDeRed as error:
        assert "cerr" in str(error)
assert fake.llamadas == ["contenido:1"]         # B y C nunca llegaron a la fuente
try:
    asinc.enviar_catalogo(ids_de(["x"]))
    assert False, "debió lanzar ErrorDeRed"
except ErrorDeRed as error:
    print("Error esperado:", error)
asinc.cerrar()                                  # cerrar dos veces es inofensivo

print("Sección 1.8 OK")