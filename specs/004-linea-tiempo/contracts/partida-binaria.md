# Contrato: archivo de partida, formato 4 (004)

`FORMATO_VERSION = 4`. Todo lo del formato 3 (feature 002) sigue igual y en el
mismo orden, salvo que la **sección de la línea se escribe antes del índice de
salas**: el índice sigue siendo lo último del archivo, así `cargar_sala` lee
solo el encabezado, el índice y su sala, sin pasar por la línea (análisis F1).

```text
encabezado fijo           magic, version_formato (4), offset_indice
encabezado lógico         como el formato 3
con_linea                 booleano (verdadero en un guardado, falso en un punto de control)
jugador, salas, eventos   como el formato 3
[si con_linea] sección de la línea:
  k                       entero   (acciones por bloque)
  acciones                entero   (n, acciones que siguen existiendo)
  cantidad_contenidos     entero
    por contenido: id_sala (entero) + contenido inicial de la sala tal como lo
    dio el servicio: sala (entero), enemigos (cantidad + instancia texto, tipo
    texto, vida entero opcional), objetos (cantidad + id de ficha texto),
    trampas (cantidad + instancia texto, tipo texto)
  cantidad_bloques        entero
    por bloque:
      primera_accion      entero
      tiempo_inicio       entero
      longitud            entero   + punto de control (bytes crudos, con_linea falso)
      cantidad_entradas   entero
        por entrada: tipo (texto "A" o "P")
          "A": texto de la acción (Accion.texto()) + tiempo_decision (entero)
          "P": tiempo (entero), inventario (cantidad + id_objeto, id_ficha, equipado),
               pergaminos en el suelo (cantidad + id_sala, id_objeto, id_ficha),
               estado del random.Random (como el encabezado lógico),
               secuencia_agenda (entero), siguiente_id_objeto (entero)
índice de salas           como el formato 3 (lo último del archivo)
```

- **Bandera `con_linea`** (análisis F3): un punto de control tiene la misma
  versión 4 que un guardado, pero `con_linea` en falso y sin la sección de la
  línea; `desde_bytes` la usa para saber si debe leer la sección. Un punto de
  control nunca guarda la línea dentro de sí mismo.
- Cargar reconstruye la línea entera y la conecta a la partida; las consultas
  dan lo mismo que antes de guardar (FR-009).
- Así quedó en el código (T026, T038): las entradas "P" guardan también el
  estado del azar, la secuencia de la agenda y el próximo id de objeto, los
  tres campos que T021 agregó a `AjustePergamino` (el Diario no los revierte y
  sin ellos re-simular después de un pergamino daría otros sorteos e ids).
  Las acciones se leen con `accion_desde_texto` de `registroArchivo.py`, ahora
  pública. `a_bytes(partida, con_linea)`: `guardar` pasa `con_linea=True` y un
  punto de control usa el valor por omisión, falso.
- Un archivo de versión 3 o anterior: `VersionIncompatible` con la versión
  encontrada y la esperada; no se carga (FR-010).
- `cargar_sala` (carga parcial de §4.10 de la primera parte) sigue leyendo solo
  el encabezado fijo, el índice y la sala pedida; la cantidad de bytes que lee
  no depende del tamaño de la línea (prueba en T025).
