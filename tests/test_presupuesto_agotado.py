import unittest

from adaptadores.error_presupuesto import ErrorPresupuesto
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from adaptadores.mapeadores.mapeador_criptas import datos_cripta_desde_json
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from controlador.partida import ControladorPartida
from modelo.cache_catalogo import CacheCatalogo
from tests.test_partida import VistaMuda

SALAS = 12


class FuenteConTope:
    """Cripta en línea de 12 salas (1 al sur, 12 al norte). Después de 'tope' lotes de
    contenido, cualquier otra solicitud de contenido se queda sin presupuesto."""

    def __init__(self, tope):
        self.tope = tope
        self.lotes = 0

    def datos_cripta(self, cripta_id):
        return datos_cripta_desde_json({
            "id": "linea", "version": "v1", "salas_total": SALAS, "paginas": 1,
            "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": SALAS,
            "llave_salida": "itm_llave", "presupuesto_solicitudes": 9, "inventario_max": 5,
            "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})

    def pagina_salas(self, cripta_id, pagina):
        salas = []
        for i in range(1, SALAS + 1):
            salidas = {}
            if i < SALAS:
                salidas["N"] = {"sala": i + 1}
            if i > 1:
                salidas["S"] = {"sala": i - 1}
            salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
        return pagina_salas_desde_json({"pagina": 1, "total_paginas": 1, "salas": salas})

    def contenido(self, cripta_id, salas):
        if self.lotes >= self.tope:
            raise ErrorPresupuesto("presupuesto agotado")
        self.lotes += 1
        return tuple(contenido_sala_desde_json({"sala": s, "enemigos": [], "objetos": [],
                                                "trampas": []}) for s in salas)

    def catalogo(self, ids):
        raise AssertionError("esta cripta no tiene fichas")


class PruebasPresupuestoAgotado(unittest.TestCase):

    def test_avisa_una_sola_vez_y_no_deja_entrar_a_salas_sin_contenido(self):
        fuente = FuenteConTope(tope=1)
        datos = fuente.datos_cripta("linea")
        controlador = ControladorPartida(datos, fuente, CacheCatalogo(fuente), VistaMuda(), 1)
        for _ in range(SALAS + 3):
            controlador.ejecutar("n")
        estado = controlador.estado
        mensajes = controlador.vista.mensajes
        avisos = [m for m in mensajes if "Se acabó el presupuesto" in m]
        self.assertEqual(len(avisos), 1)
        # el primer lote trajo las salas 1 a 10; a la 11 no se puede entrar
        self.assertEqual(estado.jugador.sala, 10)
        self.assertTrue(estado.contenido_cargado(estado.jugador.sala))
        self.assertTrue(any("aún no llegó" in m for m in mensajes))


if __name__ == "__main__":
    unittest.main()
