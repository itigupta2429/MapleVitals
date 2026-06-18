import streamlit as st
from pathlib import Path

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


# -- read interpretation.txt once and split it into {filename: text} --
def load_interpretations(path="examples/interpretation.txt"):
    raw = Path(path).read_text(encoding="utf-8")
    blocks = {}
    current_file = None
    current_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.endswith(".png"):          # a filename line = start of a new block
            if current_file:                    # save the previous block before starting new
                blocks[current_file] = "\n".join(current_lines).strip()
            current_file = stripped
            current_lines = []
        elif set(stripped) == {"="} or stripped == "":
            continue                            # skip separator lines and blanks at edges
        elif current_file:
            current_lines.append(line)
    if current_file:                            # save the last block
        blocks[current_file] = "\n".join(current_lines).strip()
    return blocks


interpretations = load_interpretations()

# -- map a friendly question to its chart file --
examples = {
    "How does fair/poor mental health vary by age & gender in Alberta (18–34)?":
        "mental_health_alberta_18_34.png",
    "What does heavy drinking look like in Alberta (2024)?":
        "heavy_drinking_alberta_2024.png",
    "Are young Canadians smoking less (18–34)?":
        "smoking_trend_18_34.png",
    "How does self-reported obesity rank by province (2024)?":
        "Self-reported_obesity__ranked_by_province__2024.png",
    "Healthcare access vs. perceived health: young Alberta women":
        "access_vs_health_alberta.png",
}

# -- dropdown so the visitor can pick which question's result to see --
choice = st.selectbox("Pick a question the agent answered:", list(examples))
chart_file = examples[choice]

# -- show the chart, then its interpretation (pulled from the txt file) --
st.image(f"examples/{chart_file}", caption=f"Chart for: {choice}")
st.markdown(interpretations.get(chart_file, "_Interpretation not found for this chart._"))