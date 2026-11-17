# Feature Specification: Verificación de resolubilidad

**Feature Branch**: `003-resolubilidad`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Capacidad 'verificación de resolubilidad'. Reglas: @docs/enunciado_parte2.md §3.5, §4.2, §4.3, §5.4, §7.3 y Apéndice B (sección Resolubilidad). Antes de iniciar una partida el programa determina si la cripta puede ganarse usando el esqueleto y la ubicación de las llaves (GET /criptas/<id>/llaves, que cuenta en el presupuesto y se persiste validada por versión). Supuestos: se atraviesa cualquier salida abierta y cualquier salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se obtiene en la sala donde ese enemigo inicia; trampas y cierres automáticos no bloquean. Resoluble: partiendo de la sala inicial se obtiene llave_salida y se llega a sala_salida por una puerta que la requiere. Si es resoluble, se informa un orden determinista de obtención de llaves donde cada llave aparece después de las necesarias para alcanzarla. Si no: llaves no obtenibles, puertas de la frontera bloqueada con la llave que pide cada una y dónde está cada llave, y el ciclo concreto si una llave está detrás de puertas que solo ella abre, directamente o por una cadena de llaves. Sin resolubilidad la partida no inicia salvo con --forzar. --verificar <cripta> solo verifica, sin la vista. La interfaz muestra el reporte al iniciar. Límite: 200 ms en la cripta publicada más grande; el costo debe crecer de forma aproximadamente lineal con salas, salidas y llaves. Incluye los 4 casos del Apéndice B. Los requisitos se numeran desde FR-201."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber antes de jugar si la cripta se puede ganar (Priority: P1)

Como jugador, quiero que el programa me diga antes de empezar si la cripta tiene solución y, si la tiene, en qué orden conseguir las llaves.

**Why this priority**: El servicio publica criptas imposibles; jugar una de ellas sin saberlo es perder el tiempo.

**Independent Test**: Verificar una cripta resoluble y comprobar el orden de llaves que se informa.

**Acceptance Scenarios**:

1. **Given** una cripta resoluble, **When** se verifica, **Then** el resultado es «resoluble» con un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. (FR-201, FR-203, FR-204)
2. **Given** una cripta con varios órdenes válidos de obtención de llaves, **When** se verifica dos veces, **Then** las dos ejecuciones informan el mismo orden. (FR-204) *(Apéndice B)*
3. **Given** una llave que está en el campo `suelta` de un enemigo errante, **When** se verifica, **Then** la llave se considera obtenible en la sala donde ese enemigo inicia, aunque el enemigo se mueva durante la partida. (FR-202) *(Apéndice B)*
4. **Given** una partida que va a empezar, **When** termina la verificación, **Then** la interfaz muestra el reporte antes del primer turno. (FR-209)

---

### User Story 2 - Entender por qué una cripta no tiene solución (Priority: P1)

Como jugador, si la cripta no se puede ganar quiero saber qué llaves faltan, qué puertas bloquean el avance, dónde están sus llaves y si hay un ciclo de llaves, y que la partida no empiece salvo que yo lo fuerce.

**Why this priority**: Es lo que distingue un reporte útil de un simple «no».

**Independent Test**: Verificar una cripta con un ciclo de llaves y revisar el reporte.

**Acceptance Scenarios**:

1. **Given** `llave_salida` está detrás de la única puerta que ella misma abre, **When** se verifica, **Then** la cripta no es resoluble y el reporte señala el ciclo de esa llave consigo misma. (FR-205, FR-206) *(Apéndice B)*
2. **Given** una llave A detrás de una puerta que pide la llave B y la llave B detrás de una puerta que pide la llave A, **When** se verifica, **Then** el reporte muestra el ciclo A → B → A con las puertas involucradas. (FR-206)
3. **Given** una cripta no resoluble, **When** se verifica, **Then** el reporte lista las llaves no obtenibles, cada puerta cerrada adyacente a la región alcanzable con la llave que pide, y dónde está cada una de esas llaves. (FR-205)
4. **Given** una cripta no resoluble y sin `--forzar`, **When** se intenta iniciar la partida, **Then** la partida no inicia y se muestra el reporte. (FR-207) *(Apéndice B)*
5. **Given** una cripta no resoluble y con `--forzar`, **When** se inicia la partida, **Then** se muestra el reporte y la partida empieza igual. (FR-207)
6. **Given** `--verificar <cripta>`, **When** se ejecuta, **Then** se imprime el reporte sin instanciar la vista interactiva ni empezar una partida, y el código de salida indica si es resoluble. (FR-208)

---

### Edge Cases

- Una puerta cerrada que no declara llave nunca se abre: forma parte de la frontera si bloquea, con la indicación «sin llave». (FR-205)
- Una puerta pide una llave que no aparece en la ubicación de llaves: esa llave no es obtenible y el reporte dice que no está en la cripta. (FR-205)
- `llave_salida` se obtiene pero ninguna puerta alcanzable que la pide lleva a `sala_salida`: no resoluble. (FR-203)
- La sala de salida es alcanzable por una puerta abierta, pero no por una que pida `llave_salida`: no cuenta como resoluble. (FR-203)
- Varias llaves en la misma sala: se obtienen en orden de id. (FR-204)
- Una llave en una sala inalcanzable incluso abriendo todas las puertas con llave (por ejemplo, detrás de una puerta sin llave): no obtenible y sin ciclo. (FR-205, FR-206)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-201**: Antes de iniciar una partida, el programa determina si la cripta es resoluble usando solo el esqueleto (con el estado inicial de sus puertas) y la ubicación de las llaves que publica el servicio.
- **FR-202**: Supuestos de la verificación: se puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se obtiene en la sala donde ese enemigo inicia; las trampas y los cierres automáticos no bloquean.
- **FR-203**: Una cripta es resoluble si, partiendo de la sala inicial, se puede obtener `llave_salida` y llegar a `sala_salida` a través de una salida cerrada que la requiere.
- **FR-204**: Si es resoluble, el resultado incluye un orden de obtención de las llaves alcanzables en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. El orden es determinista: misma cripta, mismo orden.
- **FR-205**: Si no es resoluble, el resultado incluye: las llaves no obtenibles (y las que ninguna sala contiene); las puertas de la frontera bloqueada, es decir, las salidas cerradas cuyo origen es alcanzable y cuyo destino no lo es, con la llave que requiere cada una; y dónde se encuentra cada una de esas llaves (sala, y enemigo si la suelta uno).
- **FR-206**: Si una llave está detrás de puertas que solo ella abre, directamente o mediante una cadena de llaves, el reporte señala ese ciclo con las llaves y las puertas que lo forman. La detección es determinista y reporta un ciclo concreto.
- **FR-207**: Si la cripta no es resoluble, la partida no inicia salvo que se use `--forzar`; en ambos casos se muestra el reporte.
- **FR-208**: `--verificar <cripta>` ejecuta solo la verificación, imprime el reporte y termina sin instanciar la vista interactiva. Código de salida 0 si es resoluble y 1 si no.
- **FR-209**: La interfaz muestra el reporte de resolubilidad al iniciar una partida.
- **FR-210**: La ubicación de las llaves se obtiene del servicio (cuenta en `presupuesto_solicitudes`), se guarda junto con el resto de los datos de la cripta y se reutiliza mientras la versión de la cripta no cambie. El modo `--offline` la lee del paquete local.

### Performance Requirements

- **PR-201**: La verificación termina en menos de 200 ms en la cripta publicada más grande.
- **PR-202**: El costo total crece aproximadamente de forma lineal con salas, salidas y llaves: obtener una llave no repite el recorrido de lo ya alcanzado, y el reporte de una cripta no resoluble sale del mismo recorrido.

### Key Entities

- **Ubicación de llave**: id de la llave, sala y, si la suelta un enemigo, su instancia.
- **Reporte de resolubilidad**: resoluble o no, orden de llaves, llaves no obtenibles, frontera bloqueada, ciclo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-201**: Los 4 casos del Apéndice B (resolubilidad) tienen una prueba automatizada que los cita.
- **SC-202**: La verificación de la cripta de referencia tarda menos de 200 ms.
- **SC-203**: En criptas sintéticas con muchas llaves encadenadas, el recorrido incremental crece linealmente y el recorrido repetido por llave no.

## Assumptions

- **Estado inicial**: la verificación usa las puertas como las declara el API al iniciar, no como estén en una partida en curso.
- **Llave de la salida**: la puerta de la salida es la que pide `llave_salida` y tiene como destino `sala_salida`.
- **Replay**: `--replay` no verifica; reproduce lo que se jugó.
