import json
import re
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="MapleVitals", page_icon="🍁", layout="wide")

# -----------------------------------------------------------------------------
# Theme: the viewer chooses light or dark; dark stays the default.
# -----------------------------------------------------------------------------
_, _theme_col = st.columns([5, 1])
with _theme_col:
    _light = st.toggle("Light mode", value=False, key="mv_light")
theme = "light" if _light else "dark"

THEME_TOKENS = {
    "dark": """
      --ink:#0C0F14; --surface:#151A22; --surface-2:#1E2530;
      --line:#283040; --text:#E8EDF3; --muted:#93A1B1; --soft:#C3CCD8;
      --maple:#E0533D; --flag:#E6B450;
      --imgshadow:0 8px 28px rgba(0,0,0,0.35);
    """,
    "light": """
      --ink:#F5F7FA; --surface:#FFFFFF; --surface-2:#EDF1F6;
      --line:#D6DCE5; --text:#16202E; --muted:#48566A; --soft:#33415A;
      --maple:#C13A20; --flag:#8A5E10;
      --imgshadow:0 8px 24px rgba(20,30,50,0.10);
    """,
}

# -----------------------------------------------------------------------------
# Styling: fonts, palette tokens, component polish, and the flag-legend signature
# -----------------------------------------------------------------------------
st.markdown(f"<style>:root{{{THEME_TOKENS[theme]}}}</style>", unsafe_allow_html=True)

# Load the brand fonts via <link> (faster and more reliable on Community Cloud
# than @import alone). Without these the wordmark silently falls back to a
# system font on deploy, which is part of why it looked different there.
st.markdown(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&'
    'family=IBM+Plex+Mono:wght@400;500&display=swap">',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    /* Lock the root size with !important so rem units compute identically in
       every Streamlit version (Community Cloud can run a different build than
       your local conda env). This is also the single knob that scales every
       rem-based size up together: raise this number to make everything bigger. */
    html{ font-size:20px !important; }

    /* Background + base text target STABLE selectors. Streamlit renames its
       hashed class names (.css-* -> .st-emotion-cache-*) between versions, so the
       old [class*="css"] selector silently stops matching after an upgrade,
       which is exactly what made the deployed page render smaller and unstyled. */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"]{ background:var(--ink) !important; }
    .stApp{ font-size:1rem; }
    .stApp, .stApp p, .stApp li, .stApp span, .stApp label,
    [data-testid="stMarkdownContainer"]{
      font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
      color:var(--text);
    }
    h1,h2,h3,.mv-wordmark{
      font-family:'Space Grotesk',system-ui,sans-serif; letter-spacing:-0.02em;
    }
    .block-container,
    [data-testid="stMainBlockContainer"]{ max-width:96%; margin:0 auto; padding:2.4rem 2.5rem 3rem; }
    .block-container p, .block-container li{ font-size:1rem; line-height:1.7; }
    .block-container h2{ font-size:1.55rem; }
    .block-container h3{ font-size:1.25rem; }

    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{ display:none; }
    header[data-testid="stHeader"]{ background:transparent; }

    .mv-eyebrow{
      font-family:'IBM Plex Mono',monospace; font-size:0.82rem; letter-spacing:0.18em;
      color:var(--muted); text-transform:uppercase; margin-bottom:0.5rem;
    }
    .mv-wordmark{
      font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:3.2rem;
      line-height:1.04; letter-spacing:-0.03em; margin:0; animation:mv-rise 0.6s ease-out both;
    }
    .mv-thesis{
      font-size:1.28rem; color:var(--soft); margin:0.85rem 0 1.3rem;
      line-height:1.5; text-wrap:balance;
    }
    .mv-flags{ display:flex; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.4rem; }
    .mv-flag{
      font-family:'IBM Plex Mono',monospace; font-size:0.9rem; color:var(--muted);
      background:var(--surface); border:1px solid var(--line); border-radius:7px;
      padding:0.38rem 0.7rem;
    }
    .mv-flag b{ color:var(--flag); margin-right:0.35rem; }

    .mv-rule{ height:1px; background:var(--line); border:0; margin:2rem 0 1.3rem; }
    .mv-section{
      font-family:'IBM Plex Mono',monospace; font-size:0.86rem; letter-spacing:0.18em;
      color:var(--maple); text-transform:uppercase; margin-bottom:0.8rem;
    }

    [data-testid="stSelectbox"] label{ color:var(--soft); font-weight:600; font-size:1.05rem; }
    [data-testid="stWidgetLabel"] p{ color:var(--soft) !important; }

    /* Streamlit widget chrome is themed by Streamlit, not our CSS, so override it
       here to follow the toggle. Closed selectbox control + the dropdown popover. */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
      background:var(--surface) !important; border-color:var(--line) !important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] *{ color:var(--text) !important; }
    [data-testid="stSelectbox"] div[data-baseweb="select"] svg{ fill:var(--muted) !important; }
    div[data-baseweb="popover"] [role="listbox"]{
      background:var(--surface) !important; border:1px solid var(--line) !important;
    }
    div[data-baseweb="popover"] li[role="option"]{
      background:var(--surface) !important; color:var(--text) !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] li[aria-selected="true"]{ background:var(--surface-2) !important; }

    [data-testid="stImage"]{
      background:#ffffff; padding:14px; border-radius:12px;
      border:1px solid var(--line); box-shadow:var(--imgshadow);
    }
    [data-testid="stImage"] img{ width:100%; height:auto; border-radius:6px; }

    .mv-card-label{
      font-family:'IBM Plex Mono',monospace; font-size:0.82rem; letter-spacing:0.14em;
      color:var(--muted); text-transform:uppercase; margin:1.4rem 0 0.5rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]{
      background:var(--surface); border:1px solid var(--line) !important;
      border-radius:12px;
    }

    .mv-how{ display:grid; grid-template-columns:repeat(3,1fr); gap:0.8rem; }
    .mv-step{
      background:var(--surface); border:1px solid var(--line);
      border-radius:12px; padding:1rem 1rem 1.1rem;
    }
    .mv-step-k{
      font-family:'IBM Plex Mono',monospace; font-size:0.8rem; letter-spacing:0.12em;
      color:var(--maple); text-transform:uppercase; margin-bottom:0.45rem;
    }
    .mv-step-t{ font-size:1.02rem; color:var(--soft); line-height:1.55; }
    @media (max-width:640px){
      .mv-how{ grid-template-columns:1fr; }
      .block-container{ padding:1.6rem 1.2rem 2rem; }
      .mv-wordmark{ font-size:2.4rem; }
    }

    .mv-maplegend{
      font-family:'IBM Plex Mono',monospace; font-size:0.86rem; color:var(--muted);
      margin-top:0.4rem;
    }

    .mv-footer{
      margin-top:1.6rem; padding-top:1.2rem; border-top:1px solid var(--line);
      font-size:0.95rem; color:var(--muted); line-height:1.7;
    }
    .mv-footer a{ color:var(--maple); font-weight:600; text-decoration:none;
                  border-bottom:1px solid var(--maple); }
    .mv-footer a:hover{ opacity:0.78; }
    .mv-footer .mv-mono{ font-family:'IBM Plex Mono',monospace; color:var(--muted); }

    @keyframes mv-rise{ from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:none;} }
    @media (prefers-reduced-motion:reduce){ .mv-wordmark{ animation:none; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="mv-eyebrow">Canadian public-health intelligence</div>
    <div class="mv-wordmark">🍁 MapleVitals</div>
    <div class="mv-thesis">
      An agent that turns Statistics Canada health data into charts and plain&#8209;language
      reads, with the data&#8209;quality checks an epidemiologist would insist on.
    </div>
    <div class="mv-flags">
      <span class="mv-flag"><b>E</b> high variability &middot; flagged with caution</span>
      <span class="mv-flag"><b>F</b> suppressed &middot; withheld from results</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data loading (verified agent outputs) + meta-narration safety strip
# -----------------------------------------------------------------------------
def load_interpretations(path="examples/interpretations.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean(text):
    m = re.search(r"^#+ ", text, flags=re.M)
    if m:
        text = text[m.start():]
    text = text.replace("\n---\n", "\n")
    # Drop em dashes from displayed prose (en dashes are kept so ranges like 2015-2024 survive).
    text = text.replace("&mdash;", "\u2014").replace("&#8212;", "\u2014")
    text = re.sub(r"\s*\u2014\s*", ", ", text)
    text = re.sub(r" +", " ", text)
    return text.strip()


data = load_interpretations()
labels = {entry["label"]: slug for slug, entry in data.items()}


# -----------------------------------------------------------------------------
# Province map: filters the full StatCan CSV live and draws the flags on the map
# -----------------------------------------------------------------------------
PROVINCES = [
    "Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia", "New Brunswick",
    "Quebec", "Ontario", "Manitoba", "Saskatchewan", "Alberta", "British Columbia",
]
MAPLE_SCALE = [[0, "#6E2A22"], [0.4, "#B23E28"], [0.72, "#E0633A"], [1, "#F2853F"]]
MAP_COLORS = {
    "dark":  {"bg": "#0C0F14", "border": "#0C0F14", "grey": "#262D38",
              "grey_line": "#3A4252", "font": "#E8EDF3"},
    "light": {"bg": "#F5F7FA", "border": "#FFFFFF", "grey": "#E2E8F0",
              "grey_line": "#C4CCD8", "font": "#16202E"},
}


@st.cache_data
def load_geojson(path="examples/canada_provinces.geojson"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data
def load_csv(path="data/map_slim.csv"):
    return pd.read_csv(path)


def province_records(df, indicator, sex, age, year):
    """Province -> (value, status) for the point-estimate percentage only."""
    sub = df[(df["Indicators"] == indicator) & (df["Sex"] == sex) & (df["Age group"] == age)
             & (df["REF_DATE"] == year) & (df["UOM"] == "Percent")
             & (df["Characteristics"] == "Percent") & (df["GEO"].isin(PROVINCES))]
    return {r["GEO"]: (r["VALUE"], (str(r["STATUS"]).strip() if pd.notna(r["STATUS"]) else ""))
            for _, r in sub.iterrows()}


def build_province_map(recs, geo, theme="dark"):
    c = MAP_COLORS[theme]
    grey_scale = [[0, c["grey"]], [1, c["grey"]]]
    all_names = {f["properties"]["name"] for f in geo["features"]}
    base = {p: v for p, (v, s) in recs.items() if s != "E" and pd.notna(v)}
    eflag = {p: v for p, (v, s) in recs.items() if s == "E" and pd.notna(v)}
    suppressed = [p for p, (v, s) in recs.items() if (s in ("F", "x")) or pd.isna(v)]
    nodata = sorted(all_names - set(recs))

    if not base and not eflag:
        return None

    zvals = list(base.values()) + list(eflag.values())
    zmin, zmax = min(zvals), max(zvals)
    traces = [go.Choropleth(
        geojson=geo, featureidkey="properties.name",
        locations=list(base), z=list(base.values()),
        colorscale=MAPLE_SCALE, zmin=zmin, zmax=zmax,
        marker_line_color=c["border"], marker_line_width=0.6,
        colorbar=dict(title=dict(text="%", font=dict(size=15)), tickfont=dict(size=14),
                      thickness=14, len=0.75, outlinewidth=0),
        hovertemplate="<b>%{location}</b><br>%{z}%<extra></extra>")]
    if eflag:
        traces.append(go.Choropleth(
            geojson=geo, featureidkey="properties.name",
            locations=list(eflag), z=list(eflag.values()),
            colorscale=MAPLE_SCALE, zmin=zmin, zmax=zmax, showscale=False,
            marker_line_color="#E6B450", marker_line_width=2.5,
            hovertemplate="<b>%{location}</b><br>%{z}% · E-flagged (high variability)<extra></extra>"))
    for names, note in [(suppressed, "Suppressed (F) · withheld"), (nodata, "No data")]:
        if names:
            traces.append(go.Choropleth(
                geojson=geo, featureidkey="properties.name",
                locations=names, z=[0] * len(names), colorscale=grey_scale, showscale=False,
                marker_line_color=c["grey_line"], marker_line_width=0.8,
                hovertemplate="<b>%{location}</b><br>" + note + "<extra></extra>"))

    fig = go.Figure(traces)
    fig.update_geos(
        visible=False, showframe=False,
        projection_type="conic conformal",
        projection_parallels=[49, 77],
        projection_rotation=dict(lon=-96, lat=0, roll=0),
        lataxis_range=[40, 83], lonaxis_range=[-141, -52],
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=c["font"], size=15), hoverlabel=dict(font_size=14),
                      height=580, dragmode=False)
    return fig


PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

MAP_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="__CDN__"></script>
<style>html,body{margin:0;padding:0;background:__BG__;}#map{width:100%;}</style>
</head><body>
<div id="map"></div>
<script>
var fig = __FIG__;
var gd = document.getElementById('map');
Plotly.newPlot(gd, fig.data, fig.layout, {displayModeBar:false, scrollZoom:false, responsive:true});
// remember each trace's base border so we can restore it after hover
var base = fig.data.map(function(t){
  var ln = (t.marker && t.marker.line) ? t.marker.line : {};
  return {color: ln.color || '#0C0F14', width: (ln.width==null ? 0.6 : ln.width),
          n: (t.locations || []).length};
});
gd.on('plotly_hover', function(ev){
  var p = ev.points[0], ci = p.curveNumber, pi = p.pointNumber, b = base[ci];
  var colors = [], widths = [];
  for (var i=0;i<b.n;i++){ colors.push(b.color); widths.push(b.width); }
  colors[pi] = '#FFFFFF'; widths[pi] = 3.4;
  Plotly.restyle(gd, {'marker.line.color':[colors], 'marker.line.width':[widths]}, [ci]);
});
gd.on('plotly_unhover', function(ev){
  var ci = ev.points[0].curveNumber, b = base[ci];
  Plotly.restyle(gd, {'marker.line.color':b.color, 'marker.line.width':b.width}, [ci]);
});
</script>
</body></html>
"""


def render_map(fig, theme="dark"):
    html = (MAP_HTML.replace("__CDN__", PLOTLY_CDN)
            .replace("__BG__", MAP_COLORS[theme]["bg"])
            .replace("__FIG__", fig.to_json()))
    components.html(html, height=600, scrolling=False)

# -----------------------------------------------------------------------------
# Showcase
# -----------------------------------------------------------------------------
st.markdown('<hr class="mv-rule">', unsafe_allow_html=True)
st.markdown('<div class="mv-section">Showcase &middot; real agent outputs</div>', unsafe_allow_html=True)

choice = st.selectbox("Pick a question the agent answered", list(labels))
entry = data[labels[choice]]

st.image(entry["chart"])

st.markdown('<div class="mv-card-label">Agent interpretation</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(clean(entry["interpretation"]))

# -----------------------------------------------------------------------------
# Interactive province map (full-data explorer)
# -----------------------------------------------------------------------------
st.markdown('<hr class="mv-rule">', unsafe_allow_html=True)
st.markdown('<div class="mv-section">Map · explore by province</div>', unsafe_allow_html=True)

geo = load_geojson()
df = load_csv()

# filter options derived from the data so they're always valid
indicators = sorted(df["Indicators"].dropna().unique())
sexes = [s for s in ["Both sexes", "Males", "Females"] if s in set(df["Sex"])]
ages = list(df["Age group"].dropna().unique())
years = sorted(df["REF_DATE"].dropna().unique())

_def_ind = "Body mass index, adjusted self-reported, obese"
indicator = st.selectbox(
    "Characteristic", indicators,
    index=indicators.index(_def_ind) if _def_ind in indicators else 0,
)
c1, c2, c3 = st.columns(3)
with c1:
    sex = st.selectbox("Gender", sexes, index=sexes.index("Females") if "Females" in sexes else 0)
with c2:
    _def_age = "18 to 34 years"
    age = st.selectbox("Age group", ages, index=ages.index(_def_age) if _def_age in ages else 0)
with c3:
    year = st.selectbox("Year", years, index=len(years) - 1)

recs = province_records(df, indicator, sex, age, year)
fig = build_province_map(recs, geo, theme)
if fig is None:
    st.markdown(
        '<div class="mv-maplegend">No province-level percentage for this combination. '
        'Try another age group, year, or gender.</div>', unsafe_allow_html=True)
else:
    render_map(fig, theme)
    has_e = any(s == "E" for v, s in recs.values())
    has_f = any((s in ("F", "x")) or pd.isna(v) for v, s in recs.values())
    parts = ["Shade shows the rate (scale at right). Hover to highlight a province."]
    if has_e:
        parts.append("Amber outline = E-flagged (high variability).")
    parts.append("Grey = no survey data" + (" or suppressed (F)." if has_f else " (e.g. northern territories)."))
    st.markdown('<div class="mv-maplegend">' + " ".join(parts) + "</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# The agent - how it works (showing the build)
# -----------------------------------------------------------------------------
st.markdown('<hr class="mv-rule">', unsafe_allow_html=True)
st.markdown('<div class="mv-section">The agent · how it works</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="mv-how">
      <div class="mv-step">
        <div class="mv-step-k">Real data</div>
        <div class="mv-step-t">Queries the Canadian Community Health Survey
        (StatCan table 13-10-0905-01) directly. No synthetic numbers.</div>
      </div>
      <div class="mv-step">
        <div class="mv-step-k">Quality guardrails</div>
        <div class="mv-step-t">Reads StatCan's reliability flags on every estimate:
        caveats high-variability values, withholds suppressed ones.</div>
      </div>
      <div class="mv-step">
        <div class="mv-step-k">Correctness check</div>
        <div class="mv-step-t">Every figure is computed from the data before it's stated,
        and rankings exclude unreliable estimates.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Footer  (EDIT: set your LinkedIn URL below)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="mv-footer">
      Built by <b>Iti Gupta</b> &middot; <a href="https://www.linkedin.com/in/iti-gupta-ph-d-05278a56/">LinkedIn</a><br>
      Source: Statistics Canada, Canadian Community Health Survey,
      <span class="mv-mono">table 13-10-0905-01</span>. A portfolio showcase of real,
      quality-checked agent outputs; live querying runs privately.
    </div>
    """,
    unsafe_allow_html=True,
)
