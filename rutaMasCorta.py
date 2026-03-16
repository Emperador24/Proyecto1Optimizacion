import pandas as pd
import math
import heapq

# -----------------------------
# 1. Leer datos
# -----------------------------
df = pd.read_csv("matriz_de_datos.csv", sep=",")
df.columns = df.columns.str.strip()

origenes = [1, 2]
destinos = [78, 79, 80]

ALPHA = 0.0   # 0 = solo distancia

# -----------------------------
# 2. Preparar arcos y pesos
# -----------------------------
max_costo = df["Costo"].max()
max_dist = df["Distancia"].max()

df["costo_norm"] = df["Costo"] / max_costo
df["dist_norm"] = df["Distancia"] / max_dist

df["peso"] = ALPHA * df["costo_norm"] + (1 - ALPHA) * df["dist_norm"]

arcos = [(int(row["Origen"]), int(row["Destino"])) for _, row in df.iterrows()]

# -----------------------------
# 3. Construir grafo
# -----------------------------
grafo = {}

for _, row in df.iterrows():

    i = int(row["Origen"])
    j = int(row["Destino"])
    peso = float(row["peso"])
    costo = float(row["Costo"])
    distancia = float(row["Distancia"])

    if i not in grafo:
        grafo[i] = []

    grafo[i].append((j, peso, costo, distancia))

# -----------------------------
# 4. Algoritmo de Dijkstra
# -----------------------------
def dijkstra(grafo, origen):

    dist = {}
    prev = {}
    costo_acum = {}
    dist_real_acum = {}

    for u in grafo.keys():
        dist[u] = math.inf
        costo_acum[u] = 0
        dist_real_acum[u] = 0

    for u in grafo:
        for v, _, _, _ in grafo[u]:
            if v not in dist:
                dist[v] = math.inf
                costo_acum[v] = 0
                dist_real_acum[v] = 0

    dist[origen] = 0
    heap = [(0, origen)]

    while heap:

        dist_u, u = heapq.heappop(heap)

        if dist_u > dist[u]:
            continue

        if u not in grafo:
            continue

        for v, w, c, d in grafo[u]:

            alt = dist[u] + w

            if alt < dist[v]:

                dist[v] = alt
                prev[v] = u
                costo_acum[v] = costo_acum.get(u, 0) + c
                dist_real_acum[v] = dist_real_acum.get(u, 0) + d

                heapq.heappush(heap, (alt, v))

    return dist, prev, costo_acum, dist_real_acum


# -----------------------------
# 5. Reconstruir ruta
# -----------------------------
def reconstruir_ruta(prev, origen, destino):

    if destino not in prev and destino != origen:
        return None

    ruta = [destino]
    actual = destino

    while actual != origen:

        if actual not in prev:
            return None

        actual = prev[actual]
        ruta.append(actual)

    ruta.reverse()

    return ruta


# -----------------------------
# 6. Calcular rutas desde orígenes
# -----------------------------
resultados = {}

for o in origenes:

    dist, prev, costo_acum, dist_real_acum = dijkstra(grafo, o)

    resultados[o] = {
        "dist": dist,
        "prev": prev,
        "costo": costo_acum,
        "dist_real": dist_real_acum
    }


# -----------------------------
# 7. Mostrar resultados
# -----------------------------
for o in origenes:

    print(f"\n===== ORIGEN {o} =====")

    dist_o = resultados[o]["dist"]
    prev_o = resultados[o]["prev"]
    costo_o = resultados[o]["costo"]
    dist_real_o = resultados[o]["dist_real"]

    for destino in destinos:

        if destino not in dist_o or math.isinf(dist_o[destino]):

            print(f"No hay ruta desde {o} hasta {destino}")

        else:

            ruta = reconstruir_ruta(prev_o, o, destino)

            print(f"\nDestino {destino}")
            print("Ruta:", " -> ".join(map(str, ruta)))
            print("Distancia total:", dist_real_o.get(destino))
            print("Costo total:", costo_o.get(destino))


# -----------------------------
# 8. Mejor origen por destino
# -----------------------------
print("\n=== Mejores rutas por destino (entre origen 1 y 2) ===")

for destino in destinos:

    mejor_origen = None
    mejor_dist = math.inf
    mejor_ruta = None
    mejor_distancia_real = None

    for o in origenes:

        dist_o = resultados[o]["dist"]

        if destino not in dist_o or math.isinf(dist_o[destino]):
            continue

        if dist_o[destino] < mejor_dist:

            mejor_dist = dist_o[destino]
            mejor_origen = o
            mejor_ruta = reconstruir_ruta(resultados[o]["prev"], o, destino)
            mejor_distancia_real = resultados[o]["dist_real"].get(destino)

    if mejor_origen is None:

        print(f"Destino {destino}: no hay ruta")

    else:

        print(f"\nDestino {destino}")
        print(f"Mejor origen: {mejor_origen}")
        print("Ruta:", " -> ".join(map(str, mejor_ruta)))
        print("Distancia total:", mejor_distancia_real)