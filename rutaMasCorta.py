"""
rutaMasCorta.py
Ruta Más Corta — Red Logística de Ayuda Humanitaria
Algoritmo de Dijkstra para encontrar la ruta de menor distancia
desde los nodos origen {1, 2} hacia los nodos destino {78, 79, 80}.

Se compara el mejor origen para cada destino y se presenta el análisis
de sensibilidad ante cambios en la ponderación distancia/costo.
"""

import pandas as pd
import math
import heapq

# ─────────────────────────────────────────
# 1. Leer datos
# ─────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")
df.columns = df.columns.str.strip()

origenes = [1, 2]
destinos = [78, 79, 80]

# ALPHA = 0  → solo distancia geográfica (km)
# ALPHA = 1  → solo costo de transporte
ALPHA = 0.0

# ─────────────────────────────────────────
# 2. Normalizar y calcular peso compuesto
# ─────────────────────────────────────────
max_costo = df["Costo"].max()
max_dist  = df["Distancia"].max()

df["costo_norm"] = df["Costo"]     / max_costo
df["dist_norm"]  = df["Distancia"] / max_dist
df["peso"]       = ALPHA * df["costo_norm"] + (1 - ALPHA) * df["dist_norm"]

# ─────────────────────────────────────────
# 3. Construir grafo
# ─────────────────────────────────────────
grafo = {}

for _, row in df.iterrows():
    i = int(row["Origen"])
    j = int(row["Destino"])
    if i not in grafo:
        grafo[i] = []
    grafo[i].append({
        "destino"  : j,
        "peso"     : float(row["peso"]),
        "costo"    : float(row["Costo"]),
        "distancia": float(row["Distancia"]),
    })

# ─────────────────────────────────────────
# 4. Algoritmo de Dijkstra generalizado
# ─────────────────────────────────────────
def dijkstra(grafo, origen):
    """
    Retorna:
        dist_min   : diccionario nodo → distancia mínima acumulada (peso compuesto)
        previo     : diccionario nodo → nodo predecesor en la ruta óptima
        costo_acum : diccionario nodo → costo real acumulado
        dist_acum  : diccionario nodo → distancia real acumulada (km)
    """
    # Obtener todos los nodos de la red
    todos = set(grafo.keys())
    for nodos_lista in grafo.values():
        for v in nodos_lista:
            todos.add(v["destino"])

    dist_min   = {n: math.inf for n in todos}
    costo_acum = {n: 0.0      for n in todos}
    dist_acum  = {n: 0.0      for n in todos}
    previo     = {}

    dist_min[origen] = 0.0
    heap = [(0.0, origen)]

    while heap:
        d_u, u = heapq.heappop(heap)

        if d_u > dist_min[u]:   # entrada obsoleta
            continue

        if u not in grafo:
            continue

        for arco in grafo[u]:
            v   = arco["destino"]
            alt = dist_min[u] + arco["peso"]

            if alt < dist_min[v]:
                dist_min[v]   = alt
                previo[v]     = u
                costo_acum[v] = costo_acum[u] + arco["costo"]
                dist_acum[v]  = dist_acum[u]  + arco["distancia"]
                heapq.heappush(heap, (alt, v))

    return dist_min, previo, costo_acum, dist_acum


# ─────────────────────────────────────────
# 5. Reconstruir ruta desde destino a origen
# ─────────────────────────────────────────
def reconstruir_ruta(previo, origen, destino):
    if destino not in previo and destino != origen:
        return None
    ruta  = [destino]
    actual = destino
    while actual != origen:
        if actual not in previo:
            return None
        actual = previo[actual]
        ruta.append(actual)
    ruta.reverse()
    return ruta


# ─────────────────────────────────────────
# 6. Calcular rutas desde cada origen
# ─────────────────────────────────────────
resultados = {}
for o in origenes:
    dist_min, previo, costo_acum, dist_acum = dijkstra(grafo, o)
    resultados[o] = {
        "dist_min"  : dist_min,
        "previo"    : previo,
        "costo"     : costo_acum,
        "distancia" : dist_acum,
    }


# ─────────────────────────────────────────
# 7. Resultados por origen
# ─────────────────────────────────────────
criterio = "Distancia (km)" if ALPHA == 0 else f"Combinado (α={ALPHA})"
print("=" * 65)
print(f"  RUTA MÁS CORTA — Criterio: {criterio}")
print("=" * 65)

for o in origenes:
    print(f"\n  ▶ ORIGEN {o}")
    print("  " + "-" * 55)
    for d in destinos:
        r = reconstruir_ruta(resultados[o]["previo"], o, d)
        dist_real = resultados[o]["distancia"].get(d, math.inf)
        costo_r   = resultados[o]["costo"].get(d, math.inf)

        if r is None or math.isinf(resultados[o]["dist_min"].get(d, math.inf)):
            print(f"    → Destino {d}: SIN RUTA DISPONIBLE")
        else:
            ruta_str = " → ".join(map(str, r))
            saltos   = len(r) - 1
            print(f"    → Destino {d}:")
            print(f"       Ruta    : {ruta_str}")
            print(f"       Nodos   : {saltos} arcos intermedios")
            print(f"       Distancia: {dist_real:.0f} km")
            print(f"       Costo   : {costo_r:.0f}")


# ─────────────────────────────────────────
# 8. Tabla comparativa — mejor origen
# ─────────────────────────────────────────
print("\n" + "=" * 65)
print("  TABLA COMPARATIVA — MEJOR ORIGEN POR DESTINO")
print("=" * 65)
print(f"  {'Destino':>8}  {'Origen':>7}  {'Dist(km)':>10}  {'Costo':>8}  {'Ruta'}")
print("  " + "-" * 62)

for d in destinos:
    mejor_origen   = None
    mejor_dist     = math.inf
    mejor_ruta_str = ""
    mejor_costo    = 0

    for o in origenes:
        dm = resultados[o]["dist_min"].get(d, math.inf)
        if dm < mejor_dist:
            mejor_dist     = dm
            mejor_origen   = o
            mejor_costo    = resultados[o]["costo"].get(d, 0)
            r = reconstruir_ruta(resultados[o]["previo"], o, d)
            mejor_ruta_str = " → ".join(map(str, r)) if r else "N/A"

    dist_real = resultados[mejor_origen]["distancia"].get(d, 0)
    print(f"  {d:>8}  {mejor_origen:>7}  {dist_real:>10.0f}  {mejor_costo:>8.0f}  {mejor_ruta_str}")

