from modelo.esqueleto import Esqueleto
from modelo.verificador_resolubilidad import VerificadorResolubilidad


class VerificacionCripta:
    """Trae el esqueleto y la ubicación de las llaves y verifica si la cripta se puede
    ganar (§3.5). Devuelve también el esqueleto, para que la partida no lo vuelva a pedir."""

    @staticmethod
    def ejecutar(fuente, datos):
        esqueleto = Esqueleto()
        for numero in range(1, datos.paginas + 1):
            esqueleto.agregar_pagina(fuente.pagina_salas(datos.id, numero))
        verificador = VerificadorResolubilidad(esqueleto, fuente.llaves(datos.id))
        reporte = verificador.verificar(datos.sala_inicial, datos.sala_salida, datos.llave_salida)
        return esqueleto, reporte
