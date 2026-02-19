import io
import pandas as pd
import streamlit as st
from wtw.scorer import get_feature_guide, score_all, write_output

st.set_page_config(page_title="Words Their Way Scorer", page_icon="📝", layout="centered")

st.title("Words Their Way Scorer")
st.markdown("Upload a student spelling test workbook, choose a feature guide, and download scored results.")

# --- Level selection ---
level_labels = {
    "Primary (K–1)": "primary",
    "Elementary (K–2)": "elementary",
    "Upper Level (Grades 3–7+)": "upper-level",
}
level_label = st.radio("Feature guide level", list(level_labels.keys()))
level = level_labels[level_label]

# --- File upload ---
uploaded_file = st.file_uploader("Upload spelling test workbook (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        test = pd.read_excel(uploaded_file)
        test = test.rename(columns={"name": "feature"}).set_index("feature")
        st.success(f"Loaded **{uploaded_file.name}** — {len(test.columns)} student(s) detected.")
        st.write("Students found:", list(test.columns))
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    if st.button("Score workbook", type="primary"):
        result = get_feature_guide(level)
        if result is None:
            st.error("Failed to load feature guide.")
            st.stop()
        _, feature_guide = result

        with st.spinner("Scoring..."):
            results = score_all(level, feature_guide, test)

        if results is None:
            st.error("Scoring failed — one or more students are missing required features.")
            st.stop()

        # Summary table
        st.subheader("Results")
        summary = pd.DataFrame([[r[0], r[1]] for r in results], columns=["Name", "Learning Stage"])
        st.dataframe(summary, use_container_width=True, hide_index=True)

        # Write output to in-memory buffer
        buffer = io.BytesIO()
        write_output(buffer, results)
        buffer.seek(0)

        out_name = uploaded_file.name.rsplit(".", 1)[0] + "_output.xlsx"
        st.download_button(
            label="Download scored workbook",
            data=buffer,
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
