import random
import unittest

from estructuras.min_heap import MinHeap


class PruebasMinHeap(unittest.TestCase):

    def test_heap_vacio(self):
        heap = MinHeap()
        self.assertTrue(heap.esta_vacio())
        self.assertEqual(heap.tamano(), 0)
        with self.assertRaises(IndexError):
            heap.ver_minimo()
        with self.assertRaises(IndexError):
            heap.extraer_minimo()

    def test_ejemplo_del_juego(self):
        heap = MinHeap()
        for elemento in [(100, 1), (66, 2), (80, 3), (300, 4)]:
            heap.insertar(elemento)
        self.assertEqual(heap.ver_minimo(), (66, 2))
        self.assertEqual(heap.tamano(), 4)
        salida = [heap.extraer_minimo() for _ in range(4)]
        self.assertEqual(salida, [(66, 2), (80, 3), (100, 1), (300, 4)])
        self.assertTrue(heap.esta_vacio())

    def test_empate_por_secuencia(self):
        heap = MinHeap()
        for elemento in [(100, 5), (100, 2), (100, 9), (50, 7)]:
            heap.insertar(elemento)
        salida = [heap.extraer_minimo() for _ in range(4)]
        self.assertEqual(salida, [(50, 7), (100, 2), (100, 5), (100, 9)])

    def test_ver_minimo_no_saca(self):
        heap = MinHeap()
        heap.insertar((10, 1))
        heap.insertar((5, 2))
        self.assertEqual(heap.ver_minimo(), (5, 2))
        self.assertEqual(heap.ver_minimo(), (5, 2))
        self.assertEqual(heap.tamano(), 2)

    def test_insertar_y_extraer_intercalado(self):
        heap = MinHeap()
        heap.insertar((30, 1))
        heap.insertar((10, 2))
        self.assertEqual(heap.extraer_minimo(), (10, 2))
        heap.insertar((20, 3))
        heap.insertar((5, 4))
        self.assertEqual(heap.extraer_minimo(), (5, 4))
        self.assertEqual(heap.extraer_minimo(), (20, 3))
        self.assertEqual(heap.extraer_minimo(), (30, 1))

    def test_mil_aleatorios_salen_ordenados(self):
        azar = random.Random(42)
        heap = MinHeap()
        for secuencia in range(1000):
            heap.insertar((azar.randint(0, 1000), secuencia))
        salida = [heap.extraer_minimo() for _ in range(1000)]
        for i in range(1, len(salida)):
            self.assertLess(salida[i - 1], salida[i])


if __name__ == "__main__":
    unittest.main()