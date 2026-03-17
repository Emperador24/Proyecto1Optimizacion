"""
sensibilidad_flujoMaximo.py
Análisis de Sensibilidad — Flujo Máximo
Red Logística de Ayuda Humanitaria — Córdoba

El análisis incluye:
  1. Identificación del corte mínimo (Teorema Max-Flow Min-Cut)
  2. Arcos cuello de botella y su precio sombra
  3. Escenarios de ampliación de capacidad con impacto cuantificado
  4. Modificación justificada con comparación antes/después
"""

import pandas as pd
import networkx as nx
import pulp

# ──────────────────────────────────────────────────────────
# 1. Datos
# ──────────────────────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")

origenes = [1, 2]
destinos  = [78, 79, 80]

arcos       = [(int(r["Origen"]), int(r["Destino"])) for _, r in df.iterrows()]
capacidades = {(int(r["Origen"]), int(r["Destino"])): float(r["Capacidad"]) for _, r in df.iterrows()}
nodos       = set(df["Origen"].astype(int)).union(set(df["Destino"].astype(int)))

# ──────────────────────────────────────────────────────────
# 2. Función: construir grafo y resolver flujo máximo
# ──────────────────────────────────────────────────────────
def resolver_flujo_maximo(cap_override=None, arco_extra=None):
    """
    Resuelve el flujo máximo con super-fuente S y super-sumidero T.
    cap_override: dict {(i,j): nueva_capacidad}
    arco_extra:   (i, j, capacidad) para agregar un arco nuevo
    Retorna (flujo_total, flow_dict, G)
    """
    G = nx.DiGraph()
    for (i, j) in arcos:
        cap = (cap_override or {}).get((i, j), capacidades[i, j])
        G.add_edge(i, j, capacity=cap)

    if arco_extra:
        i_e, j_e, cap_e = arco_extra
        G.add_edge(i_e, j_e, capacity=cap_e)

    G.add_node("S"); G.add_node("T")
    for o in origenes: G.add_edge("S", o, capacity=1e9)
    for d in destinos: G.add_edge(d, "T", capacity=1e9)

    flujo_total, flow_dict = nx.maximum_flow(G, "S", "T")
    return flujo_total, flow_dict, G


# ──────────────────────────────────────────────────────────
# 3. Solución base
# ──────────────────────────────────────────────────────────
flujo_base, flow_base, G_base = resolver_flujo_maximo()

print("=" * 65)
print("  FLUJO MÁXIMO — SOLUCIÓN BASE")
print("=" * 65)
print(f"  Flujo máximo total : {flujo_base:.0f} unidades")

print("\n  Despacho desde orígenes:")
for o in origenes:
    print(f"    Nodo {o}: {flow_base['S'].get(o, 0):.0f} unidades")

print("\n  Recepción en zonas afectadas:")
for d in destinos:
    rec = flow_base[d].get("T", 0)
    pct = 100 * rec / flujo_base
    print(f"    Nodo {d}: {rec:.0f} unidades  ({pct:.1f} %)")

# ──────────────────────────────────────────────────────────
# 4. Corte mínimo — Teorema Max-Flow Min-Cut
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  TEOREMA MAX-FLOW MIN-CUT — IDENTIFICACIÓN DEL CORTE MÍNIMO")
print("=" * 65)

print("""
  El Teorema Max-Flow Min-Cut establece que:
    Flujo máximo = Capacidad del corte mínimo

  El corte mínimo es el conjunto de arcos que, si se eliminan,
  desconecta completamente los orígenes de los destinos.
  Son exactamente los "cuellos de botella" que limitan el flujo.
  Ampliar cualquiera de estos arcos aumenta el flujo máximo.
""")

cut_val, (S_side, T_side) = nx.minimum_cut(G_base, "S", "T")
cut_arcs = [(u, v, G_base[u][v]["capacity"])
            for u in S_side for v in T_side
            if G_base.has_edge(u, v) and u != "S" and v != "T"]
cut_arcs.sort(key=lambda x: -x[2])

print(f"  Capacidad del corte mínimo: {cut_val:.0f}  ✓ = Flujo máximo ({flujo_base:.0f})")
print(f"\n  Arcos que forman el corte mínimo ({len(cut_arcs)} arcos):")
print(f"  {'Arco':>12}  {'Capacidad':>10}  {'% del corte':>12}")
print("  " + "-" * 40)
for u, v, cap in cut_arcs:
    pct_corte = 100 * cap / cut_val
    print(f"  {u:>5} -> {v:>3}  {cap:>10.0f}  {pct_corte:>11.1f}%")
print(f"\n  Suma total: {sum(c for _,_,c in cut_arcs):.0f}  ✓ = Flujo máximo")

# ──────────────────────────────────────────────────────────
# 5. Precio sombra por arco del corte mínimo
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  PRECIO SOMBRA — IMPACTO DE AMPLIAR CADA ARCO DEL CORTE")
print("=" * 65)

print("""
  Para cada arco del corte mínimo, se calcula cuánto aumenta el
  flujo máximo si se amplía su capacidad en 1 unidad (precio sombra = 1
  para arcos del corte; = 0 para arcos fuera del corte mínimo).
""")

print(f"  {'Arco':>12}  {'Cap actual':>10}  {'Cap +20':>8}  {'Flujo nuevo':>12}  {'Ganancia':>9}")
print("  " + "-" * 58)

for u, v, cap in cut_arcs:
    f_nuevo, _, _ = resolver_flujo_maximo(cap_override={(u, v): cap + 20})
    ganancia = f_nuevo - flujo_base
    print(f"  {u:>5} -> {v:>3}  {cap:>10.0f}  {cap+20:>8.0f}  {f_nuevo:>12.0f}  {ganancia:>+9.0f}")

# ──────────────────────────────────────────────────────────
# 6. Arcos saturados en la solución base
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  ARCOS SATURADOS (flujo = capacidad máxima)")
print("=" * 65)

saturados = []
for (i, j) in arcos:
    f_ij = flow_base.get(i, {}).get(j, 0)
    cap_ij = capacidades[i, j]
    if f_ij >= cap_ij - 1e-6 and f_ij > 1e-6:
        saturados.append((i, j, f_ij, cap_ij))
saturados.sort(key=lambda t: -t[2])

print(f"\n  Total de arcos saturados: {len(saturados)}")
print(f"\n  {'Arco':>12}  {'Flujo':>8}  {'Cap':>8}  {'En corte mínimo':>16}")
print("  " + "-" * 50)
corte_set = {(u, v) for u, v, _ in cut_arcs}
for i, j, f, cap in saturados[:12]:
    en_corte = "✓ SÍ" if (i, j) in corte_set else "No"
    print(f"  {i:>5} -> {j:>3}  {f:>8.0f}  {cap:>8.0f}  {en_corte:>16}")

# ──────────────────────────────────────────────────────────
# 7. Modificación justificada
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  MODIFICACIÓN JUSTIFICADA")
print("=" * 65)

# El arco del corte con mayor capacidad (mayor impacto al ampliarse)
u_mod, v_mod, cap_mod = cut_arcs[0]
delta_cap = 20

print(f"""
  Modificación: Ampliar la capacidad del arco {u_mod} → {v_mod}
                de {cap_mod:.0f} a {cap_mod + delta_cap:.0f} unidades (+{delta_cap})

  Justificación:
    · El arco {u_mod}→{v_mod} pertenece al corte mínimo de la red,
      lo que significa que es uno de los arcos que directamente
      limitan el flujo máximo alcanzable.
    · Su capacidad actual es {cap_mod:.0f} unidades, siendo el mayor
      arco del corte, concentrando el {100*cap_mod/cut_val:.1f}% de la
      restricción total.
    · En el contexto humanitario, estos nodos ({u_mod} y {v_mod})
      representan centros de acopio cuya conexión es crítica para
      que la ayuda fluya hacia las comunidades afectadas.
    · Ampliar esta ruta (p.ej. habilitando vías adicionales o
      incrementando la capacidad de los vehículos en ese tramo)
      produce el mayor beneficio marginal de toda la red.
""")

f_nuevo, flow_nuevo, _ = resolver_flujo_maximo(cap_override={(u_mod, v_mod): cap_mod + delta_cap})

print(f"  {'Indicador':<35}  {'ANTES':>8}  {'DESPUÉS':>9}  {'Cambio':>8}")
print("  " + "-" * 65)
print(f"  {'Flujo máximo total':<35}  {flujo_base:>8.0f}  {f_nuevo:>9.0f}  {f_nuevo-flujo_base:>+8.0f}")
for d in destinos:
    antes  = flow_base[d].get("T", 0)
    despues = flow_nuevo[d].get("T", 0)
    print(f"  {'Recepción nodo '+str(d):<35}  {antes:>8.0f}  {despues:>9.0f}  {despues-antes:>+8.0f}")
for o in origenes:
    antes  = flow_base["S"].get(o, 0)
    despues = flow_nuevo["S"].get(o, 0)
    print(f"  {'Despacho desde '+str(o):<35}  {antes:>8.0f}  {despues:>9.0f}  {despues-antes:>+8.0f}")

print(f"""
  Conclusión:
    · Al ampliar el arco {u_mod}→{v_mod} en {delta_cap} unidades de capacidad,
      el flujo máximo aumenta de {flujo_base:.0f} a {f_nuevo:.0f} unidades
      (+{f_nuevo-flujo_base:.0f} unidades adicionales de ayuda humanitaria).
    · Esto equivale a un incremento del {100*(f_nuevo-flujo_base)/flujo_base:.1f}% en la
      capacidad total de distribución de la red.
    · La inversión en este arco tiene precio sombra = {(f_nuevo-flujo_base)/delta_cap:.1f},
      es decir, cada unidad de capacidad adicional genera
      {(f_nuevo-flujo_base)/delta_cap:.1f} unidades adicionales de flujo.
""")