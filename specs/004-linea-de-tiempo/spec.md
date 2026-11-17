# Feature Specification: Línea de tiempo con puntos de control

**Feature Branch**: `004-linea-de-tiempo`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Capacidad 'línea de tiempo'. Reglas: @docs/enunciado_parte2.md §3.6, §5.5, §6.1, §7.3 y Apéndice B (sección Línea de tiempo). El pergamino sigue limitado a 5 acciones; la línea de tiempo es independiente y permite consultar sin modificar la partida el estado en cualquier instante desde el inicio. Estado en t: después de todos los eventos con tiempo <= t; si a t le corresponde una decisión del jugador, justo antes de tomarla. 'historia <t>' e 'historia #k' (estado justo antes de la acción k) muestran reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido; no consumen tiempo, no se registran como acción y no alteran el juego ni el historial de retroceso. '--replay partida.log --hasta <t>' imprime el mismo resumen sin la vista. Las acciones revertidas con un pergamino dejan de existir en la línea; consultar un instante posterior al reloj actual se rechaza. Memoria: copias completas del estado (puntos de control) como máximo una cada K acciones del jugador, K con --checkpoint-cada y valor por defecto justificado con mediciones; una consulta no aplica ni deshace más de K acciones; fuera de los puntos de control solo se guarda lo necesario para reconstruir. Si se re-simula, el punto de control incluye el estado del random. Guardar y cargar conserva la línea completa; el formato cambia y un archivo de la primera parte se detecta incompatible. Límite: 50 ms por consulta en una partida de al menos 5000 acciones con K por defecto. Incluye los 6 casos del Apéndice B. Los requisitos se numeran desde FR-301."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el pasado de la partida (Priority: P1)

Como jugador, quiero ver cómo estaba la partida en un instante pasado o antes de una acción mía, sin cambiar nada de la partida actual.

**Why this priority**: Es la función nueva de la capacidad.

**Independent Test**: Jugar varias acciones, consultar `historia #1` y comprobar que muestra el estado inicial y que la partida sigue igual.

**Acceptance Scenarios**:

1. **Given** una partida con varias acciones, **When** el jugador pide `historia #k`, **Then** se muestra el estado justo antes de su acción número k: reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y mapa conocido. (FR-301, FR-302, FR-303)
2. **Given** un instante t pasado, **When** el jugador pide `historia t`, **Then** se muestra el estado después de todos los eventos con tiempo menor o igual que t; si a t le corresponde una decisión del jugador, el estado justo antes de tomarla. (FR-301, FR-302)
3. **Given** varios eventos que ocurren en el mismo instante t, **When** el jugador pide `historia t`, **Then** el estado mostrado es el de después de todos ellos. (FR-302) *(Apéndice B)*
4. **Given** un t mayor que el reloj actual, **When** el jugador pide `historia t`, **Then** la consulta se rechaza. (FR-306) *(Apéndice B)*
5. **Given** cualquier consulta de historia, **When** termina, **Then** el reloj no avanzó, la consulta no está en partida.log, el pergamino puede deshacer exactamente lo mismo que antes y el estado de la partida es idéntico. (FR-304) *(Apéndice B)*
6. **Given** el jugador usó un pergamino que revirtió su última acción, **When** consulta la historia, **Then** la acción revertida no aparece: `historia #k` del número que tenía esa acción muestra el estado actual. (FR-305) *(Apéndice B)*

---

### User Story 2 - Consultar sin jugar (Priority: P2)

Como desarrollador o evaluador, quiero ver el estado de una partida grabada en un instante sin abrir la interfaz.

**Why this priority**: Permite revisar partidas y depurar sin interacción.

**Independent Test**: Reproducir una bitácora con `--hasta` y comparar el resumen con `historia` en la partida original.

**Acceptance Scenarios**:

1. **Given** una partida.log, **When** se ejecuta `--replay partida.log --hasta t`, **Then** se imprime el mismo resumen que mostraría `historia t`, sin instanciar la vista interactiva. (FR-307)
2. **Given** un t posterior al final de la partida grabada, **When** se ejecuta `--replay partida.log --hasta t`, **Then** se muestra el estado final y se indica que la partida terminó antes. (FR-307) *(Apéndice B)*

---

### User Story 3 - Memoria acotada y persistencia (Priority: P1)

Como jugador de partidas largas, quiero que la línea de tiempo no llene la memoria, que las consultas sean rápidas y que guardar y cargar la conserve.

**Why this priority**: Sin estas propiedades la capacidad no cumple las restricciones del enunciado.

**Independent Test**: Jugar 5000 acciones, medir memoria y tiempo de consulta, guardar, cargar y volver a consultar.

**Acceptance Scenarios**:

1. **Given** una partida de 5000 acciones con K por defecto, **When** se consulta cualquier instante, **Then** la consulta aplica o deshace cambios de como máximo K acciones y tarda menos de 50 ms. (FR-308, PR-301)
2. **Given** `--checkpoint-cada K`, **When** se juega, **Then** no hay más de una copia completa del estado cada K acciones del jugador. (FR-308)
3. **Given** una partida guardada con su línea de tiempo, **When** se carga, **Then** las consultas de historia dan los mismos resultados que antes de guardar. (FR-309)
4. **Given** un archivo de partida de la primera parte, **When** se intenta cargar, **Then** se reporta la incompatibilidad de formato y no se carga en silencio. (FR-310) *(Apéndice B)*

---

### Edge Cases

- `historia #k` con k menor que 1 o mayor que el número de la decisión actual: se rechaza. (FR-306)
- `historia` con un argumento que no es número: se rechaza con la forma correcta del comando. (FR-306)
- `historia` en t = 0: el estado inicial, justo antes de la primera acción. (FR-302)
- `historia` del instante actual: el estado actual. (FR-302)
- Consulta en medio de un período en que el jugador espera su turno (entre dos decisiones): se ven los eventos ya ocurridos hasta t. (FR-302)
- Partida terminada: se puede consultar cualquier instante hasta el reloj final. (FR-301)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-301**: El jugador puede consultar el estado de la partida en cualquier instante desde el inicio hasta el reloj actual con `historia <t>`, y el estado justo antes de su acción número k con `historia #k`.
- **FR-302**: El estado en el instante t es el que resulta de ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.
- **FR-303**: La consulta muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento.
- **FR-304**: La consulta no consume tiempo virtual, no se registra como acción ni en partida.log y no altera ningún estado del juego ni del historial de retroceso.
- **FR-305**: Las acciones revertidas con un pergamino dejan de existir en la línea de tiempo: la línea describe la historia de la partida tal como quedó.
- **FR-306**: Consultar un instante posterior al reloj actual, una acción que no existe o un argumento inválido se rechaza sin cambiar nada.
- **FR-307**: `--replay partida.log --hasta <t>` reproduce la partida hasta t e imprime el mismo resumen sin instanciar la vista. Si t es posterior al final de la partida, muestra el estado final e indica que la partida terminó antes.
- **FR-308**: Se guardan copias completas del estado (puntos de control) como máximo una cada K acciones del jugador; K se configura con `--checkpoint-cada K` y su valor por defecto se justifica con mediciones. Una consulta no puede requerir aplicar ni deshacer cambios de más de K acciones del jugador. Fuera de los puntos de control solo se guarda lo necesario para reconstruir los cambios. Si la reconstrucción re-simula, el punto de control incluye el estado del generador de azar.
- **FR-309**: Guardar y cargar la partida conserva la línea de tiempo completa.
- **FR-310**: El formato del archivo de partida cambia de versión; un archivo de una versión anterior (incluida la de la primera parte) se reporta como incompatible y nunca se carga en silencio.

### Performance Requirements

- **PR-301**: Una consulta de historia tarda menos de 50 ms en una partida de al menos 5000 acciones del jugador con K por defecto.
- **PR-302**: La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K acciones; nunca con «acciones por tamaño del estado». Al usar un pergamino, la línea se recorta sin recorrer toda la historia.

### Key Entities

- **Punto de control**: copia completa del estado justo antes de una acción del jugador, una cada K acciones.
- **Registro de la línea**: lo mínimo para reconstruir cada cambio entre puntos de control y el instante de cada decisión del jugador.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-301**: Los 6 casos del Apéndice B (línea de tiempo) tienen una prueba automatizada que los cita.
- **SC-302**: Con K por defecto, una consulta en una partida de 5000 acciones tarda menos de 50 ms.
- **SC-303**: El bench muestra memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control.

## Assumptions

- **Pergamino**: sigue limitado a 5 acciones y su uso no es una acción; la línea de tiempo no lo amplía.
- **Mover el cursor del inventario**: no es una acción, pero sí un cambio de estado que la línea reproduce; el pergamino lo revierte junto con la acción a la que sigue.
- **Llegada de contenido**: traer el contenido de una sala no es una acción del juego y el pergamino no lo deshace; la línea lo reproduce en el mismo orden.
