# Quickstart: validar Terreno y cazador

**Feature**: `001-terreno-cazador` | **Plan**: [plan.md](plan.md)

Todo se ejecuta desde la raíz del repositorio (la carpeta que contiene `cripta/`
y `pruebas/`), con Python 3.11 o superior y las dependencias de
`requirements.txt`.

## 1. Pruebas automatizadas

```bash
python -m pruebas.ejecutar_pruebas
```

Resultado esperado: todas pasan, incluidas `prueba_reglas` (sin dict, list,
heapq ni sorted en `cripta/`) y las pruebas nuevas de esta capacidad:

| Prueba | Qué demuestra | Requisitos |
|---|---|---|
| `prueba_costo_salidas` | costo por omisión 100; intervalo `max(1, costo*100//velocidad)`; velocidad 1000 y costo 1 dan 1; reescalado al cambiar la velocidad; atacar y esperar no cambian; errante y rastreador eligen igual que antes | FR-001, FR-004 a FR-008, FR-028 |
| `prueba_datos_costo` | costo inválido; caras con costos distintos; una sola cara declarada; ficha de cazador sin rango | FR-003, FR-009, FR-019, FR-020, FR-027 |
| `prueba_cazador` | los 9 escenarios de la Historia 2: ataca, espera sin ruta, espera fuera de rango, rango justo, ruta más barata con más salas, desempate por menor id, puerta que se cierra, salas sin descargar, no abre puertas | FR-010 a FR-016 |
| `prueba_cazador_equivalencia` | ≥ 1000 situaciones al azar (semilla fija) con turnos encadenados: puertas que cambian, el jugador que se mueve, deshacer. La decisión coincide siempre con el oráculo desde cero | FR-017, FR-018, SC-002 |
| `prueba_persistencia_cazador` | guardar y cargar con costos y cazadores, formato v2; un v1 se reporta incompatible; replay idéntico | FR-021, FR-022, SC-005 |
| `prueba_vista_costos` | `SalidaVisible.costo` y `ActorVisible.es_cazador` llegan bien armados a la vista | FR-023, FR-024 |

Cada prueba cita en su docstring los FR que ejerce (definición de hecho de la
constitución).

## 2. Mediciones

```bash
python -m cripta.controlador.bench.benchCazador --rapido   # versión corta
python -m cripta.controlador.bench.benchCazador            # completa
python main.py --bench                                     # todas las mediciones
```

Resultado esperado:

- **Ciclo de eventos**: con 20, 50 y 100 cazadores, el mínimo es < 20 ms en
  la cripta de referencia y en la malla de 1024 salas (FR-025, SC-003).
- **Salas examinadas**: idénticas en la cripta base y en la 10 veces más
  grande, y dentro de la cota de FR-026 (FR-026, SC-004).
- **Comparación**: mapa compartido frente a búsqueda por cazador desde cero,
  con las mismas decisiones. Va a DECISIONES.md.

## 3. Prueba manual (Vista)

1. Usar el paquete sin conexión de prueba con costos y cazadores (lo crea la
   tarea de datos de prueba en `pruebas/datos/terreno_cazador/`, con la
   misma estructura que `datos_offline/`).
2. `python main.py --offline=pruebas/datos/terreno_cazador` y entrar a esa
   cripta.
3. Comprobar:
   - Cada salida de la sala actual muestra su costo, y 100 si no se declaró
     (SC-006).
   - El cazador se reconoce frente a otros enemigos sin depender solo del
     color.
   - Al cruzar una salida de costo alto, los enemigos actúan más veces antes
     de tu siguiente turno.
   - Al cerrar el paso (si una puerta se cierra sola), el cazador se desvía o
     se queda esperando.

## 4. Reproducción

```bash
python main.py --replay partidas/<archivo>.log
```

Una partida jugada en el paso 3 se reproduce sin interacción, con las mismas
acciones y el mismo estado final (SC-005).
