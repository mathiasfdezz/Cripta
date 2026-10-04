# descarga las respuestas del API a datos_offline/ para poder jugar con --offline
# uso (desde la carpeta cripta): python -m scripts.descargar_offline [cripta_id ...]
# sin ids descarga todas las criptas publicadas
import sys

from adaptadores.conexion_api import ConexionApi
from adaptadores.descargador_offline import DescargadorOffline
from adaptadores.error_red import ErrorRed
from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.rutas_offline import RutasOffline


def avisar_espera(operacion, segundos, intento):
    print(f"[429] {operacion}: esperando {segundos}s (intento {intento})")


def principal():
    conexion = ConexionApi(al_esperar=avisar_espera)
    descargador = DescargadorOffline(conexion, RutasOffline())
    try:
        publicadas = descargador.descargar_lista_criptas()
        for cripta_id in sys.argv[1:] or publicadas:
            descargador.descargar_cripta(cripta_id)
            print(f"{cripta_id}: descargada")
    except (ErrorRed, ErrorDatos) as error:
        print(f"[ERROR] {error}")
    print(f"Solicitudes usadas: {conexion.solicitudes_realizadas()}")


if __name__ == "__main__":
    principal()