class ErrorDatos(Exception):
    pass


def leer_campo(datos, clave, donde):
    if clave not in datos:
        raise ErrorDatos(f"{donde}: falta el campo '{clave}'")
    return datos[clave]