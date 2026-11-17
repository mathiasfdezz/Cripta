import random
import unittest

from modelo.buscador_rutas import BuscadorRutas
from modelo.estado_partida import EstadoPartida
from tests.criptas_prueba import enemigo, esqueleto, partida, ronda, salida

INFINITO = 10 ** 9


def ida_y_vuelta(a, direccion, b, costo=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, costo), salida(b, contraria, a, costo)]


def unir(*grupos):
    salidas = []
    for grupo in grupos:
        salidas.extend(grupo if isinstance(grupo, list) else [grupo])
    return salidas


class PruebasCazador(unittest.TestCase):
    """Reglas del cazador (spec 001, historia 2). Cada ronda el jugador espera 100 y el
    cazador, que también tiene velocidad 100, actúa una vez."""

    def test_cazador_sin_ruta_espera(self):
        # FR-006 (Apéndice B): la única salida hacia el jugador está cerrada
        mapa = esqueleto(salida(2, "N", 1, cerrada=True), salida(1, "S", 2))
        estado = partida(mapa)
        cazador = enemigo(estado, 2)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)
        self.assertEqual(cazador.proximo_evento.tiempo_siguiente, 100 + 100)

    def test_cazador_fuera_de_rango_espera(self):
        # FR-006 (Apéndice B): la ruta más barata cuesta 700 y el rango es 600
        mapa = esqueleto(*unir(ida_y_vuelta(1, "E", 2, 350), ida_y_vuelta(2, "E", 3, 350)))
        estado = partida(mapa)
        cazador = enemigo(estado, 3)
        ronda(estado)
        self.assertEqual(cazador.sala, 3)
        self.assertEqual(cazador.proximo_evento.tiempo_siguiente, 200)

    def test_cazador_en_el_limite_del_rango_se_mueve(self):
        # FR-014: d = rango sí persigue, y el paso cuesta lo de la salida
        mapa = esqueleto(*unir(ida_y_vuelta(1, "E", 2, 300), ida_y_vuelta(2, "E", 3, 300)))
        estado = partida(mapa)
        cazador = enemigo(estado, 3)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)
        self.assertEqual(cazador.proximo_evento.tiempo_siguiente, 100 + 300)

    def test_cazador_elige_ruta_menor_costo(self):
        # FR-005 (Apéndice B): directo 1 salida de 400; por 2 y 3, tres salidas de 100
        mapa = esqueleto(salida(1, "E", 4, 400), salida(1, "N", 2, 100),
                         salida(2, "E", 3, 100), salida(3, "S", 4, 100))
        estado = partida(mapa, sala_jugador=4)
        cazador = enemigo(estado, 1)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)

    def test_cazador_desempate_menor_id(self):
        # FR-007 (Apéndice B): por N llega a la 3 y por S a la 2; las dos rutas cuestan 200
        mapa = esqueleto(salida(1, "N", 3, 100), salida(3, "E", 4, 100),
                         salida(1, "S", 2, 150), salida(2, "E", 4, 50))
        estado = partida(mapa, sala_jugador=4)
        cazador = enemigo(estado, 1)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)

    def test_desempate_con_muchas_rutas_iguales(self):
        # FR-007: rejilla de costo uniforme, muchísimas rutas mínimas; siempre la vecina menor
        salidas = []
        for fila in range(4):
            for columna in range(4):
                sala = fila * 4 + columna + 1
                if columna < 3:
                    salidas += ida_y_vuelta(sala, "E", sala + 1)
                if fila < 3:
                    salidas += ida_y_vuelta(sala, "S", sala + 4)
        estado = partida(esqueleto(*salidas), sala_jugador=1)
        cazador = enemigo(estado, 16, "ent_espectro")
        recorrido = []
        for _ in range(6):
            ronda(estado)
            recorrido.append(cazador.sala)
        # desde 16 baja por la vecina de menor id: 12, 8, 4, 3, 2, 1
        self.assertEqual(recorrido, [12, 8, 4, 3, 2, 1])

    def test_cazador_puerta_se_cierra_entre_turnos(self):
        # FR-009 (Apéndice B): 1-2-5 cuesta 200 y 1-3-5 cuesta 300
        mapa = esqueleto(*unir(ida_y_vuelta(1, "N", 2, 100), ida_y_vuelta(2, "E", 5, 100),
                               ida_y_vuelta(1, "S", 3, 150), ida_y_vuelta(3, "E", 5, 150)))
        estado = partida(mapa, sala_jugador=5)
        cazador = enemigo(estado, 1)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)
        mapa.puerta(2, "E").cerrar()           # entre dos de sus turnos
        ronda(estado)
        # desde cero: de 2 solo queda volver a 1 y bajar por 3 (100 + 150 + 150)
        self.assertEqual(cazador.sala, 1)
        ronda(estado)
        self.assertEqual(cazador.sala, 3)

    def test_multiples_cazadores_comparten_sala(self):
        # FR-015: tres cazadores en la sala del jugador atacan los tres
        estado = partida(esqueleto(*ida_y_vuelta(1, "N", 2)))
        for _ in range(3):
            enemigo(estado, 1)
        golpes = ronda(estado)
        self.assertEqual(len(golpes), 3)
        self.assertEqual(len({g.atacante.instancia for g in golpes}), 3)

    def test_varios_cazadores_llegan_a_la_misma_sala(self):
        # FR-015: no hay límite de ocupación
        mapa = esqueleto(*unir(ida_y_vuelta(1, "N", 2), ida_y_vuelta(2, "N", 3)))
        estado = partida(mapa)
        cazadores = [enemigo(estado, 3) for _ in range(4)]
        ronda(estado)
        self.assertEqual([c.sala for c in cazadores], [2, 2, 2, 2])

    def test_cazador_salida_un_solo_sentido(self):
        # FR-005, FR-008: existe 1->2 pero no 2->1; desde 2 hay que dar la vuelta por 3
        mapa = esqueleto(salida(1, "E", 2), salida(2, "N", 3), salida(3, "O", 1))
        estado = partida(mapa)
        cazador = enemigo(estado, 2)
        ronda(estado)
        self.assertEqual(cazador.sala, 3)

    def test_cazador_puerta_cerrada_unilateral(self):
        # FR-005, FR-008: 2->1 cerrada y 1->2 abierta
        mapa = esqueleto(salida(1, "E", 2), salida(2, "O", 1, cerrada=True))
        estado = partida(mapa)
        bloqueado = enemigo(estado, 2)
        ronda(estado)
        self.assertEqual(bloqueado.sala, 2)
        estado2 = partida(esqueleto(salida(1, "E", 2), salida(2, "O", 1, cerrada=True)),
                          sala_jugador=2)
        libre = enemigo(estado2, 1)
        ronda(estado2)
        self.assertEqual(libre.sala, 2)

    def test_cazador_no_depende_del_contenido_descargado(self):
        # FR-008: la sala intermedia no tiene contenido cargado y el cazador pasa igual
        mapa = esqueleto(*unir(ida_y_vuelta(1, "E", 2), ida_y_vuelta(2, "E", 3)))
        estado = partida(mapa, cargar=(1, 3), controlar_contenido=True)
        cazador = enemigo(estado, 3)
        ronda(estado)
        self.assertEqual(cazador.sala, 2)
        self.assertFalse(estado.contenido_cargado(2))

    def test_cazador_no_abre_puertas(self):
        # supuesto de la spec: aunque la puerta pida una llave, el cazador no la abre
        mapa = esqueleto(salida(1, "E", 2), salida(2, "O", 1, cerrada=True, llave="itm_llave"))
        estado = partida(mapa)
        cazador = enemigo(estado, 2)
        for _ in range(3):
            ronda(estado)
        self.assertEqual(cazador.sala, 2)
        self.assertTrue(mapa.puerta(2, "O").esta_cerrada())


def decision_desde_cero(estado, cazador):
    """Sala a la que debería ir el cazador según §3.2, calculada aparte con relajación
    repetida (sin heap ni cachés): independiente de la implementación."""
    grafo = estado.esqueleto.grafo()
    n = grafo.cantidad_salas()
    objetivo = grafo.indice(estado.jugador.sala)
    distancia = [INFINITO] * n
    distancia[objetivo] = 0
    cambio = True
    while cambio:
        cambio = False
        for origen in range(n):
            for destino, costo, salida_ in grafo.salientes[origen]:
                if estado.esqueleto.salida_abierta(salida_) and \
                        distancia[destino] + costo < distancia[origen]:
                    distancia[origen] = distancia[destino] + costo
                    cambio = True
    desde = grafo.indice(cazador.sala)
    d = distancia[desde]
    if d >= INFINITO or d > cazador.rango:
        return cazador.sala
    vecinas = [grafo.ids[destino] for destino, costo, salida_ in grafo.salientes[desde]
               if estado.esqueleto.salida_abierta(salida_) and costo + distancia[destino] == d]
    return min(vecinas)


class PruebasEquivalencia(unittest.TestCase):

    def test_reutilizar_equivale_a_calcular_desde_cero(self):
        # FR-009: rejilla 6x6 con costos variados, 8 cazadores, puertas que se abren y
        # cierran entre rondas y un jugador que se mueve. Cada decisión se compara con
        # un cálculo desde cero hecho aparte.
        azar = random.Random(20261117)
        salidas = []
        for fila in range(6):
            for columna in range(6):
                sala = fila * 6 + columna + 1
                if columna < 5:
                    salidas += ida_y_vuelta(sala, "E", sala + 1, azar.choice((20, 50, 100, 150)))
                if fila < 5:
                    salidas += ida_y_vuelta(sala, "S", sala + 6, azar.choice((20, 50, 100, 150)))
        mapa = esqueleto(*salidas)
        estado = partida(mapa, sala_jugador=15)
        cazadores = [enemigo(estado, sala, tipo) for sala, tipo in
                     ((1, "ent_sabueso"), (6, "ent_espectro"), (31, "ent_sabueso"),
                      (36, "ent_espectro"), (3, "ent_sabueso"), (18, "ent_sabueso"),
                      (33, "ent_espectro"), (24, "ent_sabueso"))]
        original = EstadoPartida._cazar
        comparadas = []

        def cazar_y_comparar(propio, cazador):
            esperada = decision_desde_cero(propio, cazador)
            costo = original(propio, cazador)
            comparadas.append((esperada, cazador.sala))
            return costo

        EstadoPartida._cazar = cazar_y_comparar
        try:
            grafo = mapa.grafo()
            for vuelta in range(60):
                for _ in range(azar.randrange(4)):
                    puerta = mapa.puerta_de_salida(azar.randrange(grafo.cantidad_salidas()))
                    puerta.cerrar() if puerta.esta_abierta() else puerta.abrir()
                if vuelta % 5 == 0:
                    abiertas = [s.direccion for s in mapa.obtener(estado.jugador.sala).salidas
                                if mapa.puede_atravesar(estado.jugador.sala, s.direccion)]
                    if abiertas:
                        estado.mover_jugador(abiertas[0])
                        estado.avanzar_hasta_turno_jugador()
                        continue
                ronda(estado)
        finally:
            EstadoPartida._cazar = original
        self.assertGreater(len(comparadas), 100)
        for esperada, obtenida in comparadas:
            self.assertEqual(esperada, obtenida)
        buscador = estado.buscador_cazadores()
        # hubo reutilización real, no un recálculo por decisión
        self.assertGreater(buscador.reutilizados, 0)
        self.assertLess(buscador.calculos, len(comparadas))


class PruebasBuscadorRutas(unittest.TestCase):

    def test_la_cota_limita_las_salas_visitadas(self):
        # PR-001 / §5.1: con cota pequeña solo se asientan las salas cercanas
        salidas = []
        for sala in range(1, 200):
            salidas += ida_y_vuelta(sala, "E", sala + 1, 100)
        mapa = esqueleto(*salidas)
        grafo = mapa.grafo()
        buscador = BuscadorRutas(grafo, mapa.salida_abierta)
        buscador.calcular(grafo.indice(100), 300)
        self.assertEqual(buscador.salas_asentadas, 7)      # 97..103
        self.assertEqual(buscador.distancia(grafo.indice(103)), 300)
        self.assertIsNone(buscador.distancia(grafo.indice(104)))

    def test_cambio_lejano_no_invalida_y_cercano_si(self):
        # FR-009 / §5.2: una puerta fuera de la región asentada no obliga a recalcular
        salidas = []
        for sala in range(1, 50):
            salidas += ida_y_vuelta(sala, "E", sala + 1, 100)
        mapa = esqueleto(*salidas)
        grafo = mapa.grafo()
        buscador = BuscadorRutas(grafo, mapa.salida_abierta)
        objetivo = grafo.indice(10)
        buscador.asegurar(objetivo, 300)
        mapa.tomar_cambios()
        mapa.puerta(40, "E").cerrar()
        self.assertFalse(buscador.asegurar(objetivo, 300, *mapa.tomar_cambios()))
        mapa.puerta(12, "O").cerrar()
        self.assertTrue(buscador.asegurar(objetivo, 300, *mapa.tomar_cambios()))
        self.assertIsNone(buscador.distancia(grafo.indice(12)))
        # deshacer el cambio también avisa
        mapa.puerta(12, "O").cerrada = False
        self.assertTrue(buscador.asegurar(objetivo, 300, *mapa.tomar_cambios()))
        self.assertEqual(buscador.distancia(grafo.indice(12)), 200)


if __name__ == "__main__":
    unittest.main()
