import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Cashify Consumer Intelligence Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------
# Paths for GitHub / Streamlit Cloud deploy
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BUYBACK_DEFAULT = DATA_DIR / "Live Brand Study - CASHIFY Buyback - Final data.xlsx"
REFURB_DEFAULT = DATA_DIR / "Live Brand Study - CASHIFY - Refurbished_data.xlsx"

# -------------------------------------------------
# Premium styling
# -------------------------------------------------
st.markdown("""
<style>
:root {
    --bg: #f5f7fb;
    --card: #ffffff;
    --text: #142033;
    --muted: #6b778c;
    --accent: #18b7a0;
    --accent2: #4f7cff;
    --border: #e7edf5;
    --shadow: 0 12px 28px rgba(16, 24, 40, 0.06);
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.main {
    background: linear-gradient(180deg, #f8fbfd 0%, #f5f7fb 100%);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: var(--text);
    letter-spacing: -0.02em;
}

.hero {
    background: linear-gradient(135deg, rgba(24,183,160,0.10), rgba(79,124,255,0.08));
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: 1.5rem 1.6rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 1rem 1rem 0.8rem 1rem;
    box-shadow: var(--shadow);
    height: 100%;
}

.kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 0.95rem 0.95rem 0.85rem 0.95rem;
    box-shadow: var(--shadow);
    height: 100%;
}

.kpi-label {
    color: var(--muted);
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
}
.kpi-value {
    color: var(--text);
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.05;
}
.kpi-note {
    color: var(--muted);
    font-size: 0.76rem;
    margin-top: 0.2rem;
}

.section-tag {
    display: inline-block;
    font-size: 0.72rem;
    color: #0f766e;
    background: rgba(24,183,160,0.11);
    border: 1px solid rgba(24,183,160,0.16);
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
}

.section-subtext {
    color: var(--muted);
    font-size: 0.88rem;
    margin-top: -0.1rem;
    margin-bottom: 0.8rem;
}

.helper {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.45;
}

.insight-box {
    background: linear-gradient(180deg, rgba(24,183,160,0.05), rgba(79,124,255,0.03));
    border: 1px dashed #cfe6e2;
    border-radius: 18px;
    padding: 0.85rem 0.9rem;
    color: var(--text);
}

textarea {
    border-radius: 16px !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbfd 100%);
    border-right: 1px solid #e8edf4;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: var(--text);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
}
.stTabs [data-baseweb="tab"] {
    height: 42px;
    padding-left: 0.7rem;
    padding-right: 0.7rem;
    border-radius: 12px 12px 0 0;
}
.footer-note {
    color: var(--muted);
    font-size: 0.78rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def split_multi(value):
    if pd.isna(value):
        return []
    txt = str(value).replace("\n", ",").strip()
    if not txt or txt.lower() in {"none", "no", "nope", "nan"}:
        return []
    return [
        p.strip()
        for p in re.split(r"\s*,\s*", txt)
        if p.strip() and p.strip().lower() not in {"none", "never heard of any"}
    ]

def percent(n, d):
    return 0 if d == 0 else round(100 * n / d, 1)

def safe_int(x):
    try:
        return int(float(x))
    except Exception:
        return np.nan

def extract_platform_name(label):
    label = str(label).replace("\n", " ")
    if " - " in label:
        return label.split(" - ")[-1].strip()
    return label.strip()

def build_question_map(dict_df):
    return dict(zip(dict_df.iloc[:, 0].astype(str), dict_df.iloc[:, 1].astype(str)))

def load_buyback(file_obj):
    dict_df = pd.read_excel(file_obj, sheet_name="Column Dictionary")
    raw = pd.read_excel(file_obj, sheet_name="Group 6 Data", header=None)
    headers = raw.iloc[0].astype(str).tolist()
    data = raw.iloc[2:].copy()
    data.columns = headers
    return data.reset_index(drop=True), build_question_map(dict_df)

def load_refurbished(file_obj):
    dict_df = pd.read_excel(file_obj, sheet_name="Column Dictionary")
    data = pd.read_excel(file_obj, sheet_name="Group 6 Data")
    return data, build_question_map(dict_df)

@st.cache_data(show_spinner=False)
def load_datasets(buy_source, ref_source):
    buy_df, buy_map = load_buyback(buy_source)
    ref_df, ref_map = load_refurbished(ref_source)
    return buy_df, buy_map, ref_df, ref_map

def get_platform_cols(df, qmap, prefix):
    cols = [c for c in df.columns if re.fullmatch(fr"{prefix}_\d+", str(c))]
    return {extract_platform_name(qmap.get(c, c)): c for c in cols}

def parse_open_awareness(series, platform_universe):
    rows = []
    for val in series.fillna(""):
        txt = str(val).strip()
        if not txt or txt.lower() in {"no", "none", "nope", "n/a"}:
            continue
        low = txt.lower()
        matched = [p for p in platform_universe if p.lower() in low]
        rows.extend(matched if matched else [txt.title()])
    if not rows:
        return pd.DataFrame(columns=["platform", "count", "pct"])
    s = pd.Series(rows).value_counts().reset_index()
    s.columns = ["platform", "count"]
    s["pct"] = s["count"] / max(series.notna().sum(), 1) * 100
    return s

def parse_multiselect_counts(series):
    bucket = {}
    base = series.notna().sum()

    for val in series.dropna():
        for item in split_multi(val):
            bucket[item] = bucket.get(item, 0) + 1

    if not bucket:
        return pd.DataFrame(columns=["item", "count", "pct"])

    out = pd.DataFrame(
        [{"item": k, "count": v, "pct": v / max(base, 1) * 100} for k, v in bucket.items()]
    )
    return out.sort_values(["count", "item"], ascending=[False, True]).reset_index(drop=True)

def familiarity_metric(df, platform_cols):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        vals = df[col].fillna("").astype(str).str.lower()
        hits = vals.str.contains("familiar", na=False)
        rows.append({
            "platform": platform,
            "count": int(hits.sum()),
            "pct": percent(int(hits.sum()), base)
        })
    return pd.DataFrame(rows).sort_values(["pct", "platform"], ascending=[False, True])

def binary_platform_metric(df, platform_cols, positive_values=None):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        s = df[col].astype(str)
        hits = s.isin(positive_values or [])
        rows.append({
            "platform": platform,
            "count": int(hits.sum()),
            "pct": percent(int(hits.sum()), base)
        })
    return pd.DataFrame(rows).sort_values(["pct", "platform"], ascending=[False, True])

def nps_table(df, platform_cols):
    rows = []
    for platform, col in platform_cols.items():
        scores = df[col].apply(safe_int).dropna()
        if scores.empty:
            rows.append({
                "platform": platform,
                "nps": np.nan,
                "promoters": 0,
                "passives": 0,
                "detractors": 0,
                "base": 0
            })
            continue
        p = int((scores >= 9).sum())
        pa = int(((scores >= 7) & (scores <= 8)).sum())
        d = int((scores <= 6).sum())
        b = int(scores.shape[0])
        rows.append({
            "platform": platform,
            "nps": round((p / b - d / b) * 100, 1),
            "promoters": p,
            "passives": pa,
            "detractors": d,
            "base": b
        })
    return pd.DataFrame(rows).sort_values(["nps", "platform"], ascending=[False, True])

def ranking_weighted_scores(df, qmap, prefix):
    cols = [c for c in df.columns if re.fullmatch(fr"{prefix}[A-Z]?_\d+", str(c)) and df[c].notna().any()]
    rows = []
    for col in cols:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if vals.empty:
            continue
        label = extract_platform_name(qmap.get(col, col))
        rows.append({
            "factor": label,
            "weighted_score": float((6 - vals.clip(1, 5)).sum()),
            "mentions": int(vals.shape[0]),
            "avg_rank": round(vals.mean(), 2)
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["weighted_score", "mentions"], ascending=[False, False]) if not out.empty else out

def source_matrix(df, qmap):
    platform_cols = get_platform_cols(df, qmap, "Q13")
    rows = []
    for platform, col in platform_cols.items():
        counts = parse_multiselect_counts(df[col])
        if counts.empty:
            continue
        counts["platform"] = platform
        rows.append(counts.rename(columns={"item": "source"}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["platform", "source", "count", "pct"])

def filter_df(df, city, gender, age, income, work):
    out = df.copy()
    for col, selected in {"Q1": city, "Q2": gender, "Q3": age, "Q8": income, "Q7": work}.items():
        if selected and "All" not in selected and col in out.columns:
            out = out[out[col].isin(selected)]
    return out

def platform_universe(qmap, df):
    names = set()
    for prefix in ["Q13", "Q14", "Q15", "Q16"]:
        for p in get_platform_cols(df, qmap, prefix).keys():
            names.add(p)
    aided = parse_multiselect_counts(df["Q12"]) if "Q12" in df.columns else pd.DataFrame(columns=["item", "count", "pct"])
    if not aided.empty:
        names.update(aided["item"].tolist())
    return sorted(names)

def awareness_bundle(df, qmap):
    universe = platform_universe(qmap, df)
    tom = parse_open_awareness(df["Q10"] if "Q10" in df.columns else pd.Series([], dtype=object), universe)
    spont = pd.concat([
        parse_open_awareness(df["Q10"] if "Q10" in df.columns else pd.Series([], dtype=object), universe),
        parse_open_awareness(df["Q11"] if "Q11" in df.columns else pd.Series([], dtype=object), universe)
    ], ignore_index=True)

    if spont.empty:
        spont_agg = pd.DataFrame(columns=["platform", "count", "pct"])
    else:
        spont_agg = spont.groupby("platform", as_index=False)["count"].sum()
        spont_agg["pct"] = spont_agg["count"] / max(len(df), 1) * 100
        spont_agg = spont_agg.sort_values(["count", "platform"], ascending=[False, True])

    aided = parse_multiselect_counts(df["Q12"]).rename(columns={"item": "platform"}) if "Q12" in df.columns else pd.DataFrame(columns=["platform", "count", "pct"])
    return tom, spont_agg, aided

def ever_used_metric(df, qmap):
    if "Q19A" not in df.columns:
        return pd.DataFrame(columns=["platform", "count", "pct"])
    base = len(df)
    vals = df["Q19A"].fillna("").astype(str).str.strip()
    vals = vals[vals.ne("")]
    if vals.empty:
        return pd.DataFrame(columns=["platform", "count", "pct"])
    out = vals.value_counts().reset_index()
    out.columns = ["platform", "count"]
    out["pct"] = out["count"] / max(base, 1) * 100
    return out

def build_brand_health(df, qmap):
    frames = []

    aided = parse_multiselect_counts(df["Q12"]).rename(columns={"item": "platform"}) if "Q12" in df.columns else pd.DataFrame(columns=["platform", "count", "pct"])
    fam = familiarity_metric(df, get_platform_cols(df, qmap, "Q14"))
    consider = binary_platform_metric(df, get_platform_cols(df, qmap, "Q15"), positive_values=["Selected"])
    ever = ever_used_metric(df, qmap)

    stage_map = [
        ("Awareness", aided[["platform", "pct"]] if not aided.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Familiarity", fam[["platform", "pct"]] if not fam.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Consideration", consider[["platform", "pct"]] if not consider.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Ever Used", ever[["platform", "pct"]] if not ever.empty else pd.DataFrame(columns=["platform", "pct"])),
    ]

    for stage_name, stage_df in stage_map:
        if not stage_df.empty:
            temp = stage_df.copy()
            temp["stage"] = stage_name
            frames.append(temp)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["platform", "pct", "stage"])

def plot_bar(df, x, y, color=None, height=420, orientation="v", color_sequence=None):
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.info("Not enough data to show this view for the current selection.")
        return
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        height=height,
        text_auto=".1f",
        color_discrete_sequence=color_sequence
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        xaxis_title="",
        yaxis_title="",
        font=dict(size=13),
    )
    fig.update_traces(marker_line_width=0, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)

def plot_heatmap(matrix_df, index_col, col_col, value_col, height=520):
    if (
        matrix_df.empty
        or index_col not in matrix_df.columns
        or col_col not in matrix_df.columns
        or value_col not in matrix_df.columns
    ):
        st.info("Not enough data to show this view for the current selection.")
        return

    pivot = matrix_df.pivot_table(index=index_col, columns=col_col, values=value_col, fill_value=0, aggfunc="sum")
    if pivot.empty:
        st.info("Not enough data to show this view for the current selection.")
        return

    fig = px.imshow(
        pivot,
        aspect="auto",
        text_auto=".0f",
        color_continuous_scale=[
            [0.0, "#edf9f7"],
            [0.25, "#ccefe7"],
            [0.5, "#93e0cf"],
            [0.75, "#49c9b1"],
            [1.0, "#18b7a0"],
        ],
        height=height,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar_title="Count",
        font=dict(size=12),
    )
    st.plotly_chart(fig, use_container_width=True)

def kpi(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.title("Dashboard Controls")

use_upload = st.sidebar.toggle("Use uploaded Excel files instead", value=False)

if use_upload:
    buy_file = st.sidebar.file_uploader("Upload Buyback workbook", type=["xlsx"], key="buy")
    ref_file = st.sidebar.file_uploader("Upload Refurbished workbook", type=["xlsx"], key="ref")
    if not (buy_file and ref_file):
        st.markdown(
            '<div class="hero"><h2 style="margin-bottom:0.3rem;">Cashify Consumer Intelligence Dashboard</h2><p class="helper">Upload both Excel files from the sidebar to start the dashboard.</p></div>',
            unsafe_allow_html=True
        )
        st.stop()
else:
    if not BUYBACK_DEFAULT.exists() or not REFURB_DEFAULT.exists():
        st.error("Excel files not found in the repo. Make sure both files are inside the 'data' folder in GitHub.")
        st.code(
            "data/\n"
            "├── Live Brand Study - CASHIFY Buyback - Final data.xlsx\n"
            "└── Live Brand Study - CASHIFY - Refurbished_data.xlsx"
        )
        st.stop()
    buy_file = BUYBACK_DEFAULT
    ref_file = REFURB_DEFAULT

buy_df, buy_map, ref_df, ref_map = load_datasets(buy_file, ref_file)

journey = st.sidebar.radio("Consumer Journey", ["Buyback", "Refurbished"])
df = buy_df.copy() if journey == "Buyback" else ref_df.copy()
qmap = buy_map if journey == "Buyback" else ref_map

def mfilter(label, col):
    vals = sorted([v for v in df[col].dropna().astype(str).unique().tolist() if v.strip()]) if col in df.columns else []
    return st.sidebar.multiselect(label, ["All"] + vals, default=["All"])

city = mfilter("City / Tier", "Q1")
gender = mfilter("Gender", "Q2")
age = mfilter("Age Bucket", "Q3")
income = mfilter("Household Income", "Q8")
work = mfilter("Working Status", "Q7")
filtered = filter_df(df, city, gender, age, income, work)

# -------------------------------------------------
# Top metrics
# -------------------------------------------------
tom, spontaneous, aided = awareness_bundle(filtered, qmap)
consider_df = binary_platform_metric(filtered, get_platform_cols(filtered, qmap, "Q15"), positive_values=["Selected"])
nps_df = nps_table(filtered, get_platform_cols(filtered, qmap, "Q16"))
brand_health_df = build_brand_health(filtered, qmap)

cashify_tom = tom.loc[tom["platform"].str.lower().eq("cashify"), "pct"].max() if not tom.empty else 0
cashify_aw = aided.loc[aided["platform"].str.lower().eq("cashify"), "pct"].max() if not aided.empty else 0
cashify_cons = consider_df.loc[consider_df["platform"].str.lower().eq("cashify"), "pct"].max() if not consider_df.empty else 0
cashify_nps = nps_df.loc[nps_df["platform"].str.lower().eq("cashify"), "nps"].max() if not nps_df.empty else np.nan

# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown(f"""
<div class="hero">
    <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
        <div style="flex:1;">
            <div class="section-tag">MIS + DSS</div>
            <h1 style="margin:0 0 0.35rem 0;">Cashify Consumer Intelligence Dashboard</h1>
            <div class="section-subtext">
                Premium decision-support dashboard for the <b>{journey}</b> journey. Use the sidebar filters to compare awareness, brand health, consideration, NPS, sources, drivers, and barriers.
            </div>
        </div>
        <div style="min-width:220px; max-width:240px;">
            <div class="kpi-card">
                <div class="kpi-label">Filtered Sample</div>
                <div class="kpi-value">{len(filtered)}</div>
                <div class="kpi-note">Current respondent base in view</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    kpi("Cashify TOM", f"{cashify_tom:.1f}%", "Top-of-mind saliency")
with kc2:
    kpi("Cashify Aided Awareness", f"{cashify_aw:.1f}%", "Recognition from prompted list")
with kc3:
    kpi("Cashify Consideration", f"{cashify_cons:.1f}%", "Included in next-time shortlist")
with kc4:
    kpi("Cashify NPS", "NA" if pd.isna(cashify_nps) else f"{cashify_nps:.1f}", "Promoters minus detractors")

tabs = st.tabs([
    "Overview",
    "Awareness",
    "Brand Health",
    "Consideration & NPS",
    "Sources",
    "Drivers & Barriers",
    "Decision Support",
])

# -------------------------------------------------
# Overview
# -------------------------------------------------
with tabs[0]:
    st.markdown('<div class="section-tag">Context</div>', unsafe_allow_html=True)
    st.subheader("Study Overview & Sample Snapshot")
    st.markdown('<div class="section-subtext">Use this page for the methodology, target group, and sample profile section in the PPT.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.05, 1])

    with left:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">How to use this dashboard</h4>
            <div class="helper">
                <ul>
                    <li>Switch between <b>Buyback</b> and <b>Refurbished</b> using the sidebar.</li>
                    <li>Use demographic filters to create directional cuts where sample size permits.</li>
                    <li>Lift charts directly into the PPT for awareness, consideration, NPS, sources, drivers, and barriers.</li>
                    <li>Because the current base is limited, segment findings should be interpreted as <b>directional</b>.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        demo_cols = [c for c in ["Q1", "Q2", "Q3", "Q7", "Q8"] if c in filtered.columns]
        frames = []
        for col in demo_cols:
            vc = filtered[col].astype(str).value_counts().reset_index()
            vc.columns = ["Option", "Count"]
            vc["Question"] = col
            frames.append(vc.head(5))
        demo_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Option", "Count", "Question"])
        plot_bar(
            demo_df,
            x="Option",
            y="Count",
            color="Question",
            height=450,
            color_sequence=["#4f7cff", "#7eb6ff", "#ff6b6b", "#ffb3b3", "#18b7a0"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Awareness
# -------------------------------------------------
with tabs[1]:
    st.markdown('<div class="section-tag">Awareness</div>', unsafe_allow_html=True)
    st.subheader("Saliency / Brand Awareness Analysis")
    st.markdown('<div class="section-subtext">Top-of-mind, spontaneous, and aided awareness for Cashify versus competing platforms.</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)

    with a1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Top-of-Mind Recall</h4>', unsafe_allow_html=True)
        plot_bar(
            tom.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#18b7a0"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Spontaneous Awareness</h4>', unsafe_allow_html=True)
        plot_bar(
            spontaneous.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#4f7cff"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with a3:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Aided Awareness</h4>', unsafe_allow_html=True)
        plot_bar(
            aided.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#142033"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Brand Health
# -------------------------------------------------
with tabs[2]:
    st.markdown('<div class="section-tag">Brand Health</div>', unsafe_allow_html=True)
    st.subheader("Brand Health Ladder")
    st.markdown('<div class="section-subtext">A cleaner view than the earlier funnel: this compares how each platform performs across awareness, familiarity, consideration, and—where derivable—ever used.</div>', unsafe_allow_html=True)

    if not brand_health_df.empty:
        top_platforms = (
            brand_health_df.groupby("platform")["pct"]
            .max()
            .sort_values(ascending=False)
            .head(6)
            .index
            .tolist()
        )
        chart_df = brand_health_df[brand_health_df["platform"].isin(top_platforms)]

        bh1, bh2 = st.columns([1.25, 0.75])

        with bh1:
            st.markdown('<div class="card"><h4 style="margin-top:0;">Brand Health by Stage</h4>', unsafe_allow_html=True)
            fig = px.bar(
                chart_df,
                x="stage",
                y="pct",
                color="platform",
                barmode="group",
                height=500,
                text_auto=".1f",
                color_discrete_sequence=[
                    "#18b7a0", "#4f7cff", "#8cc7ff", "#ff7a7a", "#8b5cf6", "#0f172a"
                ],
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="",
                yaxis_title="Percent of respondents",
                legend_title_text="",
                font=dict(size=13),
            )
            fig.update_traces(marker_line_width=0, cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with bh2:
            st.markdown('<div class="card"><h4 style="margin-top:0;">Brand Health Table</h4>', unsafe_allow_html=True)
            pivot = brand_health_df.pivot_table(index="platform", columns="stage", values="pct", fill_value=0).reset_index()
            st.dataframe(pivot, use_container_width=True, hide_index=True)
            st.markdown("""
            <div class="insight-box" style="margin-top:0.8rem;">
                <b>Reading tip:</b><br>
                Use this as a ladder, not a strict mathematical funnel. It shows how strong each brand is across stages rather than implying a perfect sequential conversion path.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough data to show the Brand Health Ladder.")

# -------------------------------------------------
# Consideration & NPS
# -------------------------------------------------
with tabs[3]:
    st.markdown('<div class="section-tag">Conversion</div>', unsafe_allow_html=True)
    st.subheader("Consideration & NPS")
    st.markdown('<div class="section-subtext">Which brands enter the shortlist, and how strongly users recommend them.</div>', unsafe_allow_html=True)

    l1, l2 = st.columns(2)

    with l1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Consideration Set</h4>', unsafe_allow_html=True)
        plot_bar(
            consider_df.sort_values("pct", ascending=True),
            x="pct",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#18b7a0"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with l2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">NPS by Platform</h4>', unsafe_allow_html=True)
        plot_bar(
            nps_df.sort_values("nps", ascending=True),
            x="nps",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#4f7cff"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if not nps_df.empty:
        st.markdown('<div class="card" style="margin-top:0.9rem;">', unsafe_allow_html=True)
        st.markdown("#### Promoter / Passive / Detractor Split")
        melt = nps_df.melt(
            id_vars=["platform", "base", "nps"],
            value_vars=["promoters", "passives", "detractors"],
            var_name="segment",
            value_name="count"
        )
        plot_bar(
            melt,
            x="platform",
            y="count",
            color="segment",
            height=420,
            color_sequence=["#18b7a0", "#f5c24b", "#ff6b6b"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Sources
# -------------------------------------------------
with tabs[4]:
    st.markdown('<div class="section-tag">Channels</div>', unsafe_allow_html=True)
    st.subheader("Source of Awareness")
    st.markdown('<div class="section-subtext">Where people heard about Cashify and the competing platforms.</div>', unsafe_allow_html=True)

    source_df = source_matrix(filtered, qmap)

    s1, s2 = st.columns([1.35, 0.75])

    with s1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Platform × Source Heatmap</h4>', unsafe_allow_html=True)
        plot_heatmap(source_df, "platform", "source", "count", height=540)
        st.markdown("</div>", unsafe_allow_html=True)

    with s2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Top Awareness Sources</h4>', unsafe_allow_html=True)
        top_sources = (
            source_df.groupby("source", as_index=False)["count"].sum().sort_values("count", ascending=True)
            if not source_df.empty else pd.DataFrame(columns=["source", "count"])
        )
        plot_bar(
            top_sources.tail(10),
            x="count",
            y="source",
            orientation="h",
            height=540,
            color_sequence=["#18b7a0"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Drivers & Barriers
# -------------------------------------------------
with tabs[5]:
    st.markdown('<div class="section-tag">Drivers</div>', unsafe_allow_html=True)
    st.subheader("Choice Drivers, Barriers & Category Fears")
    st.markdown('<div class="section-subtext">What drives brand choice, what blocks Cashify, and what concerns define the category.</div>', unsafe_allow_html=True)

    d1, d2 = st.columns(2)

    with d1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Why Cashify was chosen</h4>', unsafe_allow_html=True)
        chosen_cashify = ranking_weighted_scores(filtered, qmap, "Q20")
        if chosen_cashify.empty:
            st.info("No rank-based Cashify choice data available in the current view.")
        else:
            plot_bar(
                chosen_cashify.sort_values("weighted_score", ascending=True),
                x="weighted_score",
                y="factor",
                orientation="h",
                height=450,
                color_sequence=["#18b7a0"]
            )
            st.dataframe(chosen_cashify, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Why another platform was chosen</h4>', unsafe_allow_html=True)
        chosen_other = ranking_weighted_scores(filtered, qmap, "Q21A")
        if chosen_other.empty:
            st.info("No competitor rank-based data available in the current view.")
        else:
            plot_bar(
                chosen_other.sort_values("weighted_score", ascending=True),
                x="weighted_score",
                y="factor",
                orientation="h",
                height=450,
                color_sequence=["#4f7cff"]
            )
            st.dataframe(chosen_other, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns(2)

    with b1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Barriers to choosing Cashify</h4>', unsafe_allow_html=True)
        barriers = parse_multiselect_counts(filtered["Q21B"]) if "Q21B" in filtered.columns else pd.DataFrame(columns=["item", "count", "pct"])

        if barriers.empty or "pct" not in barriers.columns or "item" not in barriers.columns:
            st.info("No barrier data available for the current selection.")
        else:
            plot_bar(
                barriers.sort_values("pct", ascending=True),
                x="pct",
                y="item",
                orientation="h",
                height=420,
                color_sequence=["#ff6b6b"]
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Category Drivers & Fears</h4>', unsafe_allow_html=True)

        driver_col = "Q24" if "Q24" in filtered.columns else ("Q22" if "Q22" in filtered.columns else None)

        st.markdown("**Top category drivers**")
        if driver_col:
            if driver_col == "Q24":
                # top-3 driver variables are often separate binary columns
                q24_cols = [c for c in filtered.columns if re.fullmatch(r"Q24_\d+", str(c))]
                rows = []
                for col in q24_cols:
                    label = extract_platform_name(qmap.get(col, col))
                    count = filtered[col].astype(str).str.strip().replace("nan", "").ne("").sum()
                    rows.append({"item": label, "count": int(count), "pct": percent(int(count), len(filtered))})
                driver_df = pd.DataFrame(rows).sort_values(["count", "item"], ascending=[False, True]) if rows else pd.DataFrame(columns=["item","count","pct"])
            else:
                driver_df = parse_multiselect_counts(filtered[driver_col])

            if driver_df.empty or "pct" not in driver_df.columns or "item" not in driver_df.columns:
                st.info("No category driver data available for the current selection.")
            else:
                plot_bar(
                    driver_df.sort_values("pct", ascending=True).tail(10),
                    x="pct",
                    y="item",
                    orientation="h",
                    height=240,
                    color_sequence=["#18b7a0"]
                )
        else:
            st.info("No category driver variable found in this dataset.")

        st.markdown("**Biggest category fears / hesitations**")
        fear_df = parse_multiselect_counts(filtered["Q23"]) if "Q23" in filtered.columns else pd.DataFrame(columns=["item", "count", "pct"])
        if fear_df.empty or "pct" not in fear_df.columns or "item" not in fear_df.columns:
            st.info("No fear / hesitation data available for the current selection.")
        else:
            plot_bar(
                fear_df.sort_values("pct", ascending=True).tail(10),
                x="pct",
                y="item",
                orientation="h",
                height=240,
                color_sequence=["#ff8f6b"]
            )

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Decision Support
# -------------------------------------------------
with tabs[6]:
    st.markdown('<div class="section-tag">Action</div>', unsafe_allow_html=True)
    st.subheader("Manager Interpretation Space")
    st.markdown('<div class="section-subtext">This section is intentionally left non-prescriptive. The dashboard should inform the manager’s summary and way forward, not hardcode them.</div>', unsafe_allow_html=True)

    ds1, ds2 = st.columns(2)

    with ds1:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">Summary to be derived from the charts</h4>
            <div class="helper">
                Use the Awareness, Brand Health, Sources, and Drivers tabs to draft the final summary in the PPT.
                This space is intentionally not auto-filled because the interpretation should depend on the selected dataset and filters.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.text_area(
            "Manager Notes — Summary",
            value="",
            height=220,
            placeholder="Write the key summary points here after reviewing the charts above...",
            key="summary_notes"
        )

    with ds2:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">Way Forward to be decided by management</h4>
            <div class="helper">
                Recommendations should follow from the specific findings in the dashboard.
                This space is intentionally open rather than static.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.text_area(
            "Manager Notes — Way Forward",
            value="",
            height=220,
            placeholder="Write the way forward here based on the actual analysis and segment view...",
            key="action_notes"
        )

st.markdown(
    '<div class="footer-note">Built for a classroom MIS live project. With the current sample size, segment cuts should be interpreted directionally.</div>',
    unsafe_allow_html=True
)
