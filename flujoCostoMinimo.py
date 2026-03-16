"""
flujoCostoMinimo.py
Modelo de Flujo de Costo Mínimo — Red Logística de Ayuda Humanitaria
Distribución de 500 unidades de ayuda con mínimo 20 % al nodo 80 (zona más crítica).

"""

import pandas as pd
import pulp

# ─────────────────────────────────────────
# 1. Leer datos
# ─────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")

arcos       = [(int(r["Origen"]), int(r["Destino"])) for _, r in df.iterrows()]
costos      = {(int(r["Origen"]), int(r["Destino"])): r["Costo"]     for _, r in df.iterrows()}
capacidades = {(int(r["Origen"]), int(r["Destino"])): r["Capacidad"] for _, r in df.iterrows()}
nodos       = set(df["Origen"].astype(int)).union(set(df["Destino"].astype(int)))

origenes = [1, 2]
destinos = [78, 79, 80]
DEMANDA_TOTAL   = 500
MINIMO_NODO_80  = 100    # ≥ 20 % de 500

# ─────────────────────────────────────────
# 2. Modelo PuLP
# ─────────────────────────────────────────
modelo = pulp.LpProblem("Flujo_Costo_Minimo", pulp.LpMinimize)

x = pulp.LpVariable.dicts("flujo", arcos, lowBound=0)

# ─────────────────────────────────────────
# 3. Función objetivo
# ─────────────────────────────────────────
modelo += pulp.lpSum(costos[i, j] * x[i, j] for (i, j) in arcos), "Costo_Total"

# ─────────────────────────────────────────
# 4. Restricciones de capacidad
# ─────────────────────────────────────────
for (i, j) in arcos:
    modelo += x[i, j] <= capacidades[i, j], f"Cap_{i}_{j}"

# ─────────────────────────────────────────
# 5. Oferta en orígenes
# ─────────────────────────────────────────
for o in origenes:
    salida_o = pulp.lpSum(x[i, j] for (i, j) in arcos if i == o)
    modelo += salida_o <= DEMANDA_TOTAL, f"Oferta_{o}"

# ─────────────────────────────────────────
# 6. Conservación de flujo (nodos intermedios)
# ─────────────────────────────────────────
for n in nodos:
    if n in origenes or n in destinos:
        continue
    entrada = pulp.lpSum(x[i, j] for (i, j) in arcos if j == n)
    salida  = pulp.lpSum(x[i, j] for (i, j) in arcos if i == n)
    modelo += entrada == salida, f"Conservacion_{n}"

# ─────────────────────────────────────────
# 7. Demanda total en destinos
# ─────────────────────────────────────────
modelo += (
    pulp.lpSum(x[i, j] for (i, j) in arcos if j in destinos) == DEMANDA_TOTAL,
    "Demanda_Total"
)

# ─────────────────────────────────────────
# 8. Mínimo 20 % al nodo 80
# ─────────────────────────────────────────
modelo += (
    pulp.lpSum(x[i, j] for (i, j) in arcos if j == 80) >= MINIMO_NODO_80,
    "Minimo_Nodo80"
)

# ─────────────────────────────────────────
# 9. Resolver
# ─────────────────────────────────────────
modelo.solve(pulp.PULP_CBC_CMD(msg=0))

# ─────────────────────────────────────────
# 10. Resultados
# ─────────────────────────────────────────
estado = pulp.LpStatus[modelo.status]
costo_total = pulp.value(modelo.objective)

print("=" * 60)
print("  FLUJO DE COSTO MÍNIMO — RESULTADOS")
print("=" * 60)
print(f"  Estado         : {estado}")
print(f"  Costo total    : {costo_total:,.0f}")
print(f"  Demanda total  : {DEMANDA_TOTAL} unidades")
print(f"  Mínimo nodo 80 : {MINIMO_NODO_80} unidades (20 %)")
print("=" * 60)

print("\n  Flujos activos (x_ij > 0):\n")
print(f"  {'Origen':>7}  {'Destino':>8}  {'Flujo':>8}  {'Costo_unit':>12}  {'Costo_parcial':>14}")
print("  " + "-" * 58)

flujos_activos = [(i, j, x[i, j].value()) for (i, j) in arcos if (x[i, j].value() or 0) > 1e-6]
flujos_activos.sort(key=lambda t: t[2], reverse=True)

for i, j, f in flujos_activos:
    costo_p = costos[i, j] * f
    print(f"  {i:>7} -> {j:>7}   {f:>8.1f}   {costos[i,j]:>12.1f}   {costo_p:>14.1f}")

print("\n  Resumen por nodo destino:\n")
for d in destinos:
    recibido = sum((x[i, j].value() or 0) for (i, j) in arcos if j == d)
    pct = 100 * recibido / DEMANDA_TOTAL
    print(f"    Nodo {d:>3}: {recibido:>7.1f} unidades  ({pct:.1f} %)")

print("\n  Despacho desde orígenes:\n")
for o in origenes:
    enviado = sum((x[i, j].value() or 0) for (i, j) in arcos if i == o)
    print(f"    Nodo {o:>3}: {enviado:>7.1f} unidades enviadas")
