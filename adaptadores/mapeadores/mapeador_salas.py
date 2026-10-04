from adaptadores.mapeadores.error_datos import ErrorDatos, leer_campo
from dtos.pagina_salas import PaginaSalas
from dtos.sala import Sala
from dtos.salida import Salida

DIRECCIONES = ("N", "S", "E", "O")


def pagina_salas_desde_json(datos):
    donde = f"página de salas {datos.get('pagina', '?')}"
    return PaginaSalas(
        pagina=leer_campo(datos, "pagina", donde),
        total_paginas=leer_campo(datos, "total_paginas", donde),
        salas=tuple(sala_desde_json(s) for s in leer_campo(datos, "salas", donde)),
    )


def sala_desde_json(datos):
    donde = f"sala {datos.get('id', '?')}"
    # el contrato permite una sala sin "salidas"
    salidas_json = datos.get("salidas") or {}
    for direccion in salidas_json:
        if direccion not in DIRECCIONES:
            raise ErrorDatos(f"{donde}: dirección desconocida '{direccion}'")
    # orden fijo N, S, E, O para no depender del orden en que venga el JSON
    salidas = tuple(
        _salida(d, salidas_json[d], f"{donde}, salida {d}")
        for d in DIRECCIONES if d in salidas_json
    )
    return Sala(
        id=leer_campo(datos, "id", donde),
        nombre=leer_campo(datos, "nombre", donde),
        salidas=salidas,
    )


def _salida(direccion, datos, donde):
    return Salida(
        direccion=direccion,
        sala_destino=leer_campo(datos, "sala", donde),
        cerrada=bool(datos.get("cerrada")),
        llave=datos.get("llave"),
        cierre_automatico=datos.get("cierre_automatico"),
    )