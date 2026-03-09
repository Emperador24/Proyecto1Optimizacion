import pandas as pd
import pulp

# -----------------------------
# 1. Leer datos
# -----------------------------
df = pd.read_csv("matriz_de_datos.csv")

arcos = list(zip(df["Origen"], df["Destino"]))

costos = {(row["Origen"], row["Destino"]): row["Costo"] for _,row in df.iterrows()}
capacidades = {(row["Origen"], row["Destino"]): row["Capacidad"] for _,row in df.iterrows()}

nodos = set(df["Origen"]).union(set(df["Destino"]))

# -----------------------------
# 2. Crear modelo
# -----------------------------
model = pulp.LpProblem("Flujo_Costo_Minimo", pulp.LpMinimize)

# -----------------------------
# 3. Variables de flujo
# -----------------------------
x = pulp.LpVariable.dicts(
    "flujo",
    arcos,
    lowBound=0
)

# -----------------------------
# 4. Función objetivo
# -----------------------------
model += pulp.lpSum(
    costos[i,j] * x[i,j]
    for (i,j) in arcos
)

# -----------------------------
# 5. Restricción de capacidad
# -----------------------------
for (i,j) in arcos:
    model += x[i,j] <= capacidades[i,j]

# -----------------------------
# 6. Balance de flujo
# -----------------------------

origenes = [1,2]
destinos = [78,79,80]

oferta_total = 500

# Orígenes
model += pulp.lpSum(x[1,j] for (i,j) in arcos if i==1) <= oferta_total
model += pulp.lpSum(x[2,j] for (i,j) in arcos if i==2) <= oferta_total

# Nodos intermedios
for n in nodos:
    if n not in origenes and n not in destinos:

        entrada = pulp.lpSum(x[i,j] for (i,j) in arcos if j==n)
        salida = pulp.lpSum(x[i,j] for (i,j) in arcos if i==n)

        model += entrada == salida

# -----------------------------
# 7. Flujo total a destinos
# -----------------------------
flujo_destinos = pulp.lpSum(
    x[i,j] for (i,j) in arcos if j in destinos
)

model += flujo_destinos == 500

# -----------------------------
# 8. 20% mínimo al nodo 80
# -----------------------------
flujo_80 = pulp.lpSum(
    x[i,j] for (i,j) in arcos if j==80
)

model += flujo_80 >= 100

# -----------------------------
# 9. Resolver modelo
# -----------------------------
model.solve()

print("Estado:", pulp.LpStatus[model.status])

# -----------------------------
# 10. Resultados
# -----------------------------
print("\nFlujos utilizados:\n")

for (i,j) in arcos:
    if x[i,j].value() > 0:
        print(f"{i} -> {j} : {x[i,j].value()}")

print("\nCosto total:", pulp.value(model.objective))