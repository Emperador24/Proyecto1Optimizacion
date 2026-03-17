"""
sensibilidad_rutaMasCorta.py
Análisis de Sensibilidad — Ruta Más Corta
Red Logística de Ayuda Humanitaria — Córdoba

El análisis incluye:
  1. Holgura de optimalidad: cuánto puede crecer cada arco
     de la ruta antes de que deje de ser óptima
  2. Análisis de robustez variando el criterio (α: distancia vs costo)
  3. Arcos críticos: cuáles tienen menor margen de seguridad
  4. Modificación justificada con comparación antes/después
"""

import pandas as pd
import math
import heapq
from collections import defaultdict

# ──────────────────────────────────────────────────────────
# 1. Datos
# ──────────────────────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")
df.columns = df.columns.str.strip()

origenes = [1, 2]
destinos  = [78, 79, 80]

# ──────────────────────────────────────────────────────────
# 2. Dijkstra general
# ──────────────────────────────────────────────────────────
def construir_grafo(df, alpha=0.0, dist_override=None):
    """
    alpha = 0: solo distancia geográfica
    alpha = 1: solo costo de transporte
    dist_override: dict {(i,j): nueva_distancia}
    """
    max_c = df["Costo"].max()
    max_d = df["Distancia"].max()
    grafo = defaultdict(list)
    for _, row in df.iterrows():
        i = int(row["Origen"]); j = int(row["Destino"])
        dist_ij = (dist_override or {}).get((i, j), float(row["Distancia"]))
        costo_ij = float(row["Costo"])
        cn = costo_ij / max_c
        dn = dist_ij  / max_d
        peso = alpha * cn + (1 - alpha) * dn
        grafo[i].append((j, peso, costo_ij, dist_ij))
    return grafo

def dijkstra(grafo, origen):
    todos = set(grafo.keys())
    for lst in grafo.values():
        for v, _, _, _ in lst: todos.add(v)
    dist  = {n: math.inf for n in todos}
    cost  = {n: 0.0      for n in todos}
    dreal = {n: 0.0      for n in todos}
    prev  = {}
    dist[origen] = 0.0
    heap = [(0.0, origen)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]: continue
        for v, w, c, dr in grafo.get(u, []):
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt; prev[v] = u
                cost[v]  = cost[u]  + c
                dreal[v] = dreal[u] + dr
                heapq.heappush(heap, (alt, v))
    return dist, prev, cost, dreal

def reconstruir(prev, o, d):
    if d not in prev: return None
    r = [d]; a = d
    while a != o:
        if a not in prev: return None
        a = prev[a]; r.append(a)
    return list(reversed(r))

def segunda_mejor_ruta(grafo_base, df, origen, destino, alpha=0.0):
    """
    Elimina cada arco de la ruta óptima uno a la vez y
    calcula la mejor ruta alternativa (k=2 shortest paths).
    Retorna (distancia_2da_mejor, ruta_2da_mejor, arco_critico)
    """
    g0 = construir_grafo(df, alpha)
    dist0, prev0, _, dreal0 = dijkstra(g0, origen)
    ruta0 = reconstruir(prev0, origen, destino)
    if ruta0 is None: return math.inf, None, None
    dist_opt = dreal0[destino]

    mejor_alt = math.inf
    mejor_alt_ruta = None
    arco_critico = None

    arcos_ruta = [(ruta0[k], ruta0[k+1]) for k in range(len(ruta0)-1)]
    for arc in arcos_ruta:
        # Construir grafo sin este arco
        df_tmp = df[~((df["Origen"]==arc[0])&(df["Destino"]==arc[1]))]
        g_tmp = construir_grafo(df_tmp, alpha)
        d_tmp, p_tmp, _, dr_tmp = dijkstra(g_tmp, origen)
        if dr_tmp[destino] < mejor_alt:
            mejor_alt = dr_tmp[destino]
            mejor_alt_ruta = reconstruir(p_tmp, origen, destino)
            arco_critico = arc

    return mejor_alt, mejor_alt_ruta, arco_critico


# ──────────────────────────────────────────────────────────
# 3. Solución base (α = 0, solo distancia)
# ──────────────────────────────────────────────────────────
ALPHA_BASE = 0.0
grafo_base = construir_grafo(df, ALPHA_BASE)

print("=" * 70)
print("  RUTA MÁS CORTA — SOLUCIÓN BASE  (criterio: distancia geográfica)")
print("=" * 70)

rutas_base = {}
for o in origenes:
    dist, prev, cost, dreal = dijkstra(grafo_base, o)
    for d in destinos:
        r = reconstruir(prev, o, d)
        rutas_base[(o, d)] = {
            "ruta": r, "distancia": dreal[d], "costo": cost[d]
        }
        print(f"  Origen {o} → Destino {d}:")
        print(f"    Ruta     : {' → '.join(map(str, r))}")
        print(f"    Distancia: {dreal[d]:.0f} km   Costo: {cost[d]:.0f}")

# ──────────────────────────────────────────────────────────
# 4. Mejor origen por destino
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  MEJOR ORIGEN POR DESTINO")
print("=" * 70)
print(f"\n  {'Destino':>8}  {'Mejor origen':>13}  {'Dist (km)':>10}  {'Costo':>8}  Ruta")
print("  " + "-" * 67)
for d in destinos:
    mejor = min(origenes, key=lambda o: rutas_base[(o,d)]["distancia"])
    info = rutas_base[(mejor, d)]
    ruta_str = " → ".join(map(str, info["ruta"]))
    print(f"  {d:>8}  {mejor:>13}  {info['distancia']:>10.0f}  {info['costo']:>8.0f}  {ruta_str}")

# ──────────────────────────────────────────────────────────
# 5. Holgura de optimalidad (precio sombra por arco)
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  HOLGURA DE OPTIMALIDAD — ARCOS CRÍTICOS DE CADA RUTA")
print("=" * 70)

print("""
  La holgura de un arco es la máxima distancia adicional que puede
  tener ese arco antes de que la ruta deje de ser óptima.

  Holgura = Distancia(2ª mejor ruta) − Distancia(ruta óptima)

  · Holgura pequeña → arco muy crítico (poco margen de error)
  · Holgura grande  → ruta robusta aunque el arco empeore
""")

print(f"  {'Orig→Dest':>10}  {'Dist óptima':>12}  {'2ª mejor dist':>14}  {'Holgura (km)':>13}  {'Arco crítico':>13}")
print("  " + "-" * 68)

for d in destinos:
    for o in origenes:
        info = rutas_base[(o, d)]
        d2, r2, arc_crit = segunda_mejor_ruta(grafo_base, df, o, d, ALPHA_BASE)
        holgura = d2 - info["distancia"] if d2 < math.inf else math.inf
        arc_str = f"{arc_crit[0]}→{arc_crit[1]}" if arc_crit else "N/A"
        hol_str = f"{holgura:.0f} km" if holgura < math.inf else "∞"
        print(f"  {o}→{d:>6}  {info['distancia']:>12.0f}  {d2:>14.0f}  {hol_str:>13}  {arc_str:>13}")

# ──────────────────────────────────────────────────────────
# 6. Análisis de robustez — variación de alpha
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  ANÁLISIS DE ROBUSTEZ — VARIACIÓN DEL CRITERIO (α)")
print("=" * 70)

print("""
  Se varía α de 0 (100% distancia) a 1 (100% costo).
  Si la ruta óptima cambia al variar α, existen rutas alternativas
  competitivas. Si no cambia, la solución es ROBUSTA.
""")

alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
for d in destinos:
    print(f"  Destino {d}:")
    print(f"  {'α':>6}  {'Criterio':<22}  {'Orig':>5}  {'Dist(km)':>9}  {'Costo':>7}  Ruta")
    print("  " + "-" * 72)
    ruta_anterior = None
    for alpha in alphas:
        g_a = construir_grafo(df, alpha)
        mejor_o = None; mejor_d = math.inf; mejor_info = None
        for o in origenes:
            dist_a, prev_a, cost_a, dreal_a = dijkstra(g_a, o)
            if dist_a[d] < mejor_d:
                mejor_d = dist_a[d]
                mejor_o = o
                ruta_a = reconstruir(prev_a, o, d)
                mejor_info = {"ruta": ruta_a, "distancia": dreal_a[d], "costo": cost_a[d]}

        criterio = f"{'dist pura' if alpha==0 else 'costo puro' if alpha==1 else f'mixto α={alpha}'}"
        cambio = " ← CAMBIA" if ruta_anterior and mejor_info["ruta"] != ruta_anterior else ""
        ruta_str = " → ".join(map(str, mejor_info["ruta"]))
        print(f"  {alpha:>6.2f}  {criterio:<22}  {mejor_o:>5}  "
              f"{mejor_info['distancia']:>9.0f}  {mejor_info['costo']:>7.0f}  "
              f"{ruta_str}{cambio}")
        ruta_anterior = mejor_info["ruta"]
    print()

# ──────────────────────────────────────────────────────────
# 7. Modificación justificada
# ──────────────────────────────────────────────────────────
print("=" * 70)
print("  MODIFICACIÓN JUSTIFICADA — CAMBIO DE CRITERIO A MIXTO (α = 0.4)")
print("=" * 70)

print("""
  Contexto de la modificación:
    En situaciones de emergencia humanitaria, la distancia mínima
    no siempre es el único criterio relevante. Las inundaciones
    en Córdoba también generan costos adicionales de transporte
    (combustible, mantenimiento de vehículos en vías deterioradas).
    Se justifica usar un criterio mixto que combine distancia y
    costo con α = 0.4 (40% costo, 60% distancia).
""")

alpha_mod = 0.4
g_mod = construir_grafo(df, alpha_mod)

print(f"  Comparación: α=0.0 (base) vs α={alpha_mod} (modificado)")
print(f"\n  {'Dest':>5}  {'Orig':>5}  {'Métrica':<14}  {'α=0.0 (base)':>14}  {'α='+str(alpha_mod)+' (mod)':>14}  {'Δ':>8}")
print("  " + "-" * 68)

for d in destinos:
    # Base
    info_b = min([rutas_base[(o,d)] for o in origenes], key=lambda x: x["distancia"])
    o_b = min(origenes, key=lambda o: rutas_base[(o,d)]["distancia"])

    # Modificado
    mejor_o_m = None; mejor_dm = math.inf; info_m = None
    for o in origenes:
        dist_m, prev_m, cost_m, dreal_m = dijkstra(g_mod, o)
        if dist_m[d] < mejor_dm:
            mejor_dm = dist_m[d]
            mejor_o_m = o
            info_m = {"ruta": reconstruir(prev_m, o, d),
                      "distancia": dreal_m[d], "costo": cost_m[d]}

    print(f"  {d:>5}  {o_b:>5}  {'Distancia (km)':<14}  {info_b['distancia']:>14.0f}  "
          f"{info_m['distancia']:>14.0f}  {info_m['distancia']-info_b['distancia']:>+8.0f}")
    print(f"  {d:>5}  {mejor_o_m:>5}  {'Costo':<14}  {info_b['costo']:>14.0f}  "
          f"{info_m['costo']:>14.0f}  {info_m['costo']-info_b['costo']:>+8.0f}")

    r_b_str = " → ".join(map(str, info_b["ruta"]))
    r_m_str = " → ".join(map(str, info_m["ruta"]))
    cambio = "IGUAL" if info_b["ruta"] == info_m["ruta"] else "CAMBIA"
    print(f"  {d:>5}         {'Ruta base':<14}: {r_b_str}")
    print(f"  {d:>5}         {'Ruta mod.':<14}: {r_m_str}  [{cambio}]")
    print()

print("""  Conclusión:
    · Cuando la ruta óptima NO cambia al modificar α, la solución
      es ROBUSTA: la misma ruta es buena tanto en distancia como
      en costo, lo cual es ideal para operaciones humanitarias.
    · Cuando la ruta SÍ cambia, se detecta un trade-off relevante:
      existe una ruta más corta en km pero más costosa, y el
      tomador de decisiones debe elegir según la disponibilidad
      de presupuesto vs. urgencia de la entrega.
    · En emergencias con recursos limitados, se recomienda α = 0.3-0.5
      para balancear velocidad de respuesta y eficiencia económica.
""")