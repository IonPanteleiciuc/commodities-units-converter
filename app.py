# app.py
import streamlit as st
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List

st.set_page_config(
    page_title="Energy Unit Converter", page_icon="🔁", layout="centered"
)

DEFAULT_MMBTU_PER_BARREL = 5.8  # configurable in Settings


@dataclass(frozen=True)
class Unit:
    label: str
    to_mmbtu: float  # factor to convert 1 unit -> MMBtu


UNITS_ORDER = ["TBtu", "MMBtu", "Mth", "GWh", "MWh", "bbl"]


def unit_map(mmbtu_per_barrel: float) -> Dict[str, Unit]:
    return {
        "TBtu": Unit("Trillion Btu (TBtu)", 1_000_000.0),  # 1 TBtu = 1,000,000 MMBtu
        "MMBtu": Unit("Million Btu (MMBtu)", 1.0),
        "Mth": Unit(
            "Million therms (Mth)", 100_000.0
        ),  # 1 therm = 0.1 MMBtu → 1M therms = 100,000 MMBtu
        "GWh": Unit(
            "Gigawatt-hour (GWh)", 3_412.141633
        ),  # 1 GWh = 1000 MWh ≈ 3412.141633 MMBtu
        "MWh": Unit("Megawatt-hour (MWh)", 3.412141633),  # 1 MWh ≈ 3.412141633 MMBtu
        "bbl": Unit(
            "Barrel (crude)", mmbtu_per_barrel
        ),  # default 5.8 MMBtu/bbl (adjustable)
    }


def convert(
    value: float, from_unit: str, to_unit: str, mmbtu_per_barrel: float
) -> float:
    umap = unit_map(mmbtu_per_barrel)
    val_in_mmbtu = value * umap[from_unit].to_mmbtu
    return val_in_mmbtu / umap[to_unit].to_mmbtu


def parse_numbers(s: str) -> List[float]:
    parts = [p.strip() for p in s.replace(",", " ").split()]
    out = []
    for p in parts:
        try:
            out.append(float(p))
        except ValueError:
            pass
    return out


# ---------------- Sidebar (settings) ----------------
st.sidebar.title("🔧 Settings")
if "precision" not in st.session_state:
    st.session_state.precision = 6
if "mmbtu_per_barrel" not in st.session_state:
    st.session_state.mmbtu_per_barrel = DEFAULT_MMBTU_PER_BARREL

st.session_state.precision = st.sidebar.slider(
    "Display precision (digits)", 2, 10, st.session_state.precision
)
st.session_state.mmbtu_per_barrel = st.sidebar.number_input(
    "MMBtu per barrel (crude)",
    min_value=4.0,
    max_value=8.0,
    step=0.1,
    value=float(st.session_state.mmbtu_per_barrel),
    help="Typical crude range ~5.6–6.2 MMBtu/bbl.",
)

st.sidebar.markdown("---")
st.sidebar.caption("All conversions route through **MMBtu** for consistency.")

# ---------------- Header ----------------
st.title("🔁 Energy Unit Converter")
st.caption(
    "Convert between **TBtu**, **MMBtu**, **Mth**, **GWh**, **MWh**, and **bbl** (barrels)."
)

# ---------------- UI: Single & Multi-target ----------------
colU1, colU2, colSwap = st.columns([1, 1, 0.3])
umap = unit_map(st.session_state.mmbtu_per_barrel)

with colU1:
    from_unit = st.selectbox(
        "From unit",
        UNITS_ORDER,
        index=1,
        format_func=lambda k: f"{k}",
    )
with colU2:
    to_unit = st.selectbox(
        "To unit", UNITS_ORDER, index=0, format_func=lambda k: f"{k}"
    )

values_str = st.text_input(
    "Values (comma or space separated)",
    value="1",
    help="Enter one or more numbers, e.g. `1`, `10 25`, or `1, 2.5, 100`",
)
values = parse_numbers(values_str)

# Multi-target selection
targets = st.multiselect(
    "Also convert to (multi‑select)",
    options=[u for u in UNITS_ORDER if u != from_unit],
    help="Pick extra target units to compute at once.",
)
apply_all = st.checkbox("Convert to ALL units", value=False)

# ---------------- Compute ----------------
if not values:
    st.info("Enter at least one numeric value to convert.")
else:
    precision = st.session_state.precision

    # Primary conversion (from -> to)
    results_primary = []
    for v in values:
        res = convert(v, from_unit, to_unit, st.session_state.mmbtu_per_barrel)
        results_primary.append(
            {"Input": v, "From": from_unit, "To": to_unit, "Result": res}
        )

    st.subheader("Result")
    df_main = pd.DataFrame(results_primary)
    st.dataframe(
        df_main.assign(
            **{
                "Input": df_main["Input"].map(lambda x: float(f"{x:.{precision}g}")),
                "Result": df_main["Result"].map(lambda x: float(f"{x:.{precision}g}")),
            }
        ),
        use_container_width=True,
    )

    # Additional targets or ALL
    extra_units = [u for u in UNITS_ORDER if u != from_unit]
    if apply_all:
        extra_targets = extra_units
    else:
        extra_targets = targets

    if extra_targets:
        st.subheader("Additional Conversions")
        rows = []
        for v in values:
            for tgt in extra_targets:
                rows.append(
                    {
                        "Input": v,
                        "From": from_unit,
                        "To": tgt,
                        "Result": convert(
                            v, from_unit, tgt, st.session_state.mmbtu_per_barrel
                        ),
                    }
                )
        df_extra = pd.DataFrame(rows)
        st.dataframe(
            df_extra.assign(
                **{
                    "Input": df_extra["Input"].map(
                        lambda x: float(f"{x:.{precision}g}")
                    ),
                    "Result": df_extra["Result"].map(
                        lambda x: float(f"{x:.{precision}g}")
                    ),
                }
            ),
            use_container_width=True,
        )

# ---------------- Reference ----------------
with st.expander("📘 Reference factors (via MMBtu)"):
    ref = pd.DataFrame(
        {
            "Unit": UNITS_ORDER,
            "Label": [umap[k].label for k in UNITS_ORDER],
            "MMBtu per unit": [umap[k].to_mmbtu for k in UNITS_ORDER],
        }
    )
    ref["MMBtu per unit"] = ref["MMBtu per unit"].map(
        lambda x: float(f"{x:.{st.session_state.precision}g}")
    )
    st.dataframe(ref, use_container_width=True)
