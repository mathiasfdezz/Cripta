from adaptadores.mapeadores.error_datos import leer_campo
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.instancia_trampa import InstanciaTrampa


def contenido_sala_desde_json(datos):
    donde = f"contenido de sala {datos.get('sala', '?')}"
    return ContenidoSala(
        sala=leer_campo(datos, "sala", donde),
        enemigos=tuple(_enemigo(e, donde) for e in leer_campo(datos, "enemigos", donde)),
        objetos=tuple(leer_campo(datos, "objetos", donde)),
        trampas=tuple(_trampa(t, donde) for t in leer_campo(datos, "trampas", donde)),
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