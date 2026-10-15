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
# nombres probables del número dentro de un efecto, si el API lo manda como objeto
CLAVES_DE_CANTIDAD = ("daño", "dano", "cantidad", "valor", "cura")


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
        veneno=_cantidad_de_efecto(datos, "veneno", donde),
        regeneracion=_cantidad_de_efecto(datos, "regeneracion", donde),
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


def _cantidad_de_efecto(datos, campo, donde):
    """El contrato del API todavía no define estos campos: se acepta un número entero o un
    objeto con un número adentro. Cualquier otra cosa es un error de datos con contexto,
    no una caída en medio de la partida."""
    valor = datos.get(campo)
    if valor is None:
        return None
    if isinstance(valor, dict):
        numeros = [valor[c] for c in CLAVES_DE_CANTIDAD if c in valor]
        if not numeros:
            numeros = [v for v in valor.values() if _es_entero(v)]
        if len(numeros) != 1:
            raise ErrorDatos(f"{donde}: no se entiende el campo '{campo}': {valor}")
        valor = numeros[0]
    if not _es_entero(valor) or valor < 0:
        raise ErrorDatos(f"{donde}: '{campo}' debe ser un entero no negativo, llegó {valor!r}")
    return int(valor) or None


def _es_entero(valor):
    if isinstance(valor, bool):
        return False
    return isinstance(valor, int) or (isinstance(valor, float) and valor.is_integer())


def _obligatorios(clase):
    for nombre, campos in OBLIGATORIOS_POR_CLASE:
        if nombre == clase:
            return campos
    return ()