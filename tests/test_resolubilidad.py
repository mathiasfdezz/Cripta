import unittest

from adaptadores.cliente_offline import ClienteOffline
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from dtos.ubicacion_llave import UbicacionLlave
from modelo.esqueleto import Esqueleto
from modelo.verificador_resolubilidad import VerificadorResolubilidad
from tests.criptas_prueba import esqueleto, salida


def ida_y_vuelta(a, direccion, b, cerrada=False, llave=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, cerrada=cerrada, llave=llave), salida(b, contraria, a)]


def verificar(salidas, llaves, inicial=1, sala_salida=9, llave_salida="negra"):
    mapa = esqueleto(*salidas)
    ubicaciones = [UbicacionLlave(*l) for l in llaves]
    return VerificadorResolubilidad(mapa, ubicaciones).verificar(inicial, sala_salida, llave_salida)


class PruebasResoluble(unittest.TestCase):

    def test_resoluble_con_orden(self):
        # FR-201, FR-203, FR-204: bronce abre 2->3, en 3 está la negra, que abre 3->9
        salidas = (ida_y_vuelta(1, "N", 2) + ida_y_vuelta(2, "N", 3, True, "bronce")
                   + ida_y_vuelta(3, "E", 9, True, "negra"))
        reporte = verificar(salidas, [("bronce", 2), ("negra", 3)])
        self.assertTrue(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ("bronce", "negra"))

    def test_orden_determinista_con_varios_validos(self):
        # FR-204 (Apéndice B): tres llaves alcanzables sin depender entre sí; cualquier
        # orden sirve, pero dos verificaciones dan el mismo
        salidas = (ida_y_vuelta(1, "N", 2) + ida_y_vuelta(1, "E", 3) + ida_y_vuelta(1, "S", 4)
                   + ida_y_vuelta(4, "S", 9, True, "negra"))
        llaves = [("negra", 3), ("plata", 2), ("bronce", 4)]
        primero = verificar(salidas, llaves)
        segundo = verificar(salidas, list(reversed(llaves)))
        self.assertTrue(primero.resoluble)
        self.assertEqual(primero.orden_llaves, segundo.orden_llaves)
        # en anchura y en orden N, S, E, O desde la 1: la 2 (N), luego la 4 (S), luego la 3 (E)
        self.assertEqual(primero.orden_llaves, ("plata", "bronce", "negra"))

    def test_cada_llave_despues_de_las_que_necesita(self):
        # FR-204: cadena 1 -a-> 2 -b-> 3 -c-> 4 con cada llave en la sala anterior a su puerta
        salidas = (ida_y_vuelta(1, "E", 2, True, "a") + ida_y_vuelta(2, "E", 3, True, "b")
                   + ida_y_vuelta(3, "E", 4, True, "c") + ida_y_vuelta(4, "E", 9, True, "negra"))
        reporte = verificar(salidas, [("negra", 4), ("c", 3), ("b", 2), ("a", 1)])
        self.assertEqual(reporte.orden_llaves, ("a", "b", "c", "negra"))

    def test_llave_de_errante_en_su_sala_inicial(self):
        # FR-202 (Apéndice B): la negra la suelta un errante que inicia en la 2
        salidas = ida_y_vuelta(1, "N", 2) + ida_y_vuelta(1, "E", 9, True, "negra")
        reporte = verificar(salidas, [("negra", 2, "e-7")])
        self.assertTrue(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ("negra",))

    def test_criptas_publicadas_resolubles(self):
        # FR-201: las criptas 02, 03, 04 y 06 del paquete offline se pueden ganar
        for cripta in ("cripta-02", "cripta-03", "cripta-04", "cripta-06"):
            with self.subTest(cripta=cripta):
                self.assertTrue(verificar_offline(cripta).resoluble)


def verificar_offline(cripta):
    fuente = ClienteOffline()
    datos = fuente.datos_cripta(cripta)
    mapa = Esqueleto()
    for pagina in range(1, datos.paginas + 1):
        mapa.agregar_pagina(fuente.pagina_salas(cripta, pagina))
    return VerificadorResolubilidad(mapa, fuente.llaves(cripta)).verificar(
        datos.sala_inicial, datos.sala_salida, datos.llave_salida)


class PruebasNoResoluble(unittest.TestCase):

    def test_llave_salida_detras_de_su_propia_puerta(self):
        # FR-205, FR-206 (Apéndice B): la negra está en la 3, detrás de 2->3 que pide la negra
        salidas = (ida_y_vuelta(1, "N", 2) + ida_y_vuelta(2, "N", 3, True, "negra")
                   + ida_y_vuelta(2, "E", 9, True, "negra"))
        reporte = verificar(salidas, [("negra", 3)])
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclo, ("negra", "negra"))
        self.assertEqual([(p.sala, p.direccion, p.destino) for p in reporte.puertas_del_ciclo],
                         [(2, "N", 3)])
        self.assertIn("negra", reporte.no_obtenibles)

    def test_ciclo_de_dos_llaves(self):
        # FR-206: la A está detrás de una puerta que pide la B y la B detrás de una que pide la A
        salidas = (ida_y_vuelta(1, "N", 2, True, "b") + ida_y_vuelta(1, "E", 3, True, "a")
                   + ida_y_vuelta(3, "E", 4) + ida_y_vuelta(4, "S", 9, True, "negra"))
        reporte = verificar(salidas, [("a", 2), ("b", 4), ("negra", 1)])
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclo, ("a", "b", "a"))
        self.assertEqual([(p.sala, p.destino, p.llave) for p in reporte.puertas_del_ciclo],
                         [(1, 2, "b"), (1, 3, "a")])

    def test_cripta_sellada_publicada(self):
        # FR-205, FR-206: cripta-05 del paquete offline; la negra (salida) está en la 23,
        # detrás de 7->22 que pide la hierro, y la hierro en la 24, detrás de 12->24 (negra)
        reporte = verificar_offline("cripta-05")
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclo, ("itm_llave_hierro", "itm_llave_negra", "itm_llave_hierro"))
        self.assertEqual(reporte.no_obtenibles, ("itm_llave_hierro", "itm_llave_negra"))
        self.assertEqual(reporte.orden_llaves, ("itm_llave_bronce",))

    def test_reporte_frontera_y_ubicaciones(self):
        # FR-205: frontera = salidas cerradas con origen alcanzable y destino no alcanzable,
        # con su llave y dónde está; una puerta cerrada hacia una sala ya alcanzable no cuenta
        salidas = (ida_y_vuelta(1, "N", 2) + ida_y_vuelta(2, "E", 5, True, "roja")
                   + [salida(1, "E", 2, cerrada=True, llave="verde")]
                   + ida_y_vuelta(5, "N", 9, True, "negra") + ida_y_vuelta(5, "E", 6))
        reporte = verificar(salidas, [("roja", 6), ("negra", 5), ("verde", 6, "e-3")])
        self.assertFalse(reporte.resoluble)
        frontera = [(p.sala, p.direccion, p.destino, p.llave,
                     [(u.sala, u.enemigo) for u in p.ubicaciones]) for p in reporte.frontera]
        self.assertEqual(frontera, [(2, "E", 5, "roja", [(6, None)])])
        self.assertEqual(reporte.no_obtenibles, ("negra", "roja", "verde"))
        self.assertEqual(reporte.ciclo, ("roja", "roja"))

    def test_puerta_sin_llave(self):
        # FR-205: una puerta cerrada que no declara llave nunca se abre; queda en la frontera
        # la puerta 1->3 está cerrada y no pide ninguna llave
        mapa = Esqueleto()
        mapa.agregar_pagina(pagina_salas_desde_json({"pagina": 1, "total_paginas": 1, "salas": [
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 3, "cerrada": True}}},
            {"id": 3, "nombre": "B", "salidas": {"S": {"sala": 1},
                                                 "E": {"sala": 9, "cerrada": True, "llave": "negra"}}},
            {"id": 9, "nombre": "Salida", "salidas": {}}]}))
        sin_llave = mapa.puerta(1, "N")
        self.assertIsNone(sin_llave.llave)
        reporte = VerificadorResolubilidad(mapa, [UbicacionLlave("negra", 3)]).verificar(
            1, 9, "negra")
        self.assertFalse(reporte.resoluble)
        self.assertEqual([(p.sala, p.destino, p.llave) for p in reporte.frontera], [(1, 3, None)])
        self.assertEqual(reporte.ciclo, ())

    def test_llave_que_no_esta(self):
        # FR-205: la puerta pide una llave que ninguna sala contiene
        salidas = ida_y_vuelta(1, "N", 9, True, "negra")
        reporte = verificar(salidas, [])
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.sin_ubicacion, ("negra",))
        self.assertEqual(reporte.frontera[0].ubicaciones, ())

    def test_salida_sin_puerta_que_la_pida(self):
        # FR-203: se llega a la salida por una puerta abierta y se tiene la llave, pero ninguna
        # puerta que pide la llave lleva ahí
        salidas = ida_y_vuelta(1, "N", 9) + ida_y_vuelta(1, "E", 2)
        reporte = verificar(salidas, [("negra", 2)])
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ("negra",))


class PruebasLineal(unittest.TestCase):

    def test_cada_salida_se_mira_una_vez(self):
        # PR-202: cadena de 300 llaves; la verificación termina y el orden es el de la cadena
        salidas = []
        llaves = []
        for sala in range(1, 301):
            salidas += ida_y_vuelta(sala, "E", sala + 1, True, f"k{sala:03d}")
            llaves.append((f"k{sala:03d}", sala))
        salidas += ida_y_vuelta(301, "N", 999, True, "negra")
        llaves.append(("negra", 301))
        reporte = verificar(salidas, llaves, sala_salida=999)
        self.assertTrue(reporte.resoluble)
        self.assertEqual(len(reporte.orden_llaves), 301)
        self.assertEqual(reporte.orden_llaves[:3], ("k001", "k002", "k003"))


if __name__ == "__main__":
    unittest.main()
