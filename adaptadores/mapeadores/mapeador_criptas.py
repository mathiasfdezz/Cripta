from adaptadores.mapeadores.error_datos import leer_campo
from dtos.datos_cripta import DatosCripta
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.resumen_cripta import ResumenCripta


def resumen_cripta_desde_json(datos):
    donde = "lista de criptas"
    return ResumenCripta(
        id=leer_campo(datos, "id", donde),
        nombre=leer_campo(datos, "nombre", donde),
        salas=leer_campo(datos, "salas", donde),
        dificultad=leer_campo(datos, "dificultad", donde),
    )


def datos_cripta_desde_json(datos):
    donde = f"datos de {datos.get('id', '¿cripta?')}"
    return DatosCripta(
        id=leer_campo(datos, "id", donde),
        version=leer_campo(datos, "version", donde),
        salas_total=leer_campo(datos, "salas_total", donde),
        paginas=leer_campo(datos, "paginas", donde),
        salas_por_pagina=leer_campo(datos, "salas_por_pagina", donde),
        sala_inicial=leer_campo(datos, "sala_inicial", donde),
        sala_salida=leer_campo(datos, "sala_salida", donde),
        llave_salida=leer_campo(datos, "llave_salida", donde),
        presupuesto_solicitudes=leer_campo(datos, "presupuesto_solicitudes", donde),
        inventario_max=leer_campo(datos, "inventario_max", donde),
        jugador=_estadisticas_jugador(leer_campo(datos, "jugador", donde), donde),
    )


def _estadisticas_jugador(datos, donde):
    return EstadisticasJugador(
        vida_max=leer_campo(datos, "vida_max", donde),
        ataque=leer_campo(datos, "ataque", donde),
        defensa=leer_campo(datos, "defensa", donde),
        velocidad=leer_campo(datos, "velocidad", donde),
    )