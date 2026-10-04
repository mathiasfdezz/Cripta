import json

from adaptadores.error_offline import ErrorOffline
from adaptadores.fuente_datos import FuenteDatos, validar_lote
from adaptadores.mapeadores.error_datos import leer_campo
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from adaptadores.mapeadores.mapeador_criptas import (datos_cripta_desde_json,
                                                     resumen_cripta_desde_json)
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from adaptadores.rutas_offline import RutasOffline


class ClienteOffline(FuenteDatos):
    def __init__(self, rutas=None):
        self._rutas = rutas if rutas is not None else RutasOffline()
        self._presupuesto = None

    def fijar_presupuesto(self, presupuesto):
        self._presupuesto = presupuesto

    def solicitudes_realizadas(self):
        # leer de disco no cuenta como solicitud de red
        return 0

    def listar_criptas(self):
        operacion = "listar criptas"
        datos = self._leer(self._rutas.criptas(), operacion)
        return tuple(resumen_cripta_desde_json(c) for c in leer_campo(datos, "criptas", operacion))

    def datos_cripta(self, cripta_id):
        operacion = f"datos de {cripta_id}"
        return datos_cripta_desde_json(self._leer(self._rutas.datos_cripta(cripta_id), operacion))

    def version_cripta(self, cripta_id):
        operacion = f"versión de {cripta_id}"
        datos = self._leer(self._rutas.version_cripta(cripta_id), operacion)
        return leer_campo(datos, "version", operacion)

    def pagina_salas(self, cripta_id, pagina):
        operacion = f"esqueleto de {cripta_id}, página {pagina}"
        return pagina_salas_desde_json(self._leer(self._rutas.pagina_salas(cripta_id, pagina), operacion))

    def contenido(self, cripta_id, salas):
        validar_lote(salas, "contenido")
        return tuple(
            contenido_sala_desde_json(
                self._leer(self._rutas.contenido_sala(cripta_id, sala), f"contenido de sala {sala}"))
            for sala in salas
        )

    def version_catalogo(self):
        operacion = "versión del catálogo"
        return leer_campo(self._leer(self._rutas.version_catalogo(), operacion), "version", operacion)

    def catalogo(self, ids):
        validar_lote(ids, "catálogo")
        return tuple(
            ficha_catalogo_desde_json(self._leer(self._rutas.ficha(ficha_id), f"ficha {ficha_id}"))
            for ficha_id in ids
        )

    def _leer(self, ruta, operacion):
        try:
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)
        except FileNotFoundError:
            raise ErrorOffline(f"{operacion}: no está descargado ({ruta}). "
                               f"Ejecute: python -m scripts.descargar_offline")
        except json.JSONDecodeError:
            raise ErrorOffline(f"{operacion}: el archivo está dañado ({ruta})")