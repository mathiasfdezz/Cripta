# Data Model: Terreno y cazador

## Entidades de Dominio

### Puerta / Salida (Actualización)
- **Campos Nuevos**:
    - `costo`: Entero >= 1. Valor predeterminado: 100.
    - `indice_origen`: Entero denso $[0, V-1]$ (resuelto al cargar la cripta).
    - `indice_destino`: Entero denso $[0, V-1]$ (resuelto al cargar la cripta).
- **Reglas**:
    - Las salidas son estrictamente dirigidas según el API. No se asume simetría en existencia ni en estado de puertas.

## Estructuras de Soporte (Modelo)

### RastreadorCazador (Mapa de Distancias)
- **Atributos**:
    - `mapeo_indices`: `VectorOrdenado` (`id_sala -> indice_denso`).
    - `salidas_entrantes`: Lista de listas (de tamaño $V$) construida en $O(V + E)$ al cargar la cripta. Cada elemento almacena tuplas de `(indice_origen, costo, referencia_puerta)`.
    - `distancias`: Lista de enteros de tamaño $V$.
    - `epoca_visita`: Lista de enteros de tamaño $V$.
    - `epoca_actual`: Entero.
    - `sucio`: Booleano.
    - `rango_max_vigente`: Entero.
- **Optimización**: El uso de salidas entrantes pre-calculadas y el sistema de épocas permite un Dijkstra acotado a la región alcanzable ($R, E_R$) sin inicialización total de memoria.
