"""
Rebanada delgada #1 - Gestor de insumos y descartables médicos
Pregunta: ¿qué 10 descartables médicos pasaron más días sin stock en Farmacia Central
entre el 01/10/2025 y el 30/09/2026?

Entrada (base de trabajo basada en exportaciones de Geclisa, carpeta data/raw):
  - MEDICACION_Y_DESCARTABLE.xlsx : movimientos de stock de 12 meses
  - stock_al_01102025.xlsx        : saldo de cada insumo al 01/10/2025
Salida (carpeta output/):
  - dias_sin_stock_descartables.csv : métricas por insumo
  - top10_dias_sin_stock.png        : gráfico de barras del top 10
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RAW = Path("data/raw")
OUT = Path("output")
OUT.mkdir(exist_ok=True)

INICIO, FIN = "2025-10-01", "2026-09-30"
FARMACIA_CENTRAL = 1          # id del depósito en Geclisa
MIN_MESES_CON_CONSUMO = 6     # criterio de "insumo activo"

# 1. Extracción: solo las columnas necesarias para el análisis.
mov = pd.read_excel(
    RAW / "MEDICACION_Y_DESCARTABLE.xlsx",
    usecols=["ELE_NOMBRE", "FECHA", "CAN", "DEP_IDORIG", "DEP_IDDEST", "TE_NOMBRE"],
)
saldo_ini = pd.read_excel(RAW / "stock_al_01102025.xlsx", usecols=["ele_cod", "saldo"])
saldo_ini = saldo_ini.rename(columns={"ele_cod": "cod", "saldo": "saldo_inicial"})

# 2. Preparación: separar código y nombre ("20114 - GUANTE ESTERIL ...")
mov[["cod", "nombre"]] = mov["ELE_NOMBRE"].str.split(" - ", n=1, expand=True)
mov["cod"] = mov["cod"].astype(int)
mov["nombre"] = mov["nombre"].str.strip(" -")

# Signo del movimiento visto desde Farmacia Central:
# sale de Farmacia Central -> egreso (-), entra a Farmacia Central -> ingreso (+)
mov["signo"] = 0
mov.loc[mov["DEP_IDORIG"] == FARMACIA_CENTRAL, "signo"] = -1
mov.loc[(mov["DEP_IDORIG"] == 0) & (mov["DEP_IDDEST"] == FARMACIA_CENTRAL), "signo"] = 1
mov["cantidad"] = mov["CAN"] * mov["signo"]

# Validaciones mínimas (DoD)
assert mov["FECHA"].notna().all(), "Hay movimientos sin fecha"
assert (mov["CAN"] > 0).all(), "Hay cantidades en cero o negativas"
assert set(mov["cod"]) <= set(saldo_ini["cod"]), "Hay insumos sin saldo inicial"

# JBGE: solo descartables
desc = mov[mov["TE_NOMBRE"] == "Descartable"]

# Insumo activo = tuvo egresos en al menos 6 de los 12 meses
egresos = desc[desc["signo"] == -1]
meses_con_consumo = egresos.groupby("cod")["FECHA"].apply(lambda f: f.dt.to_period("M").nunique())
activos = meses_con_consumo[meses_con_consumo >= MIN_MESES_CON_CONSUMO].index

# 3. Modelado: reconstruir el stock al cierre de cada día y contar días en cero
dias = pd.date_range(INICIO, FIN, freq="D")
neto_diario = (
    desc[desc["cod"].isin(activos)]
    .groupby(["cod", "FECHA"])["cantidad"].sum()
    .unstack("cod").reindex(dias, fill_value=0).fillna(0)
)
stock_diario = neto_diario.cumsum() + saldo_ini.set_index("cod").loc[neto_diario.columns, "saldo_inicial"]
# Validación: Geclisa no permite descargar sin stock, el saldo nunca puede ser negativo
assert (stock_diario >= 0).all().all(), "Hay saldos negativos: revisar la base"
sin_stock = stock_diario == 0

resumen = pd.DataFrame({
    "dias_sin_stock": sin_stock.sum(),
    "episodios": (sin_stock & ~sin_stock.shift(fill_value=False)).sum(),
})
resumen["consumo_anual"] = -egresos.groupby("cod")["cantidad"].sum()
resumen["consumo_mensual_prom"] = (resumen["consumo_anual"] / 12).round(1)
resumen = resumen.join(desc.groupby("cod")["nombre"].first()).sort_values("dias_sin_stock", ascending=False)
resumen.to_csv(OUT / "dias_sin_stock_descartables.csv")

# 4. Evaluación: cifras de control
print(f"Descartables activos analizados: {len(resumen)}")
print(f"Con al menos un día sin stock: {(resumen['dias_sin_stock'] > 0).sum()}")
print(resumen.head(10)[["nombre", "dias_sin_stock", "episodios", "consumo_mensual_prom"]].to_string())

# Gráfico del top 10
top = resumen.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(top["nombre"].str.slice(0, 45), top["dias_sin_stock"], color="#D9480F", height=0.6)
for y, v in enumerate(top["dias_sin_stock"]):
    ax.text(v + 2, y, f"{v} días", va="center", fontsize=9)
ax.set_xlabel("Días con stock en cero (01/10/2025 - 30/09/2026)")
ax.set_title("Top 10 descartables con más días sin stock en Farmacia Central", loc="left")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "top10_dias_sin_stock.png", dpi=200)
