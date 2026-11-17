def lineas_historia(estado, que, instante):
    """Resumen de un estado de la línea de tiempo (FR-303). 'que' describe la consulta
    ('#3', 't=250'); 'instante' es el reloj que se muestra. Lo usan la consola y
    --replay --hasta, que no abre la vista interactiva."""
    jugador = estado.jugador
    sala = estado.esqueleto.obtener(jugador.sala)
    inventario = jugador.inventario
    lineas = [f"Historia {que}: reloj {instante}"
              + (f" (último evento en t={estado.tiempo})" if estado.tiempo != instante else ""),
              f"  Sala {jugador.sala} - {sala.nombre if sala is not None else '?'}",
              f"  Vida {jugador.vida}/{jugador.vida_max}   ataque {jugador.ataque_efectivo()}   "
              f"defensa {jugador.defensa_efectiva()}   velocidad {jugador.velocidad}   "
              f"acciones {estado.acciones}"]
    objetos = []
    for nodo in inventario.lista.recorrer():
        marca = " [equipado]" if inventario.esta_equipado(nodo) else ""
        marca += " <" if nodo is inventario.actual else ""
        objetos.append(nodo.dato.nombre + marca)
    lineas.append(f"  Inventario {len(inventario)}/{inventario.capacidad}: "
                  + (", ".join(objetos) if objetos else "vacío"))
    efectos = []
    if estado.antorcha_hasta is not None:
        efectos.append(f"antorcha hasta t={estado.antorcha_hasta}")
    if estado.veneno_hasta is not None:
        efectos.append(f"veneno ({estado.veneno_dano} cada 80) hasta t={estado.veneno_hasta}")
    if jugador.velocidad != jugador.velocidad_base:
        efectos.append(f"velocidad modificada ({jugador.velocidad})")
    lineas.append("  Efectos activos: " + (", ".join(efectos) if efectos else "ninguno"))
    enemigos = estado.enemigos_en_sala(jugador.sala)
    if enemigos:
        lineas.append("  Enemigos en la sala: " + ", ".join(
            f"{e.nombre} {e.instancia} {e.vida}/{e.vida_max}"
            + (" (dormido)" if not e.activo else "") for e in enemigos))
    else:
        lineas.append("  Enemigos en la sala: ninguno")
    if estado.mapa is not None:
        exploradas = estado.mapa.salas_exploradas()
        avistadas = estado.mapa.salas_avistadas()
        lineas.append(f"  Mapa conocido: {len(exploradas)} exploradas ("
                      + ", ".join(str(s) for s in exploradas) + f"), {len(avistadas)} avistadas")
    if estado.terminada():
        lineas.append(f"  La partida ya había terminado: {estado.resultado}")
    return lineas

