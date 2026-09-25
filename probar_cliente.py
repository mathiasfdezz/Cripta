# uso: python probar_cliente.py [cripta_id]
import sys

from adaptadores.cliente_red import MAX_POR_LOTE, ClienteRed, ErrorRed

cripta_id = sys.argv[1] if len(sys.argv) > 1 else "cripta-01"
cliente = ClienteRed()
print(f"Client ID: {cliente.client_id}")

try:
    datos = cliente.datos_cripta(cripta_id)
    cliente.fijar_presupuesto(datos["presupuesto_solicitudes"])
    print(f"{cripta_id}: {datos['salas_total']} salas, {datos['paginas']} página(s), "
          f"presupuesto {datos['presupuesto_solicitudes']}")

    salas = []
    for pagina in range(1, datos["paginas"] + 1):
        respuesta = cliente.pagina_salas(cripta_id, pagina)
        salas.extend(respuesta["salas"])
    print(f"Esqueleto: {len(salas)} salas descargadas")

    # aquí se pide todo solo para probar, en el juego va por cercanía
    contenidos = []
    ids_sala = [sala["id"] for sala in salas]
    for i in range(0, len(ids_sala), MAX_POR_LOTE):
        respuesta = cliente.contenido(cripta_id, ids_sala[i:i + MAX_POR_LOTE])
        contenidos.extend(respuesta["contenido"])

    tipos = []
    for c in contenidos:
        for enemigo in c["enemigos"]:
            if enemigo["tipo"] not in tipos:
                tipos.append(enemigo["tipo"])
        for objeto in c["objetos"]:
            if objeto not in tipos:
                tipos.append(objeto)
        for trampa in c["trampas"]:
            if trampa["tipo"] not in tipos:
                tipos.append(trampa["tipo"])
    print(f"Tipos distintos de catálogo: {len(tipos)} -> {tipos}")

    fichas = []
    for i in range(0, len(tipos), MAX_POR_LOTE):
        respuesta = cliente.catalogo(tipos[i:i + MAX_POR_LOTE])
        fichas.extend(respuesta["entidades"])
    for ficha in fichas:
        print(f"  - {ficha['id']} ({ficha['clase']}): {ficha['nombre']}")

except ErrorRed as error:
    print(f"[ERROR] {error}")

print(f"\nSolicitudes usadas: {cliente.solicitudes}/{cliente.presupuesto}")
