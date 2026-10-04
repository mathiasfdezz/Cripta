from adaptadores.error_fuente_datos import ErrorFuenteDatos


class ErrorDatos(ErrorFuenteDatos):
    pass


def leer_campo(datos, clave, donde):
    if clave not in datos:
        raise ErrorDatos(f"{donde}: falta el campo '{clave}'")
    return datos[clave]