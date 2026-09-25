import time
import uuid

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
MAX_POR_LOTE = 10


class ErrorRed(Exception):
    pass


class ErrorPresupuesto(ErrorRed):
    pass


class ClienteRed:
    def __init__(self, timeout=10, max_reintentos=3):
        # un solo id por ejecución
        self.client_id = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.client_id}
        self.timeout = timeout
        self.max_reintentos = max_reintentos
        self.solicitudes = 0
        self.presupuesto = None

    def fijar_presupuesto(self, presupuesto):
        self.presupuesto = presupuesto

    def _get(self, ruta, operacion):
        url = f"{BASE_URL}{ruta}"

        for intento in range(1, self.max_reintentos + 1):
            if self.presupuesto is not None and self.solicitudes >= self.presupuesto:
                raise ErrorPresupuesto(
                    f"{operacion}: presupuesto agotado "
                    f"({self.solicitudes}/{self.presupuesto} solicitudes)")

            # los reintentos también cuentan
            self.solicitudes += 1
            try:
                respuesta = requests.get(url, headers=self.headers, timeout=self.timeout)
            except requests.Timeout:
                raise ErrorRed(f"{operacion}: el servidor no respondió en {self.timeout}s")
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
                print(f"[429] {operacion}: esperando {espera}s "
                      f"(intento {intento}/{self.max_reintentos})")
                # tiempo real, no afecta el reloj del juego
                time.sleep(espera)
                continue

            raise ErrorRed(f"{operacion}: HTTP {respuesta.status_code} -> {respuesta.text[:200]}")

        raise ErrorRed(f"{operacion}: se agotaron {self.max_reintentos} reintentos por HTTP 429")

    def listar_criptas(self):
        return self._get("/criptas", "listar criptas")

    def datos_cripta(self, cripta_id):
        return self._get(f"/criptas/{cripta_id}", f"datos de {cripta_id}")

    def version_cripta(self, cripta_id):
        return self._get(f"/criptas/{cripta_id}/version", f"versión de {cripta_id}")

    def pagina_salas(self, cripta_id, pagina):
        return self._get(f"/criptas/{cripta_id}/salas?pagina={pagina}",
                         f"esqueleto de {cripta_id}, página {pagina}")

    def contenido(self, cripta_id, salas):
        if len(salas) == 0 or len(salas) > MAX_POR_LOTE:
            raise ValueError(f"contenido acepta de 1 a {MAX_POR_LOTE} salas, se pidieron {len(salas)}")
        lista = ",".join(str(s) for s in salas)
        return self._get(f"/criptas/{cripta_id}/contenido?salas={lista}",
                         f"contenido de salas {lista}")

    def version_catalogo(self):
        return self._get("/catalogo/version", "versión del catálogo")

    def catalogo(self, ids):
        if len(ids) == 0 or len(ids) > MAX_POR_LOTE:
            raise ValueError(f"catálogo acepta de 1 a {MAX_POR_LOTE} ids, se pidieron {len(ids)}")
        lista = ",".join(ids)
        return self._get(f"/catalogo?ids={lista}", f"catálogo {lista}")
