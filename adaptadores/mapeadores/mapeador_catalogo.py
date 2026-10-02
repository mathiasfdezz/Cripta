from adaptadores.mapeadores.error_datos import leer_campo
from dtos.ficha_catalogo import FichaCatalogo


def ficha_catalogo_desde_json(datos):
    donde = f"ficha {datos.get('id', '?')}"
    return FichaCatalogo(
        id=leer_campo(datos, "id", donde),
        nombre=leer_campo(datos, "nombre", donde),
        clase=leer_campo(datos, "clase", donde),
        vida_max=datos.get("vida_max"),
        ataque=datos.get("ataque"),
        defensa=datos.get("defensa"),
        velocidad=datos.get("velocidad"),
        comportamiento=datos.get("comportamiento"),
        suelta=tuple(datos.get("suelta", ())),
        regeneracion=datos.get("regeneracion"),
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