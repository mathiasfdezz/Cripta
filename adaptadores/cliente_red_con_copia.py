import json
import os
import re
import shutil

from adaptadores.cliente_red import ClienteRed
from adaptadores.fuente_datos import validar_lote
from adaptadores.mapeadores.error_datos import ErrorDatos, leer_campo
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from adaptadores.rutas_offline import RutasOffline
from estructuras.vector_ordenado import VectorOrdenado

# solo ids de este tipo se usan como nombre de carpeta (evita borrar fuera de la caché)
ID_SEGURO = re.compile(r"^[A-Za-z0-9_-]+$")


class ClienteRedConCopia(ClienteRed):
    """ClienteRed que guarda en disco el esqueleto y el contenido de cada cripta y los
    vuelve a usar mientras la versión de la cripta no cambie (sección 4.4). Una segunda
    partida de la misma cripta ya no pide páginas ni contenido.

    Los archivos usan la misma organización que el paquete --offline. Si algo falla al
    leer o escribir el disco, simplemente se usa la red: la copia nunca rompe el juego."""

    def __init__(self, conexion=None, carpeta="cache_criptas"):
        super().__init__(conexion)
        self._carpeta = carpeta
        self._rutas = RutasOffline(carpeta)
        self._vigentes = VectorOrdenado()   # criptas cuya copia es de la versión actual

    def datos_cripta(self, cripta_id):
        datos = super().datos_cripta(cripta_id)
        if ID_SEGURO.match(cripta_id):
            self._validar_copia(cripta_id, datos.version)
        return datos

    def pagina_salas(self, cripta_id, pagina):
        if not self._vigentes.contiene(cripta_id):
            return super().pagina_salas(cripta_id, pagina)
        ruta = self._rutas.pagina_salas(cripta_id, pagina)
        guardada = self._mapear(self._leer(ruta), pagina_salas_desde_json)
        if guardada is not None:
            return guardada
        operacion = f"esqueleto de {cripta_id}, página {pagina}"
        crudo = self._conexion.obtener_json(f"/criptas/{cripta_id}/salas?pagina={pagina}",
                                            operacion)
        resultado = pagina_salas_desde_json(crudo)
        self._guardar(ruta, crudo)
        return resultado

    def contenido(self, cripta_id, salas):
        if not self._vigentes.contiene(cripta_id):
            return super().contenido(cripta_id, salas)
        validar_lote(salas, "contenido")
        listos = VectorOrdenado()   # sala -> ContenidoSala
        faltan = []
        for sala in salas:
            guardado = self._mapear(self._leer(self._rutas.contenido_sala(cripta_id, sala)),
                                    contenido_sala_desde_json)
            if guardado is None:
                faltan.append(sala)
            else:
                listos.insertar(sala, guardado)
        if faltan:
            # solo se piden las que no estaban, en un único lote
            lista = ",".join(str(s) for s in faltan)
            operacion = f"contenido de salas {lista}"
            respuesta = self._conexion.obtener_json(
                f"/criptas/{cripta_id}/contenido?salas={lista}", operacion)
            for crudo in leer_campo(respuesta, "contenido", operacion):
                contenido = contenido_sala_desde_json(crudo)
                self._guardar(self._rutas.contenido_sala(cripta_id, contenido.sala), crudo)
                listos.insertar(contenido.sala, contenido)
        return tuple(listos.buscar(sala) for sala in salas if listos.contiene(sala))

    def _validar_copia(self, cripta_id, version):
        ruta = self._rutas.version_cripta(cripta_id)
        guardada = self._leer(ruta)
        if guardada is None or guardada.get("version") != version:
            # otra versión: lo guardado ya no sirve
            shutil.rmtree(os.path.join(self._carpeta, cripta_id), ignore_errors=True)
            if not self._guardar(ruta, {"id": cripta_id, "version": version}):
                return
        self._vigentes.insertar(cripta_id, True)

    @staticmethod
    def _mapear(crudo, mapeador):
        # un archivo dañado o incompleto cuenta como si no estuviera
        if crudo is None:
            return None
        try:
            return mapeador(crudo)
        except (ErrorDatos, KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _leer(ruta):
        try:
            with open(ruta, encoding="utf-8") as archivo:
                return json.load(archivo)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _guardar(ruta, datos):
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False)
            return True
        except OSError:
            return False
