import unittest

from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.movimiento import NADA_QUE_DESHACER, MovimientoInvalido, SIN_PERGAMINO
from tests.test_esqueleto import esqueleto, sala

FICHAS = (
    FichaCatalogo(id="ent_rata", nombre="Rata", clase="enemigo", vida_max=12, ataque=5,
                  defensa=1, velocidad=150, comportamiento="rastreador", suelta=("itm_pocion",)),
    FichaCatalogo(id="itm_pocion", nombre="Poción", clase="pocion", peso=1, valor=5, cura=8),
    FichaCatalogo(id="itm_daga", nombre="Daga", clase="arma", peso=2, valor=15, ataque_bonus=3),
    FichaCatalogo(id="itm_perg", nombre="Pergamino", clase="pergamino_retroceso", peso=1, valor=40),
    FichaCatalogo(id="itm_llave", nombre="Llave", clase="llave", peso=1, valor=0),
)


def ficha(id_ficha):
    for f in FICHAS:
        if f.id == id_ficha:
            return f
    raise KeyError(id_ficha)


def partida(pergaminos=1, objetos_sala_1=(), enemigos_sala_1=(), semilla=4):
    mapa = esqueleto(sala(1, N=2, E=(3, True)), sala(2, S=1), sala(3, O=1))
    jugador = Jugador(1, EstadisticasJugador(30, 6, 2, 100), Inventario(10))
    estado = EstadoPartida(semilla, jugador, mapa, obtener_ficha=ficha)
    estado.cargar_contenido(ContenidoSala(1, tuple(enemigos_sala_1), tuple(objetos_sala_1), ()))
    estado.cargar_contenido(ContenidoSala(2, (), (), ()))
    estado.cargar_contenido(ContenidoSala(3, (), (), ()))
    for _ in range(pergaminos):
        jugador.inventario.recoger(ficha("itm_perg"))
    estado.iniciar()
    return estado


def foto(estado):
    """Todo lo observable de la partida, para comparar antes y después de deshacer."""
    agenda = sorted((t, s, e.tipo, e.objetivo) for t, s, e in estado.agenda._heap._datos
                    if not e.cancelado)
    enemigos = [(e.id, e.vida, e.sala, e.activo) for _, e in estado._enemigos]
    inventario = [f.id for f in estado.jugador.inventario.obtener_elementos()
                  if f.clase != "pergamino_retroceso"]
    return (estado.tiempo, estado.jugador.vida, estado.jugador.sala, estado.acciones,
            agenda, enemigos, inventario, estado.suelo(1), estado.suelo(2),
            [estado.rastro.tiempo_en(s) for s in (1, 2, 3)], estado.azar.getstate(),
            estado.enemigos_derrotados)


class PruebasRetroceso(unittest.TestCase):

    def test_deshacer_un_movimiento(self):
        estado = partida()
        antes = foto(estado)
        estado.mover_jugador("N")
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual(foto(estado), antes)
        self.assertTrue(estado.es_turno_del_jugador())

    def test_deshacer_un_ataque_y_lo_que_hicieron_los_enemigos(self):
        # el ejemplo del enunciado: el ataque, el contraataque y el reloj vuelven atrás
        rata = InstanciaEnemigo("e-1", "ent_rata", 12)
        estado = partida(enemigos_sala_1=[rata])
        antes = foto(estado)
        estado.jugador_ataca("e-1")
        golpes = estado.avanzar_hasta_turno_jugador()
        self.assertTrue(golpes)                                 # la rata alcanzó a atacar
        self.assertNotEqual(foto(estado), antes)
        estado.deshacer()
        self.assertEqual(foto(estado), antes)

    def test_repetir_tras_deshacer_da_lo_mismo(self):
        rata = InstanciaEnemigo("e-1", "ent_rata", 12)
        estado = partida(pergaminos=1, enemigos_sala_1=[rata])
        primero = estado.jugador_ataca("e-1").dano
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual(estado.jugador_ataca("e-1").dano, primero)   # el azar también volvió

    def test_deshacer_una_muerte_devuelve_al_enemigo_y_quita_lo_que_solto(self):
        rata = InstanciaEnemigo("e-1", "ent_rata", 1)
        estado = partida(enemigos_sala_1=[rata])
        antes = foto(estado)
        self.assertTrue(estado.jugador_ataca("e-1").murio)
        self.assertEqual(estado.suelo(1), ["itm_pocion"])
        estado.deshacer()
        self.assertEqual(foto(estado), antes)
        self.assertIsNotNone(estado.enemigo("e-1").proximo_evento)   # vuelve a actuar

    def test_deshacer_recoger_equipar_y_soltar(self):
        estado = partida(pergaminos=3, objetos_sala_1=["itm_daga", "itm_pocion"])
        inicial = foto(estado)
        estado.recoger("itm_daga")
        estado.avanzar_hasta_turno_jugador()
        despues_recoger = foto(estado)
        inventario = estado.jugador.inventario
        while inventario.obtener_actual().id != "itm_daga":
            inventario.avanzar()
        estado.equipar()
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(inventario.bonus_ataque(), 3)
        estado.soltar()
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()                                       # vuelve a tenerla equipada
        self.assertEqual(inventario.bonus_ataque(), 3)
        estado.deshacer()                                       # ya no está equipada
        self.assertEqual(inventario.bonus_ataque(), 0)
        self.assertEqual(foto(estado), despues_recoger)
        estado.deshacer()
        self.assertEqual(foto(estado), inicial)

    def test_el_pergamino_usado_no_vuelve(self):
        estado = partida(pergaminos=2)
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual(estado.jugador.inventario.cantidad_pergaminos(), 1)

    def test_pergamino_recogido_en_el_intervalo_no_se_devuelve_al_suelo(self):
        # Apéndice B: la reversión no toca la cantidad de pergaminos
        estado = partida(pergaminos=0, objetos_sala_1=["itm_perg"])
        estado.recoger("itm_perg")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.jugador.inventario.cantidad_pergaminos(), 1)
        estado.deshacer()
        self.assertEqual(estado.tiempo, 0)                      # la acción sí se revirtió
        self.assertEqual(estado.suelo(1), [])                   # pero el pergamino no vuelve
        self.assertEqual(estado.jugador.inventario.cantidad_pergaminos(), 0)   # y se gastó

    def test_dos_pergaminos_seguidos_deshacen_dos_acciones(self):
        estado = partida(pergaminos=2)
        estado.mover_jugador("N")
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("S")
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual(estado.jugador.sala, 2)
        estado.deshacer()
        self.assertEqual(estado.jugador.sala, 1)
        self.assertEqual(estado.tiempo, 0)
        self.assertEqual(estado.acciones, 0)

    def test_maximo_cinco_acciones(self):
        estado = partida(pergaminos=7)
        for _ in range(7):
            estado.esperar()
            estado.avanzar_hasta_turno_jugador()
        for _ in range(5):
            estado.deshacer()
        self.assertEqual(estado.acciones, 2)
        with self.assertRaises(MovimientoInvalido) as ctx:
            estado.deshacer()
        self.assertEqual(ctx.exception.motivo, NADA_QUE_DESHACER)

    def test_sin_pergamino_no_se_puede(self):
        estado = partida(pergaminos=0)
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        with self.assertRaises(MovimientoInvalido) as ctx:
            estado.deshacer()
        self.assertEqual(ctx.exception.motivo, SIN_PERGAMINO)

    def test_deshacer_no_cuenta_como_accion_ni_gasta_tiempo(self):
        estado = partida(pergaminos=1)
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual((estado.acciones, estado.tiempo), (0, 0))

    def test_deshacer_abrir_una_puerta(self):
        estado = partida(pergaminos=1)
        estado.jugador.inventario.recoger(FichaCatalogo(id="itm_llave", nombre="Llave",
                                                        clase="llave", peso=1, valor=0))
        estado.abrir_puerta("E")
        self.assertTrue(estado.esqueleto.puede_atravesar(1, "E"))
        estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertFalse(estado.esqueleto.puede_atravesar(1, "E"))


if __name__ == "__main__":
    unittest.main()
