import time
import uuid

import requests

from adaptadores.error_presupuesto import ErrorPresupuesto
from adaptadores.error_red import ErrorRed
from adaptadores.fuente_datos import MAX_POR_LOTE, FuenteDatos
from adaptadores.mapeadores.error_datos import leer_campo
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from adaptadores.mapeadores.mapeador_criptas import (datos_cripta_desde_json,
                                                     resumen_cripta_desde_json)
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class ClienteRed(FuenteDatos):
    def __init__(self, timeout=10, max_reintentos=3, al_esperar=None, esperar=time.sleep):
        # un solo id por ejecución
        self.client_id = str(uuid.uuid4())
        self._headers = {"X-Cripta-Client-Id": self.client_id}
        self._timeout = timeout
        self._max_reintentos = max_reintentos
        # al_esperar(operacion, segundos, intento): para que la vista avise del 429 si quiere
        self._al_esperar = al_esperar
        self._esperar = esperar
        self._solicitudes = 0
        self._presupuesto = None

    def fijar_presupuesto(self, presupuesto):
        self._presupuesto = presupuesto

    def solicitudes_realizadas(self):
        return self._solicitudes

    def listar_criptas(self):
        operacion = "listar criptas"
        datos = self._get("/criptas", operacion)
        return tuple(resumen_cripta_desde_json(c) for c in leer_campo(datos, "criptas", operacion))

    def datos_cripta(self, cripta_id):
        return datos_cripta_desde_json(self._get(f"/criptas/{cripta_id}", f"datos de {cripta_id}"))

    def version_cripta(self, cripta_id):
        operacion = f"versión de {cripta_id}"
        datos = self._get(f"/criptas/{cripta_id}/version", operacion)
        return leer_campo(datos, "version", operacion)

    def pagina_salas(self, cripta_id, pagina):
        operacion = f"esqueleto de {cripta_id}, página {pagina}"
        return pagina_salas_desde_json(
            self._get(f"/criptas/{cripta_id}/salas?pagina={pagina}", operacion))

    def contenido(self, cripta_id, salas):
        self._validar_lote(salas, "contenido")
        lista = ",".join(str(s) for s in salas)
        operacion = f"contenido de salas {lista}"
        datos = self._get(f"/criptas/{cripta_id}/contenido?salas={lista}", operacion)
        return tuple(contenido_sala_desde_json(c) for c in leer_campo(datos, "contenido", operacion))

    def version_catalogo(self):
        operacion = "versión del catálogo"
        return leer_campo(self._get("/catalogo/version", operacion), "version", operacion)

    def catalogo(self, ids):
        self._validar_lote(ids, "catálogo")
        lista = ",".join(ids)
        operacion = f"catálogo {lista}"
        datos = self._get(f"/catalogo?ids={lista}", operacion)
        return tuple(ficha_catalogo_desde_json(f) for f in leer_campo(datos, "entidades", operacion))

    def _validar_lote(self, elementos, nombre):
        if len(elementos) == 0 or len(elementos) > MAX_POR_LOTE:
            raise ValueError(f"{nombre} acepta de 1 a {MAX_POR_LOTE} elementos, "
                             f"se pidieron {len(elementos)}")

    def _get(self, ruta, operacion):
        url = f"{BASE_URL}{ruta}"

        for intento in range(1, self._max_reintentos + 1):
            if self._presupuesto is not None and self._solicitudes >= self._presupuesto:
                raise ErrorPresupuesto(
                    f"{operacion}: presupuesto agotado "
                    f"({self._solicitudes}/{self._presupuesto} solicitudes)")

            # los reintentos también cuentan
            self._solicitudes += 1
            try:
                respuesta = requests.get(url, headers=self._headers, timeout=self._timeout)
            except requests.Timeout:
                raise ErrorRed(f"{operacion}: el servidor no respondió en {self._timeout}s")
            except requests.RequestException as error:
                raise ErrorRed(f"{operacion}: no se pudo conectar ({error})")

            if respuesta.status_code == 200:
                try:
                    return respuesta.json()
                except ValueError:
                    raise ErrorRed(f"{operacion}: la respuesta no es JSON válido")

            if respuesta.status_code == 429:
                try:
                    espera = respuesta.json().get("reintentar_en", 1)
                except ValueError:
                    espera = 1
                if self._al_esperar is not None:
                    self._al_esperar(operacion, espera, intento)
                # tiempo real, no afecta el reloj del juego
                self._esperar(espera)
                continue

            raise ErrorRed(f"{operacion}: HTTP {respuesta.status_code} -> {respuesta.text[:200]}")

        raise ErrorRed(f"{operacion}: se agotaron {self._max_reintentos} reintentos por HTTP 429")