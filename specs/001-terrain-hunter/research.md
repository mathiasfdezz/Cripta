# Research: Terreno y cazador

## Decisiones Técnicas

### 1. Algoritmo de Búsqueda y Desempate (Salidas Dirigidas y Conectividad Real)
- **Naturaleza Dirigida**: El API describe cada salida como dirigida con su propio estado de puerta y costo (§3.1, §4.1). No se asume simetría estructural ni de estado de puertas: una salida de $A$ a $B$ puede existir sin que exista la inversa de $B$ a $A$, o tener puertas con estados independientes.
- **Construcción de Salidas Entrantes**: Al cargar la cripta, se procesan todas las salas y salidas del esqueleto para construir, en un tiempo único de $O(V + E)$, una estructura de adyacencia de **salidas entrantes** por cada sala (índice denso). Cada entrada almacena el índice denso del origen, el costo de la salida y una referencia directa a la puerta correspondiente en el esqueleto para consultar su estado actual en tiempo de ejecución.
- **Recorrido desde el Jugador**: El algoritmo de Dijkstra parte de la sala actual del jugador y explora las **salidas entrantes** (en el sentido inverso, es decir, propagando la distancia desde las salas que conectan hacia la actual) para calcular el costo mínimo $d$ hacia los cazadores.
- **Complejidad Asintótica**: Gracias al sistema de épocas (que evita inicializar las $V$ posiciones en cada corrida) y a la exploración restringida al subgrafo alcanzable dentro del radio del `rango` máximo, la complejidad del Dijkstra es $O(R + E_R \log R)$, donde $R$ es el número de salas dentro del rango y $E_R$ es el número de salidas entrantes en esas salas.
- **Desempate**: Tras obtener las distancias mínimas, para un cazador en $u$, se examinan sus vecinos salientes y se elige $v$ tal que $costo(u, v) + dist(v, jugador) == dist(u, jugador)$ y el $id(v)$ sea el mínimo.

### 2. Cálculo Compartido e Invalidación
- **Decisión**: Un único cálculo bajo demanda (lazy) invalidado mediante un flag `sucio`.
- **Condiciones de Invalidación**: El mapa se marca como `sucio` si:
    1. El jugador cambia de sala.
    2. Una puerta cambia de estado (abierta/cerrada).
    3. El `rango` máximo entre los cazadores activos cambia.
- **Justificación de Equivalencia (§3.2) y Análisis de Eventos**: 
  Entre dos turnos de un cazador pueden ocurrir diversos eventos. Analizamos su impacto en el mapa de distancias:
  1. *Apertura o cierre de puertas*: **Invalida el mapa**. Modifica la transitabilidad de las salidas dirigidas, alterando las rutas mínimas.
  2. *Movimiento del jugador*: **Invalida el mapa**. Cambia la sala origen del cálculo de distancias.
  3. *Cambios de sala de otros actores*: **No invalida el mapa**. No afectan el esqueleto ni las puertas.
  4. *Cambios de velocidad*: **No invalida el mapa**. No afectan la topología del esqueleto.

### 3. Reescalado de Tiempo (FR-013)
- **Decisión**: Reutilizar `AgendaEventos.cambiar_velocidad` sin modificaciones, validando su cumplimiento con una prueba específica.

## Alternativas Consideradas para Medición (--bench)
1. **Cálculo Individual vs Compartido** con decenas de cazadores.
2. **Recalcular Siempre vs Caché** con puertas estables vs inestables.
3. **Casos Específicos de Asimetría**: Incluir pruebas en `--bench` y unitarias para criptas con salidas de un solo sentido y puertas cerradas en un solo sentido.
