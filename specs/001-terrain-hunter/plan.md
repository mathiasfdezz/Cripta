# Implementation Plan: Terreno y cazador

**Feature Branch**: `001-terrain-hunter`

**Created**: 2026-11-15

**Status**: Draft

## Technical Context

- **Feature Spec**: [specs/001-terrain-hunter/spec.md](spec.md)
- **Research**: [research.md](research.md)
- **Data Model**: [data-model.md](data-model.md)
- **Dependencies**:
    - `estructuras.min_heap.MinHeap`: Reutilizado para Dijkstra.
    - `modelo.agenda_eventos.AgendaEventos`: Reutilizado para reescalado de tiempo (FR-013).
    - `modelo.esqueleto.Esqueleto`: Modificado para numerar las salidas y anotar qué puertas cambiaron.
    - `modelo.grafo_cripta.GrafoCripta` (nuevo): índices densos, salidas entrantes y salientes con costo, construido en $O(V + E)$ al inicio.
    - `modelo.buscador_rutas.BuscadorRutas` (nuevo): Dijkstra acotado desde el jugador con épocas e invalidación selectiva.

## Constitution Check

- **Propia Implementación**: Se usará `MinHeap` artesanal y listas indexadas mediante índices densos (Principio I).
- **Determinismo**: El desempate por ID y el uso de la agenda garantizan determinismo (Principio II).
- **Rendimiento**: Se medirán alternativas con decenas de cazadores y escenarios de asimetría (Principio VI).

## Borrador para DECISIONES.md

### Capacidad: Terreno y cazador

#### 1. Búsqueda de ruta de costo mínimo (Cazador y Salidas Dirigidas)
**Problema**: Encontrar el camino de menor costo acumulado hacia el jugador considerando que las salidas son estrictamente dirigidas y con estados de puertas independientes (sin asumir simetría).

**Alternativas Medidas**:
1. **Dijkstra Individual**: Cada cazador realiza su propia búsqueda.
2. **Dijkstra Compartido (Caché con Salidas Entrantes)**: Un único cálculo desde el jugador utilizando la lista de salidas entrantes pre-calculadas en $O(V + E)$ al cargar la cripta.

**Decisión**: Dijkstra Compartido con Salidas Entrantes. El recorrido parte del jugador y explora las salidas entrantes (sentido inverso) evaluando el estado real de cada puerta. La cota es el mayor rango de los cazadores conocidos.
**Complejidad**: $O(R + E_R \log R)$, donde $R$ es el número de salas dentro del rango y $E_R$ son las salidas entrantes en dichas salas, evitando inicializaciones globales gracias a las épocas.

#### 2. Estrategia de Invalidación y Equivalencia
**Problema**: Reutilizar el cálculo previo sin alterar la decisión de "calcular desde cero".
**Decisión**: Caché con Invalidación.
**Justificación**: El movimiento del jugador invalida el mapa (cambia el origen). La apertura o cierre de la salida u→x invalida solo si x quedó asentada en el último cálculo (research.md §2 tiene la demostración); una puerta lejana no obliga a recalcular. Los cambios de sala de otros actores, las muertes y los cambios de velocidad no alteran la topología. Reutilizarlo produce exactamente el mismo resultado que un cálculo desde cero, cumpliendo §3.2; las pruebas lo comparan en cada turno contra un cálculo desde cero.

**Casos Especiales de Prueba**: Se incluirán criptas de prueba con salidas de un solo sentido y puertas cerradas unilateralmente.

#### 3. Reescalado de Tiempo (FR-013)
**Problema**: Reprogramar la próxima acción tras un cambio de velocidad.
**Decisión**: Reutilizar `AgendaEventos.cambiar_velocidad` sin modificaciones.

---

## Mediciones Planificadas

- Cripta de referencia (cripta-06, 300 salas, 36 cazadores en su contenido) con todos los cazadores activos: ciclo entre dos decisiones del jugador, límite 20 ms (PR-001).
- Cripta sintética de 900 salas con 60 cazadores, rango 300 y rango 2400: compartido frente a individual.
- Puertas estables frente a inestables: reutilizar frente a recalcular siempre.

## Tareas Iniciales

1. Actualizar `Esqueleto` y `Puerta` para numerar las salidas, gestionar costos y anotar cambios de puertas; construir `GrafoCripta` ($O(V+E)$).
2. Implementar `BuscadorRutas` con Dijkstra acotado ($R, E_R$), sistema de épocas y manejo de salidas dirigidas.
3. Integrar la invalidación selectiva del `BuscadorRutas` en el modelo.
4. Implementar el comportamiento `cazador` en los enemigos.
5. Añadir escenarios de benchmark en `bench/bench_cazadores.py`, incluyendo criptas con salidas de un solo sentido y puertas cerradas en un solo sentido.
