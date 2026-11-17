# Tasks: Línea de tiempo con puntos de control

**Input**: `specs/004-linea-de-tiempo/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`)
**Requirements Coverage**: FR-301 a FR-310, PR-301, PR-302.

## Phase 1: Foundational

- [X] T301 Copia propia en `modelo/puerta.py`, `modelo/evento.py`, `modelo/esqueleto.py` y `modelo/grafo_cripta.py`; `EstadoPartida.copiar()` con la copia completa del estado (memo con lo inmutable compartido, historial vacío, sin cachés de búsqueda) (FR-308).
- [X] T302 `EstadoPartida`: el cursor del inventario se mueve por el modelo y queda en el historial; `avanzar_hasta_tiempo(t)`; anotar cada operación en la línea si la partida tiene una (FR-302, FR-305, FR-308).
- [X] T303 `modelo/punto_de_control.py` y `modelo/linea_tiempo.py`: operaciones, decisiones, puntos de control cada K, recorte por pergamino, consulta por acción y por instante con búsqueda binaria propia (FR-301, FR-302, FR-305, FR-306, FR-308, PR-302).

## Phase 2: User Story 1 - Consultar el pasado (P1)

### Tests (primero)
- [X] T304 [P] [US1] `tests/test_linea_tiempo.py::test_historia_k_es_el_estado_antes_de_la_accion` y `test_historia_t` comparando contra la partida jugada (FR-301, FR-302, FR-303).
- [X] T305 [P] [US1] `test_eventos_en_el_mismo_instante` (FR-302, Apéndice B).
- [X] T306 [P] [US1] `test_t_mayor_que_el_reloj_se_rechaza` y casos inválidos (FR-306, Apéndice B).
- [X] T307 [P] [US1] `test_consulta_no_altera_nada` (FR-304, Apéndice B).
- [X] T308 [P] [US1] `test_pergamino_quita_acciones_de_la_linea` (FR-305, Apéndice B).
- [X] T309 [P] [US1] `test_nunca_mas_de_k_acciones` (también: nunca más de ⌈acciones/K⌉ puntos guardados) y `test_equivalencia_en_partida_larga` con K por defecto y un tope holgado de tiempo por consulta (FR-308, PR-301).

### Implementation
- [X] T310 [US1] `vista/texto_historia.py` (resumen) y comando `historia <t>` / `historia #k` en `controlador/partida.py` y `vista/consola.py`; `historia` fuera de partida.log (FR-301, FR-303, FR-304).

## Phase 3: User Story 2 - Consultar sin jugar (P2)

- [X] T311 [P] [US2] `tests/test_replay_hasta.py`: mismo resumen que `historia t`; t posterior al final (FR-307, Apéndice B).
- [X] T312 [US2] `main.py`: `--replay partida.log --hasta t` sin vista interactiva y `--checkpoint-cada K` (FR-307, FR-308).

## Phase 4: User Story 3 - Persistencia (P1)

- [X] T313 [P] [US3] `tests/test_linea_tiempo.py::test_guardar_y_cargar_conserva_la_linea` y `test_archivo_de_la_primera_parte_incompatible` (FR-309, FR-310, Apéndice B).
- [X] T314 [US3] Formato 5 en `adaptadores/guardado_binario.py` y `adaptadores/guardado_partida.py`: operaciones serializadas, re-simulación al cargar y comprobación contra el estado guardado (FR-309, FR-310).

## Phase 5: Mediciones (PR-301, PR-302)

- [ ] T315 `bench/bench_linea_tiempo.py`: 5000 acciones; memoria y consulta con K = 10, 50, 200 y sin puntos de control; costo de un punto de control en la cripta de referencia; repetición del bench del retroceso (§5.6); elección del K por defecto (PR-301, PR-302).

## Phase 6: Documentación

- [ ] T316 Sección «Línea de tiempo» en `DECISIONES.md`; `README.md` con `historia`, `--checkpoint-cada` y `--replay --hasta`; `PROMPTS_LLM.md`.

## Dependencies

Phase 1 → Phase 2 → Phase 3 y 4. Phase 5 depende de Phase 2. Phase 6 al final.
