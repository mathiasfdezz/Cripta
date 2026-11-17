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
    - `modelo.esqueleto.Esqueleto`: Modificado para almacenar costos y construir la lista de salidas entrantes en $O(V + E)$ al inicio.

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

**Decisión**: Dijkstra Compartido con Salidas Entrantes. El recorrido parte del jugador y explora las salidas entrantes (sentido inverso) evaluando el estado real de cada puerta. 
**Complejidad**: $O(R + E_R \log R)$, donde $R$ es el número de salas dentro del rango y $E_R$ son las salidas entrantes en dichas salas, evitando inicializaciones globales gracias a las épocas.

#### 2. Estrategia de Invalidación y Equivalencia
**Problema**: Reutilizar el cálculo previo sin alterar la decisión de "calcular desde cero".
**Decisión**: Caché con Invalidación.
**Justificación**: La apertura/cierre de puertas y el movimiento del jugador invalidan el mapa por modificar la conectividad o el origen. Los cambios de sala de otros actores o modificaciones de velocidad no alteran la topología, por lo que no invalidan el mapa. Reutilizarlo produce exactamente el mismo resultado que un cálculo desde cero, cumpliendo §3.2.

**Casos Especiales de Prueba**: Se incluirán criptas de prueba con salidas de un solo sentido y puertas cerradas unilateralmente.

#### 3. Reescalado de Tiempo (FR-013)
**Problema**: Reprogramar la próxima acción tras un cambio de velocidad.
**Decisión**: Reutilizar `AgendaEventos.cambiar_velocidad` sin modificaciones.

---

## Tareas Iniciales

1. Actualizar `Esqueleto` y `Puerta` para gestionar costos y construir el índice de salidas entrantes ($O(V+E)$).
2. Implementar `RastreadorCazador` con Dijkstra acotado ($R, E_R$), sistema de épocas y manejo de salidas dirigidas.
3. Integrar la invalidación del `RastreadorCazador` en el modelo.
4. Implementar el comportamiento `cazador` en los enemigos.
5. Añadir escenarios de benchmark en `bench/bench_cazadores.py`, incluyendo criptas con salidas de un solo sentido y puertas cerradas en un solo sentido.
