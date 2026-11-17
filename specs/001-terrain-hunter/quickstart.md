# Quickstart: Validación de Terreno y cazador

Este documento describe cómo validar la capacidad con las pruebas, el modo interactivo y `--bench`.

## Pruebas de aceptación

```bash
python -m unittest tests.test_movimiento_terreno tests.test_cazador tests.test_vista_terreno
```

Cada prueba cita en su nombre o comentario el requisito (FR-xxx) que verifica.

## Escenarios de Validación Manual

### 1. Costo de Terreno e Intervalo
1. `python main.py cripta-02 --offline --semilla 1`
2. La lista de salidas muestra el costo de cada una (la salida norte de la sala 1 cuesta 60).
3. Moverse al norte: el reloj avanza `max(1, 60 * 100 // 100) = 60`.

### 2. Comportamiento del Cazador (Persecución)
1. En la cripta de referencia (`python main.py cripta-06 --offline`) los cazadores aparecen marcados como tales en la lista de enemigos.
2. Tras activarlos, pasar el turno (`esperar`): los que están dentro de su rango se acercan por la ruta de menor costo acumulado; los demás esperan.

### 3. Rango, desempate y reescalado de velocidad
Se verifican con las pruebas automáticas (`tests/test_cazador.py` y `tests/test_movimiento_terreno.py`), que construyen criptas mínimas con la ruta, el rango o la poción que cada caso necesita.

## Pruebas de Rendimiento (--bench)

```bash
python main.py --bench
```
- La sección «Cazadores» compara un cálculo por cazador con el cálculo compartido, con rango pequeño y grande, y reutilizar con recalcular siempre con puertas estables e inestables.
- La sección «Ciclo» mide el ciclo entre dos decisiones del jugador en la cripta de referencia con todos sus cazadores activos. **Éxito**: menos de 20 ms.
