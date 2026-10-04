# prueba manual contra el API real, gasta solicitudes
# uso (desde la carpeta cripta): python -m scripts.probar_cliente [cripta_id]
import sys

from adaptadores.cliente_red import ClienteRed
from adaptadores.conexion_api import ConexionApi
from adaptadores.error_red import ErrorRed
from adaptadores.fuente_datos import MAX_POR_LOTE
from adaptadores.mapeadores.error_datos import ErrorDatos


def avisar_espera(operacion, segundos, intento):
    print(f"[429] {operacion}: esperando {segundos}s (intento {intento})")


def principal():
    cripta_id = sys.argv[1] if len(sys.argv) > 1 else "cripta-01"
    cliente = ClienteRed(ConexionApi(al_esperar=avisar_espera))
    presupuesto = "?"
    print(f"Client ID: {cliente.client_id}")

    try:
        datos = cliente.datos_cripta(cripta_id)
        presupuesto = datos.presupuesto_solicitudes
        cliente.fijar_presupuesto(presupuesto)
        print(f"{datos.id}: {datos.salas_total} salas, presupuesto {presupuesto}")

        salas = []
        for numero in range(1, datos.paginas + 1):
            salas.extend(cliente.pagina_salas(cripta_id, numero).salas)
        print(f"Esqueleto: {len(salas)} salas")

        contenidos = []
        ids_sala = [sala.id for sala in salas]
        for i in range(0, len(ids_sala), MAX_POR_LOTE):
            contenidos.extend(cliente.contenido(cripta_id, ids_sala[i:i + MAX_POR_LOTE]))

        tipos = []
        for c in contenidos:
            for tipo in [e.tipo for e in c.enemigos] + list(c.objetos) + [t.tipo for t in c.trampas]:
                if tipo not in tipos:
                    tipos.append(tipo)

        fichas = []
        for i in range(0, len(tipos), MAX_POR_LOTE):
            fichas.extend(cliente.catalogo(tipos[i:i + MAX_POR_LOTE]))
        for ficha in fichas:
            print(f"  - {ficha.id} ({ficha.clase}): {ficha.nombre}")

    except (ErrorRed, ErrorDatos) as error:
        print(f"[ERROR] {error}")

    print(f"\nSolicitudes usadas: {cliente.solicitudes_realizadas()}/{presupuesto}")


if __name__ == "__main__":
    principal()