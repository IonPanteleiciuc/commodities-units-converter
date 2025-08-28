# app.py
import streamlit as st
import pandas as pd
from dataclasses import dataclass
from typing import Dict

st.set_page_config(
    page_title="Energy Unit Converter", page_icon="🔁", layout="centered"
)

# -----------------------------
# Defaults (can be overridden in Settings)
# -----------------------------
DEFAULT_MMBTU_PER_BARREL = 5.8
DEFAULT_BBL_PER_TONNE = 7.33

@dataclass(frozen=True)
class Unit:
    label: str
    to_mmbtu: float  # factor to convert 1 unit -> MMBtu

# -----------------------------
# Unit map (all conversions via MMBtu)
# -----------------------------
def unit_map(mmbtu_per_barrel: float, bbl_per_tonne: float) -> Dict[str, Unit]:
    return {
        "TBtu": Unit("TBtu", 1_000_000.0),  # 1 TBtu = 1,000,000 MMBtu
        "MMBtu": Unit("MMBtu", 1.0),
        "Mth": Unit("Mth", 100_000.0),  # 1M therms = 100,000 MMBtu
        "TWh": Unit("TWh", 3_412_141.633),  # 1 TWh = 1,000,000 MWh ≈ 3,412,141.633 MMBtu
        "MWh": Unit("MWh", 3.412141633),   # 1 MWh ≈ 3.412141633 MMBtu
        "bbl": Unit("Barrel (crude)", mmbtu_per_barrel),   # configurable
        "mt": Unit("Metric tonne (crude)", mmbtu_per_barrel * bbl_per_tonne), # tonne = bbl * MMBtu/bbl
    }

def convert(value: float, from_unit: str, to_unit: str, mmbtu_per_barrel: float, bbl_per_tonne: float) -> float:
    umap = unit_map(mmbtu_per_barrel, bbl_per_tonne)
    value_in_mmbtu = value * umap[from_unit].to_mmbtu
    return value_in_mmbtu / umap[to_unit].to_mmbtu

# ---------------- Sidebar (Settings) ----------------
st.sidebar.title("🔧 Settings")

if "precision" not in st.session_state:
    st.session_state.precision = 6
if "mmbtu_per_barrel" not in st.session_state:
    st.session_state.mmbtu_per_barrel = DEFAULT_MMBTU_PER_BARREL
if "bbl_per_tonne" not in st.session_state:
    st.session_state.bbl_per_tonne = DEFAULT_BBL_PER_TONNE

st.session_state.precision = st.sidebar.slider(
    "Display precision (digits)", 2, 10, st.session_state.precision
)
st.session_state.mmbtu_per_barrel = st.sidebar.number_input(
    "MMBtu per barrel (crude)",
    min_value=4.0,
    max_value=8.0,
    step=0.1,
    value=float(st.session_state.mmbtu_per_barrel),
    help="Typical crude range ~5.6–6.2 MMBtu/bbl."
)
st.session_state.bbl_per_tonne = st.sidebar.number_input(
    "Barrels per metric tonne (crude)",
    min_value=6.0,
    max_value=8.5,
    step=0.01,
    value=float(st.session_state.bbl_per_tonne),
    help="Typical crude range ~7.2–7.5 bbl/tonne depending on density."
)

st.sidebar.markdown("---")
st.sidebar.caption("All conversions route through **MMBtu** for consistency.")

# ---------------- Header ----------------
st.title("🔁 Energy Unit Converter")
st.caption("Convert between **metric tonnes, barrels, MWh, TWh, MMBtu, TBtu, and Mth**.")

# ---------------- Input ----------------
umap = unit_map(st.session_state.mmbtu_per_barrel, st.session_state.bbl_per_tonne)
UNITS_ORDER = ["mt", "bbl", "MWh", "TWh", "MMBtu", "TBtu", "Mth"]

value = st.number_input("Value", min_value=0.0, value=1.0, step=1.0)
from_unit = st.selectbox("From unit", UNITS_ORDER, index=0, format_func=lambda k: umap[k].label)

# ---------------- Compute ----------------
if value > 0:
    results = []
    for u in UNITS_ORDER:
        results.append({
            "Unit": u,
            "Label": umap[u].label,
            "Value": convert(value, from_unit, u, st.session_state.mmbtu_per_barrel, st.session_state.bbl_per_tonne)
        })
    df = pd.DataFrame(results)
    df["Value"] = df["Value"].map(lambda x: float(f"{x:.{st.session_state.precision}g}"))
    st.subheader("Converted Values")
    st.dataframe(df, use_container_width=True)

# ---------------- Reference ----------------
with st.expander("📘 Reference factors (via MMBtu)"):
    ref = pd.DataFrame({
        "Unit": UNITS_ORDER,
        "Label": [umap[k].label for k in UNITS_ORDER],
        "MMBtu per unit": [umap[k].to_mmbtu for k in UNITS_ORDER],
    })
    ref["MMBtu per unit"] = ref["MMBtu per unit"].map(lambda x: float(f"{x:.{st.session_state.precision}g}"))
    st.dataframe(ref, use_container_width=True)
