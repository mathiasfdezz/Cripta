import json
import os

from adaptadores.fuente_datos import MAX_POR_LOTE
from adaptadores.mapeadores.error_datos import ErrorDatos, leer_campo


class DescargadorOffline:
    def __init__(self, conexion, rutas):
        self._conexion = conexion
        self._rutas = rutas

    def descargar_lista_criptas(self):
        operacion = "listar criptas"
        datos = self._conexion.obtener_json("/criptas", operacion)
        self._guardar(self._rutas.criptas(), datos)
        return [leer_campo(c, "id", operacion) for c in leer_campo(datos, "criptas", operacion)]

    def descargar_cripta(self, cripta_id):
        operacion = f"datos de {cripta_id}"
        datos = self._conexion.obtener_json(f"/criptas/{cripta_id}", operacion)
        self._guardar(self._rutas.datos_cripta(cripta_id), datos)

        version = self._conexion.obtener_json(f"/criptas/{cripta_id}/version", f"versión de {cripta_id}")
        self._guardar(self._rutas.version_cripta(cripta_id), version)

        ids_sala = []
        for pagina in range(1, leer_campo(datos, "paginas", operacion) + 1):
            operacion_pagina = f"esqueleto de {cripta_id}, página {pagina}"
            respuesta = self._conexion.obtener_json(
                f"/criptas/{cripta_id}/salas?pagina={pagina}", operacion_pagina)
            self._guardar(self._rutas.pagina_salas(cripta_id, pagina), respuesta)
            for sala in leer_campo(respuesta, "salas", operacion_pagina):
                ids_sala.append(leer_campo(sala, "id", operacion_pagina))

        tipos = []
        descargadas = []
        for i in range(0, len(ids_sala), MAX_POR_LOTE):
            lista = ",".join(str(s) for s in ids_sala[i:i + MAX_POR_LOTE])
            operacion_lote = f"contenido de salas {lista}"
            respuesta = self._conexion.obtener_json(
                f"/criptas/{cripta_id}/contenido?salas={lista}", operacion_lote)
            for contenido in leer_campo(respuesta, "contenido", operacion_lote):
                sala = leer_campo(contenido, "sala", operacion_lote)
                self._guardar(self._rutas.contenido_sala(cripta_id, sala), contenido)
                descargadas.append(sala)
                for enemigo in contenido.get("enemigos") or []:
                    self._agregar_sin_repetir(tipos, leer_campo(enemigo, "tipo", operacion_lote))
                for objeto in contenido.get("objetos") or []:
                    self._agregar_sin_repetir(tipos, objeto)
                for trampa in contenido.get("trampas") or []:
                    self._agregar_sin_repetir(tipos, leer_campo(trampa, "tipo", operacion_lote))

        faltan = [s for s in ids_sala if s not in descargadas]
        if faltan:
            raise ErrorDatos(f"{operacion}: el API no devolvio el contenido de las salas {faltan}")

        self.descargar_catalogo(tipos)

    def descargar_catalogo(self, ids):
        version = self._conexion.obtener_json("/catalogo/version", "versión del catálogo")
        self._guardar(self._rutas.version_catalogo(), version)

        pendientes = list(ids)
        descargados = []
        while pendientes:
            lote = pendientes[:MAX_POR_LOTE]
            pendientes = pendientes[MAX_POR_LOTE:]
            lista = ",".join(lote)
            operacion = f"catálogo {lista}"
            respuesta = self._conexion.obtener_json(f"/catalogo?ids={lista}", operacion)
            for ficha in leer_campo(respuesta, "entidades", operacion):
                ficha_id = leer_campo(ficha, "id", operacion)
                self._guardar(self._rutas.ficha(ficha_id), ficha)
                descargados.append(ficha_id)
                for soltado in ficha.get("suelta") or []:
                    if soltado not in descargados and soltado not in pendientes:
                        pendientes.append(soltado)

    def _agregar_sin_repetir(self, lista, elemento):
        if elemento not in lista:
            lista.append(elemento)

    def _guardar(self, ruta, datos):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)