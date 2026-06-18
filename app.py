import json
import re
from pathlib import Path

import streamlit as st

# -- page setup: title in the browser tab + page heading --
st.set_page_config(page_title="MapleVitals", page_icon="🍁")
st.title("🍁 MapleVitals")
st.caption(
    "An AI agent that turns questions about Canadian health data into charts "
    "and plain-language interpretation. Data: CCHS, StatCan table 13-10-0905-01."
)

# -- a note explaining why it's a showcase, not the live version --
st.info(
    "This is a showcase of real agent outputs. Live querying runs privately "
    "to protect data quality and keep results trustworthy."
)


# -- load the structured agent output: {slug: {label, chart, interpretation}} --
def load_interpretations(path="examples/interpretations.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# -- safety net: strip any leaked agent meta-narration before rendering --
def clean(text):
    # drop everything before the first markdown heading (kills "Perfect! Now let me...")
    m = re.search(r"^#+ ", text, flags=re.M)
    if m:
        text = text[m.start():]
    # drop stray horizontal-rule fences
    text = text.replace("\n---\n", "\n")
    return text.strip()


data = load_interpretations()

# -- dropdown driven by the JSON labels (single source of truth) --
labels = {entry["label"]: slug for slug, entry in data.items()}
choice = st.selectbox("Pick a question the agent answered:", list(labels))
entry = data[labels[choice]]

# -- show the chart, then its cleaned interpretation --
st.image(entry["chart"], caption=f"Chart for: {choice}")
st.markdown(clean(entry["interpretation"]))