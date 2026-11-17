# Bitácora de prompts - CRIPTA, segunda parte

Herramientas: Gemini CLI (constitución) y Claude Code (capacidades 001 a 004), las dos con GitHub spec-kit 1.1.0.
Cada entrada indica fecha, herramienta, prompt textual y para qué se usó la respuesta.

---

## Prompt 1 · 03/11/2026
**Herramienta:** Gemini CLI + spec-kit 1.1.0 (`/speckit.constitution`)

```text
/speckit.constitution Escribe la constitución del proyecto CRIPTA (segunda parte), en español. Es un juego de consola en Python que consume un API REST; la primera parte ya está implementada en este repositorio y se continúa sobre ella. Usa lenguaje DEBE / DEBERÍA. Principios: (1) Estructuras propias: las estructuras de datos de los problemas evaluados se implementan a mano en el proyecto. Está prohibido usar dict o set como índice, caché o tabla de búsqueda, y también heapq, bisect, collections (deque, OrderedDict, defaultdict, Counter), networkx o cualquier biblioteca de grafos o de búsqueda de rutas. Los dict que devuelve respuesta.json() solo se leen para convertirlos en objetos. list se permite solo como almacenamiento de bajo nivel. (2) Determinismo: la misma cripta, la misma semilla y la misma secuencia de acciones producen exactamente la misma partida. Toda aleatoriedad usa la instancia random.Random(semilla) de la partida, nunca el generador global. El orden de los eventos lo define el tiempo y un número de secuencia, nunca la hora del sistema ni el orden de llegada de respuestas de red. (3) Separación MVC: el modelo no conoce HTTP, archivos ni la interfaz. El acceso a red y disco va en adaptadores detrás de interfaces. Los modos --replay, --bench y --verificar se ejecutan sin instanciar la vista interactiva. (4) Sin datos de una cripta en el código: ningún número de sala, id de entidad, cantidad de páginas, presupuesto ni estadística de una cripta concreta puede estar escrito en el código. (5) Presupuesto de red: se respeta presupuesto_solicitudes; toda solicitud HTTP cuenta, incluidos los reintentos por HTTP 429. Se usan lotes, precarga y persistencia validada por versión para gastar lo menos posible. (6) Rendimiento con evidencia: toda afirmación de rendimiento se respalda con mediciones reproducibles de --bench, con criptas sintéticas deterministas por semilla. Se respetan los límites del enunciado (por ejemplo, 20 ms por ciclo de eventos). (7) Especificación antes que código: ninguna capacidad se implementa sin su especificación, plan y tareas confirmados antes en Git. Cada requisito funcional tiene un identificador estable (FR-001...), cada tarea indica los requisitos que atiende y cada escenario de aceptación tiene al menos una prueba automatizada que cita su identificador. Si la especificación estaba mal, se corrige primero la especificación y después el código, en confirmaciones separadas. (8) Pruebas: se usa unittest y todas las pruebas se ejecutan con "python -m unittest". Una tarea no está terminada hasta que todas las pruebas pasan. (9) Estado reversible y persistente: todo estado nuevo del juego DEBE poder revertirse con el pergamino de retroceso y guardarse en el archivo de partida sin copiar el estado completo. Un cambio de formato del guardado cambia su versión y los archivos viejos se reportan como incompatibles. (10) Simplicidad y legibilidad: Python 3.11 o superior; una clase por archivo; los DTO son inmutables y sin lógica; nombres en español; comentarios breves; no se agregan dependencias nuevas sin justificarlo en el plan. Se elige el diseño más simple que cumpla la especificación.
```

**Uso de la respuesta:** generar la constitución inicial (`.specify/memory/constitution.md`) con los principios heredados de la primera parte (§2.3).

---

## Prompt 2 · 03/11/2026
**Herramienta:** Gemini CLI + spec-kit 1.1.0 (`/speckit.constitution`)

```text
/speckit.constitution Corrige la constitución antes de confirmarla, sin cambiar los 10 principios salvo en esto: (a) Principio IX: agrega la excepción de que se permiten copias completas del estado solo como puntos de control de la línea de tiempo, como máximo uno cada K acciones del jugador (K configurable con --checkpoint-cada), y que fuera de esos puntos solo se guarda lo necesario para reconstruir los cambios; (b) Principio III: los modos --replay, --bench y --verificar no instancian la vista interactiva; elimina la exigencia de que la suite de pruebas no importe la vista, porque las pruebas de la vista sí la importan; (c) Principio V: si el presupuesto se agota, el programa no se cae, avisa una vez y nunca deja al jugador en una sala cuyo contenido no conoce; elimina "terminar ordenadamente"; (d) Principio VI y Gate 4: los límites de tiempo (20 ms por ciclo y los demás del enunciado) se miden con la cripta de referencia; las pruebas de estrés con criptas sintéticas más grandes documentan límites conocidos y no son una condición de aceptación; y el documento de decisiones es DECISIONES.md en la raíz del repositorio, no docs/decisiones.md; (e) Gobernanza: las enmiendas se registran en una confirmación de Git dedicada con su justificación, sin exigir issues. Mantén la versión 1.0.0 porque la constitución todavía no se ha confirmado.
```

**Uso de la respuesta:** corregir cinco reglas que Gemini agregó por su cuenta y que contradecían el enunciado (los puntos de control de §3.6) o el código existente.


## Segunda herramienta: Claude Code

Desde el 17/11/2026 el grupo usa Claude Code como agente (integración `claude` de spec-kit, `specify integration install claude --script ps`). La integración de Gemini sigue instalada.

---

## Prompt 3 · 15/11/2026
**Herramienta:** spec-kit 1.1.0 (agente indicado por Abraham) (`/speckit.specify`)

```text
/speckit.specify Capacidad 'terreno y cazador'. Reglas: @docs/enunciado_parte2.md §3.1, §3.2 y Apéndice B (sección Terreno y cazador). Cubre: (1) costo por salida (entero >= 1, 100 si no se declara o es null, igual en ambos sentidos); mover cuesta el costo de la salida e intervalo = max(1, costo_salida*100//velocidad) para todos los actores; atacar, esperar y demás acciones no cambian; errantes y rastreadores solo cambian lo que tarda su movimiento. (2) Cazador: ficha con rango; reglas en orden (ataca si comparte sala; si no, costo mínimo d por salidas abiertas en ese instante; espera con costo 100 si no hay ruta o d > rango; si no, un paso por una ruta de costo d); desempate: la vecina de menor id; conoce esqueleto completo y puertas actuales, no le afecta la niebla ni el contenido descargado; no abre puertas; su decisión equivale siempre a calcular desde cero. (3) La vista muestra costos de las salidas de la sala actual y distingue cazadores. Incluye los 7 casos del Apéndice B de esta capacidad como escenarios de aceptación, y el requisito de 20 ms por ciclo con decenas de cazadores activos.
```

**Uso de la respuesta:** generar `specs/001-terrain-hunter/spec.md`. Texto tomado de la cabecera de la especificación; los comandos `/speckit.clarify`, `/speckit.plan` y `/speckit.tasks` de esta capacidad los ejecutó Abraham y su texto lo agrega él (tarea T033).

---

## Prompt 4 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-analyze`)

```text
/speckit-analyze Revisa la consistencia de specs/001-terrain-hunter (spec.md, plan.md, tasks.md) contra la constitución 1.1.0 y contra el código actual del repositorio: rutas de archivos que las tareas nombran, nombres que choquen con conceptos de la primera parte, si la invalidación de rutas responde §5.2 (qué eventos invalidan qué), si el modelo de datos sirve para copiar el estado en los puntos de control de la capacidad 004, comandos del quickstart que no existan y requisitos sin prueba.
```

**Uso de la respuesta:** hallazgos A1 a A10 en `specs/001-terrain-hunter/analisis.md`; se corrigió primero spec.md (FR-012 y supuestos) y después plan, research, data-model, tasks y quickstart, en commits separados.

---

## Prompt 5 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-implement`)

```text
/speckit-implement Implementa specs/001-terrain-hunter/tasks.md en orden de fases, marcando cada tarea al terminarla, con un commit por fase y sin push. Pruebas primero en cada historia; cada prueba cita su FR.
```

**Uso de la respuesta:** fases 1 a 6 de la capacidad 001 (T001-T030).

---

## Prompt 6 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-specify`)

```text
/speckit-specify Capacidad 'niebla de guerra e ir a'. Reglas: @docs/enunciado_parte2.md §3.3, §3.4, §7.3 y Apéndice B (sección Niebla de guerra e «ir a»). Cubre: (1) estados de sala para el jugador: explorada (entró al menos una vez; la inicial desde t=0), avistada (destino de una salida de una sala explorada) y desconocida; (2) memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta y el mapa recuerda el último estado observado; (3) antorcha encendida: al entrar a una sala se exploran también sus vecinas por cualquier salida, sin activar enemigos ni trampas ni revelar contenido; (4) la vista y 'ir a' usan solo el conocimiento del jugador; el esqueleto completo sigue siendo infraestructura de precarga; (5) el conocimiento se guarda, se revierte con el pergamino y entra en la línea de tiempo; (6) comando para ver el mapa conocido; (7) 'ir a <sala>' hacia una sala explorada por una secuencia de movimientos ordinarios, ruta de costo mínimo solo por salas exploradas y salidas recordadas abiertas, desempate como el cazador, recálculo antes de cada paso, se detiene al llegar, al entrar a una sala con enemigos, al recibir daño o si deja de existir ruta, no abre puertas, cada paso va a partida.log como movimiento y la orden como comentario, el pergamino revierte solo el último paso. Incluye los 6 casos del Apéndice B y el límite de 5 ms por paso con el mapa completo de la cripta de referencia. Los requisitos se numeran desde FR-101 para que sean únicos en el proyecto.
```

**Uso de la respuesta:** generar `specs/002-niebla-ir-a/spec.md` (niebla de guerra e ir a) y su checklist de calidad.

---

## Prompt 7 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-clarify`)

```text
/speckit-clarify Resuelve las ambigüedades de specs/002-niebla-ir-a/spec.md que cambian el resultado observable del juego; registra cada pregunta y respuesta en la sección Clarifications sin agregar nombres de estructuras ni de módulos.
```

**Uso de la respuesta:** sección Clarifications de la especificación, en un commit propio.

---

## Prompt 8 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-plan`)

```text
/speckit-plan Planifica specs/002-niebla-ir-a respetando la constitución 1.1.0: estructuras propias (sin dict, set, heapq, bisect, collections ni bibliotecas de grafos), alternativas consideradas, complejidad, módulos afectados y mediciones para el bench; reutiliza lo que ya existe en el repositorio (GrafoCripta, BuscadorRutas, MinHeap, Fila, VectorOrdenado) cuando sirva.
```

**Uso de la respuesta:** plan.md, research.md y data-model.md.

---

## Prompt 9 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-tasks`)

```text
/speckit-tasks Descompone el plan de specs/002-niebla-ir-a en tareas pequeñas y verificables, pruebas primero, con la ruta exacta de cada archivo y los FR que atiende cada tarea.
```

**Uso de la respuesta:** tasks.md.

---

## Prompt 10 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-analyze`)

```text
/speckit-analyze Revisa la consistencia entre spec.md, plan.md y tasks.md de specs/002-niebla-ir-a y contra la constitución; lista requisitos sin tarea o sin prueba y casos del Apéndice B sin escenario.
```

**Uso de la respuesta:** analisis.md y las correcciones de tareas, en un commit propio antes del código.

---

## Prompt 11 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-implement`)

```text
/speckit-implement Implementa specs/002-niebla-ir-a/tasks.md por fases, con un commit por fase y sin push; si la especificación resulta incompleta, se corrige primero la especificación.
```

**Uso de la respuesta:** el código, las pruebas y el bench de la capacidad.

---

## Prompt 12 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-specify`)

```text
/speckit-specify Capacidad 'verificación de resolubilidad'. Reglas: @docs/enunciado_parte2.md §3.5, §4.2, §4.3, §5.4, §7.3 y Apéndice B (sección Resolubilidad). Antes de iniciar una partida el programa determina si la cripta puede ganarse usando el esqueleto y la ubicación de las llaves (GET /criptas/<id>/llaves, que cuenta en el presupuesto y se persiste validada por versión). Supuestos: se atraviesa cualquier salida abierta y cualquier salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se obtiene en la sala donde ese enemigo inicia; trampas y cierres automáticos no bloquean. Resoluble: partiendo de la sala inicial se obtiene llave_salida y se llega a sala_salida por una puerta que la requiere. Si es resoluble, se informa un orden determinista de obtención de llaves donde cada llave aparece después de las necesarias para alcanzarla. Si no: llaves no obtenibles, puertas de la frontera bloqueada con la llave que pide cada una y dónde está cada llave, y el ciclo concreto si una llave está detrás de puertas que solo ella abre, directamente o por una cadena de llaves. Sin resolubilidad la partida no inicia salvo con --forzar. --verificar <cripta> solo verifica, sin la vista. La interfaz muestra el reporte al iniciar. Límite: 200 ms en la cripta publicada más grande; el costo debe crecer de forma aproximadamente lineal con salas, salidas y llaves. Incluye los 4 casos del Apéndice B. Los requisitos se numeran desde FR-201.
```

**Uso de la respuesta:** generar `specs/003-resolubilidad/spec.md` (verificación de resolubilidad) y su checklist de calidad.

---

## Prompt 13 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-clarify`)

```text
/speckit-clarify Resuelve las ambigüedades de specs/003-resolubilidad/spec.md que cambian el resultado observable del juego; registra cada pregunta y respuesta en la sección Clarifications sin agregar nombres de estructuras ni de módulos.
```

**Uso de la respuesta:** sección Clarifications de la especificación, en un commit propio.

---

## Prompt 14 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-plan`)

```text
/speckit-plan Planifica specs/003-resolubilidad respetando la constitución 1.1.0: estructuras propias (sin dict, set, heapq, bisect, collections ni bibliotecas de grafos), alternativas consideradas, complejidad, módulos afectados y mediciones para el bench; reutiliza lo que ya existe en el repositorio (GrafoCripta, BuscadorRutas, MinHeap, Fila, VectorOrdenado) cuando sirva.
```

**Uso de la respuesta:** plan.md, research.md y data-model.md.

---

## Prompt 15 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-tasks`)

```text
/speckit-tasks Descompone el plan de specs/003-resolubilidad en tareas pequeñas y verificables, pruebas primero, con la ruta exacta de cada archivo y los FR que atiende cada tarea.
```

**Uso de la respuesta:** tasks.md.

---

## Prompt 16 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-analyze`)

```text
/speckit-analyze Revisa la consistencia entre spec.md, plan.md y tasks.md de specs/003-resolubilidad y contra la constitución; lista requisitos sin tarea o sin prueba y casos del Apéndice B sin escenario.
```

**Uso de la respuesta:** analisis.md y las correcciones de tareas, en un commit propio antes del código.

---

## Prompt 17 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-implement`)

```text
/speckit-implement Implementa specs/003-resolubilidad/tasks.md por fases, con un commit por fase y sin push; si la especificación resulta incompleta, se corrige primero la especificación.
```

**Uso de la respuesta:** el código, las pruebas y el bench de la capacidad.

---

## Prompt 18 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-specify`)

```text
/speckit-specify Capacidad 'línea de tiempo'. Reglas: @docs/enunciado_parte2.md §3.6, §5.5, §6.1, §7.3 y Apéndice B (sección Línea de tiempo). El pergamino sigue limitado a 5 acciones; la línea de tiempo es independiente y permite consultar sin modificar la partida el estado en cualquier instante desde el inicio. Estado en t: después de todos los eventos con tiempo <= t; si a t le corresponde una decisión del jugador, justo antes de tomarla. 'historia <t>' e 'historia #k' (estado justo antes de la acción k) muestran reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido; no consumen tiempo, no se registran como acción y no alteran el juego ni el historial de retroceso. '--replay partida.log --hasta <t>' imprime el mismo resumen sin la vista. Las acciones revertidas con un pergamino dejan de existir en la línea; consultar un instante posterior al reloj actual se rechaza. Memoria: copias completas del estado (puntos de control) como máximo una cada K acciones del jugador, K con --checkpoint-cada y valor por defecto justificado con mediciones; una consulta no aplica ni deshace más de K acciones; fuera de los puntos de control solo se guarda lo necesario para reconstruir. Si se re-simula, el punto de control incluye el estado del random. Guardar y cargar conserva la línea completa; el formato cambia y un archivo de la primera parte se detecta incompatible. Límite: 50 ms por consulta en una partida de al menos 5000 acciones con K por defecto. Incluye los 6 casos del Apéndice B. Los requisitos se numeran desde FR-301.
```

**Uso de la respuesta:** generar `specs/004-linea-de-tiempo/spec.md` (línea de tiempo) y su checklist de calidad.

---

## Prompt 19 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-clarify`)

```text
/speckit-clarify Resuelve las ambigüedades de specs/004-linea-de-tiempo/spec.md que cambian el resultado observable del juego; registra cada pregunta y respuesta en la sección Clarifications sin agregar nombres de estructuras ni de módulos.
```

**Uso de la respuesta:** sección Clarifications de la especificación, en un commit propio.

---

## Prompt 20 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-plan`)

```text
/speckit-plan Planifica specs/004-linea-de-tiempo respetando la constitución 1.1.0: estructuras propias (sin dict, set, heapq, bisect, collections ni bibliotecas de grafos), alternativas consideradas, complejidad, módulos afectados y mediciones para el bench; reutiliza lo que ya existe en el repositorio (GrafoCripta, BuscadorRutas, MinHeap, Fila, VectorOrdenado) cuando sirva.
```

**Uso de la respuesta:** plan.md, research.md y data-model.md.

---

## Prompt 21 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-tasks`)

```text
/speckit-tasks Descompone el plan de specs/004-linea-de-tiempo en tareas pequeñas y verificables, pruebas primero, con la ruta exacta de cada archivo y los FR que atiende cada tarea.
```

**Uso de la respuesta:** tasks.md.

---

## Prompt 22 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-analyze`)

```text
/speckit-analyze Revisa la consistencia entre spec.md, plan.md y tasks.md de specs/004-linea-de-tiempo y contra la constitución; lista requisitos sin tarea o sin prueba y casos del Apéndice B sin escenario.
```

**Uso de la respuesta:** analisis.md y las correcciones de tareas, en un commit propio antes del código.

---

## Prompt 23 · 17/11/2026
**Herramienta:** Claude Code (Claude Opus 5.5) + spec-kit 1.1.0 (`/speckit-implement`)

```text
/speckit-implement Implementa specs/004-linea-de-tiempo/tasks.md por fases, con un commit por fase y sin push; si la especificación resulta incompleta, se corrige primero la especificación.
```

**Uso de la respuesta:** el código, las pruebas y el bench de la capacidad.
