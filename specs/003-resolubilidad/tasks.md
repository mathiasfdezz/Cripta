# Tasks: Verificación de resolubilidad

**Input**: `specs/003-resolubilidad/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`)
**Requirements Coverage**: FR-201 a FR-210, PR-201, PR-202.

## Phase 1: Datos de las llaves (FR-210)

- [X] T201 [P] `dtos/ubicacion_llave.py` y `adaptadores/mapeadores/mapeador_llaves.py`, con prueba de mapeo en `tests/test_mapeador_llaves.py` (FR-210).
- [X] T202 `llaves(cripta_id)` en `adaptadores/fuente_datos.py`, `cliente_red.py`, `cliente_red_con_copia.py` (copia en disco validada por versión), `cliente_offline.py` y `rutas_offline.py`; `descargador_offline.py` también la descarga; pruebas en `tests/test_cliente_red_con_copia.py` y `tests/test_cliente_offline.py` (FR-210).

## Phase 2: User Story 1 y 2 - Verificador (P1)

### Tests (primero)
- [ ] T203 [P] [US1] `tests/test_resolubilidad.py::test_resoluble_con_orden` (FR-201, FR-203, FR-204).
- [ ] T204 [P] [US1] `test_orden_determinista_con_varios_validos` (FR-204, Apéndice B).
- [ ] T205 [P] [US1] `test_llave_de_errante_en_su_sala_inicial` (FR-202, Apéndice B).
- [ ] T206 [P] [US2] `test_llave_salida_detras_de_su_propia_puerta` (FR-205, FR-206, Apéndice B).
- [ ] T207 [P] [US2] `test_ciclo_de_dos_llaves` y `test_cripta_sellada_publicada` con el paquete offline (FR-206).
- [ ] T208 [P] [US2] `test_reporte_frontera_y_ubicaciones`, `test_puerta_sin_llave`, `test_llave_que_no_esta`, `test_salida_sin_puerta_que_la_pida` (FR-203, FR-205).

### Implementation
- [ ] T209 `modelo/puerta_bloqueada.py` y `modelo/reporte_resolubilidad.py` (FR-204, FR-205, FR-206).
- [ ] T210 `modelo/verificador_resolubilidad.py`: recorrido incremental con puertas pendientes por llave, frontera, dependencias por 0-1 BFS y ciclo por DFS iterativo (FR-201 a FR-206, PR-202).

## Phase 3: Integración (FR-207, FR-208, FR-209)

- [ ] T211 `controlador/verificacion_cripta.py`: carga esqueleto y llaves y verifica; `ControladorPartida` acepta el esqueleto ya cargado (FR-201, FR-210).
- [ ] T212 `vista/texto_resolubilidad.py` (formateador) y `Consola.mostrar_resolubilidad` (FR-209).
- [ ] T213 `main.py`: `--verificar <cripta>` sin vista y con código de salida; `--forzar`; verificación antes de cada partida (FR-207, FR-208).
- [ ] T214 [P] `tests/test_verificar_main.py`: no resoluble sin `--forzar` no inicia y muestra el reporte (Apéndice B); con `--forzar` inicia; la consola muestra el reporte antes del primer turno; `--verificar` no instancia `Consola` y devuelve 0 o 1 (FR-207, FR-208, FR-209).

## Phase 4: Mediciones (PR-201, PR-202)

- [ ] T215 `bench/resolubilidad_repetida.py` (alternativa) y `bench/bench_resolubilidad.py`: criptas publicadas y sintéticas con 50, 200 y 800 llaves encadenadas; integración en `bench/bench.py` (PR-201, PR-202).

## Phase 5: Documentación

- [ ] T216 Sección «Resolubilidad» en `DECISIONES.md`; `README.md` con `--verificar` y `--forzar`; `PROMPTS_LLM.md` con los comandos de spec-kit de esta capacidad.

## Dependencies

Phase 1 → Phase 2 → Phase 3. Phase 4 depende de Phase 2. Phase 5 al final.
