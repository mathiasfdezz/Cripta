from estructuras.lista_doble import ListaDoble
from estructuras.vector_ordenado import VectorOrdenado

LOTE_MAXIMO = 10   # limite del servicio para GET /catalogo?ids=...


class _Entrada:
    __slots__ = ("ficha", "refs")

    def __init__(self, ficha):
        self.ficha = ficha
        self.refs = 0


class CacheCatalogo:
    """Cache de fichas del catalogo con desalojo LRU (4.3 y 4.4).

    - Busqueda por id: VectorOrdenado (busqueda binaria, muchas lecturas,
      pocas inserciones).
    - Orden de uso: ListaDoble. Cabeza = usada mas recientemente,
      cola = usada hace mas tiempo. Tocar una ficha es O(1).
    - Contador de referencias: una ficha con refs > 0 jamas se desaloja.
      Si todas estan en uso la cache excede temporalmente su tope y se
      reajusta cuando se liberan.

    El modelo no conoce HTTP ni archivos. Recibe dos adaptadores:
      fuente: FuenteDatos, usa fuente.catalogo(ids) -> FichaCatalogo (red u offline)
      almacen: leer(id) -> FichaCatalogo|None, guardar(ficha), version(),
               guardar_version(v), limpiar()                 (disco)
    """

    def __init__(self, fuente, almacen=None, capacidad=25):
        if capacidad < 1:
            raise ValueError("la capacidad de la cache debe ser >= 1")
        self.capacidad = capacidad
        self._fuente = fuente
        self._almacen = almacen
        self._indice = VectorOrdenado()   # id -> nodo de la lista LRU
        self._lru = ListaDoble()          # dato = _Entrada
        self.aciertos = 0
        self.fallos = 0
        self.lecturas_disco = 0
        self.lotes_red = 0
        self.desalojos = 0

    # ------------------------------------------------------------ version

    def validar_version(self, version_actual):
        """Compara con la version global del catalogo. Si el disco guarda otra,
        descarta lo persistido. Devuelve True si se conservo."""
        if self._almacen is None:
            return True
        guardada = self._almacen.version()
        if guardada == version_actual:
            return True
        self._almacen.limpiar()
        self._almacen.guardar_version(version_actual)
        self._olvidar_memoria_sin_uso()
        return False

    def _olvidar_memoria_sin_uso(self):
        nodo = self._lru.cola
        while nodo is not None:
            anterior = nodo.anterior
            if nodo.dato.refs == 0:
                self._sacar(nodo)
            nodo = anterior

    # ----------------------------------------------------------- consultas

    def __len__(self):
        return len(self._lru)

    def esta_en_memoria(self, id_ficha):
        return self._indice.contiene(id_ficha)

    def obtener(self, id_ficha):
        """Ficha desde memoria (cuenta acierto/fallo). Si falta, la resuelve."""
        resultado = self.resolver([id_ficha])
        return resultado[0]

    def resolver(self, ids):
        """Devuelve las fichas de 'ids' en el mismo orden. Cada id distinto se
        busca una vez: memoria -> disco -> red (en lotes de hasta 10)."""
        unicos = self._sin_repetidos(ids)
        faltan = []
        halladas = VectorOrdenado()   # id -> ficha, solo para esta llamada

        for id_ficha in unicos:
            nodo = self._indice.buscar(id_ficha)
            if nodo is not None:
                self.aciertos += 1
                self._lru.mover_al_frente(nodo)
                halladas.insertar(id_ficha, nodo.dato.ficha)
                continue

            self.fallos += 1
            ficha = self._leer_disco(id_ficha)
            if ficha is not None:
                self._insertar(ficha)
                halladas.insertar(id_ficha, ficha)
            else:
                faltan.append(id_ficha)

        for inicio in range(0, len(faltan), LOTE_MAXIMO):
            lote = faltan[inicio:inicio + LOTE_MAXIMO]
            self.lotes_red += 1
            for ficha in self._fuente.catalogo(lote):
                self._insertar(ficha)
                halladas.insertar(ficha.id, ficha)
                if self._almacen is not None:
                    self._almacen.guardar(ficha)

        resultado = []
        for id_ficha in ids:
            ficha = halladas.buscar(id_ficha)
            if ficha is None:
                raise KeyError("el catalogo no devolvio la ficha: " + str(id_ficha))
            resultado.append(ficha)
        return resultado

    # ------------------------------------------------------ fichas en uso

    def retener(self, id_ficha):
        """Marca una referencia activa (enemigo vivo, objeto en inventario o
        suelo de la sala actual, trampa de la sala actual)."""
        nodo = self._indice.buscar(id_ficha)
        if nodo is None:
            raise KeyError("no se puede retener una ficha fuera de memoria: "
                           + str(id_ficha))
        nodo.dato.refs += 1

    def liberar(self, id_ficha):
        nodo = self._indice.buscar(id_ficha)
        if nodo is None or nodo.dato.refs == 0:
            return
        nodo.dato.refs -= 1
        if nodo.dato.refs == 0:
            self._ajustar_tope()

    def referencias(self, id_ficha):
        nodo = self._indice.buscar(id_ficha)
        return 0 if nodo is None else nodo.dato.refs

    # ------------------------------------------------------------ interno

    def _sin_repetidos(self, ids):
        vistos = VectorOrdenado()
        unicos = []
        for id_ficha in ids:
            if vistos.insertar(id_ficha, True):
                unicos.append(id_ficha)
        return unicos

    def _leer_disco(self, id_ficha):
        if self._almacen is None:
            return None
        ficha = self._almacen.leer(id_ficha)
        if ficha is not None:
            self.lecturas_disco += 1
        return ficha

    def _insertar(self, ficha):
        if self._indice.contiene(ficha.id):
            return
        nodo = self._lru.agregar_frente(_Entrada(ficha))
        self._indice.insertar(ficha.id, nodo)
        self._ajustar_tope(protegido=nodo)   # no expulsar la recien llegada

    def _ajustar_tope(self, protegido=None):
        while len(self._lru) > self.capacidad:
            victima = self._lru.cola
            while victima is not None and (victima.dato.refs > 0
                                           or victima is protegido):
                victima = victima.anterior
            if victima is None:
                return   # todo esta en uso: no se puede desalojar nada
            self._sacar(victima)
            self.desalojos += 1

    def _sacar(self, nodo):
        self._indice.eliminar(nodo.dato.ficha.id)
        self._lru.eliminar_nodo(nodo)