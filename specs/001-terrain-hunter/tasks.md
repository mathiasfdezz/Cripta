# Tasks: Terreno y cazador

**Input**: Design documents from `/specs/001-terrain-hunter/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`)
**Requirements Coverage**: FR-001 a FR-015, PR-001.
**Revisión**: corregido tras `/speckit-analyze` (ver analisis.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecución en paralelo permitida (archivos independientes, sin dependencias mutuas)
- **[Story]**: Historia de usuario asociada ([US1], [US2], [US3])
- Rutas exactas en cada tarea

---

## Phase 1: Setup & Data Contracts

**Purpose**: Actualización de DTOs y adaptadores para recibir los nuevos campos del servicio/esqueleto.

- [X] T001 [P] Actualizar `dtos/salida.py` agregando el campo `costo: int = 100` con validación de entero >= 1 (FR-001).
- [X] T002 [P] Actualizar `dtos/ficha_catalogo.py` agregando el campo opcional `rango: int | None = None` y permitiendo `comportamiento == "cazador"` (FR-004).
- [X] T003 Actualizar `adaptadores/mapeadores/mapeador_salas.py` para deserializar `costo` (entero >= 1, 100 si no se declara o es `null`) en las salidas (FR-001).
- [X] T003a [P] Escribir pruebas en `tests/test_mapeador_salas.py`: costo ausente o `null` da 100; costo 0, negativo o no entero es un error de datos (FR-001).
- [X] T004 Actualizar `adaptadores/mapeadores/mapeador_catalogo.py` para mapear `rango` y comportamiento `cazador` desde el catálogo JSON (FR-004).
- [X] T004a [P] Escribir pruebas en `tests/test_mapeador_catalogo.py`: un cazador sin `rango` es un error de datos; con `rango` se mapea (FR-004).

---

## Phase 2: Foundational (Infraestructura de Topología e Índices Densos)

**Purpose**: Construcción de adyacencias dirigidas, resolución de índices densos en $O(V+E)$ y soporte de costos en el esqueleto.

- [ ] T005 Actualizar `modelo/puerta.py` para almacenar `costo: int` y avisar al esqueleto el índice de su salida cada vez que cambia su estado, también al deshacer o cargar (FR-001, FR-009).
- [ ] T006 Crear `modelo/grafo_cripta.py` (`GrafoCripta`) y modificar `modelo/esqueleto.py` para numerar las salidas, resolver los índices densos `[0, V-1]` y construir las listas de **salidas entrantes** y salientes con su costo e índice de salida en $O(V+E)$ (FR-001, FR-008).

---

## Phase 3: User Story 1 - Movimiento por terreno con costos variables (Priority: P1) 🎯 MVP

**Goal**: Todos los actores consumen tiempo e intervalo según el costo de la salida atravesada, preservando la fórmula de velocidad y reescalado de tiempo.

### Tests for User Story 1 (TDD - Escribir primero)
- [ ] T007 [P] [US1] Escribir prueba unitaria `test_intervalo_movimiento_costo_variable` en `tests/test_movimiento_terreno.py` citando FR-002 y FR-003: actor vel 200 en salida costo 50 da intervalo 25 (`max(1, 50 * 100 // 200)`).
- [ ] T008 [P] [US1] Escribir prueba unitaria `test_intervalo_velocidad_alta_costo_uno` en `tests/test_movimiento_terreno.py` citando FR-003 (Apéndice B): velocidad alta atravesando costo 1 da intervalo al menos 1 (`max(1, 1 * 100 // 1000) >= 1`).
- [ ] T009 [P] [US1] Escribir prueba unitaria `test_reescalado_velocidad_salida_costosa` en `tests/test_movimiento_terreno.py` citando FR-013 (Apéndice B): reescalado del tiempo restante por cambio de velocidad durante acción en agenda según P1 §2.3.
- [ ] T010 [P] [US1] Escribir prueba unitaria `test_costos_acciones_no_cambian` en `tests/test_movimiento_terreno.py` citando FR-012: verificar que atacar/esperar (costo 100), usar objeto (50), recoger/soltar (25) y abrir puerta (50) conservan sus costos base.

### Implementation for User Story 1
- [ ] T011 [US1] Actualizar `mover_jugador` en `modelo/estado_partida.py` para que el costo de la acción sea `salida.costo` y el intervalo programado sea `max(1, costo_salida * 100 // velocidad)` (FR-002, FR-003).
- [ ] T012 [US1] Adaptar `_comportarse` y `programar_accion` en `modelo/estado_partida.py` (y la vecindad de `modelo/rastro.py`) para que errantes y rastreadores usen el costo de la salida que atraviesan, conservando sus comportamientos (FR-003, FR-012).

---

## Phase 4: User Story 2 - Comportamiento del Cazador y Búsqueda Compartida (Priority: P1)

**Goal**: Enemigo cazador persigue al jugador por la ruta de costo mínimo usando salidas abiertas, desempate por ID, rango y cálculo bajo demanda equivalente a calcular desde cero.

### Tests for User Story 2 (TDD - Escribir primero)
- [ ] T013 [P] [US2] Escribir prueba unitaria `test_cazador_sin_ruta_espera` en `tests/test_cazador.py` citando FR-006 (Apéndice B): cazador sin ruta abierta hacia el jugador espera con costo 100.
- [ ] T014 [P] [US2] Escribir prueba unitaria `test_cazador_fuera_de_rango_espera` en `tests/test_cazador.py` citando FR-006 (Apéndice B): ruta mínima $d > rango$ causa que el cazador espere con costo 100.
- [ ] T015 [P] [US2] Escribir prueba unitaria `test_cazador_elige_ruta_menor_costo` en `tests/test_cazador.py` citando FR-005 (Apéndice B): entre ruta de menos salas pero más costo y ruta de más salas pero menor costo, sigue la de menor costo.
- [ ] T016 [P] [US2] Escribir prueba unitaria `test_cazador_desempate_menor_id` en `tests/test_cazador.py` citando FR-007 (Apéndice B): dos vecinas que inician rutas de igual costo mínimo desempatan por la de menor ID de sala vecina.
- [ ] T017 [P] [US2] Escribir prueba unitaria `test_cazador_puerta_se_cierra_entre_turnos` en `tests/test_cazador.py` citando FR-009 (Apéndice B): puerta en su ruta se cierra entre dos turnos y el cazador decide en el siguiente turno como si calculara desde cero.
- [ ] T018 [P] [US2] Escribir prueba unitaria `test_multiples_cazadores_comparten_sala` en `tests/test_cazador.py` citando FR-015: múltiples cazadores en la misma sala atacan o actúan individualmente sin bloquearse entre sí.
- [ ] T019 [P] [US2] Escribir prueba unitaria `test_cazador_salida_un_solo_sentido` en `tests/test_cazador.py` citando FR-005 y FR-008: verificación de que el cazador solo transita salidas dirigidas válidas hacia el jugador.
- [ ] T020 [P] [US2] Escribir prueba unitaria `test_cazador_puerta_cerrada_unilateral` en `tests/test_cazador.py` citando FR-005 y FR-008: una puerta cerrada solo en un sentido bloquea el paso en ese sentido pero no en el inverso.

### Implementation for User Story 2
- [ ] T021 [US2] Implementar `modelo/buscador_rutas.py` (`BuscadorRutas`) con Dijkstra artesanal desde el jugador usando las salidas entrantes, sistema de épocas para reinicio $O(1)$ sin asignación global y detención en la cota, acotado a $O(R + E_R \log R)$ (FR-005, FR-008, PR-001).
- [ ] T022 [US2] Implementar la invalidación selectiva en `modelo/buscador_rutas.py`: movimiento del jugador, cambio de una salida que entra a una sala asentada o cota mayor que la usada (FR-008, FR-009).
- [ ] T023 [US2] Implementar el comportamiento `cazador` en `modelo/enemigo.py` (constante y `rango`) y `modelo/estado_partida.py`: 1. Atacar si comparte sala; 2. Consultar el costo mínimo en `BuscadorRutas`; 3. Esperar (costo 100) si no hay ruta o $d > rango$; 4. Moverse a la vecina de costo $d$ desempatando por menor ID, con el costo de esa salida (FR-004, FR-005, FR-006, FR-007, FR-014).
- [ ] T023a [P] [US2] Escribir prueba `test_reutilizar_equivale_a_calcular_desde_cero` en `tests/test_cazador.py` citando FR-009: en una partida con puertas que se abren y cierran, cada decisión con el mapa reutilizado coincide con la de un buscador nuevo.

---

## Phase 5: User Story 3 - Visualización Táctica (Priority: P2)

**Goal**: Mostrar costos de salidas de la sala actual y distinguir cazadores en la interfaz interactiva.

### Tests for User Story 3 (TDD - Escribir primero)
- [ ] T024 [P] [US3] Escribir prueba unitaria `test_vista_muestra_costos_salidas` en `tests/test_vista_terreno.py` citando FR-010: verificar formateo de costos de salidas en la descripción de la sala actual.
- [ ] T025 [P] [US3] Escribir prueba unitaria `test_vista_distingue_cazadores` en `tests/test_vista_terreno.py` citando FR-011: verificar que los cazadores se diferencian en la lista de enemigos visibles.

### Implementation for User Story 3
- [ ] T026 [US3] Actualizar `vista/consola.py` y `vista/estilo.py` para renderizar el costo de cada salida en la sala del jugador (ej. `N (costo 100)`) (FR-010).
- [ ] T027 [US3] Actualizar `vista/consola.py` para distinguir enemigos cazadores de errantes y rastreadores (FR-011).

---

## Phase 6: Benchmarks, Medición y Rendimiento (PR-001)

**Purpose**: Verificación de presupuestos de tiempo y análisis empírico para DECISIONES.md.

- [ ] T028 Implementar módulo `bench/bench_cazadores.py` (criptas sintéticas deterministas por semilla en `bench/cripta_sintetica.py`) con escenarios reproducibles por semilla para:
  1. Cálculo individual frente a compartido (con 10, 50 y decenas de cazadores) (PR-001).
  2. Recalcular siempre frente a caché con invalidación (PR-001).
  3. Puertas estables frente a puertas inestables (frecuentes aperturas/cierres) (PR-001).
  4. Criptas sintéticas con salidas de un solo sentido y puertas cerradas en un solo sentido (PR-001).
- [ ] T029 Actualizar `bench/bench_agenda.py` y `bench/bench_ciclo.py` para repetir las mediciones de la primera parte con la carga añadida de decenas de cazadores activos y verificar que el ciclo se mantiene bajo 20 ms en la cripta de referencia (PR-001).
- [ ] T030 Integrar las nuevas opciones de benchmark en `bench/bench.py` y `main.py --bench`.

---

## Phase 7: Documentación y Cierre

**Purpose**: Registro de decisiones de diseño, manual de usuario y bitácora de prompts.

- [ ] T031 Redactar la sección "Terreno y cazador" en `DECISIONES.md` documentando las alternativas medidas, justificación matemática, evidencia empírica de `--bench` y análisis de complejidad $O(R + E_R \log R)$.
- [ ] T032 Actualizar `README.md` documentando los nuevos comandos de ejecución, opciones de `--bench` para cazadores y la forma de correr las pruebas de aceptación con `python -m unittest`.
- [ ] T033 Registrar en `PROMPTS_LLM.md` los prompts de especificación, clarificación, planificación y tareas ejecutados para esta capacidad.

---

## Dependencies & Execution Order

1. **Phase 1 (Setup)** y **Phase 2 (Foundational)** deben completarse antes de iniciar cualquier User Story.
2. **User Story 1 (Phase 3)**: Pruebas (T007-T010) → Implementación (T011-T012).
3. **User Story 2 (Phase 4)**: Pruebas (T013-T020) → Implementación (T021-T023). Requiere US1 completo.
4. **User Story 3 (Phase 5)**: Pruebas (T024-T025) → Implementación (T026-T027). Requiere US1 y US2.
5. **Phase 6 (Benchmarks)**: Requiere US1 y US2 completamente implementados.
6. **Phase 7 (Documentación)**: Requiere datos finales de Phase 6.

## Parallel Opportunities

- **T001 y T002** pueden ejecutarse en paralelo (DTOs distintos).
- **T007, T008, T009 y T010** pueden escribirse en paralelo.
- **T013 a T020** pueden redactarse en paralelo antes de comenzar `modelo/rastreador_cazador.py`.
- **T024 y T025** pueden implementarse en paralelo.
