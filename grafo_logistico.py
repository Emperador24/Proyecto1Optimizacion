import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -----------------------------
# 1. Leer CSV
# -----------------------------
archivo = "matriz_de_datos.csv"
df = pd.read_csv(archivo)

# -----------------------------
# 2. Crear grafo
# -----------------------------
G = nx.DiGraph()

for _, row in df.iterrows():
    G.add_edge(row["Origen"], row["Destino"])

print("Nodos:", G.number_of_nodes())
print("Aristas:", G.number_of_edges())

# -----------------------------
# 3. Definir tipos de nodos
# -----------------------------
origenes = [1,2]
destinos = [78,79,80]

intermedios = [n for n in G.nodes() if n not in origenes + destinos]

cerca_origen = []
cerca_destino = []
otros = []

for n in intermedios:

    vecinos_entrada = list(G.predecessors(n))
    vecinos_salida = list(G.successors(n))

    if any(v in origenes for v in vecinos_entrada):
        cerca_origen.append(n)

    elif any(v in destinos for v in vecinos_salida):
        cerca_destino.append(n)

    else:
        otros.append(n)

# -----------------------------
# 4. Crear posiciones
# -----------------------------
pos = {}

SEPARACION = 10   # aumentar este valor separa más los nodos

def colocar_columna(nodos, x):

    for i,node in enumerate(sorted(nodos)):

        y = -i * SEPARACION
        pos[node] = (x, y)

colocar_columna(origenes,0)
colocar_columna(cerca_origen,4)
colocar_columna(otros,8)
colocar_columna(cerca_destino,12)
colocar_columna(destinos,16)

# -----------------------------
# 5. Colores
# -----------------------------
colors = []

for node in G.nodes():

    if node in origenes:
        colors.append("green")

    elif node in destinos:
        colors.append("red")

    elif node in cerca_origen:
        colors.append("orange")

    elif node in cerca_destino:
        colors.append("purple")

    else:
        colors.append("skyblue")

# -----------------------------
# 6. Dibujar grafo
# -----------------------------
plt.figure(figsize=(24,22))

nx.draw_networkx_nodes(
    G,pos,
    node_color=colors,
    node_size=450
)

nx.draw_networkx_labels(
    G,pos,
    font_size=8
)

nx.draw_networkx_edges(
    G,pos,
    arrows=True,
    alpha=0.25,
    width=0.6
)

plt.title("Red logística de ayuda humanitaria - Inundaciones en Córdoba", fontsize=20)

plt.axis("off")
plt.show()