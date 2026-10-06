import json
import os
import unittest

from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from modelo.esqueleto import Esqueleto
from modelo.precarga import salas_a_precargar

RUTA_CRIPTA_01 = os.path.join(os.path.dirname(__file__), "..", "datos_offline",
                              "cripta-01", "salas", "pagina_1.json")


def sala(id_sala, **salidas):
    """sala(1, N=2, E=(7, True)) -> dict con la forma del API."""
    d = {}
    for dir_, v in salidas.items():
        if isinstance(v, tuple):
            d[dir_] = {"sala": v[0], "cerrada": v[1], "llave": "itm_llave"}
        else:
            d[dir_] = {"sala": v}
    return {"id": id_sala, "nombre": "S" + str(id_sala), "salidas": d}


def pagina(*salas, numero=1, total=1):
    return pagina_salas_desde_json({"pagina": numero, "total_paginas": total, "salas": list(salas)})


def esqueleto(*salas):
    e = Esqueleto()
    e.agregar_pagina(pagina(*salas))
    return e


def esqueleto_cripta_01():
    with open(RUTA_CRIPTA_01, encoding="utf-8") as f:
        e = Esqueleto()
        e.agregar_pagina(pagina_salas_desde_json(json.load(f)))
    return e


class PruebasPuertaCompartida(unittest.TestCase):

    def test_cripta_01_puerta_2_y_5_es_la_misma_desde_ambos_lados(self):
        e = esqueleto_cripta_01()
        desde_2 = e.puerta(2, "E")
        desde_5 = e.puerta(5, "O")
        self.assertIsNotNone(desde_2)
        self.assertIs(desde_2, desde_5)
        # el JSON solo la declara cerrada desde la sala 2, pero es una sola puerta
        self.assertTrue(desde_2.esta_cerrada())
        self.assertFalse(e.puede_atravesar(2, "E"))
        self.assertFalse(e.puede_atravesar(5, "O"))

    def test_cripta_01_datos_de_la_puerta_se_ven_desde_ambos_lados(self):
        e = esqueleto_cripta_01()
        for id_sala, direccion in ((2, "E"), (5, "O")):
            puerta = e.puerta(id_sala, direccion)
            self.assertEqual(puerta.llave, "itm_llave_bronce")
            self.assertEqual(puerta.cierre_automatico, 500)
        self.assertEqual(set(e.puerta(2, "E").lados), {(2, "E"), (5, "O")})

    def test_cripta_01_abrir_desde_la_sala_2_la_abre_desde_la_5(self):
        e = esqueleto_cripta_01()
        e.puerta(2, "E").abrir()
        self.assertTrue(e.puede_atravesar(2, "E"))
        self.assertTrue(e.puede_atravesar(5, "O"))
        self.assertTrue(e.puerta(5, "O").esta_abierta())

    def test_cripta_01_abrir_desde_la_sala_5_la_abre_desde_la_2(self):
        e = esqueleto_cripta_01()
        e.puerta(5, "O").abrir()
        self.assertTrue(e.puede_atravesar(2, "E"))
        self.assertTrue(e.puede_atravesar(5, "O"))

    def test_cripta_01_cerrar_de_nuevo_afecta_a_los_dos_lados(self):
        e = esqueleto_cripta_01()
        e.puerta(2, "E").abrir()
        e.puerta(5, "O").cerrar()
        self.assertFalse(e.puede_atravesar(2, "E"))
        self.assertFalse(e.puede_atravesar(5, "O"))

    def test_cripta_01_otra_puerta_cerrada_es_independiente(self):
        e = esqueleto_cripta_01()
        self.assertIsNot(e.puerta(2, "E"), e.puerta(4, "E"))
        # 4 <-> 6 tiene el mismo caso: cerrada solo desde la sala 4
        self.assertIs(e.puerta(4, "E"), e.puerta(6, "O"))
        self.assertFalse(e.puede_atravesar(6, "O"))
        e.puerta(2, "E").abrir()
        self.assertFalse(e.puede_atravesar(4, "E"))
        self.assertFalse(e.puede_atravesar(6, "O"))

    def test_declarada_cerrada_solo_desde_el_otro_lado(self):
        # la sala con id menor es la que no la declara cerrada
        e = esqueleto(sala(1, E=4), sala(4, O=(1, True)))
        self.assertIs(e.puerta(1, "E"), e.puerta(4, "O"))
        self.assertFalse(e.puede_atravesar(1, "E"))
        self.assertFalse(e.puede_atravesar(4, "O"))

    def test_puerta_con_las_salas_en_paginas_distintas(self):
        e = Esqueleto()
        e.agregar_pagina(pagina(sala(2, E=(5, True)), numero=1, total=2))
        e.agregar_pagina(pagina(sala(5, O=2), numero=2, total=2))
        self.assertIs(e.puerta(2, "E"), e.puerta(5, "O"))
        self.assertFalse(e.puede_atravesar(5, "O"))
        e.puerta(5, "O").abrir()
        self.assertTrue(e.puede_atravesar(2, "E"))

    def test_agregar_otra_vez_la_pagina_no_reinicia_las_puertas(self):
        e = Esqueleto()
        p = pagina(sala(2, E=(5, True)), sala(5, O=2))
        e.agregar_pagina(p)
        e.puerta(2, "E").abrir()
        e.agregar_pagina(p)
        self.assertTrue(e.puede_atravesar(2, "E"))
        self.assertTrue(e.puede_atravesar(5, "O"))

    def test_puerta_abierta_desde_el_inicio(self):
        e = esqueleto(sala(1, N=2), sala(2, S=1))
        self.assertIs(e.puerta(1, "N"), e.puerta(2, "S"))
        self.assertTrue(e.puede_atravesar(1, "N"))
        self.assertTrue(e.puede_atravesar(2, "S"))


class PruebasConexionesYPuertasCerradas(unittest.TestCase):

    def test_conexiones_n_s_e_o(self):
        e = esqueleto(sala(1, O=5, E=4, S=3, N=2),    # desordenadas a proposito
                      sala(2, S=1), sala(3, N=1), sala(4, O=1), sala(5, E=1))
        self.assertEqual([s.direccion for s in e.obtener(1).salidas], ["N", "S", "E", "O"])
        for direccion, destino in (("N", 2), ("S", 3), ("E", 4), ("O", 5)):
            self.assertEqual(e.salida(1, direccion).sala_destino, destino)
            self.assertTrue(e.puede_atravesar(1, direccion))
        # y la vuelta, por la direccion contraria
        for origen, direccion in ((2, "S"), (3, "N"), (4, "O"), (5, "E")):
            self.assertEqual(e.salida(origen, direccion).sala_destino, 1)
            self.assertTrue(e.puede_atravesar(origen, direccion))

    def test_cada_direccion_tiene_su_propia_puerta(self):
        e = esqueleto(sala(1, N=(2, True), E=3), sala(2, S=1), sala(3, O=1))
        self.assertFalse(e.puede_atravesar(1, "N"))
        self.assertTrue(e.puede_atravesar(1, "E"))
        e.puerta(1, "N").abrir()
        self.assertTrue(e.puede_atravesar(1, "N"))
        self.assertTrue(e.puede_atravesar(1, "E"))

    def test_no_se_atraviesa_una_puerta_cerrada(self):
        e = esqueleto(sala(1, N=(2, True)), sala(2, S=1))
        self.assertFalse(e.puede_atravesar(1, "N"))
        self.assertFalse(e.puede_atravesar(2, "S"))
        e.puerta(1, "N").abrir()
        self.assertTrue(e.puede_atravesar(1, "N"))
        e.puerta(1, "N").cerrar()
        self.assertFalse(e.puede_atravesar(1, "N"))
        self.assertFalse(e.puede_atravesar(2, "S"))

    def test_direccion_sin_salida_o_sala_inexistente(self):
        e = esqueleto(sala(1, N=2), sala(2, S=1))
        self.assertIsNone(e.salida(1, "E"))
        self.assertIsNone(e.puerta(1, "E"))
        self.assertFalse(e.puede_atravesar(1, "E"))
        self.assertIsNone(e.salida(99, "N"))
        self.assertIsNone(e.puerta(99, "N"))
        self.assertFalse(e.puede_atravesar(99, "N"))

    def test_dos_salas_conectadas_por_dos_puertas_distintas(self):
        e = esqueleto(sala(1, N=(2, True), E=2), sala(2, S=1, O=1))
        self.assertIsNot(e.puerta(1, "N"), e.puerta(1, "E"))
        self.assertFalse(e.puede_atravesar(1, "N"))
        self.assertTrue(e.puede_atravesar(1, "E"))
        self.assertTrue(e.puede_atravesar(2, "O"))


class PruebasPrecargaConPuertaCompartida(unittest.TestCase):

    def test_precarga_no_cruza_por_abierta_una_puerta_cerrada_desde_el_otro_lado(self):
        # la puerta 1-2 solo se declara cerrada desde la sala 1; desde la 2 hay
        # que tratarla como cerrada: primero se elige la salida abierta (S -> 6)
        e = esqueleto(sala(1, S=(2, True)), sala(2, N=1, S=6), sala(6, N=2))
        self.assertEqual(salas_a_precargar(e, 2, lambda _: False, limite=2), [2, 6])

    def test_precarga_cripta_01_desde_la_sala_5(self):
        e = esqueleto_cripta_01()
        self.assertEqual(salas_a_precargar(e, 5, lambda _: False, limite=1), [5])
        self.assertEqual(salas_a_precargar(e, 5, lambda _: False), [5, 2, 3, 1, 4, 6])

    def test_precarga_ve_la_puerta_abierta(self):
        e = esqueleto(sala(1, S=(2, True)), sala(2, N=1, S=6), sala(6, N=2))
        e.puerta(1, "S").abrir()
        self.assertEqual(salas_a_precargar(e, 2, lambda _: False, limite=2), [2, 1])


if __name__ == "__main__":
    unittest.main()