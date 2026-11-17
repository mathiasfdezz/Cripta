# Tasks: Niebla de guerra y viaje automático «ir a»

**Input**: `specs/002-niebla-ir-a/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`)
**Requirements Coverage**: FR-101 a FR-114, PR-101, PR-102.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias)
- **[Story]**: historia de usuario ([US1] explorar, [US2] ir a)

---

## Phase 1: Foundational

- [ ] T101 Agregar `registrar_elemento(lista, posicion, anterior)` a `modelo/historial.py` y deshacerlo en `deshacer()`; prueba en `tests/test_historial.py` (FR-106).
- [ ] T102 Crear `modelo/mapa_conocido.py` (`MapaConocido`) con `estado` por sala y `recuerdo` por salida sobre `GrafoCripta`; `explorar`, `observar_sala`, `explorar_vecinas`, consultas O(1) y listas de exploradas y avistadas (FR-101, FR-102, FR-103, PR-102).

## Phase 2: User Story 1 - Explorar con conocimiento parcial (P1)

### Tests (primero)
- [ ] T103 [P] [US1] `tests/test_niebla.py::test_estado_inicial` y `test_entrar_explora_y_aviste` (FR-101, FR-102).
- [ ] T104 [P] [US1] `tests/test_niebla.py::test_mapa_recuerda_puerta_vieja` y `test_observa_salidas_que_llegan` (FR-103), incluidas salidas de un solo sentido y puertas cerradas de un lado.
- [ ] T105 [P] [US1] `tests/test_niebla.py::test_antorcha_explora_vecinas_sin_activar` (FR-104, Apéndice B).
- [ ] T106 [P] [US1] `tests/test_niebla.py::test_pergamino_revierte_exploracion_con_antorcha` (FR-106, Apéndice B).
- [ ] T107 [P] [US1] `tests/test_niebla.py::test_guardar_y_cargar_conserva_el_mapa` y `test_guardado_version_3_incompatible` (FR-106).

### Implementation
- [ ] T108 [US1] Integrar el mapa en `modelo/estado_partida.py`: explorar la sala inicial en `iniciar()`, explorar y observar al entrar, antorcha al entrar, observar al abrir y al cerrarse una puerta junto al jugador (FR-101 a FR-104, FR-106).
- [ ] T109 [US1] Formato de guardado 4 en `adaptadores/guardado_binario.py` y `adaptadores/guardado_partida.py` con el registro del mapa (FR-106).

## Phase 3: User Story 2 - Viajar con «ir a» (P1)

### Tests (primero)
- [ ] T110 [P] [US2] `tests/test_ir_a.py::test_destino_no_explorado_se_rechaza` y casos borde (FR-109, Apéndice B).
- [ ] T111 [P] [US2] `tests/test_ir_a.py::test_ruta_mas_barata_y_desempate` (FR-110).
- [ ] T112 [P] [US2] `tests/test_ir_a.py::test_puerta_recordada_abierta_esta_cerrada` (FR-103, FR-111, FR-112, Apéndice B).
- [ ] T113 [P] [US2] `tests/test_ir_a.py::test_enemigos_dormidos_detienen_y_se_activan` y `test_dano_detiene` (FR-112, Apéndice B).
- [ ] T114 [P] [US2] `tests/test_ir_a.py::test_pergamino_durante_viaje` (FR-114, Apéndice B).
- [ ] T115 [P] [US2] `tests/test_ir_a.py::test_bitacora_pasos_y_comentario_y_replay` (FR-113).
- [ ] T116 [P] [US2] `tests/test_ir_a.py::test_no_abre_puertas` (FR-111).

### Implementation
- [ ] T117 [US2] `EstadoPartida.paso_hacia(destino)` y motivos nuevos en `modelo/movimiento.py`, con `BuscadorRutas` sobre el mapa conocido (FR-108 a FR-111).
- [ ] T118 [US2] Comando `ir a <sala>` en `controlador/partida.py`: ciclo de pasos con precarga, detención y motivo, anotación de cada paso y del comentario en la bitácora (FR-108, FR-112, FR-113).
- [ ] T119 [US2] `adaptadores/bitacora_partida.py`: comentarios `#` que el replay ignora (FR-113).

## Phase 4: Vista (FR-105, FR-107)

- [ ] T120 [P] `tests/test_vista_niebla.py`: la pantalla no muestra nombres de salas avistadas; `mapa` lista exploradas, salidas, costos, puertas recordadas y avistadas; el motivo de detención se muestra (FR-105, FR-107, FR-112).
- [ ] T121 `vista/consola.py` y `vista/menu_acciones.py`: salidas según el conocimiento del jugador, comando `mapa`, ayuda de `ir a`, y `controlador/partida.py` para que `mapa` no vaya a la bitácora (FR-105, FR-107).

## Phase 5: Mediciones (PR-101, PR-102)

- [ ] T122 `bench/bench_mapa.py`: consultas al mapa (lista frente a `VectorOrdenado`), exploración según el tamaño del mapa, paso de «ir a» en la cripta de referencia explorada completa y en una sintética de 900 salas; integración en `bench/bench.py` (PR-101, PR-102).

## Phase 6: Documentación

- [ ] T123 Sección «Niebla de guerra e ir a» en `DECISIONES.md` con las mediciones de T122, enlaces a spec y plan, y si la decisión final coincide con el plan.
- [ ] T124 `README.md`: comandos `mapa` e `ir a`; `PROMPTS_LLM.md`: comandos de spec-kit de esta capacidad.

## Dependencies

- Phase 1 antes que todo. US1 (Phase 2) antes que US2 (Phase 3): «ir a» usa el mapa.
- Phase 4 depende de Phase 2 y 3. Phase 5 depende de Phase 3. Phase 6 al final.
