"""
sensibilidad_costoMinimo.py
Análisis de Sensibilidad — Flujo de Costo Mínimo
Red Logística de Ayuda Humanitaria — Córdoba

El análisis de sensibilidad determina:
  1. Precios sombra (dual values) de cada restricción activa
  2. Arcos saturados (cuellos de botella)
  3. Rangos de optimalidad: hasta dónde puede cambiar un parámetro
     antes de que la solución óptima cambie
  4. Modificación justificada con comparación antes/después
"""

import pandas as pd
import pulp

# ──────────────────────────────────────────────────────────
# 1. Datos
# ──────────────────────────────────────────────────────────
df = pd.read_csv("matriz_de_datos.csv")

origenes = [1, 2]
destinos  = [78, 79, 80]

arcos       = [(int(r["Origen"]), int(r["Destino"])) for _, r in df.iterrows()]
costos      = {(int(r["Origen"]), int(r["Destino"])): r["Costo"]     for _, r in df.iterrows()}
capacidades = {(int(r["Origen"]), int(r["Destino"])): r["Capacidad"] for _, r in df.iterrows()}
nodos       = set(df["Origen"].astype(int)).union(set(df["Destino"].astype(int)))

DEMANDA_TOTAL  = 500
MINIMO_NODO_80 = 100

# ──────────────────────────────────────────────────────────
# 2. Función: construir y resolver el modelo
# ──────────────────────────────────────────────────────────
def resolver_fcm(cap_override=None, demanda=500, min_80=100, verbose=False):
    """
    Resuelve el FCM con parámetros opcionales modificados.
    cap_override: dict {(i,j): nueva_capacidad}
    Retorna (costo_total, flujos, modelo)
    """
    caps = {k: v for k, v in capacidades.items()}
    if cap_override:
        caps.update(cap_override)

    m = pulp.LpProblem("FCM", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("f", arcos, lowBound=0)

    # Objetivo
    m += pulp.lpSum(costos[i, j] * x[i, j] for (i, j) in arcos)

    # Capacidades
    for (i, j) in arcos:
        m += x[i, j] <= caps[i, j], f"cap_{i}_{j}"

    # Oferta
    for o in origenes:
        m += pulp.lpSum(x[i, j] for (i, j) in arcos if i == o) <= demanda, f"oferta_{o}"

    # Conservación
    for n in nodos:
        if n not in origenes and n not in destinos:
            ent = pulp.lpSum(x[i, j] for (i, j) in arcos if j == n)
            sal = pulp.lpSum(x[i, j] for (i, j) in arcos if i == n)
            m += ent == sal, f"cons_{n}"

    # Demanda total
    m += pulp.lpSum(x[i, j] for (i, j) in arcos if j in destinos) == demanda, "demanda_total"

    # Mínimo nodo 80
    m += pulp.lpSum(x[i, j] for (i, j) in arcos if j == 80) >= min_80, "min_80"

    m.solve(pulp.PULP_CBC_CMD(msg=0))

    costo = pulp.value(m.objective)
    flujos = {(i, j): (x[i, j].value() or 0) for (i, j) in arcos}
    return costo, flujos, m


# ──────────────────────────────────────────────────────────
# 3. Solución base
# ──────────────────────────────────────────────────────────
costo_base, flujos_base, modelo_base = resolver_fcm()

print("=" * 65)
print("  FLUJO DE COSTO MÍNIMO — SOLUCIÓN BASE")
print("=" * 65)
print(f"  Estado        : {pulp.LpStatus[modelo_base.status]}")
print(f"  Costo total   : {costo_base:,.2f}")
print(f"  Demanda total : {DEMANDA_TOTAL} unidades")
print(f"  Mínimo nodo 80: {MINIMO_NODO_80} unidades (20 %)")

print("\n  Recepción por destino:")
for d in destinos:
    rec = sum(flujos_base[i, j] for (i, j) in arcos if j == d)
    print(f"    Nodo {d}: {rec:.1f} unidades  ({100*rec/DEMANDA_TOTAL:.1f} %)")

# ──────────────────────────────────────────────────────────
# 4. Precios sombra (dual values)
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  ANÁLISIS DE SENSIBILIDAD — PRECIOS SOMBRA")
print("=" * 65)

print("""
  El precio sombra (π) de una restricción indica cuánto cambia
  el costo total óptimo si se relaja esa restricción en 1 unidad.
    · π < 0 → relajar la restricción REDUCE el costo (favorable)
    · π > 0 → relajar la restricción AUMENTA el costo
    · π = 0 → restricción holgada (no está activa)
""")

restricciones_clave = {
    "demanda_total": "Demanda total (500 unidades)",
    "min_80":        "Mínimo nodo 80 (≥ 100 unidades)",
    "oferta_1":      "Oferta máxima nodo 1 (≤ 500)",
    "oferta_2":      "Oferta máxima nodo 2 (≤ 500)",
}

print(f"  {'Restricción':<35}  {'Precio sombra':>14}  {'Interpretación'}")
print("  " + "-" * 62)
for nombre, desc in restricciones_clave.items():
    c = modelo_base.constraints.get(nombre)
    if c is not None and c.pi is not None:
        pi = c.pi
        interp = (f"Cada unidad adicional de demanda cuesta {abs(pi):.2f} más"
                  if nombre == "demanda_total"
                  else f"Relajar 1 unidad {'reduce' if pi<0 else 'aumenta'} el costo en {abs(pi):.2f}")
        print(f"  {desc:<35}  {pi:>14.4f}  {interp}")

# ──────────────────────────────────────────────────────────
# 5. Arcos saturados (cuellos de botella)
# ──────────────────────────────────────────────────────────
saturados = [(i, j, flujos_base[i, j], capacidades[i, j], costos[i, j])
             for (i, j) in arcos
             if flujos_base[i, j] >= capacidades[i, j] - 1e-6
             and flujos_base[i, j] > 1e-6]
saturados.sort(key=lambda t: -t[2])

print(f"\n  Arcos saturados (flujo = capacidad máxima): {len(saturados)}")
print(f"  → Son los cuellos de botella de la red logística")
print(f"\n  {'Arco':>12}  {'Flujo':>7}  {'Cap':>6}  {'Costo_unit':>10}  {'Costo_parcial':>13}")
print("  " + "-" * 55)
for i, j, f, cap, c in saturados[:10]:
    print(f"  {i:>5} -> {j:>3}  {f:>7.1f}  {cap:>6.1f}  {c:>10.1f}  {f*c:>13.1f}")

# ──────────────────────────────────────────────────────────
# 6. Rangos de optimalidad — restricción mínimo nodo 80
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  RANGOS DE OPTIMALIDAD — RESTRICCIÓN MÍNIMO NODO 80")
print("=" * 65)

print("""
  ¿Hasta qué valor puede variar el mínimo exigido al nodo 80
  antes de que el costo total cambie significativamente?
""")

print(f"  {'Mínimo nodo 80':>18}  {'Costo total':>12}  {'Δ vs base':>10}  {'Estado'}")
print("  " + "-" * 52)

for min_val in [0, 50, 80, 100, 120, 150, 200]:
    try:
        c_val, _, m_val = resolver_fcm(min_80=min_val)
        estado = pulp.LpStatus[m_val.status]
        delta = c_val - costo_base if estado == "Optimal" else float("nan")
        marker = " ← BASE" if min_val == 100 else ""
        print(f"  {min_val:>18}  {c_val:>12,.2f}  {delta:>+10.2f}  {estado}{marker}")
    except Exception:
        print(f"  {min_val:>18}  {'INFEASIBLE':>12}")

print("""
  Interpretación:
  → El precio sombra de la restricción min_80 indica el costo
    marginal de exigir una unidad más al nodo 80.
  → Si el mínimo requerido es demasiado alto, el modelo puede
    volverse inviable (infeasible) por falta de capacidad.
""")

# ──────────────────────────────────────────────────────────
# 7. Modificación justificada — Ampliar arco más saturado
# ──────────────────────────────────────────────────────────
print("=" * 65)
print("  MODIFICACIÓN JUSTIFICADA — AMPLIAR CAPACIDAD CUELLO DE BOTELLA")
print("=" * 65)

# El arco saturado de mayor flujo
i_mod, j_mod, f_mod, cap_mod, c_mod = saturados[0]
nueva_cap = cap_mod + 30

print(f"""
  Arco seleccionado para modificación: {i_mod} → {j_mod}
  Justificación:
    · Es el arco con mayor flujo saturado ({f_mod:.0f} unidades = {cap_mod:.0f} cap. máxima)
    · Toda su capacidad está siendo utilizada: uso = 100%
    · Ampliar su capacidad permite redistribuir el flujo por
      rutas más económicas que actualmente están bloqueadas
    · En contexto humanitario, este arco es crítico porque
      concentra el mayor volumen de ayuda en tránsito

  Parámetro modificado: capacidad {i_mod}→{j_mod}: {cap_mod:.0f} → {nueva_cap:.0f} (+30 unidades)
""")

costo_mod, flujos_mod, modelo_mod = resolver_fcm(cap_override={(i_mod, j_mod): nueva_cap})

print(f"  {'Indicador':<35}  {'ANTES':>10}  {'DESPUÉS':>10}  {'Cambio':>10}")
print("  " + "-" * 68)
print(f"  {'Costo total':<35}  {costo_base:>10,.2f}  {costo_mod:>10,.2f}  {costo_mod-costo_base:>+10.2f}")

for d in destinos:
    r_antes  = sum(flujos_base[i, j] for (i, j) in arcos if j == d)
    r_despues = sum(flujos_mod[i, j]  for (i, j) in arcos if j == d)
    print(f"  {'Recepción nodo '+str(d):<35}  {r_antes:>10.1f}  {r_despues:>10.1f}  {r_despues-r_antes:>+10.1f}")

print(f"""
  Conclusión:
    · Al ampliar la capacidad del arco {i_mod}→{j_mod} en 30 unidades,
      el costo total {'disminuye' if costo_mod < costo_base else 'no cambia significativamente'}.
    · La modificación {'es favorable' if costo_mod < costo_base else 'confirma que este arco no es el único cuello de botella'}.
    · En términos operativos: habilitar mayor capacidad en este
      tramo de la red reduce el costo de distribución de ayuda
      humanitaria, permitiendo atender más comunidades con el
      mismo presupuesto.
""")