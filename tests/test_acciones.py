import unittest

from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.estado_partida import DERROTA, EN_CURSO, VICTORIA, EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.movimiento import (CONTENIDO_PENDIENTE, INVENTARIO_LLENO, MovimientoInvalido,
                               NADA_QUE_RECOGER, NO_EQUIPABLE, NO_USABLE, PARTIDA_TERMINADA,
                               SIN_OBJETO)
from tests.test_esqueleto import esqueleto, sala

FICHAS = (
    FichaCatalogo(id="ent_rata", nombre="Rata", clase="enemigo", vida_max=12, ataque=5,
                  defensa=1, velocidad=150, comportamiento="guardián"),
    FichaCatalogo(id="itm_pocion", nombre="Poción", clase="pocion", peso=1, valor=5, cura=8),
    FichaCatalogo(id="itm_rapida", nombre="Poción rápida", clase="pocion", peso=1, valor=5,
                  modificador_velocidad=100, duracion=300),
    FichaCatalogo(id="itm_daga", nombre="Daga", clase="arma", peso=2, valor=15, ataque_bonus=3),
    FichaCatalogo(id="itm_antorcha", nombre="Antorcha", clase="antorcha", peso=1, valor=5,
                  duracion=200),
    FichaCatalogo(id="itm_llave", nombre="Llave negra", clase="llave", peso=1, valor=0),
)


def ficha(id_ficha):
    for f in FICHAS:
        if f.id == id_ficha:
            return f
    raise KeyError(id_ficha)


def mapa():
    """1 -N- 2 -E(cerrada con itm_llave)- 3, que es la salida."""
    return esqueleto(sala(1, N=2), sala(2, S=1, E=(3, True)), sala(3, O=2))


def partida(objetos=(), enemigos=(), vida=30, capacidad=10, cargar=(1, 2, 3)):
    jugador = Jugador(1, EstadisticasJugador(30, 6, 2, 100), Inventario(capacidad))
    jugador.vida = vida
    estado = EstadoPartida(1, jugador, mapa(), obtener_ficha=ficha)
    estado.configurar_salida(3, "itm_llave")
    estado.controlar_contenido = True
    for numero in cargar:
        en_sala = (tuple(objetos), tuple(enemigos)) if numero == 1 else ((), ())
        estado.cargar_contenido(ContenidoSala(numero, en_sala[1], en_sala[0], ()))
    estado.iniciar()
    return estado


def turno(estado):
    estado.avanzar_hasta_turno_jugador()


class PruebasObjetos(unittest.TestCase):

    def assert_rechazo(self, estado, motivo, accion, *args):
        antes = (estado.tiempo, estado.jugador.proximo_evento, estado.acciones)
        with self.assertRaises(MovimientoInvalido) as ctx:
            accion(*args)
        self.assertEqual(ctx.exception.motivo, motivo)
        self.assertEqual(antes, (estado.tiempo, estado.jugador.proximo_evento, estado.acciones))

    def test_recoger_cuesta_25(self):
        estado = partida(objetos=["itm_daga"])
        estado.recoger()
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 25)
        self.assertEqual(estado.suelo(1), [])
        self.assertEqual(estado.jugador.inventario.obtener_actual().id, "itm_daga")

    def test_con_varios_hay_que_elegir(self):
        estado = partida(objetos=["itm_daga", "itm_pocion"])
        self.assert_rechazo(estado, NADA_QUE_RECOGER, estado.recoger)
        estado.recoger("itm_pocion")
        self.assertEqual(estado.suelo(1), ["itm_daga"])

    def test_inventario_lleno_no_gasta_tiempo(self):
        estado = partida(objetos=["itm_daga", "itm_pocion"], capacidad=1)
        estado.recoger("itm_daga")
        turno(estado)
        self.assert_rechazo(estado, INVENTARIO_LLENO, estado.recoger, "itm_pocion")

    def test_nada_que_recoger(self):
        estado = partida()
        self.assert_rechazo(estado, NADA_QUE_RECOGER, estado.recoger)

    def test_soltar_cuesta_25_y_queda_en_el_suelo(self):
        estado = partida(objetos=["itm_daga"])
        estado.recoger()
        turno(estado)
        estado.soltar()
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)
        self.assertEqual(estado.suelo(1), ["itm_daga"])
        self.assertEqual(len(estado.jugador.inventario), 0)

    def test_soltar_sin_objeto(self):
        estado = partida()
        self.assert_rechazo(estado, SIN_OBJETO, estado.soltar)

    def test_equipar_cuesta_50_y_suma_bonus(self):
        estado = partida(objetos=["itm_daga"])
        estado.recoger()
        turno(estado)
        estado.equipar()
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 75)
        self.assertEqual(estado.jugador.ataque_efectivo(), 9)

    def test_no_se_equipa_una_pocion(self):
        estado = partida(objetos=["itm_pocion"])
        estado.recoger()
        turno(estado)
        self.assert_rechazo(estado, NO_EQUIPABLE, estado.equipar)

    def test_pocion_cura_sin_pasar_de_vida_max(self):
        estado = partida(objetos=["itm_pocion"], vida=25)
        estado.recoger()
        turno(estado)
        estado.usar()
        self.assertEqual(estado.jugador.vida, 30)               # 25 + 8 se queda en 30
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 75)
        self.assertEqual(len(estado.jugador.inventario), 0)     # se consumió

    def test_un_arma_no_se_usa(self):
        estado = partida(objetos=["itm_daga"])
        estado.recoger()
        turno(estado)
        self.assert_rechazo(estado, NO_USABLE, estado.usar)

    def test_pocion_de_velocidad_acerca_el_turno_y_luego_se_acaba(self):
        estado = partida(objetos=["itm_rapida"])
        estado.recoger()
        turno(estado)                                           # t=25
        estado.usar()                                           # turno en 75 a velocidad 100
        # con velocidad 200 lo que faltaba (50) se reduce a la mitad
        self.assertEqual(estado.jugador.velocidad, 200)
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)
        for _ in range(8):
            turno(estado)
            estado.esperar()
        self.assertEqual(estado.jugador.velocidad, 100)         # pasaron las 300 unidades

    def test_antorcha_encendida_y_apagada(self):
        estado = partida(objetos=["itm_antorcha"])
        estado.recoger()
        turno(estado)
        estado.usar()                                           # en t=25 dura 200
        self.assertEqual(estado.antorcha_hasta, 225)
        for _ in range(4):
            turno(estado)
            estado.esperar()
        self.assertIsNone(estado.antorcha_hasta)

    def test_esperar_cuesta_100(self):
        estado = partida()
        estado.esperar()
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 100)
        self.assertEqual(estado.acciones, 1)


class PruebasContenidoPendiente(unittest.TestCase):

    def test_no_se_entra_a_una_sala_sin_contenido(self):
        estado = partida(cargar=(1,))
        with self.assertRaises(MovimientoInvalido) as ctx:
            estado.mover_jugador("N")
        self.assertEqual(ctx.exception.motivo, CONTENIDO_PENDIENTE)
        self.assertEqual((estado.jugador.sala, estado.tiempo), (1, 0))
        estado.cargar_contenido(ContenidoSala(2, (), (), ()))
        self.assertEqual(estado.mover_jugador("N"), 2)


class PruebasFinDePartida(unittest.TestCase):

    def test_victoria_al_entrar_a_la_salida_tras_abrir_su_puerta(self):
        estado = partida()
        estado.jugador.inventario.recoger(ficha("itm_llave"))
        estado.mover_jugador("N")
        turno(estado)
        estado.abrir_puerta("E")
        turno(estado)
        self.assertEqual(estado.resultado, EN_CURSO)
        estado.mover_jugador("E")
        self.assertEqual(estado.resultado, VICTORIA)
        self.assertTrue(estado.terminada())
        with self.assertRaises(MovimientoInvalido) as ctx:
            estado.esperar()
        self.assertEqual(ctx.exception.motivo, PARTIDA_TERMINADA)

    def test_derrota_cuando_el_jugador_muere(self):
        rata = InstanciaEnemigo("e-1", "ent_rata", 12)
        estado = partida(enemigos=[rata], vida=1)
        estado.esperar()
        turno(estado)
        self.assertEqual(estado.resultado, DERROTA)
        self.assertFalse(estado.jugador.esta_vivo())

    def test_contadores_para_el_puntaje(self):
        rata = InstanciaEnemigo("e-1", "ent_rata", 1)
        estado = partida(enemigos=[rata])
        estado.jugador_ataca("e-1")
        turno(estado)
        estado.esperar()
        self.assertEqual((estado.acciones, estado.enemigos_derrotados), (2, 1))


if __name__ == "__main__":
    unittest.main()
