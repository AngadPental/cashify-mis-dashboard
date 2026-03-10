import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Cashify Consumer Intelligence Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================================
# PATHS
# =================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BUYBACK_DEFAULT = DATA_DIR / "Live Brand Study - CASHIFY Buyback - Final data.xlsx"
REFURB_DEFAULT = DATA_DIR / "Live Brand Study - CASHIFY - Refurbished_data.xlsx"

# =================================================
# CASHIFY STYLING
# =================================================
st.markdown("""
<style>
:root {
    --cashify-teal: #42c7b8;
    --cashify-teal-dark: #20b8a7;
    --cashify-teal-soft: #ecfbf8;
    --cashify-navy: #14213d;
    --cashify-text: #1f2937;
    --cashify-muted: #6b7280;
    --cashify-line: #e5e7eb;
    --cashify-panel: #ffffff;
    --shadow: 0 10px 24px rgba(20, 33, 61, 0.06);
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--cashify-text);
}

.main {
    background: linear-gradient(180deg, #fbfdfe 0%, #f6fafb 100%);
}

.block-container {
    max-width: 1500px;
    padding-top: 0.85rem;
    padding-bottom: 2rem;
}

h1, h2, h3, h4 {
    color: var(--cashify-navy);
    letter-spacing: -0.02em;
}

.hero {
    background: linear-gradient(135deg, var(--cashify-teal) 0%, #5ad2c5 100%);
    border-radius: 28px;
    padding: 1.45rem 1.55rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
    color: white;
    overflow: hidden;
}

.hero h1, .hero h2, .hero h3, .hero p, .hero div {
    color: white !important;
}

.hero-sub {
    font-size: 0.95rem;
    opacity: 0.95;
    line-height: 1.5;
}

.panel {
    background: var(--cashify-panel);
    border: 1px solid var(--cashify-line);
    border-radius: 22px;
    padding: 1rem 1rem 0.8rem 1rem;
    box-shadow: var(--shadow);
    height: 100%;
}

.kpi-card {
    background: white;
    border: 1px solid var(--cashify-line);
    border-radius: 20px;
    padding: 0.9rem 1rem 0.85rem 1rem;
    box-shadow: var(--shadow);
    height: 100%;
}

.kpi-label {
    font-size: 0.78rem;
    color: var(--cashify-muted);
    margin-bottom: 0.18rem;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--cashify-navy);
    line-height: 1.05;
}
.kpi-note {
    font-size: 0.75rem;
    color: var(--cashify-muted);
    margin-top: 0.15rem;
}

.section-pill {
    display: inline-block;
    font-size: 0.70rem;
    color: #0f766e;
    background: var(--cashify-teal-soft);
    border: 1px solid #d7f4ee;
    padding: 0.2rem 0.52rem;
    border-radius: 999px;
    margin-bottom: 0.35rem;
}

.section-note {
    font-size: 0.88rem;
    color: var(--cashify-muted);
    margin-top: -0.1rem;
    margin-bottom: 0.8rem;
    line-height: 1.45;
}

.chart-note {
    font-size: 0.81rem;
    color: var(--cashify-muted);
    margin-top: -0.1rem;
    margin-bottom: 0.55rem;
    line-height: 1.4;
}

.empty-note {
    font-size: 0.85rem;
    color: var(--cashify-muted);
    font-style: italic;
    padding: 0.4rem 0 0.2rem 0;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f7fbfc 0%, #f4f8fb 100%);
    border-right: 1px solid var(--cashify-line);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--cashify-navy);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    padding-left: 0.7rem;
    padding-right: 0.7rem;
    border-radius: 10px 10px 0 0;
}

.footer-note {
    color: var(--cashify-muted);
    font-size: 0.76rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HELPERS
# =================================================
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
    out = pd.DataFrame([{"item": k, "count": v, "pct": v / max(base, 1) * 100} for k, v in bucket.items()])
    return out.sort_values(["count", "item"], ascending=[False, True]).reset_index(drop=True)

def familiarity_metric(df, platform_cols):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        vals = df[col].fillna("").astype(str).str.lower()
        hits = vals.str.contains("familiar", na=False)
        rows.append({"platform": platform, "count": int(hits.sum()), "pct": percent(int(hits.sum()), base)})
    return pd.DataFrame(rows).sort_values(["pct", "platform"], ascending=[False, True])

def binary_platform_metric(df, platform_cols, positive_values=None):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        s = df[col].astype(str)
        hits = s.isin(positive_values or [])
        rows.append({"platform": platform, "count": int(hits.sum()), "pct": percent(int(hits.sum()), base)})
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
    tom_vals = parse_open_awareness(df["Q10"] if "Q10" in df.columns else pd.Series([], dtype=object), list(names))
    if not tom_vals.empty:
        names.update(tom_vals["platform"].tolist())
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

def usage_platform_metric(df, journey):
    if "Q19A" not in df.columns:
        return pd.DataFrame(columns=["platform", "count", "pct"])
    vals = df["Q19A"].fillna("").astype(str).str.strip()
    vals = vals[vals.ne("")]
    if vals.empty:
        return pd.DataFrame(columns=["platform", "count", "pct"])
    out = vals.value_counts().reset_index()
    out.columns = ["platform", "count"]
    out["pct"] = out["count"] / max(len(df), 1) * 100
    return out

def build_brand_health(df, qmap, journey):
    frames = []
    aided = parse_multiselect_counts(df["Q12"]).rename(columns={"item": "platform"}) if "Q12" in df.columns else pd.DataFrame(columns=["platform", "count", "pct"])
    fam = familiarity_metric(df, get_platform_cols(df, qmap, "Q14"))
    consider = binary_platform_metric(df, get_platform_cols(df, qmap, "Q15"), positive_values=["Selected"])
    used = usage_platform_metric(df, journey)

    mapping = [
        ("Awareness", aided[["platform", "pct"]] if not aided.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Familiarity", fam[["platform", "pct"]] if not fam.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Consideration", consider[["platform", "pct"]] if not consider.empty else pd.DataFrame(columns=["platform", "pct"])),
        ("Recent / Usage Proxy", used[["platform", "pct"]] if not used.empty else pd.DataFrame(columns=["platform", "pct"])),
    ]

    for stage_name, stage_df in mapping:
        if not stage_df.empty:
            temp = stage_df.copy()
            temp["stage"] = stage_name
            frames.append(temp)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["platform", "pct", "stage"])

def filter_platform_df(df, selected_platforms):
    if df is None or df.empty:
        return df
    if not selected_platforms or "All" in selected_platforms:
        return df
    if "platform" in df.columns:
        return df[df["platform"].isin(selected_platforms)]
    return df

def plot_bar(df, x, y, color=None, height=430, orientation="v", color_sequence=None):
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        height=height,
        text_auto=".1f",
        color_discrete_sequence=color_sequence,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=5, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        xaxis_title="",
        yaxis_title="",
        font=dict(size=13, color="#1f2937"),
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
        st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        return

    pivot = matrix_df.pivot_table(index=index_col, columns=col_col, values=value_col, fill_value=0, aggfunc="sum")
    if pivot.empty:
        st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        return

    fig = px.imshow(
        pivot,
        aspect="auto",
        text_auto=".0f",
        color_continuous_scale=[
            [0.0, "#edfdf9"],
            [0.25, "#d8f7f1"],
            [0.5, "#acece2"],
            [0.75, "#70d9cb"],
            [1.0, "#42c7b8"],
        ],
        height=height,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=5, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar_title="Count",
        font=dict(size=12, color="#1f2937"),
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_brand_health(df):
    if df.empty:
        st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        return

    top_platforms = (
        df.groupby("platform")["pct"]
        .max()
        .sort_values(ascending=False)
        .head(6)
        .index
        .tolist()
    )
    chart_df = df[df["platform"].isin(top_platforms)]

    fig = px.bar(
        chart_df,
        x="stage",
        y="pct",
        color="platform",
        barmode="group",
        height=500,
        text_auto=".1f",
        color_discrete_sequence=["#42c7b8", "#20b8a7", "#7fded4", "#14213d", "#64b5f6", "#9ca3af"],
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=5, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="Percent of respondents",
        legend_title_text="",
        font=dict(size=13, color="#1f2937"),
    )
    fig.update_traces(marker_line_width=0, cliponaxis=False)
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

def awareness_funnel_df(tom_df, spont_df, aided_df):
    frames = []
    for name, source_df in [("TOM", tom_df), ("Spontaneous", spont_df), ("Aided", aided_df)]:
        if not source_df.empty:
            temp = source_df[["platform", "pct"]].copy()
            temp["stage"] = name
            frames.append(temp)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["platform", "pct", "stage"])

def conversion_table(brand_health_df):
    if brand_health_df.empty:
        return pd.DataFrame()
    pivot = brand_health_df.pivot_table(index="platform", columns="stage", values="pct", fill_value=0).reset_index()

    stage_order = [c for c in ["Awareness", "Familiarity", "Consideration", "Recent / Usage Proxy"] if c in pivot.columns]
    for i in range(1, len(stage_order)):
        prev_stage = stage_order[i - 1]
        curr_stage = stage_order[i]
        conv_col = f"{curr_stage} / {prev_stage}"
        pivot[conv_col] = np.where(
            pivot[prev_stage] > 0,
            round((pivot[curr_stage] / pivot[prev_stage]) * 100, 1),
            np.nan
        )
    return pivot

# =================================================
# LOAD DATA
# =================================================
st.sidebar.title("Dashboard Controls")

if not BUYBACK_DEFAULT.exists() or not REFURB_DEFAULT.exists():
    st.error("Excel files not found in the repo. Make sure both files are inside the 'data' folder in GitHub.")
    st.code(
        "data/\n"
        "├── Live Brand Study - CASHIFY Buyback - Final data.xlsx\n"
        "└── Live Brand Study - CASHIFY - Refurbished_data.xlsx"
    )
    st.stop()

buy_df, buy_map, ref_df, ref_map = load_datasets(BUYBACK_DEFAULT, REFURB_DEFAULT)

journey = st.sidebar.radio("Consumer Journey", ["Buyback", "Refurbished"])
df = buy_df.copy() if journey == "Buyback" else ref_df.copy()
qmap = buy_map if journey == "Buyback" else ref_map

def mfilter(label, col):
    vals = sorted([v for v in df[col].dropna().astype(str).unique().tolist() if v.strip()])
    return st.sidebar.multiselect(label, ["All"] + vals, default=["All"])

city = mfilter("City / Tier", "Q1") if "Q1" in df.columns else ["All"]
gender = mfilter("Gender", "Q2") if "Q2" in df.columns else ["All"]
age = mfilter("Age Bucket", "Q3") if "Q3" in df.columns else ["All"]
income = mfilter("Household Income", "Q8") if "Q8" in df.columns else ["All"]
work = mfilter("Working Status", "Q7") if "Q7" in df.columns else ["All"]

filtered = filter_df(df, city, gender, age, income, work)

# =================================================
# METRICS
# =================================================
tom, spontaneous, aided = awareness_bundle(filtered, qmap)
consider_df = binary_platform_metric(filtered, get_platform_cols(filtered, qmap, "Q15"), positive_values=["Selected"])
nps_df = nps_table(filtered, get_platform_cols(filtered, qmap, "Q16"))
brand_health_df = build_brand_health(filtered, qmap, journey)
source_df = source_matrix(filtered, qmap)
awareness_funnel = awareness_funnel_df(tom, spontaneous, aided)

platform_options = sorted(set(
    list(tom["platform"]) + list(spontaneous["platform"]) + list(aided["platform"]) +
    list(consider_df["platform"]) + list(nps_df["platform"]) +
    list(brand_health_df["platform"]) + list(source_df["platform"])
)) if any([
    not tom.empty, not spontaneous.empty, not aided.empty,
    not consider_df.empty, not nps_df.empty, not brand_health_df.empty, not source_df.empty
]) else []

platform_filter = st.sidebar.multiselect(
    "Platform",
    ["All"] + platform_options,
    default=["All"]
)

tom = filter_platform_df(tom, platform_filter)
spontaneous = filter_platform_df(spontaneous, platform_filter)
aided = filter_platform_df(aided, platform_filter)
consider_df = filter_platform_df(consider_df, platform_filter)
nps_df = filter_platform_df(nps_df, platform_filter)
brand_health_df = filter_platform_df(brand_health_df, platform_filter)
awareness_funnel = filter_platform_df(awareness_funnel, platform_filter)
if not source_df.empty and "platform" in source_df.columns and platform_filter and "All" not in platform_filter:
    source_df = source_df[source_df["platform"].isin(platform_filter)]

cashify_tom = tom.loc[tom["platform"].str.lower().eq("cashify"), "pct"].max() if not tom.empty else 0
cashify_aw = aided.loc[aided["platform"].str.lower().eq("cashify"), "pct"].max() if not aided.empty else 0
cashify_cons = consider_df.loc[consider_df["platform"].str.lower().eq("cashify"), "pct"].max() if not consider_df.empty else 0
cashify_nps = nps_df.loc[nps_df["platform"].str.lower().eq("cashify"), "nps"].max() if not nps_df.empty else np.nan

# =================================================
# HEADER
# =================================================
st.markdown(f"""
<div class="hero">
    <div style="
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        gap:1rem;
        flex-wrap:wrap;
    ">
        <div style="flex:1; min-width:320px;">
            <h1 style="margin:0 0 0.4rem 0;">Cashify Consumer Intelligence Dashboard</h1>
            <div class="hero-sub">
                Consumer view for the <b>{journey}</b> journey across awareness, brand strength, consideration, recommendation, source of awareness, and choice drivers.
            </div>
        </div>

        <div style="width:220px; flex:0 0 220px;">
            <div style="
                background: rgba(255,255,255,0.96);
                border-radius: 20px;
                padding: 0.9rem 1rem 0.85rem 1rem;
                box-shadow: 0 10px 24px rgba(20, 33, 61, 0.08);
            ">
                <div style="font-size:0.78rem; color:#6b7280; margin-bottom:0.18rem;">Filtered Sample</div>
                <div style="font-size:1.9rem; font-weight:800; color:#14213d; line-height:1.05;">{len(filtered)}</div>
                <div style="font-size:0.75rem; color:#6b7280; margin-top:0.15rem;">Respondents in current view</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("Cashify TOM", f"{cashify_tom:.1f}%", "Mentioned first")
with k2:
    kpi("Cashify Aided Awareness", f"{cashify_aw:.1f}%", "Recognised from list")
with k3:
    kpi("Cashify Consideration", f"{cashify_cons:.1f}%", "In next-time shortlist")
with k4:
    kpi("Cashify NPS", "NA" if pd.isna(cashify_nps) else f"{cashify_nps:.1f}", "Recommendation score")

tabs = st.tabs([
    "Overview",
    "Awareness",
    "Brand Health",
    "Consideration & NPS",
    "Sources",
    "Drivers & Barriers",
    "Data View",
])

# =================================================
# OVERVIEW
# =================================================
with tabs[0]:
    st.markdown('<div class="section-pill">Overview</div>', unsafe_allow_html=True)
    st.subheader("Study Overview & Sample Snapshot")
    st.markdown('<div class="section-note">Profile of the filtered respondents.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.0, 1.15])

    with left:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">How to read this dashboard</h4>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-note">
            <b>Awareness</b> shows which brands people know.<br>
            <b>Brand Health</b> shows platform strength across key stages.<br>
            <b>Consideration & NPS</b> shows shortlist inclusion and recommendation strength.<br>
            <b>Sources</b> shows where awareness is coming from.<br>
            <b>Drivers & Barriers</b> shows why people choose or avoid a platform.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Respondent Profile</h4>', unsafe_allow_html=True)
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
            color_sequence=["#42c7b8", "#20b8a7", "#7fded4", "#14213d", "#9ca3af"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# AWARENESS
# =================================================
with tabs[1]:
    st.markdown('<div class="section-pill">Awareness</div>', unsafe_allow_html=True)
    st.subheader("Saliency / Brand Awareness Analysis")
    st.markdown('<div class="section-note">How visible Cashify is relative to competing platforms.</div>', unsafe_allow_html=True)

    top_row_left, top_row_right = st.columns([1.2, 0.8])

    with top_row_left:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Awareness Funnel</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Compares platforms across Top-of-Mind, Spontaneous, and Aided awareness stages.</div>', unsafe_allow_html=True)
        if not awareness_funnel.empty:
            fig = px.bar(
                awareness_funnel,
                x="stage",
                y="pct",
                color="platform",
                barmode="group",
                height=460,
                text_auto=".1f",
                color_discrete_sequence=["#42c7b8", "#20b8a7", "#7fded4", "#14213d", "#64b5f6", "#9ca3af"],
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=5, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="",
                yaxis_title="Percent of respondents",
                legend_title_text="",
                font=dict(size=13, color="#1f2937"),
            )
            fig.update_traces(marker_line_width=0, cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with top_row_right:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Awareness Table</h4>', unsafe_allow_html=True)
        if not awareness_funnel.empty:
            aw_pivot = awareness_funnel.pivot_table(index="platform", columns="stage", values="pct", fill_value=0).reset_index()
            st.dataframe(aw_pivot, use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)

    with a1:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Top-of-Mind Recall</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Which brand respondents mention first without seeing a list.</div>', unsafe_allow_html=True)
        plot_bar(
            tom.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=430,
            color_sequence=["#42c7b8"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Spontaneous Awareness</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">All brands respondents recall on their own, without prompting.</div>', unsafe_allow_html=True)
        plot_bar(
            spontaneous.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=430,
            color_sequence=["#20b8a7"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with a3:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Aided Awareness</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Brands respondents recognise after seeing a prompted list.</div>', unsafe_allow_html=True)
        plot_bar(
            aided.sort_values("pct", ascending=True).tail(10),
            x="pct",
            y="platform",
            orientation="h",
            height=430,
            color_sequence=["#14213d"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# BRAND HEALTH
# =================================================
with tabs[2]:
    st.markdown('<div class="section-pill">Brand Health</div>', unsafe_allow_html=True)
    st.subheader("Brand Health Funnel")
    st.markdown('<div class="section-note">Awareness, Familiarity, Consideration, and platform-usage proxy with conversion ratios.</div>', unsafe_allow_html=True)

    bhl, bhr = st.columns([1.25, 0.95])

    with bhl:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Brand Health by Stage</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Compare how strong each platform is across the key stages.</div>', unsafe_allow_html=True)
        plot_brand_health(brand_health_df)
        st.markdown("</div>", unsafe_allow_html=True)

    with bhr:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Stage Table with Conversions</h4>', unsafe_allow_html=True)
        conv = conversion_table(brand_health_df)
        if not conv.empty:
            st.dataframe(conv, use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# CONSIDERATION & NPS
# =================================================
with tabs[3]:
    st.markdown('<div class="section-pill">Consideration & NPS</div>', unsafe_allow_html=True)
    st.subheader("Consideration & Recommendation")
    st.markdown('<div class="section-note">Shortlist inclusion and recommendation strength.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Consideration Set</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Platforms respondents would consider the next time they buy or sell.</div>', unsafe_allow_html=True)
        plot_bar(
            consider_df.sort_values("pct", ascending=True),
            x="pct",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#42c7b8"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">NPS by Platform</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Recommendation strength measured as Promoters minus Detractors.</div>', unsafe_allow_html=True)
        plot_bar(
            nps_df.sort_values("nps", ascending=True),
            x="nps",
            y="platform",
            orientation="h",
            height=470,
            color_sequence=["#14213d"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel" style="margin-top:0.9rem;"><h4 style="margin-top:0;">Promoter / Passive / Detractor Split</h4>', unsafe_allow_html=True)
    st.markdown('<div class="chart-note">Breakdown of each platform’s recommendation profile.</div>', unsafe_allow_html=True)
    if not nps_df.empty:
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
            color_sequence=["#42c7b8", "#9ca3af", "#14213d"]
        )
    else:
        st.markdown('<div class="empty-note">No data available for this view.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# SOURCES
# =================================================
with tabs[4]:
    st.markdown('<div class="section-pill">Sources</div>', unsafe_allow_html=True)
    st.subheader("Source of Awareness")
    st.markdown('<div class="section-note">Where awareness is being built across channels.</div>', unsafe_allow_html=True)

    s1, s2 = st.columns([1.3, 0.8])

    with s1:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Platform × Source Heatmap</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Channels associated with awareness for each platform.</div>', unsafe_allow_html=True)
        plot_heatmap(source_df, "platform", "source", "count", height=540)
        st.markdown("</div>", unsafe_allow_html=True)

    with s2:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Top Awareness Sources</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Strongest awareness-building channels overall.</div>', unsafe_allow_html=True)
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
            color_sequence=["#20b8a7"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# DRIVERS & BARRIERS
# =================================================
with tabs[5]:
    st.markdown('<div class="section-pill">Drivers & Barriers</div>', unsafe_allow_html=True)
    st.subheader("Choice Drivers, Barriers & Category Fears")
    st.markdown('<div class="section-note">Why people choose a platform, what blocks Cashify, and what category fears matter most.</div>', unsafe_allow_html=True)

    d1, d2 = st.columns(2)

    with d1:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Why Cashify was chosen</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Ranked reasons respondents chose Cashify, where available.</div>', unsafe_allow_html=True)
        chosen_cashify = ranking_weighted_scores(filtered, qmap, "Q20")
        if chosen_cashify.empty:
            st.markdown('<div class="empty-note">No ranked Cashify choice data available for this view.</div>', unsafe_allow_html=True)
        else:
            plot_bar(
                chosen_cashify.sort_values("weighted_score", ascending=True),
                x="weighted_score",
                y="factor",
                orientation="h",
                height=450,
                color_sequence=["#42c7b8"]
            )
            st.dataframe(chosen_cashify, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Why another platform was chosen</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">Ranked reasons respondents chose a competing platform instead.</div>', unsafe_allow_html=True)
        chosen_other = ranking_weighted_scores(filtered, qmap, "Q21A")
        if chosen_other.empty:
            st.markdown('<div class="empty-note">No competitor choice data available for this view.</div>', unsafe_allow_html=True)
        else:
            plot_bar(
                chosen_other.sort_values("weighted_score", ascending=True),
                x="weighted_score",
                y="factor",
                orientation="h",
                height=450,
                color_sequence=["#14213d"]
            )
            st.dataframe(chosen_other, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns(2)

    with b1:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Barriers to choosing Cashify</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">What stopped respondents from choosing Cashify.</div>', unsafe_allow_html=True)

        barriers = parse_multiselect_counts(filtered["Q21B"]) if "Q21B" in filtered.columns else pd.DataFrame(columns=["item", "count", "pct"])

        if barriers.empty:
            if journey == "Buyback":
                st.markdown('<div class="empty-note">No Buyback barrier responses were captured in the dataset.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-note">No barrier data available for this view.</div>', unsafe_allow_html=True)
        else:
            plot_bar(
                barriers.sort_values("pct", ascending=True),
                x="pct",
                y="item",
                orientation="h",
                height=420,
                color_sequence=["#14213d"]
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="panel"><h4 style="margin-top:0;">Category Drivers & Fears</h4>', unsafe_allow_html=True)
        st.markdown('<div class="chart-note">What matters most in the category and what hesitations consumers have.</div>', unsafe_allow_html=True)

        driver_col = "Q24" if "Q24" in filtered.columns else ("Q22" if "Q22" in filtered.columns else None)

        st.markdown("**Top category drivers**")
        if driver_col:
            if driver_col == "Q24":
                q24_cols = [c for c in filtered.columns if re.fullmatch(r"Q24_\d+", str(c))]
                rows = []
                for col in q24_cols:
                    label = extract_platform_name(qmap.get(col, col))
                    count = filtered[col].astype(str).str.strip().replace("nan", "").ne("").sum()
                    rows.append({"item": label, "count": int(count), "pct": percent(int(count), len(filtered))})
                driver_df = pd.DataFrame(rows).sort_values(["count", "item"], ascending=[False, True]) if rows else pd.DataFrame(columns=["item", "count", "pct"])
            else:
                driver_df = parse_multiselect_counts(filtered[driver_col])

            if driver_df.empty:
                st.markdown('<div class="empty-note">No category driver data available for this view.</div>', unsafe_allow_html=True)
            else:
                plot_bar(
                    driver_df.sort_values("pct", ascending=True).tail(10),
                    x="pct",
                    y="item",
                    orientation="h",
                    height=240,
                    color_sequence=["#42c7b8"]
                )
        else:
            st.markdown('<div class="empty-note">No category driver variable found in this dataset.</div>', unsafe_allow_html=True)

        st.markdown("**Biggest category fears / hesitations**")
        fear_df = parse_multiselect_counts(filtered["Q23"]) if "Q23" in filtered.columns else pd.DataFrame(columns=["item", "count", "pct"])
        if fear_df.empty:
            st.markdown('<div class="empty-note">No fear data available for this view.</div>', unsafe_allow_html=True)
        else:
            plot_bar(
                fear_df.sort_values("pct", ascending=True).tail(10),
                x="pct",
                y="item",
                orientation="h",
                height=240,
                color_sequence=["#20b8a7"]
            )
        st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# DATA VIEW
# =================================================
with tabs[6]:
    st.markdown('<div class="section-pill">Data View</div>', unsafe_allow_html=True)
    st.subheader("Underlying Data")

    d1, d2 = st.columns(2)
    with d1:
        st.metric("Rows in current view", len(filtered))
    with d2:
        st.metric("Columns", filtered.shape[1])

    show_cols = st.multiselect(
        "Select columns to display",
        options=list(filtered.columns),
        default=list(filtered.columns[:12]) if len(filtered.columns) >= 12 else list(filtered.columns)
    )

    view_df = filtered[show_cols].copy() if show_cols else filtered.copy()
    st.dataframe(view_df, use_container_width=True, height=520)

st.markdown(
    '<div class="footer-note">Built for a classroom MIS live project. Because the current sample size is limited, segment cuts should be interpreted directionally.</div>',
    unsafe_allow_html=True
)
