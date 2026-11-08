# Contrato: línea de comandos

**FR**: FR-018 a FR-024, FR-031, FR-032

## Banderas nuevas

| Bandera | Efecto |
|---|---|
| `--verificar ID` | Solo verifica la cripta `ID`: imprime el reporte y sale. No importa la Vista, no crea partida, log ni puntaje (FR-022, FR-023). Se combina con `--offline[=CARPETA]` |
| `--forzar` | En el juego interactivo, una cripta NO_RESOLUBLE o NO_VERIFICADA muestra su reporte y permite iniciar igual (FR-020, FR-031). No tiene efecto con `--verificar`, `--replay` ni `--bench` |

```text
python main.py --verificar ID [--offline[=CARPETA]]
python main.py [--offline] [--forzar] [--cache-size N]
```

## Códigos de salida de `--verificar` (FR-024)

| Código | Caso |
|---|---|
| 0 | RESOLUBLE |
| 1 | NO_RESOLUBLE |
| 2 | NO_VERIFICADA: error de red o de datos, presupuesto agotado o falta de datos sin conexión |

`--verificar` sin un ID termina con 2 y un mensaje de uso. Estos códigos son
propios de `--verificar`; los de `--replay` no cambian (en `--replay`, 1
significa que la reproducción falló).

## Salida por terminal

Las líneas del reporte de [reporte.md](reporte.md), una por línea, y al final
el resumen de red habitual (solicitudes usadas sobre el presupuesto).

## `--bench`

`--bench` agrega las tablas de `benchResolubilidad` (research.md R11):

1. Cripta de referencia: salas, salidas, llaves, tiempo mínimo en ms, y
   PASA/FALLA contra 200 ms (FR-032, SC-002). Si la cripta no tiene
   `llaves.json`, la fila dice **SIN DATOS** y el resultado no es PASA.
2. Cadenas de 100, 200 y 400 llaves (resoluble, con ciclo y **bloqueada**,
   donde cada llave está detrás de su propia puerta y la fase 2 recorre la
   cadena entera, FR-034; en esa variante el cociente de la ingenua no se
   compara porque comparte la fase 2): tiempo
   (informativo) y salidas examinadas de la verificación y de la alternativa
   ingenua; cociente de **salidas examinadas** al duplicar, con PASA/FALLA
   contra ≤ 2,5 y ≥ 3,5 (SC-003); y "mismo reporte: sí/no" (FR-035).
