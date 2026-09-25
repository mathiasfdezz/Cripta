import sys
import time
import uuid

import requests

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
TIMEOUT = 10
MAX_REINTENTOS = 3

# un solo id por ejecución
CLIENT_ID = str(uuid.uuid4())
HEADERS = {"X-Cripta-Client-Id": CLIENT_ID}


def pedir_json(ruta):
    url = f"{BASE_URL}{ruta}"

    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            respuesta = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException as error:
            print(f"[ERROR] GET {ruta}: no se pudo conectar -> {error}")
            return None

        if respuesta.status_code == 200:
            try:
                return respuesta.json()
            except ValueError:
                print(f"[ERROR] GET {ruta}: la respuesta 200 no es JSON válido")
                return None

        if respuesta.status_code == 429:
            try:
                espera = respuesta.json().get("reintentar_en", 1)
            except ValueError:
                espera = 1
            print(f"[429] GET {ruta}: esperando {espera}s (intento {intento}/{MAX_REINTENTOS})")
            time.sleep(espera)
            continue

        print(f"[ERROR] GET {ruta}: HTTP {respuesta.status_code} -> {respuesta.text[:200]}")
        return None

    print(f"[ERROR] GET {ruta}: se agotaron los {MAX_REINTENTOS} reintentos por 429")
    return None


print(f"Client ID de esta ejecución: {CLIENT_ID}\n")

datos = pedir_json("/criptas")
if datos is None:
    sys.exit(1)

print("Criptas disponibles:")
for cripta in datos["criptas"]:
    print(f"  - {cripta['id']}: {cripta['nombre']} ({cripta['salas']} salas, dificultad {cripta['dificultad']})")

# si no pasan id por consola, se usa la primera
if len(sys.argv) > 1:
    cripta_id = sys.argv[1]
else:
    cripta_id = datos["criptas"][0]["id"]

detalle = pedir_json(f"/criptas/{cripta_id}")
if detalle is not None:
    print(f"\nDetalle de {cripta_id}:")
    for clave, valor in detalle.items():
        print(f"  {clave}: {valor}")
