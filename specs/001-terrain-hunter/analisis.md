# Análisis de consistencia: Terreno y cazador

Salida de `/speckit-analyze` (Claude Code, 2026-11-17) sobre `spec.md`, `plan.md` y `tasks.md`,
antes de implementar. Las correcciones de la especificación van en un commit propio
(`spec: FR-012 incluye equipar...`); las del plan y las tareas, en el commit que agrega
este archivo.

| ID | Categoría | Severidad | Ubicación | Hallazgo | Corrección |
|----|-----------|-----------|-----------|----------|------------|
| A1 | Inconsistencia | ALTA | tasks.md T011, T012 | Las tareas apuntan a `modelo/partida.py` y `modelo/enemigo.py`, pero el movimiento del jugador y el comportamiento de los enemigos viven en `modelo/estado_partida.py` (`mover_jugador`, `_comportarse`, `programar_accion`). | Rutas corregidas. |
| A2 | Terminología | MEDIA | plan.md, research.md, data-model.md, tasks.md | `RastreadorCazador` choca con el comportamiento «rastreador» de P1 y hace pensar que es un enemigo. | Se separa en `GrafoCripta` (índices densos y salidas, estático) y `BuscadorRutas` (Dijkstra acotado con épocas). |
| A3 | Subespecificación | ALTA | research.md §2 | «Cualquier cambio de puerta invalida el mapa» no responde §5.2: hay que identificar qué eventos invalidan qué información. | Regla nueva en el plan: un cambio en la salida u→x solo invalida si x quedó asentada en el último cálculo (demostración en research.md). Se mide contra «recalcular siempre». |
| A4 | Diseño | MEDIA | data-model.md | Las listas de salidas entrantes guardan referencias a objetos `Puerta`. La línea de tiempo (capacidad 004) copia el estado en puntos de control y esas referencias quedarían apuntando a las puertas vivas. | Las aristas guardan el índice de la salida; el estado de la puerta se consulta en el esqueleto por ese índice. El grafo estático se comparte entre copias. |
| A5 | Inconsistencia | MEDIA | quickstart.md | Usa banderas que no existen (`--bench cazadores`, `--num-cazadores`, `--puertas-inestables`) y `cripta-01`, que ya no está publicada. | Se usan `python main.py --bench` y las criptas 02 y 06 del paquete offline. |
| A6 | Cobertura | MEDIA | tasks.md | FR-001 (costo inválido o ausente) y FR-004 (`rango` obligatorio para un cazador) no tienen prueba de mapeo. | Tareas T003a y T004a. |
| A7 | Ambigüedad | BAJA | spec.md PR-001 / SC-001 | «Decenas de cazadores» sin cripta concreta. | El plan fija la medición en la cripta de referencia (cripta-06, 36 cazadores en su contenido) más un escenario con 60 cazadores activos. |
| A8 | Constitución VII | MEDIA | PROMPTS_LLM.md | No están registrados los comandos de spec-kit de esta capacidad. | Se registra el texto de `/speckit.specify` (conservado en la cabecera de spec.md); los de clarify, plan y tasks los agrega quien los ejecutó (T033). |
| A9 | Cobertura | BAJA | spec.md FR-012 | La lista de costos que no cambian omitía equipar (50). | Corregido en spec.md. |
| A10 | Subespecificación | BAJA | spec.md Assumptions | No decía desde cuándo actúa un cazador ni el costo de su primera acción. | Supuestos agregados (se mantienen P1 §2.4 y costo 100). |

**Cobertura**: FR-001 a FR-015 y PR-001 tienen al menos una tarea; los 7 casos del Apéndice B
(terreno y cazador) son escenarios de aceptación con prueba asignada.

**Constitución**: no hay violaciones. El plan no propone `heapq`, `dict`, `set` ni bibliotecas de grafos.
