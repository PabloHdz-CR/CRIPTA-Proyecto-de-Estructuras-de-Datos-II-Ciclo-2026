# Quickstart: validar niebla de guerra e «ir a»

**Feature**: `002-niebla-guerra` | **Plan**: [plan.md](plan.md)

Guía para comprobar de punta a punta que la capacidad funciona. No contiene
código de implementación; los detalles están en [data-model.md](data-model.md)
y [contracts/](contracts/).

## Requisitos

- Rama `002-niebla-guerra`, Python 3.11 o superior (`py`), dependencias de
  `requirements.txt`.
- `datos_offline/` con las criptas de la Parte II (cripta-02 a cripta-06).

## 1. Suite automática

```text
py pruebas/ejecutar_pruebas.py
```

Todas en verde, incluidas las nuevas de esta capacidad:

| Prueba | Qué comprueba | Requisitos |
|---|---|---|
| `prueba_niebla_conocimiento` | estados explorada/avistada/desconocida al iniciar, al entrar y al volver | FR-001 a FR-004; US1 1–3 |
| `prueba_niebla_puertas` | observación al entrar, al cambiar con el jugador presente, recuerdo desactualizado | FR-005 a FR-007; US2 1–3 |
| `prueba_niebla_antorcha` | vecinas exploradas sin contenido, sin activar enemigos ni trampas; caras "no observada" | FR-008, FR-009; US4 1–4 |
| `prueba_ir_a` | rechazos, ruta, desempates (incluido 9 frente a 10), puerta recordada abierta, enemigos dormidos, daño y veneno, llegada, log | FR-018 a FR-026, FR-030; US3 1–11 |
| `prueba_ir_a_equivalencia` | primer paso idéntico al del oráculo Bellman-Ford en ≥ 1000 pares | FR-020, FR-021; SC-006 |
| `prueba_niebla_retroceso` | pergamino sobre entrada con antorcha; pergamino con viaje en curso; 1000 secuencias aplicar/revertir | FR-010, FR-011, FR-028, FR-029; US5 1–2; SC-003 |
| `prueba_persistencia_niebla` | guardar y cargar conserva el conocimiento; formato 2 incompatible | FR-012, FR-013; US5 3–4 |
| `prueba_replay_ir_a` | comentario `# IR_A`, movimientos individuales, mismo estado final en 20 partidas | FR-026, FR-027; US3 10, US5 5; SC-007 |
| `prueba_vista_mapa` | panel M, cursor solo en exploradas, Enter, I, nada desconocido en los DTOs | FR-014 a FR-017, FR-025, FR-035; US1 4–5; SC-002 |
| `prueba_rendimiento_ir_a` | paso de «ir a» < 5 ms con el mapa completo de la cripta de referencia | FR-031; SC-004 |
| `prueba_conteo_niebla` | consulta y exploración no crecen con el mapa conocido; registro proporcional a lo revelado | FR-032, FR-033; SC-005 |

`prueba_reglas` sigue en verde: sin dict, set, list, heapq, bisect,
collections ni bibliotecas de grafos en `cripta/`.

## 2. Mediciones

```text
py main.py --bench --rapido
```

La sección de niebla (`benchNiebla`, research R11) reporta: peor paso de «ir a»
en la cripta de referencia (< 5 ms) y en la malla de 1024 salas, con la
alternativa hacia atrás al lado; consultas y exploración con mapas de 25 a
1200 conocidas (crecimiento ≤ 1,5 al multiplicar por 4) frente a la búsqueda
lineal y la inserción ordenada; registros del Diario por entrada con
antorcha; tiempo de armar el panel. Las cifras van a DECISIONES.md.

## 3. A mano, en la ventana

```text
py main.py --offline
```

1. Elegir una cripta. Pulsar **M**: aparece solo la sala inicial (explorada)
   y sus destinos como avistados, sin nombre.
2. Moverse dos salas y pulsar **M**: las salas visitadas figuran exploradas,
   con salidas, costos y estado recordado.
3. Con el panel abierto, mover el cursor con ↑/↓ (salta las avistadas) y
   pulsar **Enter** sobre la sala inicial: el jugador vuelve paso a paso y la
   bitácora dice "Viaje detenido: llegada.".
4. Ordenar otro viaje largo y pulsar **P** a mitad de camino: el viaje se
   detiene y el jugador retrocede solo un paso.
5. Ordenar otro viaje y pulsar **I**: se detiene con "interrumpido".
6. Encender una antorcha y entrar a una sala: en **M** aparecen sus vecinas
   exploradas, con sus salidas "no observada".
7. Guardar con **G**, salir, continuar la partida y abrir **M**: el mapa es el
   mismo.
8. Revisar `partidas/<cripta>.log`: hay una línea `# IR_A <id>` antes de los
   `MOVER` de cada viaje, y `py main.py --replay partidas/<cripta>.log`
   reproduce la partida con el mismo final.

## 4. Archivo de formato anterior

Con un guardado de la versión 2 (fixture de `generar_guardado_formato_anterior.py`
adaptado a la versión 2), **C** o "continuar" muestran "Versión incompatible
de formato de archivo de partida: se esperaba 3 y se encontró 2." y la
partida no se carga.
