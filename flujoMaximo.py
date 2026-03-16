import pandas as pd
import pulp

# -----------------------------
# 1. Leer datos
# -----------------------------
df = pd.read_csv("matriz_de_datos.csv")

origenes = [1, 2]
destinos = [78, 79, 80]

# -----------------------------
# 2. Preparar arcos y capacidades
# -----------------------------
arcos = [(int(row["Origen"]), int(row["Destino"])) for _, row in df.iterrows()]
capacidades = {
    (int(row["Origen"]), int(row["Destino"])): float(row["Capacidad"])
    for _, row in df.iterrows()
}
nodos = set(df["Origen"].astype(int)).union(set(df["Destino"].astype(int)))

# Demanda minima por destino (puedes cambiar estos valores)
demanda_minima_destino = {
    80: 100,
}

# -----------------------------
# 3. Crear modelo de flujo maximo
# -----------------------------
modelo = pulp.LpProblem("Flujo_Maximo", pulp.LpMaximize)

x = pulp.LpVariable.dicts("flujo", arcos, lowBound=0)

# -----------------------------
# 4. Funcion objetivo: maximizar flujo total a destinos
# -----------------------------
flujo_total_destinos = pulp.lpSum(x[i, j] for (i, j) in arcos if j in destinos)
modelo += flujo_total_destinos

# -----------------------------
# 5. Restricciones de capacidad
# -----------------------------
for (i, j) in arcos:
    modelo += x[i, j] <= capacidades[i, j]

# -----------------------------
# 6. Balance de flujo
# -----------------------------
for n in nodos:
    entrada = pulp.lpSum(x[i, j] for (i, j) in arcos if j == n)
    salida = pulp.lpSum(x[i, j] for (i, j) in arcos if i == n)

    if n in origenes:
        # Origen: puede producir flujo (salida - entrada >= 0)
        modelo += salida - entrada >= 0
    elif n in destinos:
        # Destino: puede absorber flujo (entrada - salida >= 0)
        modelo += entrada - salida >= 0
    else:
        # Nodo intermedio: conserva flujo
        modelo += entrada == salida

# -----------------------------
# 7. Restriccion de demanda minima por destino
# -----------------------------
for destino, minimo in demanda_minima_destino.items():
    flujo_a_destino = pulp.lpSum(x[i, j] for (i, j) in arcos if j == destino)
    modelo += flujo_a_destino >= minimo

# -----------------------------
# 8. Resolver
# -----------------------------
modelo.solve()

print("Estado:", pulp.LpStatus[modelo.status])
print("Valor maximo de flujo:", pulp.value(modelo.objective))

print("\nFlujos utilizados (arcos originales):\n")
for (i, j) in arcos:
    valor = x[i, j].value()
    if valor is not None and valor > 0:
        print(f"{i} -> {j} : {valor}")

print("\nDespacho desde origenes:")
for s in origenes:
    despacho = sum((x[i, j].value() or 0) for (i, j) in arcos if i == s)
    print(f"{s} : {despacho}")

print("\nRecepcion en destinos:")
for t in destinos:
    recepcion = sum((x[i, j].value() or 0) for (i, j) in arcos if j == t)
    print(f"{t} : {recepcion}")

print("\nVerificacion de demandas minimas:")
for destino, minimo in demanda_minima_destino.items():
    recibido = sum((x[i, j].value() or 0) for (i, j) in arcos if j == destino)
    print(f"Destino {destino}: recibido={recibido} minimo={minimo}")
