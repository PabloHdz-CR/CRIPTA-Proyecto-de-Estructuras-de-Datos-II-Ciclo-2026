# CRIPTA-Proyecto-de-Estructuras-de-Datos-II-Ciclo-2026

Juego por turnos de exploración de criptas (Estructuras de Datos II, ciclo
2026), con arquitectura Modelo-Vista-Controlador más puertos y adaptadores, y
estructuras de datos propias (sin listas, dict ni ordenamientos de Python en
`cripta/`). Las decisiones de diseño están en `DECISIONES.md` y el uso de
herramientas de IA en `PROMPTS_LLM.md`.

## Requisitos

- Python 3.11 o superior (probado con 3.14 en Windows 11).
- Dependencias: `arcade` y `requests`.

```bash
py -m pip install -r requirements.txt
```

## Cómo correrlo

| Comando | Qué hace |
|---|---|
| `py main.py --offline` | Juega con los datos de `datos_offline/` (sin red). |
| `py main.py` | Juega contra el API real (gasta solicitudes del presupuesto). |
| `py main.py --replay partidas/<cripta>.log` | Reproduce un log en la terminal y verifica que sea fiel. |
| `py main.py --bench` (o `--bench --rapido`) | Mide las estructuras (§5.3). |
| `py main.py --cache-size N` | Cambia el tope de fichas en memoria (25 por defecto). |
| `py pruebas/ejecutar_pruebas.py` | Corre las 37 pruebas sin red. Las `prueba_real_*` usan el API real (gastan presupuesto) y se corren aparte. |
| `py pruebas/prueba_reglas.py` | Verifica las reglas del proyecto sobre `cripta/`. |

En Windows se usa `py`; `python` puede abrir la Microsoft Store.

## Pantallas y controles

**Título.** La bienvenida a la entrada de la cripta. **ENTER** entra al menú; **ESC** sale.

**Menú principal.**

| Tecla | Acción |
|---|---|
| Flecha arriba/abajo | Elegir cripta |
| ENTER | Jugar (o continuar la partida guardada de esa cripta) |
| X | Partida nueva desde cero, aunque haya una guardada |
| N | Escribir tu nombre (ENTER confirma, ESC cancela) |
| Flecha izquierda/derecha | Cambiar la skin del héroe (el tigre es la predeterminada) |
| P | Puntajes y replays |
| B | Benchmark rápido en la ventana |
| ESC | Salir del juego |

**Partida.**

| Tecla | Acción |
|---|---|
| Flechas | Moverse |
| Shift + flecha | Abrir la puerta en esa dirección (la llave no se gasta) |
| Espacio | Esperar |
| R | Recoger del suelo |
| A | Atacar (se elige el enemigo) |
| U / Q / S | Usar / equipar / soltar (se elige el objeto) |
| Tab / Shift + Tab | Bajar / subir en el inventario (da la vuelta en los extremos y sigue la vista ordenada) |
| O | Cambiar la vista del inventario: real → peso → valor → nombre (el orden real no cambia) |
| P | Leer un pergamino: deshace tu última acción (máximo 5) |
| G / C | Guardar / cargar la partida de esa cripta |
| L | Mostrar / ocultar la bitácora completa (últimos 20 mensajes) |
| ESC | Volver al menú (lo no guardado se descarta) |

Al elegir objetivo: flecha arriba/abajo, ENTER confirma y ESC cancela.

**Fin de partida.** Muestra el resultado y el resumen de red y caché. **R** reproduce esa partida; **ENTER** vuelve al menú.

**Puntajes.** Primero las victorias, luego las derrotas; dentro de cada grupo, menos tiempo es mejor. Flecha arriba/abajo elige una partida y **R** la reproduce (las que tienen ▶). **ENTER** vuelve.

**Replay.**

| Tecla | Acción |
|---|---|
| Espacio | Pausa / seguir |
| Flecha derecha / izquierda | Un paso adelante / atrás |
| Flecha arriba / abajo | Más rápido / más lento |
| L | Bitácora completa |
| ESC | Salir del replay |

Al terminar, la pantalla indica si el replay llegó exactamente al mismo final que la partida.

## Archivos que genera el juego

No se suben al repositorio (están en `.gitignore`):

- `guardados/<cripta>.bin`: la partida guardada de cada cripta (formato binario propio, §4.10). Se borra al ganar o morir la partida que lo usó.
- `partidas/<cripta>.log`: el log de la partida en curso; `partidas/historial/`: un log archivado por partida terminada, para el replay.
- `puntajes.jsonl`: la tabla de puntajes.
- `fichas_guardadas/`: copia en disco de las fichas del catálogo, para no volver a pedirlas a la red.

## Créditos de gráficos

- **16x16 DungeonTileset II** de 0x72 (https://0x72.itch.io/dungeontileset-ii), licencia CC0: piso, muros, puertas, las skins del héroe (caballero, caballera, elfa, mago, lagarto, enano), esqueleto, frascos, espada y corazones.
- **8 bit art pack rat monster** de Imogia Games (https://imogiagames.itch.io/8-bit-art-pack-rat-monster), licencia CC BY 4.0: la rata gigante.
- Llave de Kenney (https://kenney.nl), licencia CC0, incluida en arcade.
- El tigre humanoide (skin por defecto del héroe) es pixel art propio del equipo (`cripta/vista/pixelTigre.py`).

Las licencias completas están en `cripta/vista/recursos/*/LICENCIA.txt`.
