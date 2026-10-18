"""ConstructorEstadoVista: arma el EstadoVista (foto de solo lectura, §10.2)
a partir de la Partida real. Es el ÚNICO lugar donde se traducen clases del
modelo a los dataclasses planos de Vista (Vista nunca importa el modelo).

Complejidad de construir(), con e enemigos activos y o objetos del suelo de
la sala actual, i objetos del inventario, f efectos del jugador, 20 mensajes
y k enemigos etiquetados en la partida:
    tiempo  O(e·k + o + i + f + 20)   (cada etiqueta cuesta O(k), ver MapaEtiquetas)
          + O(i log i) si hay vista ordenada (selector de §4.9; i <= inventario_max)
    memoria O(e + o + i + f + 20) para la foto.

DECISIÓN: solo se recorre la SALA ACTUAL. Alternativa descartada: recorrer el
mundo entero en cada turno (O(salas)), que no aporta nada que la Vista pueda
mostrar (§10.2 pide sala actual, salidas, enemigos, objetos, estadísticas,
efectos y 20 mensajes).

DECISIÓN: la foto se COPIA a ListaEnlazadas nuevas en vez de pasar las
estructuras vivas del modelo: la Vista no puede mutar el modelo por error y
lo que dibuja no cambia mientras el modelo sigue procesando eventos. El
costo es el mismo orden que recorrerlas para dibujar.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..modelo.estructuras.listaEnlazada import ListaEnlazada
from ..modelo.nucleo.constantes import COSTO_MOVER
from ..modelo.objetos.inventario import CRITERIOS_ORDEN
from ..modelo.puertos.dto import DIRECCIONES
from ..modelo.reloj.efecto import (
    EfectoAntorcha, EfectoRegeneracion, EfectoVelocidad, EfectoVeneno)
from ..vista.estadoVista import (
    ActorVisible, CriptaVisible, EfectoVisible, EstadoVista, InfoReplay,
    InventarioVisible, JugadorVisible, ObjetoVisible, PuntajeVisible,
    SalaVisible, SalidaVisible, SALIDA_ABIERTA, SALIDA_CERRADA_CON_LLAVE,
    SALIDA_SIN_SALIDA)
from .mapaEtiquetas import MapaEtiquetas

if TYPE_CHECKING:
    from ..modelo.actores.jugador import Jugador
    from ..modelo.mundo.sala import Sala
    from ..modelo.nucleo.partida import Partida
    from ..modelo.nucleo.puntajes import TablaPuntajes
    from ..modelo.objetos.objeto import Objeto
    from ..modelo.puertos.registroAcciones import AlmacenRegistros
    from ..modelo.reloj.efecto import Efecto


class ConstructorEstadoVista:

    def __init__(self, mapa_etiquetas: MapaEtiquetas) -> None:
        # DECISIÓN: el MISMO MapaEtiquetas que usa TraductorComandos (se
        # inyecta): la etiqueta que se dibuja es la que después se resuelve.
        self._etiquetas = mapa_etiquetas

    # ------------------------------------------------------------------
    # Pantalla de juego
    # ------------------------------------------------------------------

    def construir(self, partida: "Partida",
                  criterio_orden: Optional[str] = None,
                  nombre_jugador: Optional[str] = None,
                  replay: Optional[InfoReplay] = None) -> EstadoVista:
        """criterio_orden: None (solo orden real) o uno de CRITERIOS_ORDEN.
        nombre_jugador y replay pasan tal cual: son de la sesión, no del
        modelo (la Partida no sabe cómo se llama el jugador)."""
        jugador = partida.jugador
        sala = partida.mundo.sala(jugador.sala)
        return EstadoVista(
            id_cripta=partida.datos.id,
            version_cripta=partida.datos.version,
            reloj=partida.reloj,
            terminada=partida.terminada(),
            resultado=partida.fin,
            jugador=self._jugador_visible(jugador),
            sala=self._sala_visible(sala),
            efectos=self._efectos_visibles(jugador, partida.reloj),
            inventario=self._inventario_visible(jugador, criterio_orden),
            mensajes=self._mensajes_visibles(partida),
            nombre_jugador=nombre_jugador,
            replay=replay,
        )

    def _jugador_visible(self, jugador: "Jugador") -> JugadorVisible:
        """O(1): ataque y defensa efectivos solo miran el arma y la armadura
        equipadas (Equipo guarda como máximo una de cada)."""
        return JugadorVisible(
            vida=jugador.vida,
            vida_max=jugador.vida_max,
            ataque_efectivo=jugador.ataque_efectivo(),
            defensa_efectiva=jugador.defensa_efectiva(),
            velocidad=jugador.velocidad,
            antorcha_encendida=jugador.antorcha_encendida,
            acciones=jugador.acciones,
            enemigos_derrotados=jugador.enemigos_derrotados,
        )

    def _sala_visible(self, sala: "Sala") -> SalaVisible:
        """O(e·k + o). Solo enemigos ACTIVOS: los dormidos de una sala ya
        visitada no existen para el jugador hasta que se activan (§2.4)."""
        enemigos = ListaEnlazada()
        for enemigo in sala.activos:
            enemigos.agregar_al_final(ActorVisible(
                etiqueta=self._etiquetas.etiqueta_de(enemigo),
                vida=enemigo.vida,
                vida_max=enemigo.vida_max,
            ))
        objetos = ListaEnlazada()
        for objeto in sala.suelo:
            objetos.agregar_al_final(self._objeto_visible(objeto, False))
        return SalaVisible(
            nombre=sala.nombre,
            salidas=self._salidas_visibles(sala),
            enemigos=enemigos,
            objetos=objetos,
        )

    def _salidas_visibles(self, sala: "Sala") -> tuple:
        # DECISIÓN: tupla fija de 4 (N, S, E, O), como Sala.salidas: acceso
        # O(1) por dirección y sin lista nativa intermedia (§7).
        return (self._salida_visible(sala, 0), self._salida_visible(sala, 1),
                self._salida_visible(sala, 2), self._salida_visible(sala, 3))

    def _salida_visible(self, sala: "Sala", indice: int) -> SalidaVisible:
        salida = sala.salidas[indice]
        if salida is None:
            estado = SALIDA_SIN_SALIDA
        elif salida.cerrada:
            estado = SALIDA_CERRADA_CON_LLAVE
        else:
            estado = SALIDA_ABIERTA
        return SalidaVisible(direccion=DIRECCIONES[indice], estado=estado)

    def _efectos_visibles(self, jugador: "Jugador", reloj: int) -> ListaEnlazada:
        """O(f)."""
        efectos = ListaEnlazada()
        for efecto in jugador.efectos:
            efectos.agregar_al_final(EfectoVisible(
                tipo=efecto.TIPO, descripcion=self._descripcion_efecto(efecto, reloj)))
        return efectos

    def _descripcion_efecto(self, efecto: "Efecto", reloj: int) -> str:
        # DECISIÓN: cadena de if por TIPO (no dict tipo -> texto, §7); 4 tipos: O(1).
        restante = self._restante(efecto, reloj)
        if efecto.TIPO == EfectoVeneno.TIPO:
            return f"veneno (próximo pulso en {restante})"
        if efecto.TIPO == EfectoVelocidad.TIPO:
            return f"velocidad {efecto.modificador:+d} ({restante} restantes)"
        if efecto.TIPO == EfectoAntorcha.TIPO:
            # El tiempo es el del reloj virtual, no salas: se traduce a
            # movimientos (cada uno cuesta COSTO_MOVER) para que se entienda.
            return (f"antorcha: quedan {restante} de tiempo "
                    f"(~{restante // COSTO_MOVER} movimientos)")
        if efecto.TIPO == EfectoRegeneracion.TIPO:
            return f"regeneración +{efecto.cantidad}"
        return efecto.TIPO

    @staticmethod
    def _restante(efecto: "Efecto", reloj: int) -> int:
        """Tiempo hasta el evento pendiente del efecto. O(1): el Efecto
        guarda su propio evento (§4.1). Alternativa descartada: buscar el
        evento en la Agenda, O(n) sobre todos los eventos pendientes."""
        if efecto.evento is None:
            return 0
        return max(0, efecto.evento.tiempo - reloj)

    def _inventario_visible(self, jugador: "Jugador",
                            criterio_orden: Optional[str]) -> InventarioVisible:
        """O(i) en orden real; O(i log i) adicional con vista ordenada."""
        inventario = jugador.inventario
        equipo = jugador.equipo
        objetos = ListaEnlazada()
        for objeto in inventario:
            objetos.agregar_al_final(
                self._objeto_visible(objeto, equipo.esta_equipado(objeto)))
        actual = inventario.actual()
        indice_actual = inventario.indice_de(actual) if actual is not None else -1

        vista_ordenada = None
        if criterio_orden in CRITERIOS_ORDEN:
            # DECISIÓN: Inventario.vista_ordenada ordena una lista NUEVA con el
            # selector automático (§4.9): el orden real nunca cambia (§4.5).
            # Alternativa descartada: ordenar el inventario real, que rompería
            # "equipar mueve al frente" y el cursor.
            vista_ordenada = ListaEnlazada()
            for objeto in inventario.vista_ordenada(criterio_orden):
                vista_ordenada.agregar_al_final(
                    self._objeto_visible(objeto, equipo.esta_equipado(objeto)))
        else:
            criterio_orden = None

        return InventarioVisible(
            objetos=objetos,
            indice_actual=indice_actual,
            capacidad=inventario.capacidad,
            cantidad_pergaminos=inventario.cantidad_pergaminos(),
            criterio_orden=criterio_orden,
            vista_ordenada=vista_ordenada,
        )

    @staticmethod
    def _objeto_visible(objeto: "Objeto", equipado: bool) -> ObjetoVisible:
        ficha = objeto.ficha
        return ObjetoVisible(
            id_objeto=objeto.id_instancia,
            nombre=objeto.nombre,
            clase=objeto.clase,
            peso=ficha.peso,
            valor=ficha.valor,
            equipado=equipado,
        )

    @staticmethod
    def _mensajes_visibles(partida: "Partida") -> ListaEnlazada:
        """Copia O(20) = O(1) de la bitácora circular (§4.8), del más antiguo
        al más reciente: la Vista recibe una foto que no cambia después."""
        mensajes = ListaEnlazada()
        for mensaje in partida.bitacora:
            mensajes.agregar_al_final(mensaje)
        return mensajes

    # ------------------------------------------------------------------
    # Menú y puntajes
    # ------------------------------------------------------------------

    @staticmethod
    def criptas_visibles(resumenes: ListaEnlazada) -> ListaEnlazada:
        """resumenes: ListaEnlazada de ResumenCriptaDTO. O(c)."""
        criptas = ListaEnlazada()
        for resumen in resumenes:
            criptas.agregar_al_final(CriptaVisible(
                id=resumen.id, nombre=resumen.nombre,
                salas=resumen.salas, dificultad=resumen.dificultad))
        return criptas

    @staticmethod
    def puntajes_visibles(tabla_puntajes: "TablaPuntajes", criterio: str = "tiempo",
                          almacen_registros: Optional["AlmacenRegistros"] = None
                          ) -> ListaEnlazada:
        """El orden lo decide TablaPuntajes.vista_ordenada con el selector
        automático de §4.9 (inserción si son pocos o casi ordenados, mezcla si
        son muchos): O(p log p) en el peor caso, p = puntajes guardados.
        Con almacen_registros, marca cuáles tienen su log archivado (replay):
        O(1) por puntaje."""
        puntajes = ListaEnlazada()
        for registro in tabla_puntajes.vista_ordenada(criterio):
            puntajes.agregar_al_final(PuntajeVisible(
                nombre=registro.nombre,
                id_cripta=registro.id_cripta,
                version_cripta=registro.version_cripta,
                acciones=registro.acciones,
                enemigos_derrotados=registro.enemigos_derrotados,
                tiempo_final=registro.tiempo_final,
                resultado=registro.resultado,
                id_partida=registro.id_partida,
                tiene_replay=(almacen_registros is not None
                              and almacen_registros.existe_archivado(registro.id_partida)),
            ))
        return puntajes
