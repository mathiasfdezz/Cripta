from adaptadores.mapeadores.error_datos import ErrorDatos, leer_campo
from dtos.ficha_catalogo import FichaCatalogo

OBLIGATORIOS_POR_CLASE = (
    ("enemigo", ("vida_max", "ataque", "defensa", "velocidad", "comportamiento")),
    ("arma", ("peso", "valor", "ataque_bonus")),
    ("armadura", ("peso", "valor", "defensa_bonus")),
    ("pocion", ("peso", "valor")),
    ("antidoto", ("peso", "valor")),
    ("llave", ("peso", "valor")),
    ("antorcha", ("peso", "valor", "duracion")),
    ("pergamino_retroceso", ("peso", "valor")),
    ("trampa", ("daño",)),
)

COMPORTAMIENTOS = ("guardián", "errante", "rastreador")


def ficha_catalogo_desde_json(datos):
    donde = f"ficha {datos.get('id', '?')}"
    clase = leer_campo(datos, "clase", donde)
    for campo in _obligatorios(clase):
        leer_campo(datos, campo, donde)
    if clase == "enemigo" and datos["comportamiento"] not in COMPORTAMIENTOS:
        raise ErrorDatos(f"{donde}: comportamiento desconocido '{datos['comportamiento']}'")

    return FichaCatalogo(
        id=leer_campo(datos, "id", donde),
        nombre=leer_campo(datos, "nombre", donde),
        clase=clase,
        vida_max=datos.get("vida_max"),
        ataque=datos.get("ataque"),
        defensa=datos.get("defensa"),
        velocidad=datos.get("velocidad"),
        comportamiento=datos.get("comportamiento"),
        suelta=tuple(datos.get("suelta") or ()),
        peso=datos.get("peso"),
        valor=datos.get("valor"),
        ataque_bonus=datos.get("ataque_bonus"),
        defensa_bonus=datos.get("defensa_bonus"),
        cura=datos.get("cura"),
        modificador_velocidad=datos.get("modificador_velocidad"),
        duracion=datos.get("duracion"),
        abre=datos.get("abre"),
        dano=datos.get("daño"),
        rearme=datos.get("rearme"),
    )


def _obligatorios(clase):
    for nombre, campos in OBLIGATORIOS_POR_CLASE:
        if nombre == clase:
            return campos
    return ()