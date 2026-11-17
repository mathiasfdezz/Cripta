from adaptadores.mapeadores.error_datos import ErrorDatos, leer_campo
from dtos.ubicacion_llave import UbicacionLlave


def llaves_desde_json(datos, cripta_id=""):
    """Respuesta de GET /criptas/<id>/llaves -> tupla de UbicacionLlave."""
    donde = f"llaves de {cripta_id}".strip()
    lista = leer_campo(datos, "llaves", donde)
    if not isinstance(lista, list):
        raise ErrorDatos(f"{donde}: 'llaves' debe ser una lista")
    return tuple(_ubicacion(llave, donde) for llave in lista)


def _ubicacion(datos, donde):
    sala = leer_campo(datos, "sala", donde)
    if isinstance(sala, bool) or not isinstance(sala, int):
        raise ErrorDatos(f"{donde}: la sala de una llave debe ser un entero, llegó {sala!r}")
    return UbicacionLlave(id=leer_campo(datos, "id", donde), sala=sala,
                          enemigo=datos.get("enemigo"))
