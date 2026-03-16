import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

df = pd.read_csv("matriz_de_datos.csv")
G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_edge(row["Origen"], row["Destino"])

origenes = [1, 2]
destinos = [78, 79, 80]
intermedios = [n for n in G.nodes() if n not in origenes + destinos]

cerca_origen  = []
cerca_destino = []
otros         = []

for n in intermedios:
    preds = list(G.predecessors(n))
    succs = list(G.successors(n))
    if any(v in origenes for v in preds):
        cerca_origen.append(n)
    elif any(v in destinos for v in succs):
        cerca_destino.append(n)
    else:
        otros.append(n)

# ── Separación proporcional: todas las columnas ocupan la misma altura total ──
SEP_ORIGEN   = 5.0
SEP_DESTINO  = 5.0
altura_max   = max((len(origenes) - 1) * SEP_ORIGEN, (len(destinos) - 1) * SEP_DESTINO)

SEP_CERCA_ORIGEN  = altura_max / max(len(cerca_origen) - 1,  1)
SEP_OTROS         = altura_max / max(len(otros) - 1,         1)
SEP_CERCA_DESTINO = altura_max / max(len(cerca_destino) - 1, 1)

pos = {}

def colocar_columna_centrada(nodos, x, sep):
    nodos = sorted(nodos)
    n = len(nodos)
    for i, node in enumerate(nodos):
        y = ((n - 1) / 2.0 - i) * sep
        pos[node] = (x, y)

colocar_columna_centrada(origenes,      x=0,  sep=SEP_ORIGEN)
colocar_columna_centrada(cerca_origen,  x=4,  sep=SEP_CERCA_ORIGEN)
colocar_columna_centrada(otros,         x=8,  sep=SEP_OTROS)
colocar_columna_centrada(cerca_destino, x=12, sep=SEP_CERCA_DESTINO)
colocar_columna_centrada(destinos,      x=16, sep=SEP_DESTINO)

# ── Colores ──
COLOR = {
    "origen":        "#27ae60",
    "cerca_origen":  "#e67e22",
    "otros":         "#2980b9",
    "cerca_destino": "#8e44ad",
    "destino":       "#c0392b",
}

def color_nodo(n):
    if n in origenes:      return COLOR["origen"]
    if n in destinos:      return COLOR["destino"]
    if n in cerca_origen:  return COLOR["cerca_origen"]
    if n in cerca_destino: return COLOR["cerca_destino"]
    return COLOR["otros"]

colores_nodos = [color_nodo(n) for n in G.nodes()]
sizes = [1100 if n in origenes + destinos else 480 for n in G.nodes()]

# ── Aristas ──
aristas_desde_origen  = [(u, v) for u, v in G.edges() if u in origenes]
aristas_hacia_destino = [(u, v) for u, v in G.edges() if v in destinos]
aristas_resto         = [(u, v) for u, v in G.edges()
                         if (u, v) not in aristas_desde_origen
                         and (u, v) not in aristas_hacia_destino]

# ── Figura ──
fig, ax = plt.subplots(figsize=(26, 26))
fig.patch.set_facecolor("white")
ax.set_facecolor("#f8f9fa")

y_vals = [y for _, y in pos.values()]
y_min_v = min(y_vals)
y_max_v = max(y_vals)

# Franjas
for xf, cf in [(0, COLOR["origen"]), (4, COLOR["cerca_origen"]),
               (8, COLOR["otros"]), (12, COLOR["cerca_destino"]),
               (16, COLOR["destino"])]:
    ax.axvspan(xf - 1.5, xf + 1.5, ymin=0, ymax=1,
               color=cf, alpha=0.07, zorder=0)

# Aristas
nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_resto,
    arrows=True, arrowsize=7, alpha=0.18, width=0.5,
    edge_color="#666666", connectionstyle="arc3,rad=0.02")
nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_desde_origen,
    arrows=True, arrowsize=10, alpha=0.55, width=1.2,
    edge_color=COLOR["cerca_origen"], connectionstyle="arc3,rad=0.02")
nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_hacia_destino,
    arrows=True, arrowsize=10, alpha=0.55, width=1.2,
    edge_color=COLOR["destino"], connectionstyle="arc3,rad=0.02")

# Nodos y etiquetas
nx.draw_networkx_nodes(G, pos, ax=ax,
    node_color=colores_nodos, node_size=sizes,
    linewidths=1.5, edgecolors="white")
nx.draw_networkx_labels(G, pos, ax=ax,
    font_size=7, font_color="white", font_weight="bold")

# ── Encabezados ──
ESPACIO_ENCABEZADO = 1.5
headers = [
    (0,  "CENTROS DE\nACOPIO",         f"Nodos 1 y 2\n({len(origenes)} nodos)",                        COLOR["origen"]),
    (4,  "NODOS PRÓXIMOS\nAL ORIGEN",  f"Conectados directamente\n({len(cerca_origen)} nodos)",         COLOR["cerca_origen"]),
    (8,  "CENTROS\nINTERMEDIOS",       f"Redistribución y tránsito\n({len(otros)} nodos)",               COLOR["otros"]),
    (12, "NODOS PRÓXIMOS\nAL DESTINO", f"Última etapa antes\nde entrega ({len(cerca_destino)} nodos)",   COLOR["cerca_destino"]),
    (16, "ZONAS\nAFECTADAS",           f"Comunidades damnificadas\nNodos 78 · 79 · 80",                 COLOR["destino"]),
]

for xh, titulo, subtitulo, color in headers:
    ax.text(xh, y_max_v + ESPACIO_ENCABEZADO, titulo,
            ha="center", va="bottom", fontsize=10, fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor=color, linewidth=2, alpha=0.95))
    ax.text(xh, y_max_v + ESPACIO_ENCABEZADO - 0.25, subtitulo,
            ha="center", va="top", fontsize=8, color="#555555")

# ── Leyenda ──
leyenda = [
    mpatches.Patch(color=COLOR["origen"],        label="Centros de acopio (1, 2)"),
    mpatches.Patch(color=COLOR["cerca_origen"],  label=f"Nodos próximos al origen ({len(cerca_origen)})"),
    mpatches.Patch(color=COLOR["otros"],         label=f"Centros intermedios ({len(otros)})"),
    mpatches.Patch(color=COLOR["cerca_destino"], label=f"Nodos próximos al destino ({len(cerca_destino)})"),
    mpatches.Patch(color=COLOR["destino"],       label="Zonas afectadas (78, 79, 80)"),
    Line2D([0],[0], color=COLOR["cerca_origen"], lw=1.5, alpha=0.7, label="Rutas desde orígenes"),
    Line2D([0],[0], color=COLOR["destino"],      lw=1.5, alpha=0.7, label="Rutas hacia destinos"),
    Line2D([0],[0], color="#666666",             lw=0.8, alpha=0.5,
           label=f"Rutas intermedias ({G.number_of_edges()} arcos total)"),
]
ax.legend(handles=leyenda, loc="lower left", fontsize=9,
          framealpha=0.95, facecolor="white", edgecolor="#cccccc",
          title="Leyenda", title_fontsize=10, borderpad=0.8, labelspacing=0.5)

# ── Título y estadísticas ──
ax.set_title(
    "Red Logística de Ayuda Humanitaria\n"
    "Inundaciones en el departamento de Córdoba — Río Sinú",
    fontsize=16, fontweight="bold", color="#2c3e50", pad=20)

stats = (f"Nodos: {G.number_of_nodes()}  ·  Arcos: {G.number_of_edges()}  ·  "
         f"Orígenes: 2  ·  Destinos: 3  ·  Intermedios: {len(intermedios)}")
ax.text(0.5, -0.01, stats, transform=ax.transAxes,
        ha="center", va="top", fontsize=8.5, color="#777777")

ax.set_xlim(-2.5, 18.5)
ax.set_ylim(y_min_v - 1.5, y_max_v + 4.5)
ax.axis("off")
plt.tight_layout(pad=1.5)

plt.savefig("grafo_logistico.png", dpi=180, bbox_inches="tight", facecolor="white")
plt.show()
print("[✓] Grafo guardado en 'grafo_logistico.png'")