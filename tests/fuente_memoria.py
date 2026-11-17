"""Fuente de datos en memoria para probar el controlador con criptas mínimas."""
import contextlib
import io

from adaptadores.fuente_datos import FuenteDatos, validar_lote
from controlador.partida import ControladorPartida
from dtos.contenido_sala import ContenidoSala
from dtos.datos_cripta import DatosCripta
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.instancia_trampa import InstanciaTrampa
from dtos.pagina_salas import PaginaSalas
from modelo.cache_catalogo import CacheCatalogo
from tests.criptas_prueba import FICHAS, esqueleto


class FuenteMemoria(FuenteDatos):

    def __init__(self, mapa, contenidos=(), llaves=(), fichas=FICHAS):
        self._salas = tuple(sala for _, sala in mapa._salas)
        self._contenidos = tuple(contenidos)
        self._fichas = fichas
        self.llaves_publicadas = tuple(llaves)

    def listar_criptas(self):
        return ()

    def datos_cripta(self, cripta_id):
        raise NotImplementedError

    def version_cripta(self, cripta_id):
        return "v1"

    def pagina_salas(self, cripta_id, pagina):
        return PaginaSalas(1, 1, self._salas)

    def contenido(self, cripta_id, salas):
        validar_lote(salas, "contenido")
        return tuple(self._de_sala(s) for s in salas)

    def _de_sala(self, sala):
        for contenido in self._contenidos:
            if contenido.sala == sala:
                return contenido
        return ContenidoSala(sala, (), (), ())

    def version_catalogo(self):
        return "c1"

    def catalogo(self, ids):
        validar_lote(ids, "catálogo")
        return tuple(f for f in self._fichas if f.id in ids)

    def llaves(self, cripta_id):
        return self.llaves_publicadas

    def fijar_presupuesto(self, presupuesto):
        pass

    def solicitudes_realizadas(self):
        return 0


class VistaMuda:
    def __getattr__(self, nombre):
        return lambda *args, **kwargs: None


def controlador(salidas, sala_inicial=1, contenidos=(), sala_salida=999, llave_salida="itm_x",
                vista=None, carpeta="partidas_prueba", velocidad=100, llaves=(), salas=()):
    mapa = esqueleto(*salidas, salas=salas)
    fuente = FuenteMemoria(mapa, contenidos, llaves)
    datos = DatosCripta("prueba", "v1", len(fuente._salas), 1, 50, sala_inicial, sala_salida,
                        llave_salida, 1000, 10, EstadisticasJugador(1000, 6, 2, velocidad))
    cache = CacheCatalogo(fuente)
    cache.validar_version("c1")
    with contextlib.redirect_stdout(io.StringIO()):
        return ControladorPartida(datos, fuente, cache, vista or VistaMuda(), 1, "c1", carpeta)


def trampa(sala, instancia="t-1"):
    return ContenidoSala(sala, (), (), (InstanciaTrampa(instancia, "trp_pinchos"),))
