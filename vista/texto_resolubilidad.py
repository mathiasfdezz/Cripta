from vista.menu_acciones import MenuAcciones


def lineas_resolubilidad(reporte, cripta_id):
    """El reporte de resolubilidad como líneas de texto. Lo usan la consola al iniciar
    una partida y --verificar, que no abre la vista interactiva."""
    legible = MenuAcciones.legible
    lineas = [f"Verificación de resolubilidad de {cripta_id} "
              f"({reporte.salas} salas, {reporte.salidas} salidas, {reporte.llaves} llaves)"]
    if reporte.resoluble:
        orden = " -> ".join(legible(k) for k in reporte.orden_llaves) or "no hace falta ninguna"
        lineas.append("  RESOLUBLE. Orden para conseguir las llaves: " + orden)
        return lineas
    lineas.append("  NO RESOLUBLE: no se puede conseguir la llave de la salida y llegar a ella.")
    if reporte.orden_llaves:
        lineas.append("  Llaves que sí se consiguen: "
                      + ", ".join(legible(k) for k in reporte.orden_llaves))
    if reporte.no_obtenibles:
        lineas.append("  Llaves que no se pueden conseguir: "
                      + ", ".join(legible(k) for k in reporte.no_obtenibles))
    if reporte.sin_ubicacion:
        lineas.append("  Llaves que ninguna sala contiene: "
                      + ", ".join(legible(k) for k in reporte.sin_ubicacion))
    if reporte.frontera:
        lineas.append("  Puertas que bloquean el avance:")
        for puerta in reporte.frontera:
            lineas.append(f"    sala {puerta.sala}, salida {puerta.direccion} -> sala "
                          f"{puerta.destino}: " + _que_pide(puerta, legible))
    if reporte.ciclo:
        lineas.append("  Ciclo de llaves: " + " -> ".join(legible(k) for k in reporte.ciclo))
        for llave, puerta in zip(reporte.ciclo, reporte.puertas_del_ciclo):
            lineas.append(f"    {legible(llave)} está detrás de la puerta {puerta.sala} "
                          f"{puerta.direccion} -> {puerta.destino}, que pide {legible(puerta.llave)}")
    return lineas


def _que_pide(puerta, legible):
    if puerta.llave is None:
        return "cerrada y sin llave que la abra"
    if not puerta.ubicaciones:
        return f"pide {legible(puerta.llave)}, que no está en la cripta"
    donde = []
    for ubicacion in puerta.ubicaciones:
        texto = f"sala {ubicacion.sala}"
        if ubicacion.enemigo:
            texto += f", la suelta {ubicacion.enemigo}"
        donde.append(texto)
    return f"pide {legible(puerta.llave)} (está en {'; '.join(donde)})"
