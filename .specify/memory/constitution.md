# Constitución de Cripta

## Core Principles

### I. Estructuras de datos propias (NO NEGOCIABLE)
Las estructuras de los problemas evaluados se implementan a mano en el
repositorio. Está prohibido usar dict o set como índice, caché o tabla de
búsqueda, y las implementaciones equivalentes de bibliotecas: heapq, bisect,
collections (deque, OrderedDict, defaultdict, Counter), networkx y cualquier
biblioteca de grafos o búsqueda de rutas. list solo se admite como
almacenamiento contiguo de bajo nivel, y los diccionarios de respuesta.json()
solo para leer JSON. Los ordenamientos evaluados no usan list.sort() ni sorted().

### II. Determinismo
La misma cripta, la misma semilla y las mismas acciones producen exactamente la
misma partida. Nunca se usa la hora del sistema ni el orden de llegada de
respuestas HTTP para decidir resultados. Toda aleatoriedad usa una instancia
propia de random.Random(semilla), nunca el generador global.

### III. Arquitectura MVC con puertos y adaptadores
El Controlador es el único orquestador. El Modelo desconoce HTTP, archivos y la
interfaz. La Vista es pasiva, está hecha con arcade y solo conoce DTOs
inmutables, nunca el Modelo. El acceso a red y disco está detrás de puertos con
adaptadores intercambiables (--offline). Los modos --replay, --bench y
--verificar no instancian la Vista.

### IV. Sin datos de criptas concretas y respeto del presupuesto de red
Ningún id, cantidad de salas, número de páginas, presupuesto ni estadística de
una cripta específica aparece en el código. Se respeta presupuesto_solicitudes:
toda solicitud HTTP cuenta, incluidos los reintentos, y nunca se excede.

### V. Reversibilidad, reproducción y persistencia versionada
Está prohibido guardar copias completas del estado para deshacer o consultar el
pasado; solo se registra la información necesaria para invertir cambios. La
única excepción son los puntos de control cada K acciones del jugador
(--checkpoint-cada, con K justificado por mediciones). Cada acción se registra
en un partida.log de solo anexado con id y versión de la cripta, versión del
catálogo y semilla; --replay lo reproduce sin interacción y, si la versión no
está disponible, reporta que no puede garantizar una reproducción fiel, nunca
reproduce en silencio contra datos distintos. Los archivos guardados llevan
versión de formato y uno anterior se reporta incompatible o se migra de forma
explícita, nunca se carga en silencio.

### VI. Medir antes de afirmar
Toda afirmación de rendimiento se respalda con mediciones propias obtenidas con
--bench, y toda decisión de estructura de datos se justifica con ellas. Reutilizar
un cálculo anterior (por ejemplo una ruta) solo es válido si se demuestra que no
cambia la decisión respecto de calcularla desde cero en ese instante.

### VII. La especificación precede al código (NO NEGOCIABLE)
Ninguna capacidad se programa sin spec.md, plan.md y tasks.md confirmados antes
en git. spec.md describe reglas, historias y escenarios con requisitos FR-xxx y
no nombra estructuras, clases ni módulos; eso va solo en plan.md. Si la
especificación estaba mal, se corrige primero ella y después el código, en
confirmaciones separadas.

## Restricciones adicionales

- Python 3.11 o superior. El código nuevo lleva anotaciones de tipo en toda
  firma pública, docstrings en clases y métodos públicos, y atributos internos
  con prefijo _ accedidos mediante propiedades.
- Nombres en español: camelCase en archivos, PascalCase en clases, snake_case en
  funciones. Jerarquía de excepciones propia (ErrorCripta).
- Patrones de diseño explícitos solo cuando resuelven un problema real (por
  ejemplo Decorator); SOLID como criterio de revisión.
- Límites de rendimiento medidos con --bench en el equipo local: ciclo de
  eventos menor a 20 ms, verificación de resolubilidad menor a 200 ms, consulta
  historia menor a 50 ms y cada paso de «ir a» menor a 5 ms.
- spec-kit y el agente son herramientas de proceso: no pueden introducir
  dependencias prohibidas en el código entregado. Todo plan generado se revisa
  contra esta constitución antes de implementar.

## Flujo de desarrollo y definición de hecho

- Cada capacidad sigue el flujo specify, clarify, plan, tasks, analyze e
  implement, con una confirmación en git por fase.
- Cada requisito FR-xxx tiene al menos una prueba automatizada o un partida.log
  que lo ejerce y cita su identificador. Cada tarea referencia los requisitos
  que atiende.
- Un bloque de código está terminado cuando pasan todas las pruebas y la
  verificación de reglas sobre cripta/, no hay dependencias prohibidas ni datos
  de criptas concretas, y DECISIONES.md tiene la sección del problema resuelto.
- Todo uso de un LLM, incluidos los comandos de spec-kit con texto propio, se
  registra en PROMPTS_LLM.md.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Si un
plan o una tarea la contradice, el error es del equipo y se corrige antes de
implementar. Una decisión de estructura de datos de la primera parte puede
cambiarse cuando las mediciones con --bench muestren que dejó de ser adecuada,
documentando el antes y el después en DECISIONES.md; no se altera la
arquitectura base para resolver un error rápido sin una especificación. Toda
enmienda se documenta y se confirma en git por separado, con versión nueva.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31