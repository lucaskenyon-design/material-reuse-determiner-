
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Material Reuse Evaluator", layout="wide")
st.title("Material Reuse & Lifespan Evaluator")

# --- Baseline Data ---
region_factor = {"West": 0.80, "North": 0.85, "South": 0.95, "East": 1.00}

if "materials" not in st.session_state:
    st.session_state.materials = [
        {"Material": "Timber", "carbon": 0.40, "life": 60, "sens": 0.8, "strength": 3, "wchange": 8, "reusable": 60},
        {"Material": "Brick",  "carbon": 0.25, "life": 150, "sens": 0.3, "strength": 4, "wchange": 2, "reusable": 70},
        {"Material": "Mortar", "carbon": 0.20, "life": 60, "sens": 0.6, "strength": 2, "wchange": 10, "reusable": 20},
        {"Material": "Steel",  "carbon": 1.70, "life": 80, "sens": 0.7, "strength": 3, "wchange": 3, "reusable": 80}
    ]

# --- Sidebar Inputs ---
st.sidebar.header("Configuration")
region = st.sidebar.selectbox("Select UK Region", list(region_factor.keys()))

st.sidebar.subheader("Add / Update Material")
with st.sidebar.form("material_form", clear_on_submit=True):
    name = st.text_input("Material Name")
    carbon = st.number_input("Embodied Carbon (kgCO2e/kg)", value=0.5, step=0.1)
    life = st.number_input("Reference Life (years)", value=100, step=10)
    sens = st.slider("Weathering Sensitivity", 0.0, 1.0, 0.5, 0.1)
    strength = st.slider("Aged Strength Score (1-5)", 1, 5, 3)
    wchange = st.number_input("% Weight Change", value=5.0, step=1.0)
    reusable = st.slider("% Reusable", 0, 100, 50)
    submitted = st.form_submit_with_button("Add / Update")

if submitted and name:
    new_mat = {"Material": name, "carbon": carbon, "life": life, "sens": sens, "strength": strength, "wchange": wchange, "reusable": reusable}
    st.session_state.materials = [m for m in st.session_state.materials if m["Material"].lower() != name.lower()]
    st.session_state.materials.append(new_mat)

if st.sidebar.button("Reset to Defaults"):
    del st.session_state.materials
    st.rerun()

# --- Calculations ---
df = pd.DataFrame(st.session_state.materials)
rf = region_factor[region]
df["adj_life"] = df["life"] * rf ** df["sens"]
df["reuse_credit"] = df["carbon"] * df["reusable"] / 100
df["carbon_per_year"] = (df["carbon"] - df["reuse_credit"]) / df["adj_life"]
df["score"] = (40 * df["strength"] / 5 + 40 * df["reusable"] / 100 + 20 * (1 - (df["wchange"].abs() / 20).clip(upper=1))).round(1)
df["verdict"] = df["score"].apply(lambda s: "Viable" if s >= 70 else "Conditional" if s >= 40 else "Not viable")

# --- Main Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"Results for Region: {region}")
    st.dataframe(df[["Material", "adj_life", "carbon_per_year", "score", "verdict"]].round(3), use_container_width=True)

with col2:
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
    ax[0].bar(df["Material"], df["score"], color="#7a4b2a")
    ax[0].set_title("Reuse Viability Score")
    ax[0].set_ylim(0, 100)
    ax[1].bar(df["Material"], df["carbon_per_year"], color="#444")
    ax[1].set_title("Adjusted Carbon per Year")
    st.pyplot(fig)
