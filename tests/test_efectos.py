import dataclasses
import os
import tempfile
import unittest

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.rutas_offline import RutasOffline
from controlador.partida import ControladorPartida
from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.cache_catalogo import CacheCatalogo
from modelo.estado_partida import SUCESO_VENENO, EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from tests.test_guardado_partida import foto
from tests.test_partida import CARPETA_OFFLINE, VistaMuda
from tests.test_esqueleto import esqueleto, sala

FICHAS = (
    # ataque 1: casi no hace daño, así lo que se mide es el efecto
    FichaCatalogo(id="ent_arana", nombre="Araña", clase="enemigo", vida_max=12, ataque=1,
                  defensa=0, velocidad=150, comportamiento="guardián", veneno=2),
    FichaCatalogo(id="ent_troll", nombre="Troll", clase="enemigo", vida_max=12, ataque=1,
                  defensa=0, velocidad=100, comportamiento="guardián", regeneracion=4),
    FichaCatalogo(id="itm_antidoto", nombre="Antídoto", clase="antidoto", peso=1, valor=5),
    FichaCatalogo(id="itm_perg", nombre="Pergamino", clase="pergamino_retroceso", peso=1,
                  valor=40),
)


def ficha(id_ficha):
    for f in FICHAS:
        if f.id == id_ficha:
            return f
    raise KeyError(id_ficha)


def partida(enemigos, inventario=()):
    """El jugador empieza en la sala 1 con los enemigos; la sala 2 queda al norte."""
    jugador = Jugador(1, EstadisticasJugador(30, 6, 2, 100), Inventario(10))
    for id_objeto in inventario:
        jugador.inventario.recoger(ficha(id_objeto))
    estado = EstadoPartida(1, jugador, esqueleto(sala(1, N=2), sala(2, S=1)),
                           obtener_ficha=ficha)
    estado.cargar_contenido(ContenidoSala(1, tuple(enemigos), (), ()))
    estado.cargar_contenido(ContenidoSala(2, (), (), ()))
    estado.iniciar()
    return estado


def esperar_hasta(estado, tiempo):
    """Espera turno a turno y devuelve cuántos pulsos de veneno hubo."""
    estado.avanzar_hasta_turno_jugador()
    pulsos = sum(1 for s in estado.tomar_sucesos() if s[0] == SUCESO_VENENO)
    while estado.tiempo < tiempo and not estado.terminada():
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        pulsos += sum(1 for s in estado.tomar_sucesos() if s[0] == SUCESO_VENENO)
    return pulsos


class PruebasVeneno(unittest.TestCase):

    def envenenado_y_lejos(self, inventario=()):
        # la araña golpea en t=66 y envenena; en t=100 el jugador se va al norte
        estado = partida([InstanciaEnemigo("e-1", "ent_arana")], inventario)
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        estado.tomar_sucesos()
        self.assertEqual((estado.veneno_hasta, estado.veneno_dano), (66 + 400, 2))
        estado.mover_jugador("N")
        return estado

    def test_quita_vida_cada_80_y_dura_400(self):
        estado = self.envenenado_y_lejos()
        vida = estado.jugador.vida
        # pulsos en 146, 226, 306, 386 y 466
        pulsos = esperar_hasta(estado, 800)
        self.assertEqual(pulsos, 5)
        self.assertEqual(estado.jugador.vida, vida - 5 * 2)
        self.assertIsNone(estado.veneno_hasta)

    def test_el_antidoto_cancela_los_pulsos_que_faltan(self):
        estado = self.envenenado_y_lejos(inventario=["itm_antidoto"])
        estado.avanzar_hasta_turno_jugador()            # t=200: ya pasó el pulso de 146
        self.assertEqual(sum(1 for s in estado.tomar_sucesos() if s[0] == SUCESO_VENENO), 1)
        vida = estado.jugador.vida
        estado.usar()
        self.assertIsNone(estado.veneno_hasta)
        self.assertEqual(esperar_hasta(estado, 800), 0)
        self.assertEqual(estado.jugador.vida, vida)

    def test_el_veneno_puede_matar(self):
        estado = self.envenenado_y_lejos()
        estado.jugador.vida = 3
        esperar_hasta(estado, 800)
        self.assertTrue(estado.terminada())
        self.assertFalse(estado.jugador.esta_vivo())
        self.assertIsNone(estado.veneno_hasta)

    def test_deshacer_quita_el_veneno_de_esa_accion(self):
        estado = partida([InstanciaEnemigo("e-1", "ent_arana")], ["itm_perg"])
        vida = estado.jugador.vida
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        self.assertIsNotNone(estado.veneno_hasta)
        estado.deshacer()
        self.assertIsNone(estado.veneno_hasta)
        self.assertEqual(estado.jugador.vida, vida)


class PruebasRegeneracion(unittest.TestCase):

    def test_cura_cada_200_sin_pasar_vida_max(self):
        estado = partida([InstanciaEnemigo("e-1", "ent_troll", vida=5)])
        troll = estado.enemigo("e-1")
        esperar_hasta(estado, 200)
        self.assertEqual(troll.vida, 9)
        esperar_hasta(estado, 400)
        self.assertEqual(troll.vida, 12)                # 9 + 4 = 13, pero el tope es 12

    def test_un_enemigo_muerto_deja_de_regenerarse(self):
        estado = partida([InstanciaEnemigo("e-1", "ent_troll", vida=1)])
        troll = estado.enemigo("e-1")
        estado.jugador_ataca("e-1")
        self.assertFalse(troll.esta_vivo())
        self.assertIsNone(troll.evento_regeneracion)
        esperar_hasta(estado, 600)
        self.assertEqual(troll.vida, 0)

    def test_sin_regeneracion_en_la_ficha_no_se_programa_nada(self):
        estado = partida([InstanciaEnemigo("e-1", "ent_arana")])
        self.assertIsNone(estado.enemigo("e-1").evento_regeneracion)


class PruebasFichaConEfectos(unittest.TestCase):

    def test_el_mapeador_lee_los_efectos_si_vienen(self):
        datos = {"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 5, "ataque": 1,
                 "defensa": 0, "velocidad": 100, "comportamiento": "guardián",
                 "veneno": 2, "regeneracion": 3}
        ficha_x = ficha_catalogo_desde_json(datos)
        self.assertEqual((ficha_x.veneno, ficha_x.regeneracion), (2, 3))
        del datos["veneno"], datos["regeneracion"]
        ficha_x = ficha_catalogo_desde_json(datos)
        self.assertEqual((ficha_x.veneno, ficha_x.regeneracion), (None, None))

    def test_el_efecto_tambien_puede_venir_como_objeto(self):
        datos = {"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 5, "ataque": 1,
                 "defensa": 0, "velocidad": 100, "comportamiento": "guardián",
                 "veneno": {"daño": 2, "cada": 80}, "regeneracion": {"cantidad": 3}}
        ficha_x = ficha_catalogo_desde_json(datos)
        self.assertEqual((ficha_x.veneno, ficha_x.regeneracion), (2, 3))

    def test_un_formato_que_no_se_entiende_es_error_de_datos_y_no_caida(self):
        base = {"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 5, "ataque": 1,
                "defensa": 0, "velocidad": 100, "comportamiento": "guardián"}
        for raro in ("2", -1, True, [1], {"a": 1, "b": 2}):
            with self.assertRaises(ErrorDatos):
                ficha_catalogo_desde_json({**base, "veneno": raro})


class PruebasEfectosAlGuardar(unittest.TestCase):
    """cripta-01 no trae veneno: para probarlo se le agrega a la rata en la ficha."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def nueva(self):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta("cripta-01")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "c")))
        version = fuente.version_catalogo()
        cache.validar_version(version)
        original = cache.obtener

        def con_veneno(id_ficha):
            leida = original(id_ficha)
            if id_ficha == "ent_rata_gigante":
                return dataclasses.replace(leida, veneno=1)
            return leida

        cache.obtener = con_veneno
        controlador = ControladorPartida(datos, fuente, cache, VistaMuda(), 5, version,
                                         os.path.join(self.carpeta.name, "partidas"))
        # las ratas pegan fuerte: que el jugador aguante para poder comparar
        controlador.estado.jugador.vida = 10 ** 6
        return controlador

    def jugar(self, controlador, comandos):
        pendientes = iter(comandos)
        controlador.jugar(lambda: next(pendientes, None))
        return controlador.estado

    def test_seguir_despues_de_cargar_con_veneno_da_lo_mismo(self):
        directo = self.jugar(self.nueva(), ["n", "esperar", "esperar"])
        con_guardado = self.jugar(self.nueva(), ["n", "guardar v", "esperar", "cargar v",
                                                 "esperar", "esperar"])
        self.assertIsNotNone(directo.veneno_hasta)
        self.assertEqual((con_guardado.veneno_hasta, con_guardado.veneno_dano),
                         (directo.veneno_hasta, directo.veneno_dano))
        self.assertEqual(foto(con_guardado), foto(directo))
        self.assertFalse(directo.terminada())


if __name__ == "__main__":
    unittest.main()