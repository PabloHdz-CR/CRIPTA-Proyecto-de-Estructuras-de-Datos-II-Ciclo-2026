# Contrato de la Vista: mapa conocido, «ir a» y motivo de detención

La Vista sigue sin conocer el Modelo (principio III): recibe solo los DTOs de
[data-model.md](../data-model.md#dtos-de-la-vista-vistaestadovistapy-se-amplían).

## Teclas de la partida

| Tecla | Contexto | Comando | Notas |
|---|---|---|---|
| **M** | partida | `alternar_mapa` (sesión) | abre o cierra el panel del mapa conocido; no consume tiempo ni va al log (FR-016, FR-017) |
| ↑ / ↓ | panel abierto | — (local) | mueven el cursor entre las salas **exploradas**; las avistadas se saltan (FR-035) |
| RePág / AvPág | panel abierto | — (local) | desplazan el panel, como el de V (D80) |
| **Enter** | panel abierto | `ir_a <id>` | viaja a la sala bajo el cursor y cierra el panel (FR-035) |
| **I** | viaje en curso | `interrumpir` | detiene el viaje (FR-028); fuera de un viaje no hace nada |
| **P** | viaje en curso | `pergamino` | detiene el viaje y revierte solo el último paso (FR-029) |
| **H** | — | — | reservada para la feature 004 (historia) |

Con el panel abierto, las flechas no mueven al jugador. Con un viaje en curso,
solo los comandos que **cambian la partida** (las teclas de acción, **G**
guardar, **C** cargar y ESC salir) detienen el viaje con el motivo
"interrumpido" y luego se procesan; los de **presentación** (**M**, Tab, **O**,
**V** y **L**) no lo detienen (research R6).

## Panel del mapa conocido

```text
Mapa conocido — 12 exploradas, 5 avistadas
> 3  Antesala                 (actual)
      N → 7   costo 100   abierta
      E → 4   costo 30    no observada
  4  Pasillo de huesos
      O → 3   costo 30    cerrada
  7  ?                        (avistada)
```

- Salas ordenadas por id numérico; salidas en N, S, E, O (FR-016).
- Una avistada muestra solo su id y la marca "(avistada)"; nunca nombre ni
  salidas (FR-002, FR-014).
- Estado de cada salida: el recordado (`abierta`, `cerrada`, `no observada`),
  nunca el real (FR-016).
- Si las filas no caben, se parten y desplazan con la misma función pura de
  la Vista que el reporte de V (`partirLineas`, D80).

## Viaje y motivo de detención

- Mientras hay viaje, el HUD muestra `Viajando a <id> <nombre> — paso <n> (I para detener)` desde `EstadoVista.viaje`.
- Al detenerse, el Controlador envía `mostrar_mensajes` con
  `Viaje detenido: <motivo>.`, y el mensaje queda en la bitácora (FR-025).
  Motivos: llegada, enemigos en la sala, daño recibido, sin ruta conocida,
  partida terminada, pergamino de retroceso, interrumpido.
- Un rechazo de la orden llega por `mostrar_error` con el texto de FR-018.

## Sala actual

`SalidaVisible.estado` de la sala actual se arma desde `recordada` (igual al
real, porque la sala del jugador siempre está observada). La Vista no recibe
ningún dato de salas desconocidas ni el nombre o las salidas de salas
avistadas (FR-014, SC-002).
