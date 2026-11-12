import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="NIST CSF 2.0 Assessment Tool", layout="wide")

st.title("🛡️ Student Org NIST CSF 2.0 Risk Dashboard")
st.subheader("Interactive Governance, Risk & Remediation Simulator")

# 1. File Uploader or Default Load
st.sidebar.header("📂 1. Data Source")
uploaded_file = st.sidebar.file_uploader("Upload your completed Excel (.xlsx)", type=["xlsx"])

@st.cache_data
def load_default_data():
    return pd.read_excel("nist_assessment.xlsx", sheet_name="Assessment")

try:
    if uploaded_file is not None:
        raw_df = pd.read_excel(uploaded_file, sheet_name="Assessment")
    else:
        raw_df = load_default_data()

    # Ensure Rating is integer
    raw_df["Rating"] = raw_df["Rating"].astype(int)

    # 2. Interactive "What-If" Remediation Simulator in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ 2. Remediation Simulator")
    st.sidebar.caption("Toggle controls below to simulate how fixing gaps improves overall maturity:")

    simulated_df = raw_df.copy()
    low_controls = simulated_df[simulated_df["Rating"] < 3]

    for idx, row in low_controls.iterrows():
        label = f"Remediate {row['Subcategory ID']} (Current: {row['Rating']})"
        if st.sidebar.checkbox(label, key=f"sim_{idx}"):
            simulated_df.at[idx, "Rating"] = 3
            simulated_df.at[idx, "Evidence & Notes"] = "✅ [SIMULATED FIX] Control upgraded to Level 3."

    # 3. Filter Controls
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 3. Filter View")
    selected_function = st.sidebar.multiselect(
        "Filter by NIST Function:",
        options=simulated_df["Function"].unique(),
        default=simulated_df["Function"].unique()
    )

    filtered_df = simulated_df[simulated_df["Function"].isin(selected_function)]

    # 4. Overall Maturity Metrics with Deltas
    orig_avg = raw_df["Rating"].mean()
    sim_avg = simulated_df["Rating"].mean()
    delta_avg = sim_avg - orig_avg

    orig_pct = (raw_df["Rating"].sum() / (len(raw_df) * 3)) * 100
    sim_pct = (simulated_df["Rating"].sum() / (len(simulated_df) * 3)) * 100
    delta_pct = sim_pct - orig_pct

    col1, col2, col3 = st.columns(3)
    col1.metric("Controls Evaluated", len(simulated_df))
    col2.metric(
        "Average Maturity Score (0-3)", 
        f"{sim_avg:.2f}", 
        delta=f"{delta_avg:+.2f}" if delta_avg != 0 else None
    )
    col3.metric(
        "Overall Security Posture", 
        f"{sim_pct:.1f}%", 
        delta=f"{delta_pct:+.1f}%" if delta_pct != 0 else None
    )

    st.markdown("---")

    # 5. Interactive Tabs for Clean Presentation
    tab1, tab2, tab3 = st.tabs(["📊 Function Chart & Heatmap", "📝 Live Editable Table", "🚨 Priority Action Items"])

    with tab1:
        st.subheader("Maturity Score by NIST Function")
        func_scores = simulated_df.groupby("Function")["Rating"].mean().reset_index()
        st.bar_chart(data=func_scores, x="Function", y="Rating", color="#2e7bcf")

        st.subheader("Detailed Control Assessment")
        def highlight_scores(val):
            if val == 0:
                return 'background-color: #ff9999; color: black;'
            elif val == 1:
                return 'background-color: #ffcc99; color: black;'
            elif val == 2:
                return 'background-color: #ffff99; color: black;'
            elif val == 3:
                return 'background-color: #99ff99; color: black;'
            return ''

        st.dataframe(
            filtered_df.style.map(highlight_scores, subset=["Rating"]),
            use_container_width=True
        )

    with tab2:
        st.subheader("Interactive Assessment Editor")
        st.info("You can directly edit ratings (0-3) or update evidence notes in the table below during your live presentation.")
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "Rating": st.column_config.NumberColumn(
                    "Rating (0-3)",
                    min_value=0,
                    max_value=3,
                    step=1,
                )
            },
            use_container_width=True,
            num_rows="fixed"
        )
        # Download updated CSV
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Updated Assessment (CSV)",
            data=csv,
            file_name="updated_nist_assessment.csv",
            mime="text/csv"
        )

    with tab3:
        st.subheader("Critical & High-Risk Gaps (Rated 0 or 1)")
        critical_gaps = simulated_df[simulated_df["Rating"] <= 1]

        if not critical_gaps.empty:
            for idx, row in critical_gaps.iterrows():
                with st.expander(f"🔴 [{row['Subcategory ID']}] {row['Subcategory Description']} — Rating: {row['Rating']}", expanded=True):
                    st.write(f"**Audit Evidence:** {row['Evidence & Notes']}")
        else:
            st.success("🎉 All critical gaps have been remediated! Every control is rated 2 or higher.")

except Exception as e:
    st.warning("👋 Welcome! Please upload your completed `nist_assessment.xlsx` file using the sidebar on the left (or ensure it is in the app folder).")
    st.info("Expected Excel sheet name: `Assessment` | Expected columns: `Function`, `Subcategory ID`, `Subcategory Description`, `Rating`, `Evidence & Notes`")
