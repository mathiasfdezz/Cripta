# Data Model: Terreno y cazador

## Entidades de Dominio

### Salida (DTO, actualización)
- **Campo nuevo**: `costo`: entero >= 1. Valor predeterminado: 100 (ausente o `null` en el JSON).
- **Reglas**: Las salidas son estrictamente dirigidas según el API. No se asume simetría en existencia ni en estado de puertas.

### FichaCatalogo (DTO, actualización)
- **Campo nuevo**: `rango`: entero >= 0, obligatorio cuando `comportamiento == "cazador"`.

### Puerta (actualización)
- Cada salida tiene su puerta. Al abrirse o cerrarse (también al deshacer o al cargar una partida) avisa al esqueleto el índice de su salida, para que la búsqueda de rutas sepa qué cambió.

## Estructuras de Soporte (Modelo)

### GrafoCripta (estático, se construye una vez por cripta)
- `ids`: lista de ids de sala en orden creciente; el índice denso de una sala es su posición.
- `indice_de`: `VectorOrdenado` (`id_sala -> indice_denso`), $O(\log V)$; solo se usa para la sala del jugador y la del cazador.
- `entrantes[i]`: lista de `(indice_origen, costo, indice_salida)` de las salidas que llegan a la sala `i`.
- `salientes[i]`: lista de `(indice_destino, costo, indice_salida)` de las salidas de la sala `i`, en orden N, S, E, O.
- No guarda objetos `Puerta`: las copias del estado (puntos de control de la capacidad 004) comparten el grafo y consultan sus propias puertas por índice de salida.

### BuscadorRutas (mapa de distancias compartido)
- `distancia`: lista de enteros de tamaño $V$.
- `epoca_asentada`: lista de enteros de tamaño $V$; una sala está asentada en el cálculo vigente si su valor es `epoca_actual`.
- `epoca_vista`: lista de enteros de tamaño $V$; distancia provisional válida en esta época.
- `origen`, `cota`: con qué sala del jugador y qué cota se hizo el último cálculo.
- Cola de prioridad: `MinHeap` propio de `(distancia, indice)`.
- **Optimización**: las épocas evitan reinicializar $V$ posiciones por cálculo; el corte por cota limita el trabajo a la región $R$.
