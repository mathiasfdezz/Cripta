# Data Model: Niebla de guerra y «ir a»

## MapaConocido (modelo)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `estado` | lista de enteros, tamaño V | 0 desconocida, 1 avistada, 2 explorada, por índice denso de sala |
| `recuerdo` | lista de enteros, tamaño E | -1 sin observar, 0 abierta, 1 cerrada, por índice de salida |

Operaciones: `estado_de(id)`, `esta_explorada(i)`, `recuerda_abierta(s)`, `explorar(i)`, `observar_sala(i)`, `explorar_vecinas(i)`, `salas_exploradas()`, `salas_avistadas()`.

Cada cambio se anota en el historial con `registrar_elemento(lista, posición, anterior)`.

## Viaje (controlador)

No se guarda: vive solo mientras se ejecuta la orden. Motivos de detención:
`llegaste`, `enemigos`, `daño`, `sin_ruta`, `fin`, `no_disponible`.

## Archivo de partida, versión 4

Después del registro del jugador, un registro del mapa con CRC:
`V` (uint32), `V` bytes de estado, `E` (uint32), `E` bytes de recuerdo (255 = sin observar).
