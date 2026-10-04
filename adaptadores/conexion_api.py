import time
import uuid

import requests

from adaptadores.error_presupuesto import ErrorPresupuesto
from adaptadores.error_red import ErrorRed

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class ConexionApi:
    def __init__(self, timeout=10, max_reintentos=3, al_esperar=None, esperar=time.sleep):
        # un solo id por ejecución
        self.client_id = str(uuid.uuid4())
        self._headers = {"X-Cripta-Client-Id": self.client_id}
        self._timeout = timeout
        self._max_reintentos = max_reintentos
        # al_esperar(operacion, segundos, intento) para que la vista avise del 429 si quiere
        self._al_esperar = al_esperar
        self._esperar = esperar
        self._solicitudes = 0
        self._presupuesto = None

    def fijar_presupuesto(self, presupuesto):
        self._presupuesto = presupuesto

    def solicitudes_realizadas(self):
        return self._solicitudes

    def obtener_json(self, ruta, operacion):
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
                    cuerpo = respuesta.json()
                    espera = cuerpo.get("reintentar_en", 1) if isinstance(cuerpo, dict) else 1
                except ValueError:
                    espera = 1
                if self._al_esperar is not None:
                    self._al_esperar(operacion, espera, intento)
                self._esperar(espera)
                continue

            raise ErrorRed(f"{operacion}: HTTP {respuesta.status_code} -> {respuesta.text[:200]}")

        raise ErrorRed(f"{operacion}: se agotaron {self._max_reintentos} reintentos por HTTP 429")