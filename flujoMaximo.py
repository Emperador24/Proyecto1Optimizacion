"""
flujoMaximo.py
Modelo de Flujo Máximo — Red Logística de Ayuda Humanitaria
Maximiza el total de ayuda que puede llegar a las zonas afectadas (78, 79, 80)
desde los centros de acopio (1, 2), respetando únicamente las capacidades de cada ruta.

Formulación:
    max  Σ_{(i,j): j ∈ {78,79,80}} x_ij
    s.a.
        x_ij ≤ cap_ij                       ∀ (i,j) ∈ A      [capacidad de ruta]
        Σ_j x_{sj} - Σ_k x_{ks} ≥ 0        ∀ s ∈ {1,2}       [orígenes solo producen]
        Σ_i x_{it} - Σ_j x_{tj} ≥ 0        ∀ t ∈ {78,79,80}  [destinos solo absorben]
        Σ_i x_{in} = Σ_j x_{nj}            ∀ n intermedios    [conservación de flujo]
        x_ij ≥ 0
"""

import pandas as pd
import pulp

# ─────────────────────────────────────────
# 1. Leer datos
# ─────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")

origenes = [1, 2]
destinos = [78, 79, 80]

arcos       = [(int(r["Origen"]), int(r["Destino"])) for _, r in df.iterrows()]
capacidades = {(int(r["Origen"]), int(r["Destino"])): float(r["Capacidad"]) for _, r in df.iterrows()}
nodos       = set(df["Origen"].astype(int)).union(set(df["Destino"].astype(int)))

# ─────────────────────────────────────────
# 2. Modelo
# ─────────────────────────────────────────
modelo = pulp.LpProblem("Flujo_Maximo", pulp.LpMaximize)

x = pulp.LpVariable.dicts("flujo", arcos, lowBound=0)

# ─────────────────────────────────────────
# 3. Función objetivo: maximizar flujo total a destinos
# ─────────────────────────────────────────
modelo += (
    pulp.lpSum(x[i, j] for (i, j) in arcos if j in destinos),
    "Flujo_Total_Destinos"
)

# ─────────────────────────────────────────
# 4. Restricciones de capacidad
# ─────────────────────────────────────────
for (i, j) in arcos:
    modelo += x[i, j] <= capacidades[i, j], f"Cap_{i}_{j}"

# ─────────────────────────────────────────
# 5. Balance de flujo por tipo de nodo
# ─────────────────────────────────────────
for n in nodos:
    entrada = pulp.lpSum(x[i, j] for (i, j) in arcos if j == n)
    salida  = pulp.lpSum(x[i, j] for (i, j) in arcos if i == n)

    if n in origenes:
        # Origen: solo puede despachar (no recibe de nadie)
        modelo += salida - entrada >= 0, f"Balance_origen_{n}"
    elif n in destinos:
        # Destino: solo absorbe flujo
        modelo += entrada - salida >= 0, f"Balance_destino_{n}"
    else:
        # Nodo intermedio: todo lo que entra debe salir
        modelo += entrada == salida, f"Conservacion_{n}"

# ─────────────────────────────────────────
# 6. Resolver
# ─────────────────────────────────────────
modelo.solve(pulp.PULP_CBC_CMD(msg=0))

estado       = pulp.LpStatus[modelo.status]
flujo_maximo = pulp.value(modelo.objective)

# ─────────────────────────────────────────
# 7. Resultados
# ─────────────────────────────────────────
print("=" * 60)
print("  FLUJO MÁXIMO — RESULTADOS")
print("=" * 60)
print(f"  Estado             : {estado}")
print(f"  Flujo máximo total : {flujo_maximo:,.1f} unidades")
print("=" * 60)

print("\n  Despacho desde orígenes:\n")
for o in origenes:
    enviado = sum((x[i, j].value() or 0) for (i, j) in arcos if i == o)
    print(f"    Nodo {o}: {enviado:>8.1f} unidades despachadas")

print("\n  Recepción en zonas afectadas:\n")
for d in destinos:
    recibido = sum((x[i, j].value() or 0) for (i, j) in arcos if j == d)
    pct = 100 * recibido / flujo_maximo if flujo_maximo > 0 else 0
    print(f"    Nodo {d}: {recibido:>8.1f} unidades  ({pct:.1f} %)")

print("\n  Flujos activos (x_ij > 0):\n")
print(f"  {'Origen':>7}  {'Destino':>8}  {'Flujo':>8}  {'Cap':>8}  {'Uso%':>7}")
print("  " + "-" * 48)

flujos_activos = [(i, j, x[i, j].value()) for (i, j) in arcos if (x[i, j].value() or 0) > 1e-6]
flujos_activos.sort(key=lambda t: t[2], reverse=True)

for i, j, f in flujos_activos:
    cap = capacidades[i, j]
    uso = 100 * f / cap
    print(f"  {i:>7} -> {j:>7}   {f:>8.1f}  {cap:>8.1f}  {uso:>6.1f}%")
