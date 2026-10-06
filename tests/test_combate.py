import random
import unittest

from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.combate import atacar, calcular_dano, puede_atacar
from modelo.enemigo import Enemigo
from modelo.estado_partida import EstadoPartida
from modelo.evento import Evento
from modelo.inventario import Inventario
from modelo.jugador import Jugador


class AzarFijo:
    """Reemplaza al random.Random: siempre devuelve el mismo valor y anota los pedidos."""

    def __init__(self, valor):
        self.valor = valor
        self.llamadas = []

    def randint(self, minimo, maximo):
        self.llamadas.append((minimo, maximo))
        return self.valor


def ficha(id_="ent_rata_gigante", vida_max=12, ataque=5, defensa=1, velocidad=150,
          suelta=("itm_pocion_menor",)):
    return FichaCatalogo(id=id_, nombre=id_, clase="enemigo", vida_max=vida_max, ataque=ataque,
                         defensa=defensa, velocidad=velocidad, comportamiento="rastreador",
                         suelta=tuple(suelta))


def jugador(sala=2, vida=30, ataque=6, defensa=2):
    return Jugador(sala, EstadisticasJugador(vida, ataque, defensa, 100), Inventario(10))


def enemigo(instancia="e-201", sala=2, vida=12, ataque=5, defensa=1):
    return Enemigo(InstanciaEnemigo(instancia, "ent_rata_gigante", vida),
                   ficha(ataque=ataque, defensa=defensa), sala)


def partida(semilla=1, sala_jugador=2, **kw):
    return EstadoPartida(semilla, jugador(sala=sala_jugador, **kw))


def con_enemigo(estado, instancia="e-201", sala=2, vida=12, **kw):
    return estado.colocar_enemigo(InstanciaEnemigo(instancia, "ent_rata_gigante", vida),
                                  ficha(**kw), sala)


class PruebasCalculoDeDano(unittest.TestCase):

    def test_formula(self):
        azar = AzarFijo(3)
        # ataque 6 + azar 3 - defensa 1
        self.assertEqual(calcular_dano(jugador(ataque=6), enemigo(defensa=1), azar), 8)
        self.assertEqual(azar.llamadas, [(0, 4)])

    def test_extremos_del_azar(self):
        atacante, defensor = enemigo(ataque=5), jugador(defensa=2)
        self.assertEqual(calcular_dano(atacante, defensor, AzarFijo(0)), 3)
        self.assertEqual(calcular_dano(atacante, defensor, AzarFijo(4)), 7)

    def test_dano_minimo_1(self):
        self.assertEqual(calcular_dano(enemigo(ataque=1), jugador(defensa=50), AzarFijo(0)), 1)
        self.assertEqual(calcular_dano(enemigo(ataque=5), jugador(defensa=9), AzarFijo(4)), 1)

    def test_el_equipo_del_jugador_cuenta(self):
        j = jugador(ataque=6, defensa=2)
        daga = FichaCatalogo(id="d", nombre="d", clase="arma", peso=1, valor=1, ataque_bonus=3)
        coraza = FichaCatalogo(id="c", nombre="c", clase="armadura", peso=1, valor=1, defensa_bonus=2)
        j.inventario.recoger(daga)
        j.inventario.equipar_actual()
        j.inventario.recoger(coraza)
        j.inventario.avanzar()
        j.inventario.equipar_actual()
        self.assertEqual(calcular_dano(j, enemigo(defensa=1), AzarFijo(2)), 6 + 3 + 2 - 1)
        self.assertEqual(calcular_dano(enemigo(ataque=5), j, AzarFijo(2)), 5 + 2 - (2 + 2))

    def test_cada_golpe_consume_un_randint_de_la_partida(self):
        estado = partida(semilla=42)
        con_enemigo(estado, vida=1000)
        espejo = random.Random(42)
        for _ in range(5):
            resultado = estado.jugador_ataca("e-201")
            self.assertEqual(resultado.dano, max(1, 6 + espejo.randint(0, 4) - 1))
        self.assertEqual(estado.azar.randint(0, 4), espejo.randint(0, 4))


class PruebasCombate(unittest.TestCase):

    def test_jugador_ataca_a_un_enemigo(self):
        estado = partida(semilla=3)
        rata = con_enemigo(estado)
        esperado = max(1, 6 + random.Random(3).randint(0, 4) - 1)
        resultado = estado.jugador_ataca("e-201")
        self.assertIs(resultado.atacante, estado.jugador)
        self.assertIs(resultado.defensor, rata)
        self.assertEqual(resultado.dano, esperado)
        self.assertFalse(resultado.murio)
        self.assertEqual(rata.vida, 12 - esperado)

    def test_solo_se_ataca_en_la_misma_sala(self):
        estado = partida(sala_jugador=1)
        lejana = con_enemigo(estado, sala=2)
        self.assertFalse(puede_atacar(estado.jugador, lejana))
        with self.assertRaises(ValueError):
            estado.jugador_ataca("e-201")
        with self.assertRaises(ValueError):
            atacar(lejana, estado.jugador, estado.azar)
        self.assertEqual(lejana.vida, 12)
        self.assertEqual(estado.jugador.vida, 30)
        # no se gasto azar en el intento
        self.assertEqual(estado.azar.randint(0, 4), random.Random(1).randint(0, 4))

    def test_adyacentes_al_estar_en_la_misma_sala(self):
        estado = partida(sala_jugador=1)
        rata = con_enemigo(estado, sala=2)
        self.assertFalse(puede_atacar(estado.jugador, rata))
        rata.sala = 1          # (el movimiento aun no existe: se cambia directo)
        self.assertTrue(puede_atacar(estado.jugador, rata))
        self.assertTrue(puede_atacar(rata, estado.jugador))

    def test_un_actor_no_se_ataca_a_si_mismo(self):
        estado = partida()
        self.assertFalse(puede_atacar(estado.jugador, estado.jugador))

    def test_elegir_a_cual_enemigo_atacar(self):
        estado = partida()
        a = con_enemigo(estado, "e-201")
        b = con_enemigo(estado, "e-202")
        resultado = estado.jugador_ataca("e-202")
        self.assertIs(resultado.defensor, b)
        self.assertEqual(a.vida, 12)
        self.assertLess(b.vida, 12)

    def test_con_varios_enemigos_hay_que_elegir(self):
        estado = partida()
        con_enemigo(estado, "e-201")
        con_enemigo(estado, "e-202")
        with self.assertRaises(ValueError):
            estado.jugador_ataca()

    def test_con_un_solo_enemigo_no_hace_falta_elegir(self):
        estado = partida()
        rata = con_enemigo(estado)
        self.assertIs(estado.jugador_ataca().defensor, rata)

    def test_atacar_sin_enemigos_o_a_un_inexistente(self):
        estado = partida()
        with self.assertRaises(ValueError):
            estado.jugador_ataca()
        with self.assertRaises(ValueError):
            estado.jugador_ataca("e-999")

    def test_enemigo_ataca_al_jugador_cuando_le_toca(self):
        estado = partida(semilla=5)
        rata = con_enemigo(estado)
        esperado = max(1, 5 + random.Random(5).randint(0, 4) - 2)
        resultado = estado.ejecutar_siguiente()
        self.assertIs(resultado.atacante, rata)
        self.assertIs(resultado.defensor, estado.jugador)
        self.assertEqual(resultado.dano, esperado)
        self.assertEqual(estado.jugador.vida, 30 - esperado)
        self.assertEqual(estado.tiempo, 66)

    def test_el_enemigo_vuelve_a_programar_su_accion(self):
        estado = partida()
        rata = con_enemigo(estado)
        primer_evento = rata.proximo_evento
        estado.ejecutar_siguiente()
        self.assertIsNot(rata.proximo_evento, primer_evento)
        self.assertEqual(estado.agenda.ver_siguiente()[0], 66 + 66)
        self.assertEqual(estado.agenda.tamano(), 1)

    def test_enemigo_en_otra_sala_no_ataca(self):
        estado = partida(sala_jugador=1)
        rata = con_enemigo(estado, sala=2)
        self.assertIsNone(estado.ejecutar_siguiente())
        self.assertEqual(estado.jugador.vida, 30)
        self.assertIsNotNone(rata.proximo_evento)          # sigue programado
        self.assertEqual(estado.azar.randint(0, 4), random.Random(1).randint(0, 4))

    def test_mismos_semilla_y_acciones_dan_el_mismo_resultado(self):
        def correr(semilla):
            estado = partida(semilla=semilla, vida=1000)
            con_enemigo(estado, "e-201", vida=1000)
            con_enemigo(estado, "e-202", vida=1000, velocidad=90)
            danos = []
            for i in range(6):
                danos.append(estado.jugador_ataca("e-201" if i % 2 == 0 else "e-202").dano)
                danos.append(estado.ejecutar_siguiente().dano)
            return danos, estado.jugador.vida

        self.assertEqual(correr(11), correr(11))
        self.assertNotEqual(correr(11), correr(12))

    def test_el_random_global_no_influye(self):
        def correr():
            estado = partida(semilla=9)
            con_enemigo(estado, vida=1000)
            return [estado.jugador_ataca("e-201").dano for _ in range(8)]

        random.seed(1)
        primero = correr()
        random.seed(2)
        self.assertEqual(primero, correr())


class PruebasMuerteDeEnemigo(unittest.TestCase):

    def test_el_enemigo_muere_al_quedarse_sin_vida(self):
        estado = partida()
        rata = con_enemigo(estado, vida=1)
        resultado = estado.jugador_ataca("e-201")
        self.assertTrue(resultado.murio)
        self.assertEqual(rata.vida, 0)                  # nunca negativa
        self.assertFalse(rata.esta_vivo())
        self.assertEqual(estado.enemigos_en_sala(2), [])

    def test_muere_tras_varios_golpes(self):
        estado = partida()
        rata = con_enemigo(estado)
        golpes = 0
        while rata.esta_vivo():
            estado.jugador_ataca("e-201")
            golpes += 1
            self.assertLess(golpes, 20)
        self.assertGreater(golpes, 1)

    def test_muerto_no_ejecuta_futuros_eventos(self):
        estado = partida()
        rata = con_enemigo(estado, vida=1)
        estado.jugador_ataca("e-201")
        self.assertIsNone(rata.proximo_evento)
        self.assertTrue(estado.agenda.esta_vacia())
        with self.assertRaises(IndexError):
            estado.ejecutar_siguiente()
        self.assertEqual(estado.jugador.vida, 30)

    def test_evento_de_un_muerto_que_llega_a_ejecutarse_se_ignora(self):
        estado = partida()
        rata = con_enemigo(estado, vida=1)
        estado.jugador_ataca("e-201")
        estado.agenda.programar(5, Evento("accion", "e-201"))   # evento colado
        self.assertIsNone(estado.ejecutar_siguiente())
        self.assertEqual(estado.jugador.vida, 30)
        self.assertTrue(estado.agenda.esta_vacia())              # y no se reprograma
        self.assertIsNone(rata.proximo_evento)

    def test_la_muerte_de_uno_no_afecta_a_los_demas(self):
        estado = partida()
        con_enemigo(estado, "e-201", vida=1)
        otra = con_enemigo(estado, "e-202")
        estado.jugador_ataca("e-201")
        self.assertEqual(estado.agenda.tamano(), 1)
        resultado = estado.ejecutar_siguiente()
        self.assertIs(resultado.atacante, otra)

    def test_suelta_sus_objetos_en_su_sala(self):
        estado = partida()
        con_enemigo(estado, vida=1, suelta=("itm_pocion_menor", "itm_llave"))
        self.assertEqual(estado.suelo(2), [])
        estado.jugador_ataca("e-201")
        self.assertEqual(estado.suelo(2), ["itm_pocion_menor", "itm_llave"])
        self.assertEqual(estado.suelo(3), [])

    def test_enemigo_que_no_suelta_nada(self):
        estado = partida()
        con_enemigo(estado, vida=1, suelta=())
        estado.jugador_ataca("e-201")
        self.assertEqual(estado.suelo(2), [])

    def test_los_objetos_se_suman_en_la_misma_sala(self):
        estado = partida()
        con_enemigo(estado, "e-201", vida=1, suelta=("a",))
        con_enemigo(estado, "e-202", vida=1, suelta=("b",))
        estado.jugador_ataca("e-201")
        estado.jugador_ataca("e-202")
        self.assertEqual(estado.suelo(2), ["a", "b"])

    def test_no_suelta_dos_veces(self):
        estado = partida()
        con_enemigo(estado, vida=1)
        estado.jugador_ataca("e-201")
        with self.assertRaises(ValueError):
            estado.jugador_ataca("e-201")
        self.assertEqual(estado.suelo(2), ["itm_pocion_menor"])


class PruebasActorMuertoNoActua(unittest.TestCase):

    def test_no_se_puede_atacar_a_un_muerto(self):
        estado = partida()
        rata = con_enemigo(estado, vida=1)
        estado.jugador_ataca("e-201")
        self.assertFalse(puede_atacar(estado.jugador, rata))
        with self.assertRaises(ValueError):
            estado.jugador_ataca("e-201")

    def test_un_muerto_no_ataca(self):
        estado = partida()
        rata = con_enemigo(estado, vida=1)
        estado.jugador_ataca("e-201")
        self.assertFalse(puede_atacar(rata, estado.jugador))
        with self.assertRaises(ValueError):
            atacar(rata, estado.jugador, estado.azar)

    def test_el_jugador_muerto_no_ataca_ni_es_atacado(self):
        estado = partida(vida=1)
        rata = con_enemigo(estado)
        resultado = estado.ejecutar_siguiente()          # la rata lo mata (dano minimo 1)
        self.assertTrue(resultado.murio)
        self.assertFalse(estado.jugador.esta_vivo())
        self.assertEqual(estado.jugador.vida, 0)
        with self.assertRaises(ValueError):
            estado.jugador_ataca("e-201")
        self.assertIsNone(estado.ejecutar_siguiente())   # ya no hay a quien atacar
        self.assertEqual(rata.vida, 12)


if __name__ == "__main__":
    unittest.main()