import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Groundwater Salinisation Dashboard", layout="wide")

st.title("🌊 Jal Shuddhi-SAMAR")
st.write("Upload hydrochemical data to identify groundwater salinisation.")

# -------------------------
# Helper functions
# -------------------------
def mgL_to_meq(mgL, mw, charge):
    return mgL / mw * charge

def classify_salinisation(ec, cl):
    score = 0
    if ec > 1500:
        score += 50
    elif ec > 750:
        score += 25

    if cl > 250:
        score += 50
    elif cl > 100:
        score += 25

    if score >= 75:
        return "🔴 Saline", score
    elif score >= 40:
        return "🟡 Slightly Saline", score
    else:
        return "🟢 Fresh", score

def generate_overall_recommendation(df):
    status_counts = df["Salinity_Status"].value_counts(normalize=True)
    saline_frac = status_counts.get("🔴 Saline", 0)
    slight_frac = status_counts.get("🟡 Slightly Saline", 0)

    median_na_cl = df["Na_Cl"].median()
    median_cl_hco3 = df["Cl_HCO3"].median()
    max_ec = df["EC"].max()

    if saline_frac < 0.2 and slight_frac < 0.3:
        return (
            "Overall groundwater quality indicates a fresh aquifer with no significant "
            "salinisation impact. Current groundwater use is sustainable; however, "
            "periodic monitoring is recommended to detect future changes."
        )

    if saline_frac < 0.4:
        return (
            "The aquifer shows early-stage salinisation, with a mix of fresh and slightly "
            "saline samples. Preventive management measures such as regulated pumping, "
            "controlled abstraction, and regular hydrochemical monitoring are advised."
        )

    if saline_frac >= 0.4:
        if 0.85 <= median_na_cl <= 1.15:
            return (
                "A significant proportion of samples indicate salinisation with Na/Cl ratios "
                "close to unity, suggesting seawater intrusion. Immediate intervention is "
                "required, including reduction of groundwater abstraction near the coast, "
                "artificial recharge, and implementation of hydraulic control measures."
            )
        elif median_na_cl > 1.15:
            return (
                "Widespread salinisation is observed, likely influenced by evaporation and "
                "ion exchange processes. Groundwater is unsuitable for drinking purposes, "
                "and alternative water sources or blending strategies should be considered."
            )
        else:
            return (
                "The aquifer is affected by chloride-dominated salinity. Restriction of "
                "domestic usage and implementation of long-term salinity mitigation "
                "strategies are strongly recommended."
            )

    return "Insufficient data to derive an overall recommendation."

# -------------------------
# Upload section
# -------------------------
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📄 Uploaded Data Preview")
    st.dataframe(df)

    required_cols = ["Na", "Ca", "Mg", "Cl", "HCO3", "EC"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # -------------------------
    # Convert to meq/L
    # -------------------------
    df["Na_meq"] = mgL_to_meq(df["Na"], 23, 1)
    df["Ca_meq"] = mgL_to_meq(df["Ca"], 40, 2)
    df["Mg_meq"] = mgL_to_meq(df["Mg"], 24.3, 2)
    df["Cl_meq"] = mgL_to_meq(df["Cl"], 35.45, 1)
    df["HCO3_meq"] = mgL_to_meq(df["HCO3"], 61, 1)

    # -------------------------
    # Ratios
    # -------------------------
    df["Na_Cl"] = df["Na_meq"] / df["Cl_meq"]
    df["Cl_HCO3"] = df["Cl_meq"] / df["HCO3_meq"]

    # -------------------------
    # Classification
    # -------------------------
    results = df.apply(
        lambda r: classify_salinisation(r["EC"], r["Cl"]), axis=1
    )

    df["Salinity_Status"] = [r[0] for r in results]
    df["Confidence_%"] = [r[1] for r in results]

    # -------------------------
    # Results summary
    # -------------------------
    st.subheader("🧪 Salinisation Results")
    st.dataframe(df[["Salinity_Status", "Confidence_%", "Na_Cl", "Cl_HCO3"]])

    # -------------------------
    # Plots
    # -------------------------
    st.subheader("📊 Diagnostic Plots")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.scatter(df["Cl_meq"], df["Na_meq"])
        ax.plot([0, df["Cl_meq"].max()], [0, df["Cl_meq"].max()], linestyle="--")
        ax.set_xlabel("Cl (meq/L)")
        ax.set_ylabel("Na (meq/L)")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.scatter(df["HCO3_meq"], df["Cl_meq"])
        ax.set_xlabel("HCO₃ (meq/L)")
        ax.set_ylabel("Cl (meq/L)")
        st.pyplot(fig)

    # -------------------------
    # Overall Recommendation (FINAL SECTION)
    # -------------------------
    st.subheader("🧠 Overall Interpretation & Management Recommendation")
    overall_rec = generate_overall_recommendation(df)
    st.success(overall_rec)

    # -------------------------
    # Download Excel
    # -------------------------
    st.subheader("⬇️ Download Results")

    out = df.copy()
    csv = out.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Results as CSV",
        csv,
        "salinisation_results.csv",
        "text/csv",
    )

else:

    st.info("👆 Upload a hydrochemical dataset to begin.")
