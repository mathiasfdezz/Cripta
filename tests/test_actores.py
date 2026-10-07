import json
import os
import random
import unittest

from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.enemigo import Enemigo
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador

CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "..", "datos_offline")


def ficha_enemigo(id_="ent_rata_gigante", nombre="Rata gigante", vida_max=12, ataque=5,
                  defensa=1, velocidad=150, comportamiento="rastreador",
                  suelta=("itm_pocion_menor",)):
    return FichaCatalogo(id=id_, nombre=nombre, clase="enemigo", vida_max=vida_max,
                         ataque=ataque, defensa=defensa, velocidad=velocidad,
                         comportamiento=comportamiento, suelta=tuple(suelta))


def ficha_objeto(id_, clase, **extra):
    return FichaCatalogo(id=id_, nombre=id_, clase=clase, peso=1, valor=1, **extra)


def jugador(sala=2, inventario=None):
    return Jugador(sala, EstadisticasJugador(vida_max=30, ataque=6, defensa=2, velocidad=100),
                   Inventario(10) if inventario is None else inventario)


def leer_json(*partes):
    with open(os.path.join(CARPETA_DATOS, *partes), encoding="utf-8") as f:
        return json.load(f)


class PruebasCreacionDeActores(unittest.TestCase):

    def test_jugador_desde_estadisticas(self):
        inventario = Inventario(10)
        j = Jugador(1, EstadisticasJugador(30, 6, 2, 100), inventario)
        self.assertEqual(j.id, "jugador")
        self.assertEqual(j.sala, 1)
        self.assertEqual((j.vida, j.vida_max), (30, 30))
        self.assertEqual((j.ataque, j.defensa, j.velocidad), (6, 2, 100))
        self.assertIsNone(j.proximo_evento)
        self.assertTrue(j.esta_vivo())
        self.assertIs(j.inventario, inventario)

    def test_jugador_suma_los_bonus_del_equipo(self):
        inventario = Inventario(10)
        j = jugador(inventario=inventario)
        self.assertEqual((j.ataque_efectivo(), j.defensa_efectiva()), (6, 2))
        inventario.recoger(ficha_objeto("itm_daga", "arma", ataque_bonus=3))
        inventario.equipar_actual()
        inventario.recoger(ficha_objeto("itm_coraza", "armadura", defensa_bonus=2))
        inventario.avanzar()
        inventario.equipar_actual()
        self.assertEqual((j.ataque_efectivo(), j.defensa_efectiva()), (9, 4))

    def test_enemigo_desde_instancia_y_ficha(self):
        e = Enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante", 12), ficha_enemigo(), 2)
        self.assertEqual(e.instancia, "e-201")
        self.assertEqual(e.id, "e-201")
        self.assertEqual(e.tipo, "ent_rata_gigante")
        self.assertEqual(e.sala, 2)
        self.assertEqual((e.vida, e.vida_max), (12, 12))
        self.assertEqual((e.ataque, e.defensa, e.velocidad), (5, 1, 150))
        self.assertEqual(e.comportamiento, "rastreador")
        self.assertEqual(e.suelta, ("itm_pocion_menor",))
        self.assertIsNone(e.proximo_evento)
        self.assertTrue(e.esta_vivo())

    def test_enemigo_sin_vida_en_la_instancia_empieza_con_la_vida_max(self):
        ficha = ficha_enemigo("ent_guardian_oseo", vida_max=20)
        e = Enemigo(InstanciaEnemigo("e-401", "ent_guardian_oseo"), ficha, 4)
        self.assertEqual(e.vida, 20)

    def test_enemigo_con_vida_de_la_instancia(self):
        e = Enemigo(InstanciaEnemigo("e-1", "ent_rata_gigante", 7), ficha_enemigo(), 2)
        self.assertEqual((e.vida, e.vida_max), (7, 12))

    def test_enemigo_con_ficha_incorrecta(self):
        with self.assertRaises(ValueError):
            Enemigo(InstanciaEnemigo("e-1", "itm_daga"), ficha_objeto("itm_daga", "arma"), 1)
        with self.assertRaises(ValueError):
            Enemigo(InstanciaEnemigo("e-1", "ent_otro"), ficha_enemigo(), 1)

    def test_velocidad_debe_ser_positiva(self):
        with self.assertRaises(ValueError):
            Enemigo(InstanciaEnemigo("e-1", "ent_rata_gigante"), ficha_enemigo(velocidad=0), 1)


class PruebasEstadoPartida(unittest.TestCase):

    def test_el_azar_es_de_la_partida(self):
        estado = EstadoPartida(7, jugador())
        self.assertEqual(estado.semilla, 7)
        self.assertIsInstance(estado.azar, random.Random)
        self.assertEqual(estado.azar.randint(0, 4), random.Random(7).randint(0, 4))

    def test_colocar_enemigo_lo_deja_inactivo(self):
        estado = EstadoPartida(1, jugador())
        e = estado.colocar_enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante", 12),
                                   ficha_enemigo(), 2)
        self.assertIs(estado.enemigo("e-201"), e)
        self.assertFalse(e.activo)
        self.assertIsNone(e.proximo_evento)
        self.assertTrue(estado.agenda.esta_vacia())

    def test_activar_programa_su_primera_accion(self):
        estado = EstadoPartida(1, jugador())
        e = estado.colocar_enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante", 12),
                                   ficha_enemigo(), 2)
        estado.activar_enemigos(2)
        self.assertTrue(e.activo)
        self.assertEqual(estado.agenda.tamano(), 1)
        tiempo, _, evento = estado.agenda.ver_siguiente()
        self.assertEqual(tiempo, 66)             # costo 100 a velocidad 150: 100 * 100 // 150
        self.assertIs(evento, e.proximo_evento)
        self.assertEqual(evento.objetivo, "e-201")

    def test_no_se_repite_la_instancia(self):
        estado = EstadoPartida(1, jugador())
        instancia = InstanciaEnemigo("e-201", "ent_rata_gigante")
        estado.colocar_enemigo(instancia, ficha_enemigo(), 2)
        with self.assertRaises(ValueError):
            estado.colocar_enemigo(instancia, ficha_enemigo(), 2)

    def test_enemigos_en_sala_solo_vivos_y_de_esa_sala(self):
        estado = EstadoPartida(1, jugador())
        estado.colocar_enemigo(InstanciaEnemigo("e-202", "ent_rata_gigante"), ficha_enemigo(), 2)
        estado.colocar_enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante"), ficha_enemigo(), 2)
        estado.colocar_enemigo(InstanciaEnemigo("e-301", "ent_rata_gigante"), ficha_enemigo(), 3)
        self.assertEqual([e.instancia for e in estado.enemigos_en_sala(2)], ["e-201", "e-202"])
        self.assertEqual([e.instancia for e in estado.enemigos_en_sala(3)], ["e-301"])
        self.assertEqual(estado.enemigos_en_sala(9), [])

    def test_actores_desde_los_datos_de_cripta_01(self):
        contenido = contenido_sala_desde_json(leer_json("cripta-01", "contenido", "sala_2.json"))
        rata = ficha_catalogo_desde_json(leer_json("catalogo", "fichas", "ent_rata_gigante.json"))
        estado = EstadoPartida(1, jugador(sala=2))
        for instancia in contenido.enemigos:
            estado.colocar_enemigo(instancia, rata, contenido.sala)

        presentes = estado.enemigos_en_sala(2)
        self.assertEqual([e.instancia for e in presentes], ["e-201", "e-202"])
        self.assertEqual([e.vida for e in presentes], [12, 12])
        self.assertEqual(estado.agenda.tamano(), 0)      # cargados, pero sin actuar
        estado.activar_enemigos(2)
        self.assertEqual(estado.agenda.tamano(), 2)

        guardian = ficha_catalogo_desde_json(leer_json("catalogo", "fichas", "ent_guardian_oseo.json"))
        contenido4 = contenido_sala_desde_json(leer_json("cripta-01", "contenido", "sala_4.json"))
        e = estado.colocar_enemigo(contenido4.enemigos[0], guardian, 4)
        self.assertEqual((e.vida, e.velocidad, e.sala), (20, 90, 4))
        self.assertEqual(e.comportamiento, "guardi\u00e1n")
        self.assertEqual(e.suelta, ())


if __name__ == "__main__":
    unittest.main()