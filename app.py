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

st.markdown("""
<style>
:root {
    --bg: #f6f8fb;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --accent: #14b8a6;
    --border: #e2e8f0;
    --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}
.main { background: linear-gradient(180deg, #f8fafc 0%, #f5f7fb 100%); }
.block-container { padding-top: 1.3rem; padding-bottom: 2rem; max-width: 1400px; }
.hero {
    background: linear-gradient(135deg, rgba(20,184,166,0.12), rgba(14,165,233,0.10));
    border: 1px solid var(--border); border-radius: 24px; padding: 1.4rem 1.5rem;
    box-shadow: var(--shadow); margin-bottom: 1rem;
}
.card, .kpi-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 22px;
    padding: 1rem; box-shadow: var(--shadow);
}
.kpi-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.3rem; }
.kpi-value { color: var(--text); font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
.kpi-note, .small-note { color: var(--muted); font-size: 0.8rem; }
.section-tag {
    display: inline-block; font-size: 0.78rem; color: #0f766e; background: rgba(20,184,166,0.12);
    border: 1px solid rgba(20,184,166,0.18); padding: 0.22rem 0.55rem; border-radius: 999px; margin-bottom: 0.65rem;
}
.insight {
    border-left: 4px solid var(--accent); background: rgba(255,255,255,0.8);
    border-radius: 14px; padding: 0.85rem 0.95rem; color: var(--text); margin-top: 0.5rem;
}
.footer-note { color: var(--muted); font-size: 0.78rem; margin-top: 1rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border-right: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

BUYBACK_DEFAULT = "Live Brand Study - CASHIFY Buyback - Final data.xlsx"
REFURB_DEFAULT = "Live Brand Study - CASHIFY - Refurbished_data.xlsx"

def split_multi(value):
    if pd.isna(value):
        return []
    txt = str(value).replace("\n", ",").strip()
    if not txt or txt.lower() in {"none", "no", "nope", "nan"}:
        return []
    return [p.strip() for p in re.split(r"\s*,\s*", txt) if p.strip() and p.strip().lower() not in {"none", "never heard of any"}]

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
    data = pd.read_excel(file_obj, sheet_name="Sheet0")
    return data, build_question_map(dict_df)

def load_refurbished(file_obj):
    dict_df = pd.read_excel(file_obj, sheet_name="Column Dictionary")
    data = pd.read_excel(file_obj, sheet_name="Sheet0")
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
    out = pd.DataFrame([{"item": k, "count": v, "pct": v / max(base, 1) * 100} for k, v in bucket.items()])
    if not out.empty:
        out = out.sort_values(["count", "item"], ascending=[False, True]).reset_index(drop=True)
    return out

def familiarity_metric(df, platform_cols):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        vals = df[col].fillna("").astype(str).str.lower()
        hits = vals.str.contains("familiar", na=False)
        rows.append({"platform": platform, "count": int(hits.sum()), "pct": percent(int(hits.sum()), base)})
    return pd.DataFrame(rows).sort_values(["pct", "platform"], ascending=[False, True])

def binary_platform_metric(df, platform_cols, positive_values=None, any_non_blank=False):
    rows = []
    base = len(df)
    for platform, col in platform_cols.items():
        s = df[col]
        if any_non_blank:
            hits = s.astype(str).str.strip().replace("nan", "").ne("") & s.notna()
        else:
            hits = s.astype(str).isin(positive_values or [])
        rows.append({"platform": platform, "count": int(hits.sum()), "pct": percent(int(hits.sum()), base)})
    return pd.DataFrame(rows).sort_values(["pct", "platform"], ascending=[False, True])

def nps_table(df, platform_cols):
    rows = []
    for platform, col in platform_cols.items():
        scores = df[col].apply(safe_int).dropna()
        if scores.empty:
            rows.append({"platform": platform, "nps": np.nan, "promoters": 0, "passives": 0, "detractors": 0, "base": 0})
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

def filter_df(df, city, gender, age, income, work, section, group):
    out = df.copy()
    for col, selected in {"Q1": city, "Q2": gender, "Q3": age, "Q8": income, "Q7": work, "Q7A": section, "Q7B": group}.items():
        if selected and "All" not in selected and col in out.columns:
            out = out[out[col].astype(str).isin([str(x) for x in selected])]
    return out

def platform_universe(qmap, df):
    names = set()
    for prefix in ["Q13", "Q14", "Q15", "Q16"]:
        for p in get_platform_cols(df, qmap, prefix).keys():
            names.add(p)
    aided = parse_multiselect_counts(df["Q12"]) if "Q12" in df.columns else pd.DataFrame()
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
        spont_agg = spont
    else:
        spont_agg = spont.groupby("platform", as_index=False)["count"].sum()
        spont_agg["pct"] = spont_agg["count"] / max(len(df), 1) * 100
        spont_agg = spont_agg.sort_values(["count", "platform"], ascending=[False, True])
    aided = parse_multiselect_counts(df["Q12"]).rename(columns={"item": "platform"}) if "Q12" in df.columns else pd.DataFrame(columns=["platform", "count", "pct"])
    return tom, spont_agg, aided

def build_health_funnel(df, qmap):
    aided = parse_multiselect_counts(df["Q12"]).rename(columns={"item": "platform"}) if "Q12" in df.columns else pd.DataFrame(columns=["platform", "count", "pct"])
    fam = familiarity_metric(df, get_platform_cols(df, qmap, "Q14"))
    consider = binary_platform_metric(df, get_platform_cols(df, qmap, "Q15"), positive_values=["Selected"])
    recent = binary_platform_metric(df, get_platform_cols(df, qmap, "Q16"), any_non_blank=True)
    frames = []
    for stage_name, stage_df in [
        ("Awareness", aided[["platform", "pct"]]),
        ("Familiarity", fam[["platform", "pct"]]),
        ("Intent / Recent", consider[["platform", "pct"]]),
        ("NPS Base", recent[["platform", "pct"]]),
    ]:
        tmp = stage_df.copy()
        tmp["stage"] = stage_name
        frames.append(tmp)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["platform", "pct", "stage"])

def plot_bar(df, x, y, color=None, height=360, orientation="v"):
    if df is None or df.empty:
        st.info("Not enough data to show this view for the current selection.")
        return
    fig = px.bar(df, x=x, y=y, color=color, orientation=orientation, height=height, text_auto=".1f")
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        xaxis_title="",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_heatmap(matrix_df, index_col, col_col, value_col, height=420):
    if matrix_df.empty:
        st.info("Not enough data to show this view for the current selection.")
        return
    pivot = matrix_df.pivot_table(index=index_col, columns=col_col, values=value_col, fill_value=0, aggfunc="sum")
    fig = px.imshow(pivot, aspect="auto", text_auto=".0f", color_continuous_scale="Tealgrn", height=height)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar_title="Count"
    )
    st.plotly_chart(fig, use_container_width=True)

def kpi(label, value, note=""):
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
        unsafe_allow_html=True
    )

st.sidebar.title("Dashboard Controls")
use_upload = st.sidebar.toggle("Use uploaded Excel files", value=False)

if use_upload:
    buy_file = st.sidebar.file_uploader("Upload Buyback workbook", type=["xlsx"], key="buy")
    ref_file = st.sidebar.file_uploader("Upload Refurbished workbook", type=["xlsx"], key="ref")
    if not (buy_file and ref_file):
        st.markdown(
            '<div class="hero"><h2 style="margin-bottom:0.3rem;">Cashify Consumer Intelligence Dashboard</h2><p class="small-note" style="margin-bottom:0;">Upload both Excel files from the sidebar to start the dashboard.</p></div>',
            unsafe_allow_html=True
        )
        st.stop()
else:
    buy_path = Path(BUYBACK_DEFAULT)
    ref_path = Path(REFURB_DEFAULT)
    if not (buy_path.exists() and ref_path.exists()):
        st.error("Default Excel files were not found in the same folder as app.py. Turn on uploads in the sidebar or place both workbooks beside the app.")
        st.stop()
    buy_file = str(buy_path)
    ref_file = str(ref_path)

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
section = mfilter("Section", "Q7A")
group = mfilter("Group", "Q7B")
filtered = filter_df(df, city, gender, age, income, work, section, group)

with st.sidebar.expander("Column Dictionary", expanded=False):
    st.caption("Use this reference to decode survey columns such as Q1, Q2, Q7A, and Q7B.")
    dict_view = pd.DataFrame(
        [(k, v) for k, v in qmap.items()],
        columns=["Column", "Question"]
    )
    dict_query = st.text_input("Search column or question", value="", key="dict_search")
    if dict_query:
        mask = dict_view["Column"].astype(str).str.contains(dict_query, case=False, na=False) | dict_view["Question"].astype(str).str.contains(dict_query, case=False, na=False)
        dict_view = dict_view[mask]
    st.dataframe(dict_view, use_container_width=True, hide_index=True, height=320)

st.markdown(f"""
<div class="hero">
    <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
        <div>
            <div class="section-tag">MIS + DSS</div>
            <h1 style="margin:0 0 0.35rem 0;">Cashify Consumer Intelligence Dashboard</h1>
            <p style="margin:0; color:#475569;">Premium decision-support dashboard for the <b>{journey}</b> journey. Use the sidebar filters to compare awareness, funnel performance, NPS, sources, drivers, and barriers.</p>
        </div>
        <div style="min-width:230px;">
            <div class="kpi-card">
                <div class="kpi-label">Filtered Sample</div>
                <div class="kpi-value">{len(filtered)}</div>
                <div class="kpi-note">Current respondent base in view</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tom, spontaneous, aided = awareness_bundle(filtered, qmap)
consider_df = binary_platform_metric(filtered, get_platform_cols(filtered, qmap, "Q15"), positive_values=["Selected"])
nps_df = nps_table(filtered, get_platform_cols(filtered, qmap, "Q16"))
cashify_tom = tom.loc[tom["platform"].str.lower().eq("cashify"), "pct"].max() if not tom.empty else 0
cashify_aw = aided.loc[aided["platform"].str.lower().eq("cashify"), "pct"].max() if not aided.empty else 0
cashify_cons = consider_df.loc[consider_df["platform"].str.lower().eq("cashify"), "pct"].max() if not consider_df.empty else 0
cashify_nps = nps_df.loc[nps_df["platform"].str.lower().eq("cashify"), "nps"].max() if not nps_df.empty else np.nan

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Cashify TOM", f"{cashify_tom:.1f}%", "Top-of-mind saliency")
with c2:
    kpi("Cashify Aided Awareness", f"{cashify_aw:.1f}%", "Recognition from prompted list")
with c3:
    kpi("Cashify Consideration", f"{cashify_cons:.1f}%", "Included in next-time shortlist")
with c4:
    kpi("Cashify NPS", "NA" if pd.isna(cashify_nps) else f"{cashify_nps:.1f}", "Promoters minus detractors")

tabs = st.tabs([
    "Overview",
    "Awareness",
    "Brand Health",
    "Consideration & NPS",
    "Sources",
    "Drivers & Barriers",
    "Decision Support"
])

with tabs[0]:
    st.markdown('<div class="section-tag">Context</div>', unsafe_allow_html=True)
    st.subheader("Study Overview & Sample Snapshot")
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">How to use this dashboard</h4>
            <ul>
                <li>Switch between <b>Buyback</b> and <b>Refurbished</b> using the sidebar.</li>
                <li>Apply demographic filters to create directional cuts by segment.</li>
                <li>Use each tab as the direct evidence base for the PPT report.</li>
                <li>Given the current base size, use segment findings as <b>directional</b> rather than final population claims.</li>
            </ul>
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
        question_help = "<br>".join([f"<b>{col}</b>: {qmap.get(col, col)}" for col in demo_cols])
        demo_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        plot_bar(demo_df, x="Option", y="Count", color="Question", height=420)
        st.caption("Question key for this chart")
        st.markdown(f"<div class='small-note'>{question_help}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="section-tag">Awareness</div>', unsafe_allow_html=True)
    st.subheader("Saliency / Brand Awareness Analysis")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Top-of-Mind Recall</h4>', unsafe_allow_html=True)
        plot_bar(tom.sort_values("pct", ascending=True).tail(10), x="pct", y="platform", orientation="h", height=360)
        st.markdown('</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Spontaneous Awareness</h4>', unsafe_allow_html=True)
        plot_bar(spontaneous.sort_values("pct", ascending=True).tail(10), x="pct", y="platform", orientation="h", height=360)
        st.markdown('</div>', unsafe_allow_html=True)
    with a3:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Aided Awareness</h4>', unsafe_allow_html=True)
        plot_bar(aided.sort_values("pct", ascending=True).tail(10), x="pct", y="platform", orientation="h", height=360)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="section-tag">Funnel</div>', unsafe_allow_html=True)
    st.subheader("Brand Health Funnel")
    funnel_df = build_health_funnel(filtered, qmap)
    if not funnel_df.empty:
        top_platforms = funnel_df.groupby("platform")["pct"].max().sort_values(ascending=False).head(6).index.tolist()
        chart_df = funnel_df[funnel_df["platform"].isin(top_platforms)]
        fig = px.line(chart_df, x="stage", y="pct", color="platform", markers=True, height=420)
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Percent of respondents",
            legend_title_text=""
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            funnel_df.pivot_table(index="platform", columns="stage", values="pct", fill_value=0).reset_index(),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Not enough data to show the funnel.")

with tabs[3]:
    st.markdown('<div class="section-tag">Conversion</div>', unsafe_allow_html=True)
    st.subheader("Consideration & NPS")
    l1, l2 = st.columns(2)
    with l1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Consideration Set</h4>', unsafe_allow_html=True)
        plot_bar(consider_df.sort_values("pct", ascending=True), x="pct", y="platform", orientation="h", height=420)
        st.markdown('</div>', unsafe_allow_html=True)
    with l2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">NPS by Platform</h4>', unsafe_allow_html=True)
        plot_bar(nps_df.sort_values("nps", ascending=True), x="nps", y="platform", orientation="h", height=420)
        st.markdown('</div>', unsafe_allow_html=True)
    if not nps_df.empty:
        melt = nps_df.melt(
            id_vars=["platform", "base", "nps"],
            value_vars=["promoters", "passives", "detractors"],
            var_name="segment",
            value_name="count"
        )
        st.markdown("#### Promoter / Passive / Detractor Split")
        plot_bar(melt, x="platform", y="count", color="segment", height=360)

with tabs[4]:
    st.markdown('<div class="section-tag">Channels</div>', unsafe_allow_html=True)
    st.subheader("Source of Awareness")
    source_df = source_matrix(filtered, qmap)
    s1, s2 = st.columns([1.25, 0.75])
    with s1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Platform × Source Heatmap</h4>', unsafe_allow_html=True)
        plot_heatmap(source_df, "platform", "source", "count", height=470)
        st.markdown('</div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Top Awareness Sources</h4>', unsafe_allow_html=True)
        top_sources = source_df.groupby("source", as_index=False)["count"].sum().sort_values("count", ascending=True) if not source_df.empty else pd.DataFrame()
        plot_bar(top_sources.tail(10), x="count", y="source", orientation="h", height=470)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[5]:
    st.markdown('<div class="section-tag">Drivers</div>', unsafe_allow_html=True)
    st.subheader("Choice Drivers, Barriers & Category Fears")
    d1, d2 = st.columns(2)
    with d1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Why Cashify was chosen</h4>', unsafe_allow_html=True)
        chosen_cashify = ranking_weighted_scores(filtered, qmap, "Q20")
        if chosen_cashify.empty:
            st.info("No rank-based Cashify choice data available in the current view.")
        else:
            plot_bar(chosen_cashify.sort_values("weighted_score", ascending=True), x="weighted_score", y="factor", orientation="h", height=420)
            st.dataframe(chosen_cashify, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with d2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Why another platform was chosen</h4>', unsafe_allow_html=True)
        chosen_other = ranking_weighted_scores(filtered, qmap, "Q21A")
        if chosen_other.empty:
            st.info("No competitor rank-based data available in the current view.")
        else:
            plot_bar(chosen_other.sort_values("weighted_score", ascending=True), x="weighted_score", y="factor", orientation="h", height=420)
            st.dataframe(chosen_other, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Barriers to choosing Cashify</h4>', unsafe_allow_html=True)
        barriers = parse_multiselect_counts(filtered["Q21B"]) if "Q21B" in filtered.columns else pd.DataFrame()
        plot_bar(barriers.sort_values("pct", ascending=True), x="pct", y="item", orientation="h", height=380)
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="card"><h4 style="margin-top:0;">Category Drivers & Fears</h4>', unsafe_allow_html=True)
        driver_col = "Q24" if "Q24" in filtered.columns else ("Q22" if "Q22" in filtered.columns else None)
        if driver_col:
            driver_df = parse_multiselect_counts(filtered[driver_col])
            st.markdown("**Top category drivers**")
            plot_bar(driver_df.sort_values("pct", ascending=True).tail(10), x="pct", y="item", orientation="h", height=240)
        fear_df = parse_multiselect_counts(filtered["Q23"]) if "Q23" in filtered.columns else pd.DataFrame()
        st.markdown("**Biggest category fears / hesitations**")
        plot_bar(fear_df.sort_values("pct", ascending=True).tail(10), x="pct", y="item", orientation="h", height=240)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[6]:
    st.markdown('<div class="section-tag">Action</div>', unsafe_allow_html=True)
    st.subheader("Decision Support Summary")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">Summary</h4>
            <ul>
                <li>Use awareness views to identify whether Cashify has a saliency problem or a conversion problem.</li>
                <li>Use the funnel to pinpoint where Cashify loses users: awareness, familiarity, or consideration.</li>
                <li>Use NPS to determine whether the main issue lies in experience or pre-usage conversion friction.</li>
                <li>Use source data to decide which communication channels deserve heavier investment.</li>
                <li>Use drivers and barriers to shape messaging, trust-builders, and service design improvements.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card">
            <h4 style="margin-top:0;">Way Forward</h4>
            <ul>
                <li><b>Build trust cues harder:</b> foreground quality checks, verification, warranty, pricing transparency, or data safety by journey.</li>
                <li><b>Close the familiarity gap:</b> if aided awareness is high but familiarity is low, invest in explanatory communication, not only reach.</li>
                <li><b>Win shortlist inclusion:</b> if awareness exists but consideration is weak, sharpen positioning around the top visible category drivers.</li>
                <li><b>Fix the biggest barrier first:</b> the barrier chart gives the cleanest first management priority.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="footer-note">Built for a classroom MIS live project. With the current sample size, segment cuts should be interpreted directionally.</div>', unsafe_allow_html=True)
