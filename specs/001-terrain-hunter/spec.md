# Feature Specification: Terreno y cazador

**Feature Branch**: `001-terrain-hunter`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Capacidad 'terreno y cazador'. Reglas: @docs/enunciado_parte2.md §3.1, §3.2 y Apéndice B (sección Terreno y cazador). Cubre: (1) costo por salida (entero >= 1, 100 si no se declara o es null, igual en ambos sentidos); mover cuesta el costo de la salida e intervalo = max(1, costo_salida*100//velocidad) para todos los actores; atacar, esperar y demás acciones no cambian; errantes y rastreadores solo cambian lo que tarda su movimiento. (2) Cazador: ficha con rango; reglas en orden (ataca si comparte sala; si no, costo mínimo d por salidas abiertas en ese instante; espera con costo 100 si no hay ruta o d > rango; si no, un paso por una ruta de costo d); desempate: la vecina de menor id; conoce esqueleto completo y puertas actuales, no le afecta la niebla ni el contenido descargado; no abre puertas; su decisión equivale siempre a calcular desde cero. (3) La vista muestra costos de las salidas de la sala actual y distingue cazadores. Incluye los 7 casos del Apéndice B de esta capacidad como escenarios de aceptación, y el requisito de 20 ms por ciclo con decenas de cazadores activos."

## Clarifications

### Session 2026-11-15

- Q: ¿Cómo deben interactuar varios cazadores que comparten sala con el jugador o entre sí? → A: No hay límite; múltiples cazadores pueden estar en la misma sala y cada uno ataca en su turno.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Movimiento por terreno con costos variables (Priority: P1)

Como cualquier actor en la cripta, quiero que mi movimiento consuma tiempo proporcional al costo de la salida que atravieso, para que el terreno influya en la velocidad de desplazamiento por el esqueleto.

**Why this priority**: Es la mecánica fundamental que altera el cálculo del tiempo y afecta a todos los comportamientos de actores.

**Independent Test**: Se puede verificar observando el incremento del reloj del juego tras un movimiento en una salida con costo distinto de 100.

**Acceptance Scenarios**:

1. **Given** un actor con velocidad 200 en una sala con una salida de costo 50, **When** el actor se mueve a través de esa salida, **Then** el intervalo de tiempo transcurrido es 25 (`max(1, 50 * 100 // 200)`). (FR-003)
2. **Given** un actor con velocidad alta (p.ej. 1000) atravesando una salida de costo 1, **When** el actor se mueve, **Then** el intervalo de tiempo resultante es al menos 1. (FR-003)
3. **Given** un actor que acaba de moverse por una salida de costo alto y cuya próxima acción está programada, **When** un efecto cambia su velocidad en el instante t, **Then** el tiempo restante hasta esa acción se reescala como `max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)` (P1 §2.3) y la acción queda reprogramada con un número de secuencia nuevo. (FR-013)

---

### User Story 2 - Comportamiento del Cazador (Priority: P1)

Como enemigo cazador, quiero perseguir al jugador utilizando la ruta de menor costo acumulado, respetando mi rango y el estado de las puertas, para actuar como un depredador eficiente.

**Why this priority**: Introduce un nuevo tipo de desafío táctico que requiere que el jugador considere los costos del terreno y el alcance del enemigo.

**Independent Test**: Colocar un cazador en una cripta con múltiples rutas y observar si elige la de menor costo y si espera cuando el jugador está fuera de rango.

**Acceptance Scenarios**:

1. **Given** un cazador que no tiene ninguna ruta de salidas abiertas hacia el jugador, **When** es su turno, **Then** el cazador espera (acción de costo 100). (FR-006)
2. **Given** un cazador cuya ruta de costo mínimo `d` hacia el jugador es tal que `d > rango`, **When** es su turno, **Then** el cazador espera (acción de costo 100). (FR-006)
3. **Given** un cazador con una ruta de menos salas pero mayor costo y otra ruta de más salas pero menor costo total, **When** es su turno, **Then** el cazador elige moverse por el primer paso de la ruta de menor costo acumulado. (FR-005)
4. **Given** un cazador con dos salas vecinas que inician rutas distintas pero de igual costo mínimo hacia el jugador, **When** debe decidir su movimiento, **Then** se mueve hacia la sala vecina que tenga el identificador (ID) numérico menor. (FR-007)
5. **Given** un cazador que tiene una ruta planificada hacia el jugador, **When** una puerta en esa ruta se cierra entre dos de sus turnos, **Then** en su siguiente turno decide su acción como si calculara desde cero, ignorando la ruta anterior. (FR-009)
6. **Given** múltiples cazadores y el jugador en la misma sala, **When** es el turno de cada cazador, **Then** cada cazador ataca individualmente sin que la presencia de otros cazadores lo impida. (FR-015)

---

### User Story 3 - Información Táctica en la Vista (Priority: P2)

Como jugador, quiero identificar visualmente a los cazadores y conocer los costos de las salidas de mi sala actual, para planificar mis movimientos y evitar ser alcanzado.

**Why this priority**: Permite al jugador interactuar con las nuevas mecánicas de forma informada.

**Independent Test**: Inspeccionar la interfaz en una sala con salidas de costos variados y presencia de cazadores.

**Acceptance Scenarios**:

1. **Given** el jugador en una sala, **When** observa las salidas disponibles, **Then** la vista muestra el costo asociado a cada una de ellas. (FR-010)
2. **Given** una sala con varios enemigos, **When** el jugador consulta los enemigos presentes, **Then** los cazadores se distinguen claramente de los errantes y rastreadores. (FR-011)

---

### Edge Cases

- **Costo no definido**: Si una salida no declara `costo` o es `null`, se asume un costo de 100. (FR-001)
- **Costo mínimo**: El costo de una salida debe ser siempre un entero >= 1. (FR-001)
- **Salidas cerradas**: El cazador solo considera rutas que utilicen puertas actualmente abiertas, aunque conoce el esqueleto completo. (FR-008)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada salida del esqueleto puede declarar un costo (entero >= 1). Si no se declara o es `null`, el costo es 100. El costo es idéntico en ambos sentidos de la salida.
- **FR-002**: La acción de moverse por una salida tiene un costo igual al valor de costo de dicha salida.
- **FR-003**: El intervalo de tiempo de un movimiento se calcula como `max(1, costo_salida * 100 // velocidad)`. Esta regla aplica a todos los actores.
- **FR-004**: Los cazadores poseen un atributo "rango" (umbral de costo acumulado).
- **FR-005**: El cazador ataca si comparte sala con el jugador. Si no, busca el costo mínimo `d` sumando los costos de las salidas de rutas abiertas.
- **FR-006**: El cazador espera (costo 100) si no existe ruta abierta hacia el jugador o si el costo mínimo `d` es mayor que su rango (`d > rango`).
- **FR-007**: Ante múltiples rutas de igual costo mínimo `d`, el cazador desempata moviéndose a la sala vecina con menor ID.
- **FR-008**: El cazador conoce el esqueleto completo y el estado actual de las puertas. No le afecta la niebla de guerra ni requiere descarga de contenido.
- **FR-009**: La decisión del cazador se calcula desde cero en cada turno.
- **FR-010**: La interfaz DEBE mostrar los costos de las salidas de la sala actual.
- **FR-011**: La interfaz DEBE distinguir a los cazadores de otros tipos de enemigos.
- **FR-012**: El costo base de otras acciones no cambia: usar objeto (50), recoger/soltar (25), abrir puerta (50), atacar/esperar (100). Solo cambia el costo de movimiento.
- **FR-013**: Si un efecto cambia la velocidad de un actor con una acción ya programada (incluida la que sigue a un movimiento por una salida costosa), el tiempo restante se reescala según P1 §2.3 y la reprogramación recibe un número de secuencia nuevo.
- **FR-014**: Si existe una ruta abierta y `d <= rango`, el cazador se mueve un paso por una ruta de costo `d`; el costo de esa acción es el de la salida que atraviesa (FR-002).
- **FR-015**: No existe límite de ocupación por sala; múltiples cazadores pueden coexistir en la misma sala y con el jugador, ejecutando cada uno su acción (ataque o movimiento) de forma independiente.

### Performance Requirements

- **PR-001**: En la cripta de referencia, el ciclo de eventos entre dos decisiones del jugador debe ejecutarse en menos de 20 ms con decenas de cazadores activos.

### Key Entities *(include if feature involves data)*

- **Salida**: Conexión en el esqueleto. Atributo clave: `costo`.
- **Cazador**: Enemigo. Atributo clave: `rango` (umbral de costo).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Procesamiento del ciclo de eventos en < 20ms con 30+ cazadores.
- **SC-002**: El 100% de los 7 casos del Apéndice B (Terreno y cazador) verificados mediante pruebas.
- **SC-003**: Cálculo exacto del intervalo de movimiento según la fórmula FR-003 para velocidades de 50 a 500 y costos de 1 a 1000.

## Assumptions

- **Persistencia**: El costo de las salidas se descarga del esqueleto y se mantiene mientras la versión de la cripta no cambie.
- **No apertura de puertas**: El cazador nunca abre puertas cerradas por sí mismo.
- **Costo de acción vs Intervalo**: Se mantiene la distinción entre el costo de la acción (que afecta al reloj de la próxima acción del actor) y el intervalo (que es el tiempo que realmente transcurre).
