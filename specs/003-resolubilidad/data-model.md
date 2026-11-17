# Data Model: Verificación de resolubilidad

## UbicacionLlave (DTO, inmutable)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | str | id de catálogo de la llave |
| `sala` | int | sala donde está (o donde inicia el enemigo que la suelta) |
| `enemigo` | str o None | instancia del enemigo que la suelta |

Origen: `GET /criptas/<id>/llaves` → `{"llaves": [{"id", "sala", "enemigo"?}]}`.

## PuertaBloqueada (modelo)

`sala`, `direccion`, `destino`, `llave` (None si la puerta no declara llave), `ubicaciones` (lista de
`UbicacionLlave` de esa llave; vacía si ninguna sala la contiene).

## ReporteResolubilidad (modelo)

| Campo | Descripción |
|-------|-------------|
| `resoluble` | bool |
| `orden_llaves` | ids en el orden en que se obtienen |
| `no_obtenibles` | ids de llaves (publicadas o pedidas por puertas) que no se obtienen |
| `frontera` | lista de `PuertaBloqueada` |
| `ciclo` | lista de ids `[k1, k2, ..., k1]` o vacía |
| `puertas_del_ciclo` | `PuertaBloqueada` que forman el ciclo, en el mismo orden |
| `salas`, `salidas`, `llaves` | tamaño de la entrada, para el reporte y el bench |

## Persistencia

`llaves.json` con la respuesta del servicio, en `datos_offline/<cripta>/` y en `cache_criptas/<cripta>/`
(se borra con el resto si cambia la versión).
