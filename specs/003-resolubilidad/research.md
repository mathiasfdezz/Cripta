# Research: Verificación de resolubilidad

## Preguntas de §8 que responde esta capacidad

**Una llave abre una región con otras tres llaves. ¿Qué hace la verificación con las puertas que encontró cerradas antes de tener esa llave?**
Las dejó anotadas en la lista de su llave. Al obtenerla, recorre esa lista una sola vez y encola los destinos; no vuelve a recorrer lo ya alcanzado. Las tres llaves nuevas se obtienen cuando el recorrido llega a sus salas, y cada una libera a su vez su propia lista.

## Decisiones

1. **Índices densos de 001** para salas y salidas; las llaves se indexan aparte (las publicadas y las que piden las puertas), ordenadas por id con `VectorOrdenado`.
2. **Estado inicial de las puertas**: se toma de los DTO `Salida` (lo que declara el API), no de los objetos `Puerta`, que cambian durante la partida.
3. **Llaves de enemigos**: el servicio ya da la sala donde inicia el enemigo; el verificador no necesita el contenido.
4. **Formato del reporte**: texto en español, igual para la pantalla al iniciar y para `--verificar`, generado por un formateador de la capa de vista que no lee la entrada del usuario.

## Datos reales (2026-11-17)

- cripta-02 a 04: resolubles. cripta-05 «Cripta sellada»: `llave_negra` (salida) está en la sala 23, detrás de la puerta 7→22 que pide `llave_hierro`; `llave_hierro` está en la 24, detrás de 12→24 que pide `llave_negra`: ciclo negra → hierro → negra.
- cripta-06 (300 salas, 4 llaves, una suelta por un errante).
