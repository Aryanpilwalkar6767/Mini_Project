import streamlit as st
from utils.hybrid_pipeline import HybridPipeline

# Page configuration
st.set_page_config(
    page_title="FormaLift — Informal to Formal Text Converter",
    page_icon="✍️",
    layout="centered"
)

# Load pipeline once
@st.cache_resource
def load_pipeline():
    return HybridPipeline()

st.title("✍️ FormaLift")
st.subheader("Hybrid Informal-to-Formal Text Converter")
st.write("Combines **Rule-Based Engine** + **Fine-Tuned T5-Small Transformer**")

pipeline = load_pipeline()

# User input
user_input = st.text_area(
    "Enter informal text:",
    placeholder="e.g. hey can u send me the report asap? thx",
    height=120
)

if st.button("Convert to Formal", type="primary"):
    if not user_input.strip():
        st.warning("Please enter some text to convert.")
    else:
        with st.spinner("Converting text using Hybrid Pipeline..."):
            result = pipeline.process(user_input)
            
            if result["success"]:
                st.markdown("### Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info("**Rule-Based Output**")
                    st.write(result["rule_based"])
                    
                with col2:
                    st.success("**Hybrid Output (Recommended)**")
                    st.write(result["hybrid"])
            else:
                st.error(result["error"])