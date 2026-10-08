import random
import unittest

from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.esqueleto import Esqueleto
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.movimiento import MovimientoInvalido
from modelo.rastro import Rastro
from tests.test_esqueleto import esqueleto, pagina, sala


def mapa_linea():
    """1 -E- 2 -E- 3 -E- 4, todas abiertas."""
    return esqueleto(sala(1, E=2), sala(2, O=1, E=3), sala(3, O=2, E=4), sala(4, O=3))


def partida(mapa, sala_jugador=1, semilla=1):
    jugador = Jugador(sala_jugador, EstadisticasJugador(1000, 6, 2, 100), Inventario(10))
    return EstadoPartida(semilla, jugador, mapa)


def ficha(comportamiento, velocidad=100):
    return FichaCatalogo(id="ent_x", nombre="X", clase="enemigo", vida_max=1000, ataque=1,
                         defensa=0, velocidad=velocidad, comportamiento=comportamiento)


def con_enemigo(estado, sala_enemigo, comportamiento, instancia="e-1", velocidad=100):
    enemigo = estado.colocar_enemigo(InstanciaEnemigo(instancia, "ent_x"),
                                     ficha(comportamiento, velocidad), sala_enemigo)
    enemigo.activo = True
    estado.programar_accion(enemigo)
    return enemigo


def una_ronda(estado):
    """El jugador espera 100 y avanzan los enemigos: cada enemigo activo actúa una vez.
    Devuelve los ataques ocurridos."""
    estado.esperar()
    return estado.avanzar_hasta_turno_jugador()


class EsqueletoContado(Esqueleto):
    """Cuenta las consultas al mapa para comprobar cuánto trabaja una decisión."""

    def __init__(self):
        super().__init__()
        self.consultas = 0

    def obtener(self, id_sala):
        self.consultas += 1
        return super().obtener(id_sala)

    def puerta(self, id_sala, direccion):
        self.consultas += 1
        return super().puerta(id_sala, direccion)


def corredor(n):
    """1 -E- 2 -E- ... -E- n, todas abiertas."""
    salas = []
    for i in range(1, n + 1):
        salidas = {}
        if i > 1:
            salidas["O"] = i - 1
        if i < n:
            salidas["E"] = i + 1
        salas.append(sala(i, **salidas))
    mapa = EsqueletoContado()
    mapa.agregar_pagina(pagina(*salas))
    mapa.consultas = 0
    return mapa


class PruebasCostos(unittest.TestCase):

    def test_atacar_cuesta_100(self):
        estado = partida(mapa_linea())
        estado.colocar_enemigo(InstanciaEnemigo("e-1", "ent_x"), ficha("guardián", 1), 1)
        estado.iniciar()
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 100)

    def test_el_segundo_ataque_es_en_el_siguiente_turno(self):
        estado = partida(mapa_linea())
        estado.colocar_enemigo(InstanciaEnemigo("e-1", "ent_x"), ficha("guardián", 1), 1)
        estado.iniciar()
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.tiempo, 0)
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.tiempo, 100)
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 200)

    def test_abrir_puerta_cuesta_50(self):
        llave = FichaCatalogo(id="itm_llave", nombre="Llave", clase="llave", peso=1, valor=0)
        mapa = esqueleto(sala(1, E=(2, True)), sala(2, O=1))
        estado = partida(mapa)
        estado.jugador.inventario.recoger(llave)
        estado.iniciar()
        estado.abrir_puerta("E")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)


class PruebasRastro(unittest.TestCase):

    def test_la_sala_inicial_tiene_rastro_en_0(self):
        estado = partida(mapa_linea())
        estado.iniciar()
        self.assertEqual(estado.rastro.tiempo_en(1), 0)
        self.assertIsNone(estado.rastro.tiempo_en(2))

    def test_moverse_marca_la_sala_destino(self):
        estado = partida(mapa_linea())
        estado.iniciar()
        estado.mover_jugador("E")
        self.assertEqual(estado.rastro.tiempo_en(2), 0)
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("E")
        self.assertEqual(estado.rastro.tiempo_en(3), 100)

    def test_mas_fresca_y_caducidad(self):
        rastro = Rastro(mapa_linea())
        rastro.marcar(1, 50)
        rastro.marcar(3, 120)
        self.assertEqual(rastro.sala_mas_fresca(2, 200), 3)
        # 120 + 399 todavía sirve; con 400 de antigüedad ya no
        self.assertEqual(rastro.sala_mas_fresca(2, 519), 3)
        self.assertIsNone(rastro.sala_mas_fresca(2, 520))

    def test_empate_gana_la_sala_de_menor_id(self):
        rastro = Rastro(mapa_linea())
        rastro.marcar(1, 80)
        rastro.marcar(3, 80)
        self.assertEqual(rastro.sala_mas_fresca(2, 100), 1)

    def test_no_mira_detras_de_puertas_cerradas(self):
        # cerrada solo desde la sala 2: el rastreador de la 2 no puede ir a la 1
        mapa = esqueleto(sala(1, E=2), sala(2, O=(1, True)))
        rastro = Rastro(mapa)
        rastro.marcar(1, 10)
        self.assertIsNone(rastro.sala_mas_fresca(2, 20))
        self.assertEqual(rastro.salidas_abiertas(2), [])
        self.assertEqual(rastro.salidas_abiertas(1), [2])

    def test_volver_a_entrar_actualiza_el_rastro(self):
        estado = partida(mapa_linea())
        estado.iniciar()
        estado.mover_jugador("E")                       # entra a la 2 en t=0
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("O")                       # vuelve a la 1 en t=100
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("E")                       # y otra vez a la 2 en t=200
        self.assertEqual(estado.rastro.tiempo_en(1), 100)
        self.assertEqual(estado.rastro.tiempo_en(2), 200)

    def test_un_movimiento_rechazado_no_deja_rastro(self):
        estado = partida(esqueleto(sala(1, E=(2, True)), sala(2, O=1)))
        estado.iniciar()
        with self.assertRaises(MovimientoInvalido):
            estado.mover_jugador("E")
        self.assertIsNone(estado.rastro.tiempo_en(2))
        self.assertEqual(estado.rastro.tiempo_en(1), 0)

    def test_rastro_de_400_o_mas_deja_de_ser_valido_para_el_rastreador(self):
        # el rastreador de la sala 3 (velocidad 25) actúa por primera vez en t=400
        for marca, destino in ((1, 2), (0, 3)):         # 399 de antigüedad sirve; 400 ya no
            estado = partida(mapa_linea())
            rastreador = con_enemigo(estado, 3, "rastreador", velocidad=25)
            estado.iniciar()
            estado.rastro.marcar(2, marca)
            for _ in range(4):
                una_ronda(estado)
            self.assertEqual(estado.tiempo, 400)
            self.assertEqual(rastreador.sala, destino, f"rastro marcado en t={marca}")


class PruebasComportamientos(unittest.TestCase):

    def test_guardian_no_deja_su_sala(self):
        estado = partida(mapa_linea())
        guardian = con_enemigo(estado, 3, "guardián")
        estado.iniciar()
        for _ in range(5):
            estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
            estado.avanzar_hasta_turno_jugador()
        self.assertEqual(guardian.sala, 3)

    def test_rastreador_sigue_el_rastro_fresco(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 3, "rastreador", velocidad=50)
        estado.iniciar()
        estado.mover_jugador("E")            # el jugador deja rastro en 2
        estado.avanzar_hasta_turno_jugador() # la rata actúa en 200 > 100: aún no
        estado.mover_jugador("O")
        estado.avanzar_hasta_turno_jugador() # en 200 la rata ve el rastro de 2 y va
        self.assertEqual(rastreador.sala, 2)

    def test_rastreador_sin_rastro_espera(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 4, "rastreador")
        estado.iniciar()
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(rastreador.sala, 4)

    def test_errante_se_mueve_por_salidas_abiertas(self):
        mapa = esqueleto(sala(1, E=2), sala(2, O=1, E=(3, True)), sala(3, O=2))
        estado = partida(mapa, sala_jugador=1)
        errante = con_enemigo(estado, 2, "errante")
        estado.iniciar()
        visitadas = []
        for _ in range(6):
            estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
            estado.avanzar_hasta_turno_jugador()
            visitadas.append(errante.sala)
        self.assertNotIn(3, visitadas)      # nunca cruza la puerta cerrada

    def test_errante_sin_salidas_espera(self):
        mapa = esqueleto(sala(1, E=2), sala(2, O=1), sala(9))
        estado = partida(mapa)
        errante = con_enemigo(estado, 9, "errante")
        estado.iniciar()
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(errante.sala, 9)

    def test_misma_semilla_mismos_movimientos(self):
        def correr(semilla):
            mapa = esqueleto(sala(1, E=2, S=3), sala(2, O=1, S=4), sala(3, N=1, E=4),
                             sala(4, N=2, O=3))
            estado = partida(mapa, semilla=semilla)
            errante = con_enemigo(estado, 4, "errante")
            estado.iniciar()
            recorrido = []
            for i in range(10):
                estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
                estado.avanzar_hasta_turno_jugador()
                recorrido.append(errante.sala)
            return recorrido

        self.assertEqual(correr(7), correr(7))

    def test_guardian_ataca_si_comparte_sala_con_el_jugador(self):
        estado = partida(mapa_linea(), sala_jugador=2)
        guardian = con_enemigo(estado, 2, "guardián")
        estado.iniciar()
        estado.rastro.marcar(3, 0)                      # un rastro cerca no lo mueve
        ataques = una_ronda(estado)
        self.assertEqual(len(ataques), 1)
        self.assertIs(ataques[0].atacante, guardian)
        self.assertLess(estado.jugador.vida, 1000)
        self.assertEqual(guardian.sala, 2)

    def test_guardian_espera_si_no_comparte_sala(self):
        estado = partida(mapa_linea())
        guardian = con_enemigo(estado, 3, "guardián")
        estado.iniciar()
        estado.rastro.marcar(2, 0)
        for ronda in (1, 2, 3):
            self.assertEqual(una_ronda(estado), [])
            self.assertEqual(guardian.sala, 3)
            # esperar también es una acción: la siguiente es 100 después
            self.assertEqual(guardian.proximo_evento.tiempo_siguiente, 100 * (ronda + 1))
        self.assertEqual(estado.jugador.vida, 1000)

    def test_compartir_sala_prioriza_el_ataque_y_no_hay_movimiento(self):
        for comportamiento in ("errante", "rastreador"):
            estado = partida(mapa_linea(), sala_jugador=2, semilla=5)
            enemigo = con_enemigo(estado, 2, comportamiento)
            estado.iniciar()
            estado.rastro.marcar(1, 0)
            estado.rastro.marcar(3, 0)
            ataques = una_ronda(estado)
            self.assertEqual(len(ataques), 1, comportamiento)
            self.assertEqual(enemigo.sala, 2, comportamiento)
            # solo se sorteó el daño del golpe: el errante no sorteó ninguna salida
            espejo = random.Random(5)
            espejo.randint(0, 4)
            self.assertEqual(estado.azar.random(), espejo.random(), comportamiento)

    def test_errante_elige_con_el_random_de_la_partida(self):
        # en la sala 1: N->2, S->3, E->4 (puerta cerrada), O->5; abiertas: 2, 3 y 5 (orden N, S, E, O)
        mapa = esqueleto(sala(1, N=2, S=3, E=(4, True), O=5), sala(2, S=1), sala(3, N=1),
                         sala(4, O=1), sala(5, E=1), sala(9))
        elegidas = set()
        for semilla in range(1, 9):
            estado = partida(mapa, sala_jugador=9, semilla=semilla)   # el jugador está lejos
            errante = con_enemigo(estado, 1, "errante")
            estado.iniciar()
            una_ronda(estado)
            espejo = random.Random(semilla)
            self.assertEqual(errante.sala, [2, 3, 5][espejo.randrange(3)], f"semilla {semilla}")
            self.assertEqual(estado.azar.random(), espejo.random())   # un solo sorteo
            elegidas.add(errante.sala)
        self.assertGreater(len(elegidas), 1)            # con otras semillas elige otras salidas

    def test_errante_no_pasa_a_una_sala_que_no_esta_en_el_mapa(self):
        mapa = esqueleto(sala(1), sala(2, E=9))         # la única salida de la 2 va a la sala 9
        estado = partida(mapa, sala_jugador=1)
        errante = con_enemigo(estado, 2, "errante")
        estado.iniciar()
        for _ in range(3):
            una_ronda(estado)
        self.assertEqual(errante.sala, 2)
        espejo = random.Random(1)
        self.assertEqual(estado.azar.random(), espejo.random())   # sin salidas no hay sorteo

    def test_errante_con_otra_semilla_o_el_random_global_distinto(self):
        def recorrido(semilla, global_):
            random.seed(global_)
            mapa = esqueleto(sala(1, E=2, S=3), sala(2, O=1, S=4), sala(3, N=1, E=4),
                             sala(4, N=2, O=3), sala(9))
            estado = partida(mapa, sala_jugador=9, semilla=semilla)
            errante = con_enemigo(estado, 4, "errante")
            estado.iniciar()
            salas = []
            for _ in range(12):
                una_ronda(estado)
                salas.append(errante.sala)
            return salas

        self.assertEqual(recorrido(3, 100), recorrido(3, 200))    # el random global no influye
        self.assertNotEqual(recorrido(3, 0), recorrido(4, 0))     # la semilla de la partida sí

    def test_rastreador_prefiere_el_rastro_mas_reciente(self):
        mapa = esqueleto(sala(5, N=7, S=3), sala(7, S=5), sala(3, N=5), sala(9))
        estado = partida(mapa, sala_jugador=9)
        rastreador = con_enemigo(estado, 5, "rastreador")
        estado.iniciar()
        estado.rastro.marcar(3, 10)
        estado.rastro.marcar(7, 60)
        una_ronda(estado)                               # actúa en t=100: 90 y 40 de antigüedad
        self.assertEqual(rastreador.sala, 7)

    def test_rastreador_empata_por_menor_id(self):
        # N->7 va antes que S->3 en el orden de salidas, pero gana la sala 3
        mapa = esqueleto(sala(5, N=7, S=3), sala(7, S=5), sala(3, N=5), sala(9))
        estado = partida(mapa, sala_jugador=9)
        rastreador = con_enemigo(estado, 5, "rastreador")
        estado.iniciar()
        estado.rastro.marcar(7, 30)
        estado.rastro.marcar(3, 30)
        una_ronda(estado)
        self.assertEqual(rastreador.sala, 3)

    def test_rastreador_solo_mira_las_salas_vecinas(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 4, "rastreador")
        estado.iniciar()
        estado.rastro.marcar(2, 0)                      # fresco, pero a dos salas de distancia
        for _ in range(3):
            una_ronda(estado)
        self.assertEqual(rastreador.sala, 4)

    def test_rastreador_no_pasa_por_una_puerta_cerrada(self):
        mapa = esqueleto(sala(1, E=2), sala(2, O=(1, True), E=3), sala(3, O=2), sala(9))
        estado = partida(mapa, sala_jugador=9)          # el jugador está lejos de todo
        rastreador = con_enemigo(estado, 2, "rastreador")
        estado.iniciar()
        estado.rastro.marcar(1, 0)                      # el único rastro está tras la puerta cerrada
        una_ronda(estado)
        self.assertEqual(rastreador.sala, 2)

    def test_rastreador_persigue_al_jugador_y_luego_lo_ataca(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 3, "rastreador")
        estado.iniciar()
        estado.mover_jugador("E")                       # el jugador pasa a la 2 en t=0
        self.assertEqual(estado.avanzar_hasta_turno_jugador(), [])   # en t=100 el rastreador va a la 2
        self.assertEqual(rastreador.sala, 2)
        self.assertEqual(estado.jugador.sala, 2)
        estado.esperar()
        ataques = estado.avanzar_hasta_turno_jugador()  # en t=200 ya comparten sala: ataca
        self.assertEqual([a.atacante for a in ataques], [rastreador])
        self.assertEqual(rastreador.sala, 2)


class PruebasCostoDeLaDecision(unittest.TestCase):

    def consultas_de_decidir(self, n):
        mapa = corredor(n)
        rastro = Rastro(mapa)
        medio = n // 2
        rastro.marcar(medio + 1, 0)
        destino = rastro.sala_mas_fresca(medio, 10)
        primera = mapa.consultas
        rastro.sala_mas_fresca(medio, 10)
        rastro.salidas_abiertas(medio)
        return destino, primera, mapa.consultas - primera

    def test_decidir_depende_de_las_salidas_y_no_del_tamano_del_mapa(self):
        chico = self.consultas_de_decidir(10)
        grande = self.consultas_de_decidir(600)
        self.assertEqual((chico[0], grande[0]), (6, 301))
        # la primera decisión solo enlaza las 2 salidas de la sala: la sala y, por
        # cada salida, su destino y su puerta; son las mismas consultas en un mapa de
        # 10 salas que en uno de 600
        self.assertEqual(chico[1], grande[1])
        self.assertLessEqual(chico[1], 1 + 2 * 2)
        # y después ya no consulta el mapa
        self.assertEqual((chico[2], grande[2]), (0, 0))


if __name__ == "__main__":
    unittest.main()