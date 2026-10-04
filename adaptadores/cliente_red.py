from adaptadores.conexion_api import ConexionApi
from adaptadores.fuente_datos import FuenteDatos, validar_lote
from adaptadores.mapeadores.error_datos import leer_campo
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from adaptadores.mapeadores.mapeador_criptas import (datos_cripta_desde_json,
                                                     resumen_cripta_desde_json)
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json


class ClienteRed(FuenteDatos):
    def __init__(self, conexion=None):
        self._conexion = conexion if conexion is not None else ConexionApi()

    @property
    def client_id(self):
        return self._conexion.client_id

    def fijar_presupuesto(self, presupuesto):
        self._conexion.fijar_presupuesto(presupuesto)

    def solicitudes_realizadas(self):
        return self._conexion.solicitudes_realizadas()

    def listar_criptas(self):
        operacion = "listar criptas"
        datos = self._conexion.obtener_json("/criptas", operacion)
        return tuple(resumen_cripta_desde_json(c) for c in leer_campo(datos, "criptas", operacion))

    def datos_cripta(self, cripta_id):
        operacion = f"datos de {cripta_id}"
        return datos_cripta_desde_json(self._conexion.obtener_json(f"/criptas/{cripta_id}", operacion))

    def version_cripta(self, cripta_id):
        operacion = f"versión de {cripta_id}"
        datos = self._conexion.obtener_json(f"/criptas/{cripta_id}/version", operacion)
        return leer_campo(datos, "version", operacion)

    def pagina_salas(self, cripta_id, pagina):
        operacion = f"esqueleto de {cripta_id}, página {pagina}"
        return pagina_salas_desde_json(
            self._conexion.obtener_json(f"/criptas/{cripta_id}/salas?pagina={pagina}", operacion))

    def contenido(self, cripta_id, salas):
        validar_lote(salas, "contenido")
        lista = ",".join(str(s) for s in salas)
        operacion = f"contenido de salas {lista}"
        datos = self._conexion.obtener_json(f"/criptas/{cripta_id}/contenido?salas={lista}", operacion)
        return tuple(contenido_sala_desde_json(c) for c in leer_campo(datos, "contenido", operacion))

    def version_catalogo(self):
        operacion = "versión del catálogo"
        datos = self._conexion.obtener_json("/catalogo/version", operacion)
        return leer_campo(datos, "version", operacion)

    def catalogo(self, ids):
        validar_lote(ids, "catálogo")
        lista = ",".join(ids)
        operacion = f"catálogo {lista}"
        datos = self._conexion.obtener_json(f"/catalogo?ids={lista}", operacion)
        return tuple(ficha_catalogo_desde_json(f) for f in leer_campo(datos, "entidades", operacion))