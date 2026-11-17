import os
import random
import tempfile
import time
import unittest

from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.guardado_binario import GuardadoIncompatible
from adaptadores.guardado_partida import GuardadoPartida
from bench.cripta_sintetica import crear_partida
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.instancia_trampa import InstanciaTrampa
from modelo.linea_tiempo import ACCION, CADA_POR_DEFECTO, LineaTiempo
from modelo.movimiento import MovimientoInvalido
from tests.criptas_prueba import enemigo, esqueleto, ficha, partida, salida
from tests.fuente_memoria import controlador


def huella(e):
    """Todo lo observable del estado, para comparar dos estados."""
    inventario = e.jugador.inventario
    objetos = tuple((n.dato.id, inventario.esta_equipado(n), n is inventario.actual)
                    for n in inventario.lista.recorrer())
    enemigos = tuple((x.instancia, x.sala, x.vida, x.activo) for _, x in e._enemigos)
    eventos = tuple(sorted((t, ev.tipo, ev.objetivo) for t, _, ev in e.agenda.pendientes()))
    suelo = tuple((sala, tuple(lista)) for sala, lista in e._suelo)
    puertas = tuple(p.cerrada for p in e.esqueleto._puertas_por_salida)
    return (e.tiempo, e.acciones, e.jugador.sala, e.jugador.vida, e.jugador.velocidad, objetos,
            enemigos, eventos, suelo, puertas, tuple(e.mapa.estado), tuple(e.mapa.recuerdo),
            e.antorcha_hasta, e.veneno_hasta, e.resultado, e.azar.getstate())


def ida_y_vuelta(a, direccion, b, costo=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, costo), salida(b, contraria, a, costo)]


def rejilla(lado=4):
    azar = random.Random(5)
    salidas = []
    for fila in range(lado):
        for columna in range(lado):
            sala = fila * lado + columna + 1
            if columna < lado - 1:
                salidas += ida_y_vuelta(sala, "E", sala + 1, azar.choice((40, 100, 150)))
            if fila < lado - 1:
                salidas += ida_y_vuelta(sala, "S", sala + lado, azar.choice((40, 100, 150)))
    return salidas


def partida_con_linea(cada=3, semilla=4):
    contenidos = [ContenidoSala(1, (), ("itm_pocion", "itm_antorcha", "itm_daga",
                                        "itm_pergamino", "itm_pergamino"), ()),
                  ContenidoSala(6, (), (), (InstanciaTrampa("t-1", "trp_pinchos"),))]
    estado = partida(esqueleto(*rejilla()), semilla=semilla, contenido=contenidos)
    estado.linea = LineaTiempo(cada)
    enemigo(estado, 16, "ent_sabueso", "e-1")
    enemigo(estado, 11, "ent_errante", "e-2")
    return estado


def jugar(estado, azar, acciones, al_decidir=None):
    """Acciones variadas al azar (del azar de la prueba, no de la partida)."""
    for _ in range(acciones):
        if estado.terminada():
            return
        if al_decidir is not None:
            al_decidir(estado)
        opciones = []
        for s in estado.esqueleto.obtener(estado.jugador.sala).salidas:
            if estado.esqueleto.puede_atravesar(estado.jugador.sala, s.direccion):
                opciones.append(("mover_jugador", s.direccion))
        opciones += [("esperar", None), ("esperar", None)]
        if estado.suelo(estado.jugador.sala) and not estado.jugador.inventario.esta_lleno():
            opciones.append(("recoger", estado.suelo(estado.jugador.sala)[0]))
        actual = estado.jugador.inventario.obtener_actual()
        if actual is not None and actual.clase in ("pocion", "antorcha"):
            opciones.append(("usar", None))
        if actual is not None and actual.clase == "arma":
            opciones.append(("equipar", None))
        if estado.enemigos_en_sala(estado.jugador.sala):
            opciones.append(("jugador_ataca", estado.enemigos_en_sala(estado.jugador.sala)[0].instancia))
        if len(estado.jugador.inventario) > 1 and azar.random() < 0.3:
            estado.mover_cursor(1 if azar.random() < 0.5 else -1)
        nombre, argumento = opciones[azar.randrange(len(opciones))]
        metodo = getattr(estado, nombre)
        metodo() if argumento is None else metodo(argumento)
        if not estado.terminada():
            estado.avanzar_hasta_turno_jugador()


class PruebasHistoriaPorAccion(unittest.TestCase):

    def test_historia_k_es_el_estado_antes_de_la_accion(self):
        # FR-301, FR-302, FR-303: cada consulta coincide con lo que se vio al jugar
        estado = partida_con_linea(cada=3)
        vistos = []
        jugar(estado, random.Random(1), 25, lambda e: vistos.append(huella(e)))
        linea = estado.linea
        self.assertEqual(linea.acciones(), len(vistos))
        for numero, esperado in enumerate(vistos, 1):
            self.assertEqual(huella(linea.estado_antes_de(estado, numero)), esperado, numero)
        # la decisión actual es la partida en curso, sin copiar
        self.assertIs(linea.estado_antes_de(estado, len(vistos) + 1), estado)

    def test_nunca_mas_de_k_acciones(self):
        # FR-308: una consulta re-aplica a lo sumo K acciones; puntos <= ceil(acciones / K)
        for cada in (1, 2, 5, 7):
            estado = partida_con_linea(cada=cada)
            jugar(estado, random.Random(cada), 30)
            linea = estado.linea
            n = linea.acciones()
            self.assertLessEqual(len(linea.puntos), -(-n // cada))
            for numero in range(1, n + 1):
                punto = linea.puntos[(numero - 1) // cada]
                aplicadas = sum(1 for op in linea.operaciones[punto.operacion:
                                                              linea.inicio_accion[numero - 1]]
                                if op[0] == ACCION)
                self.assertLess(aplicadas, cada + 1)
                self.assertLessEqual(punto.accion, numero)


class PruebasHistoriaPorInstante(unittest.TestCase):

    def test_historia_t(self):
        # FR-302: se juega evento por evento anotando el estado después de cada instante;
        # historia t debe coincidir para cada instante visto
        estado = partida_con_linea(cada=4, semilla=9)
        azar = random.Random(2)
        por_instante = []
        for _ in range(15):
            if estado.terminada():
                break
            por_instante.append((estado.tiempo, huella(estado)))   # decisión: antes de tomarla
            jugar(estado, azar, 1)
        # sin avanzar de golpe: la última acción se reemplaza por pasos de a un evento
        linea = estado.linea
        for t, esperado in por_instante:
            self.assertEqual(huella(linea.estado_en(estado, t)), esperado, t)

    def test_entre_dos_decisiones_se_ven_los_eventos_hasta_t(self):
        # FR-302: la acción se hace y luego ocurren solo los eventos con tiempo <= t
        estado = partida(esqueleto(*rejilla()))
        estado.linea = LineaTiempo(2)
        sabueso = enemigo(estado, 3, "ent_sabueso", "e-1")   # actúa en t=100, 200, ...
        estado.mover_jugador("E")                            # costo de 1->2 de la rejilla
        decision = estado.tiempo
        pasos = []
        while not estado.es_turno_del_jugador():
            estado.ejecutar_siguiente()
            pasos.append((estado.tiempo, huella(estado)))
        for t, esperado in pasos:
            self.assertEqual(huella(estado.linea.estado_en(estado, t)), esperado)
        self.assertEqual(decision, 0)
        self.assertGreater(len(pasos), 0)
        self.assertIsNotNone(sabueso)

    def test_eventos_en_el_mismo_instante(self):
        # FR-302 (Apéndice B): dos cazadores actúan en t=100 antes de la decisión del
        # jugador en t=100; historia 100 los muestra a los dos después de moverse
        estado = partida(esqueleto(*ida_y_vuelta(1, "E", 2), *ida_y_vuelta(2, "E", 3),
                                   *ida_y_vuelta(1, "S", 4), *ida_y_vuelta(4, "S", 5)))
        estado.linea = LineaTiempo(5)
        a = enemigo(estado, 3, "ent_sabueso", "e-1")
        b = enemigo(estado, 5, "ent_sabueso", "e-2")
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
        estado.esperar()                                     # en t=100, ya con los dos movidos
        estado.avanzar_hasta_turno_jugador()
        en_100 = estado.linea.estado_en(estado, 100)
        self.assertEqual(en_100.tiempo, 100)
        self.assertEqual((en_100.enemigo("e-1").sala, en_100.enemigo("e-2").sala), (2, 4))
        self.assertEqual((a.sala, b.sala), (1, 1))           # la partida siguió después

    def test_t_mayor_que_el_reloj_se_rechaza(self):
        # FR-306 (Apéndice B)
        estado = partida_con_linea()
        jugar(estado, random.Random(3), 5)
        for consulta in (lambda: estado.linea.estado_en(estado, estado.tiempo + 1),
                         lambda: estado.linea.estado_en(estado, -1),
                         lambda: estado.linea.estado_antes_de(estado, 0),
                         lambda: estado.linea.estado_antes_de(estado, 7)):
            with self.assertRaises(MovimientoInvalido):
                consulta()
        self.assertIs(estado.linea.estado_en(estado, estado.tiempo), estado)


class PruebasHistoriaEnLaPartida(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def controlador(self):
        salidas = rejilla()
        contenidos = [ContenidoSala(1, (), ("itm_pergamino", "itm_pergamino", "itm_pocion"), ()),
                      ContenidoSala(3, (InstanciaEnemigo("e-1", "ent_guardia"),), (), ())]
        return controlador(salidas, contenidos=contenidos, carpeta=self.carpeta.name)

    def test_consulta_no_altera_nada(self):
        # FR-304 (Apéndice B): ni reloj, ni partida.log, ni historial de retroceso
        c = self.controlador()
        ruta = os.path.join(self.carpeta.name, "p.log")
        bitacora = BitacoraPartida(ruta)
        bitacora.crear(CabeceraPartida("prueba", "v1", "c1", 1))
        comandos = iter(["recoger itm_pergamino", "e", "esperar", "e", "historia 150",
                         "historia #2", "historia #1", "historia 0"])
        antes = []

        def leer():
            comando = next(comandos, None)
            if comando is not None and comando.startswith("historia") and not antes:
                antes.append((huella(c.estado), c.estado.historial.acciones_guardadas(),
                              c.estado.historial.cambios_ultima_accion(),
                              c.estado.agenda.siguiente_secuencia()))
            return comando

        c.jugar(leer, bitacora)
        despues = (huella(c.estado), c.estado.historial.acciones_guardadas(),
                   c.estado.historial.cambios_ultima_accion(), c.estado.agenda.siguiente_secuencia())
        self.assertEqual(antes[0], despues)
        _, guardados = BitacoraPartida.leer(ruta)
        self.assertEqual(guardados, ["recoger itm_pergamino", "e", "esperar", "e"])
        # el pergamino sigue deshaciendo exactamente la última acción
        c.ejecutar("deshacer")
        self.assertEqual(c.estado.acciones, 3)

    def test_rechazos_sin_cambios(self):
        # FR-306
        c = self.controlador()
        c.ejecutar("esperar")
        antes = huella(c.estado)
        for orden in ("historia 99999", "historia #0", "historia #9", "historia abc", "historia"):
            c.ejecutar(orden)
            self.assertTrue(c.bitacora.ultimos()[-1].startswith("No se puede"), orden)
        self.assertEqual(huella(c.estado), antes)

    def test_pergamino_quita_acciones_de_la_linea(self):
        # FR-305 (Apéndice B): la acción revertida deja de existir
        c = self.controlador()
        c.ejecutar("recoger itm_pergamino")
        for orden in ("e", "s"):
            c.ejecutar(orden)
        antes_de_la_4 = huella(c.estado)
        c.ejecutar("esperar")
        c.ejecutar("o")                       # acción 5, que se va a revertir
        c.ejecutar("deshacer")
        linea = c.estado.linea
        self.assertEqual(linea.acciones(), 4)
        # #5 es ahora la decisión actual; no hay rastro de la acción revertida
        self.assertIs(linea.estado_antes_de(c.estado, 5), c.estado)
        self.assertEqual(huella(linea.estado_antes_de(c.estado, 4)), antes_de_la_4)
        self.assertFalse(any(op == ("accion", "mover_jugador", "O") for op in linea.operaciones))
        # una acción nueva distinta queda en la línea en su lugar
        c.ejecutar("n")
        vista = huella(c.estado)
        c.ejecutar("esperar")
        self.assertEqual(huella(linea.estado_antes_de(c.estado, 6)), vista)

    def test_guardar_y_cargar_conserva_la_linea(self):
        # FR-309: las consultas dan lo mismo antes y después de cargar
        c = self.controlador()
        c.checkpoint_cada = 3
        c.estado.linea.cada = 3
        c.ejecutar("recoger itm_pergamino")
        for orden in ("e", "s", "esperar", "e", "sig", "n", "esperar", "o"):
            c.ejecutar(orden)
        c.ejecutar("deshacer")
        consultas = [huella(c.estado.linea.estado_antes_de(c.estado, k))
                     for k in range(1, c.estado.acciones + 1)]
        en_t = [huella(c.estado.linea.estado_en(c.estado, t)) for t in range(0, c.estado.tiempo, 37)]
        actual = huella(c.estado)
        c.ejecutar("guardar con_linea")
        c.ejecutar("esperar")
        c.ejecutar("cargar con_linea")
        self.assertEqual(huella(c.estado), actual)
        linea = c.estado.linea
        self.assertEqual(linea.cada, 3)
        self.assertEqual([huella(linea.estado_antes_de(c.estado, k))
                          for k in range(1, c.estado.acciones + 1)], consultas)
        self.assertEqual([huella(linea.estado_en(c.estado, t))
                          for t in range(0, c.estado.tiempo, 37)], en_t)

    def test_archivo_de_la_primera_parte_incompatible(self):
        # FR-310 (Apéndice B): formatos 3 (primera parte) y 4 se rechazan con aviso
        c = self.controlador()
        c.ejecutar("guardar nuevo")
        ruta = os.path.join(self.carpeta.name, "nuevo.sav")
        with open(ruta, "rb") as archivo:
            crudo = bytearray(archivo.read())
        for version in (3, 4):
            crudo[4:6] = version.to_bytes(2, "little")
            with open(ruta, "wb") as archivo:
                archivo.write(bytes(crudo))
            with self.assertRaises(GuardadoIncompatible) as ctx:
                GuardadoPartida.cargar(ruta, c.datos, "c1", c.esqueleto, c.cache.obtener)
            self.assertIn(f"version {version}", str(ctx.exception))
            c.ejecutar("cargar nuevo")
            self.assertIn("no se puede cargar", c.bitacora.ultimos()[-1])


class PruebasPartidaLarga(unittest.TestCase):

    def test_equivalencia_en_partida_larga(self):
        # FR-308, PR-301: 600 acciones en una cripta sintética con cazadores y K por
        # defecto; consultas repartidas coinciden con lo visto y son rápidas
        estado = crear_partida(10, 10, 40, cazadores=8, rango=600, con_costos=True)
        estado.linea = LineaTiempo(CADA_POR_DEFECTO)
        azar = random.Random(8)
        vistos = []
        for _ in range(600):
            vistos.append(huella_sintetica(estado))
            abiertas = [s.direccion for s in estado.esqueleto.obtener(estado.jugador.sala).salidas]
            if azar.random() < 0.6 and abiertas:
                estado.mover_jugador(abiertas[azar.randrange(len(abiertas))])
            else:
                estado.esperar()
            estado.avanzar_hasta_turno_jugador()
        lento = 0.0
        for numero in range(1, 601, 37):
            inicio = time.perf_counter()
            consultado = estado.linea.estado_antes_de(estado, numero)
            lento = max(lento, time.perf_counter() - inicio)
            self.assertEqual(huella_sintetica(consultado), vistos[numero - 1])
        self.assertLess(lento, 0.5)          # el límite de 50 ms se mide en el bench


def huella_sintetica(e):
    return (e.tiempo, e.acciones, e.jugador.sala, e.jugador.vida,
            tuple((x.instancia, x.sala, x.vida) for _, x in e._enemigos), e.azar.getstate())


if __name__ == "__main__":
    unittest.main()
