# Research: Terreno y cazador

## Decisiones Técnicas

### 1. Algoritmo de Búsqueda y Desempate (Salidas Dirigidas y Conectividad Real)
- **Naturaleza Dirigida**: El API describe cada salida como dirigida con su propio estado de puerta y costo (§3.1, §4.1). No se asume simetría estructural ni de estado de puertas: una salida de $A$ a $B$ puede existir sin que exista la inversa de $B$ a $A$ (las criptas 02 y 05 tienen pares 19→20 por N y 20→19 por O), o tener puertas con estados independientes.
- **Construcción de Salidas Entrantes**: Al cargar la cripta, se procesan todas las salas y salidas del esqueleto para construir, en un tiempo único de $O(V + E)$, una estructura de adyacencia de **salidas entrantes** por cada sala (índice denso). Cada entrada guarda el índice denso del origen, el costo y el **índice de la salida**; el estado actual de la puerta se consulta en el esqueleto con ese índice (ver A4 en analisis.md).
- **Recorrido desde el Jugador**: Dijkstra parte de la sala actual del jugador y explora las **salidas entrantes** (sentido inverso) para calcular, para cada sala $x$, el costo mínimo $dist(x)$ de llegar desde $x$ hasta el jugador.
- **Cota por rango**: el recorrido se detiene cuando la menor distancia pendiente supera la cota (el mayor rango de los cazadores). Todas las salas con $dist \le cota$ quedan asentadas con su valor exacto; las demás no importan, porque un cazador en una sala con $dist > rango$ espera.
- **Complejidad Asintótica**: Con épocas (no se reinicializan las $V$ posiciones en cada corrida), el costo es $O(R + E_R \log R)$, donde $R$ es el número de salas dentro de la cota y $E_R$ las salidas entrantes de esas salas.
- **Desempate**: para un cazador en $u$ con $d = dist(u) \le rango$ se examinan sus salidas abiertas $u \to v$ y se elige la de menor id de $v$ entre las que cumplen $costo(u, v) + dist(v) = d$. Todas esas $v$ tienen $dist(v) < d \le cota$, así que están asentadas. El resultado no depende del orden en que el heap resuelva empates.

### 2. Cálculo Compartido e Invalidación
- **Decisión**: Un único cálculo bajo demanda (lazy) compartido por todos los cazadores, con una cota igual al mayor rango conocido de los cazadores de la partida.
- **Qué invalida qué** (§5.2):
  1. *Movimiento del jugador*: cambia el origen del cálculo. **Invalida todo**.
  2. *Apertura o cierre de la salida $u \to x$*: el resultado solo depende de las salidas que entran a salas asentadas. Si $x$ no quedó asentada ($dist(x) >$ cota), cualquier ruta que use esa salida cuesta más que la cota y no cambia ninguna distancia $\le$ cota, ni al abrirse ni al cerrarse. **Invalida solo si $x$ quedó asentada en el último cálculo.** Una puerta que se cierra sola lejos de los cazadores no obliga a recalcular.
  3. *Cambio de la cota* (aparece un cazador con rango mayor): **invalida** si la cota nueva supera la usada.
  4. *Cambios de sala de otros actores, muertes y cambios de velocidad*: no tocan el esqueleto ni las puertas. **No invalidan**.
- **Equivalencia observable (§3.2)**: con esas reglas, el mapa reutilizado es idéntico al que daría un cálculo desde cero en ese instante, y la decisión (incluido el desempate) también. Las pruebas lo verifican comparando contra un cálculo desde cero en cada turno.
- **Registro de cambios de puertas**: el esqueleto anota los índices de las salidas que cambiaron desde el último cálculo; al consultar se revisan solo esas.

### 3. Reescalado de Tiempo (FR-013)
- **Decisión**: Reutilizar `AgendaEventos.cambiar_velocidad` sin modificaciones, validando su cumplimiento con una prueba específica.

## Alternativas Consideradas para Medición (--bench)
1. **Cálculo individual vs compartido** con 1, 10, 30 y 60 cazadores, rango pequeño (300) y grande (2400). El individual es un Dijkstra hacia adelante desde cada cazador, cortado en su rango, que propaga el primer paso de menor id.
2. **Recalcular siempre vs reutilizar** con puertas estables y con puertas inestables (muchas aperturas y cierres por ciclo).
3. **Salidas de un solo sentido y puertas cerradas de un solo lado**: pruebas unitarias y criptas sintéticas.
