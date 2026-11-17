# Feature Specification: Niebla de guerra y viaje automático «ir a»

**Feature Branch**: `002-niebla-ir-a`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Capacidad 'niebla de guerra e ir a'. Reglas: @docs/enunciado_parte2.md §3.3, §3.4, §7.3 y Apéndice B (sección Niebla de guerra e «ir a»). Cubre: (1) estados de sala para el jugador: explorada (entró al menos una vez; la inicial desde t=0), avistada (destino de una salida de una sala explorada) y desconocida; (2) memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta y el mapa recuerda el último estado observado; (3) antorcha encendida: al entrar a una sala se exploran también sus vecinas por cualquier salida, sin activar enemigos ni trampas ni revelar contenido; (4) la vista y 'ir a' usan solo el conocimiento del jugador; el esqueleto completo sigue siendo infraestructura de precarga; (5) el conocimiento se guarda, se revierte con el pergamino y entra en la línea de tiempo; (6) comando para ver el mapa conocido; (7) 'ir a <sala>' hacia una sala explorada por una secuencia de movimientos ordinarios, ruta de costo mínimo solo por salas exploradas y salidas recordadas abiertas, desempate como el cazador, recálculo antes de cada paso, se detiene al llegar, al entrar a una sala con enemigos, al recibir daño o si deja de existir ruta, no abre puertas, cada paso va a partida.log como movimiento y la orden como comentario, el pergamino revierte solo el último paso. Incluye los 6 casos del Apéndice B y el límite de 5 ms por paso con el mapa completo de la cripta de referencia. Los requisitos se numeran desde FR-101 para que sean únicos en el proyecto."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explorar con conocimiento parcial (Priority: P1)

Como jugador, solo conozco las salas en las que estuve y lo que vi desde ellas, para que explorar la cripta sea parte del desafío.

**Why this priority**: Cambia qué información recibe el jugador en cada pantalla y es la base de «ir a».

**Independent Test**: Iniciar una partida y comprobar el estado de cada sala antes y después de moverse.

**Acceptance Scenarios**:

1. **Given** una partida recién iniciada, **When** el jugador consulta su mapa, **Then** la sala inicial está explorada, los destinos de sus salidas están avistados y el resto es desconocido. (FR-101, FR-102)
2. **Given** el jugador entra a una sala avistada, **When** se completa el movimiento, **Then** esa sala pasa a explorada y los destinos de sus salidas que eran desconocidos pasan a avistados. (FR-101, FR-102)
3. **Given** una puerta que el jugador vio abierta y que luego se cerró sola mientras estaba lejos, **When** el jugador consulta su mapa, **Then** el mapa la sigue mostrando abierta. (FR-103)
4. **Given** la antorcha encendida, **When** el jugador entra a una sala, **Then** todas las vecinas de esa sala (por cualquier salida, abierta o cerrada) quedan exploradas sin activar a sus enemigos ni sus trampas y sin revelar su contenido. (FR-104) *(Apéndice B)*
5. **Given** el jugador entró con la antorcha encendida y exploró cinco salas, **When** usa un pergamino de retroceso, **Then** las salas exploradas por esa entrada (incluidas las de la antorcha) vuelven a su estado anterior. (FR-106) *(Apéndice B)*
6. **Given** cualquier momento de la partida, **When** el jugador pide ver el mapa, **Then** se listan las salas exploradas con sus salidas, costos y estado recordado de las puertas, y las salas avistadas. (FR-107)

---

### User Story 2 - Viajar a una sala conocida con «ir a» (Priority: P1)

Como jugador, quiero ordenar «ir a <sala>» para recorrer automáticamente un camino conocido sin dar cada paso, y saber por qué se detuvo el viaje si no llegó.

**Why this priority**: Es la acción nueva que usa el mapa conocido y el cálculo de rutas.

**Independent Test**: Explorar varias salas, volver a la inicial con «ir a» y revisar los pasos registrados en la bitácora.

**Acceptance Scenarios**:

1. **Given** una sala que el jugador no ha explorado, **When** ordena «ir a» hacia ella, **Then** la orden se rechaza y el reloj no avanza. (FR-109) *(Apéndice B)*
2. **Given** dos rutas conocidas hacia el destino, **When** el jugador ordena «ir a», **Then** se sigue la de menor costo total, y entre rutas de igual costo el primer paso va a la vecina de menor id. (FR-110)
3. **Given** el mapa recuerda abierta una puerta de la ruta que en realidad está cerrada, **When** el jugador llega a una de las salas que conecta, **Then** el mapa se actualiza, la ruta se recalcula evitándola y, si no queda ruta, el viaje se detiene sin consumir tiempo adicional. (FR-103, FR-111, FR-112) *(Apéndice B)*
4. **Given** la ruta pasa por una sala con enemigos dormidos, **When** el viaje entra a esa sala, **Then** los enemigos se activan según P1 §2.4 y el viaje se detiene. (FR-112) *(Apéndice B)*
5. **Given** un viaje en curso, **When** el jugador recibe daño en un paso (ataque, trampa o veneno), **Then** el viaje se detiene después de ese paso. (FR-112)
6. **Given** un viaje que dio varios pasos, **When** el jugador usa un pergamino, **Then** se revierte solo el último paso y el viaje no continúa. (FR-114) *(Apéndice B)*
7. **Given** un viaje terminado, **When** se revisa partida.log, **Then** cada paso aparece como un movimiento individual y la orden «ir a» aparece como comentario, y al reproducir la bitácora se obtiene la misma partida. (FR-113)
8. **Given** una puerta cerrada en la única ruta conocida y el jugador tiene su llave, **When** ordena «ir a», **Then** el viaje no abre la puerta: no hay ruta y se informa sin consumir tiempo. (FR-111, FR-112)

---

### Edge Cases

- «ir a» hacia la sala actual: se informa que ya está ahí y no se consume tiempo. (FR-109)
- El destino es un número que no corresponde a ninguna sala o no es un número: se rechaza sin consumir tiempo. (FR-109)
- Durante el viaje la partida termina (victoria o derrota): el viaje se detiene. (FR-112)
- El contenido de la siguiente sala no se pudo traer (por ejemplo, presupuesto agotado): el viaje se detiene sin consumir tiempo en ese paso. (FR-112)
- Salidas de un solo sentido y puertas cerradas de un solo lado: el mapa recuerda cada salida por separado. (FR-103)
- Una sala avistada a la que solo se llega por una salida cerrada sigue avistada. (FR-102)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-101**: Para el jugador, cada sala está explorada, avistada o desconocida. Una sala queda explorada cuando el jugador entra a ella al menos una vez; la sala inicial está explorada desde el instante 0. Una sala explorada no deja de estarlo salvo por un pergamino o al consultar la línea de tiempo.
- **FR-102**: Una sala no explorada está avistada si es destino de alguna salida de una sala explorada; si no, es desconocida.
- **FR-103**: El jugador observa una salida cuando está en su sala de origen o en su sala de destino; al observarla, el mapa guarda su estado actual (abierta o cerrada). El mapa recuerda el estado de la última observación aunque la puerta haya cambiado después. Explorar una sala, entrando o con la antorcha, observa todas sus salidas en ese instante.
- **FR-104**: Mientras la antorcha está encendida, al entrar a una sala también quedan exploradas todas sus vecinas a través de cualquier salida, abierta o cerrada. Explorar una vecina así revela su nombre y salidas, no su contenido, y no activa sus enemigos ni sus trampas.
- **FR-105**: Lo que la vista muestra de la cripta y lo que usa «ir a» se deriva exclusivamente del conocimiento del jugador. La precarga de contenido puede seguir usando el esqueleto completo.
- **FR-106**: El conocimiento del jugador es estado del juego: se guarda en el archivo de partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo.
- **FR-107**: El comando `mapa` muestra las salas exploradas con sus salidas, el costo de cada salida y el estado recordado de cada puerta, y las salas avistadas. No consume tiempo ni se registra como acción.
- **FR-108**: El comando `ir a <sala>` lleva al jugador a una sala explorada mediante una secuencia de movimientos ordinarios. Cada paso es una acción completa del jugador: consume el tiempo de la salida según la capacidad 001 y entre paso y paso ocurren normalmente los eventos del reloj.
- **FR-109**: «ir a» hacia una sala que no está explorada, que no existe o que es la sala actual se rechaza sin consumir tiempo.
- **FR-110**: La ruta se calcula solo con salas exploradas y salidas que el mapa recuerda abiertas, minimizando la suma de costos; ante empate, el primer paso va a la vecina de menor id (mismo criterio que el cazador).
- **FR-111**: La ruta se recalcula antes de cada paso con el conocimiento vigente. «ir a» nunca abre puertas, aunque el jugador tenga la llave.
- **FR-112**: El viaje se detiene cuando: el jugador llega al destino; entra a una sala que contiene enemigos, activos o dormidos; recibe daño durante un paso; deja de existir una ruta conocida; la partida termina; o el siguiente paso no puede darse (por ejemplo, el contenido de la sala siguiente no está disponible). Detenerse no consume tiempo adicional. La interfaz informa el motivo.
- **FR-113**: En partida.log cada paso se registra como un movimiento individual (`n`, `s`, `e`, `o`) y la orden se registra además como comentario (`# ir a <sala>`). La reproducción ignora los comentarios.
- **FR-114**: El pergamino de retroceso revierte únicamente el último paso del viaje, porque cada paso es una acción del jugador. El viaje no se reanuda.

### Performance Requirements

- **PR-101**: Calcular un paso de «ir a» toma menos de 5 ms con el mapa conocido completo de la cripta de referencia.
- **PR-102**: Consultar el estado de una sala o el estado recordado de una puerta no depende del tamaño del mapa conocido; explorar nuevas salas cuesta proporcionalmente a las salas reveladas.

### Key Entities

- **Mapa conocido**: estado de cada sala para el jugador y estado recordado de cada salida observada.
- **Viaje**: destino, pasos dados y motivo de detención.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: Los 6 casos del Apéndice B (niebla de guerra e «ir a») tienen una prueba automatizada que los cita.
- **SC-102**: Un paso de «ir a» se calcula en menos de 5 ms en la cripta de referencia con todo su mapa explorado.
- **SC-103**: Reproducir con `--replay` una bitácora que contiene viajes produce exactamente la misma partida.

## Assumptions

- **Contenido**: explorar con la antorcha no descarga ni revela el contenido de la sala; el contenido sigue llegando por la precarga como en la primera parte.
- **Movimiento manual**: moverse sin «ir a» no cambia de reglas; solo se agrega la exploración y la observación de puertas.
- **Sin destino ambiguo**: el argumento de «ir a» es el id numérico de una sala, como lo muestra el mapa.
