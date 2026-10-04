from adaptadores.mapeadores.error_datos import leer_campo
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.instancia_trampa import InstanciaTrampa


def contenido_sala_desde_json(datos):
    donde = f"contenido de sala {datos.get('sala', '?')}"
    return ContenidoSala(
        sala=leer_campo(datos, "sala", donde),
        # en el contrato solo "sala" es obligatorio, las listas pueden faltar
        enemigos=tuple(_enemigo(e, donde) for e in datos.get("enemigos") or ()),
        objetos=tuple(datos.get("objetos") or ()),
        trampas=tuple(_trampa(t, donde) for t in datos.get("trampas") or ()),
    )


def _enemigo(datos, donde):
    return InstanciaEnemigo(
        instancia=leer_campo(datos, "instancia", donde),
        tipo=leer_campo(datos, "tipo", donde),
        vida=datos.get("vida"),
    )


def _trampa(datos, donde):
    return InstanciaTrampa(
        instancia=leer_campo(datos, "instancia", donde),
        tipo=leer_campo(datos, "tipo", donde),
    )