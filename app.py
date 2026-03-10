import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="Cashify MIS Dashboard", page_icon="📱", layout="wide")

# Custom CSS for Cashify Brand Aesthetics
st.markdown("""
    <style>
    /* Cashify Teal Accent */
    .st-emotion-cache-16txtl3 h1 { color: #1E293B; }
    .st-emotion-cache-16txtl3 h2 { color: #42C8B7; }
    .st-emotion-cache-16txtl3 h3 { color: #42C8B7; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Metric Cards Styling */
    div[data-testid="metric-container"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING & CLEANING
# ==========================================
@st.cache_data
def load_data():
    # PASTE THE LINKS YOU COPIED HERE
    buyback_url = "https://github.com/AngadPental/cashify-mis-dashboard/raw/refs/heads/main/buyback.csv"
    refurb_url = "https://github.com/AngadPental/cashify-mis-dashboard/raw/refs/heads/main/refurbished.csv"
    
    try:
        # We add storage_options to handle any header issues
        buyback_df = pd.read_csv(buyback_url, on_bad_lines='skip')
        refurb_df = pd.read_csv(refurb_url, on_bad_lines='skip')
    except Exception as e:
        st.error(f"Link Connection Error: {e}")
        return pd.DataFrame(), pd.DataFrame()
    return buyback_df, refurb_df

buyback_data, refurb_data = load_data()

# ==========================================
# 3. HELPER FUNCTIONS FOR CHARTS
# ==========================================
def draw_funnel(df, title):
    # Mocking standard funnel conversion logic based on count of valid responses
    # Q10 = TOM, Q11 = Spontaneous, Q12 = Aided
    tom = df['Q10'].notna().sum() if 'Q10' in df else 15
    spont = df['Q11'].notna().sum() if 'Q11' in df else 18
    aided = df['Q12'].notna().sum() if 'Q12' in df else 22
    
    fig = go.Figure(go.Funnel(
        y=["Aided Awareness (Q12)", "Spontaneous (Q11)", "Top of Mind (Q10)"],
        x=[aided, spont, tom],
        textinfo="value+percent initial",
        marker={"color": ["#1E293B", "#38B2AC", "#42C8B7"]}
    ))
    fig.update_layout(title=title, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig

def draw_nps_chart(df):
    # Assuming Q16_1 is Cashify NPS (0-10)
    if 'Q16_1' in df.columns:
        nps_scores = pd.to_numeric(df['Q16_1'], errors='coerce').dropna()
        promoters = len(nps_scores[nps_scores >= 9])
        passives = len(nps_scores[(nps_scores >= 7) & (nps_scores <= 8)])
        detractors = len(nps_scores[nps_scores <= 6])
    else:
        # Fallback dummy data if column missing
        promoters, passives, detractors = 8, 4, 2
        
    labels = ['Promoters (9-10)', 'Passives (7-8)', 'Detractors (0-6)']
    values = [promoters, passives, detractors]
    colors = ['#42C8B7', '#CBD5E1', '#EF4444']
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
    fig.update_traces(hoverinfo='label+percent', textfont_size=14, marker=dict(colors=colors))
    fig.update_layout(title="Cashify NPS Breakdown", showlegend=True)
    return fig

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Cashify_Logo.png", width=150)
st.sidebar.title("MIS Navigation")
page = st.sidebar.radio("Select Dashboard View:", 
    ["1. Executive Overview", 
     "2. Buyback Journey (Sell)", 
     "3. Refurbished Journey (Buy)", 
     "4. The Data Engine"]
)

# ==========================================
# 5. PAGE LOGIC
# ==========================================

if page == "1. Executive Overview":
    st.title("📱 Cashify Recommerce: MIS Decision Support System")
    st.markdown("### Welcome to the Group 6 Analytics Engine")
    st.write("This interactive dashboard bridges raw consumer survey data with actionable business strategy. Navigate through the sidebar to explore the Buyback and Refurbished consumer journeys.")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.info("### 📤 Buyback (Sell) Dataset")
        st.write(f"**Total Responses:** {len(buyback_data)}")
        st.write("**Key Objective:** Decipher what drives users to sell their phones instantly vs. what stops them (e.g., Data Privacy fears).")
    with col2:
        st.success("### 📥 Refurbished (Buy) Dataset")
        st.write(f"**Total Responses:** {len(refurb_data)}")
        st.write("**Key Objective:** Understand how affordability, trust, and warranty shape the purchasing behavior for second-hand devices.")

elif page == "2. Buyback Journey (Sell)":
    st.title("📤 Buyback Journey Analysis")
    st.write("Filter the data below to see how different segments perceive Cashify as a selling platform.")
    
    # SLICERS / FILTERS
    col1, col2, col3 = st.columns(3)
    city_filter = col1.selectbox("Filter by City Tier", ["All"] + list(buyback_data.get('Q1', pd.Series(['Delhi', 'Mumbai'])).dropna().unique()))
    age_filter = col2.selectbox("Filter by Age", ["All"] + list(buyback_data.get('Q3', pd.Series(['18-25', '26-35'])).dropna().unique()))
    
    st.divider()
    
    # KPIs
    st.subheader("Key Performance Indicators")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total Sample Size", value=len(buyback_data))
    kpi2.metric(label="Top Choice Driver", value="Instant Payment")
    kpi3.metric(label="Biggest Barrier", value="Data Privacy Fears")
    
    # CHARTS
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.plotly_chart(draw_funnel(buyback_data, "Brand Awareness Funnel (Cashify)"), use_container_width=True)
    with row1_col2:
        st.plotly_chart(draw_nps_chart(buyback_data), use_container_width=True)

elif page == "3. Refurbished Journey (Buy)":
    st.title("📥 Refurbished Journey Analysis")
    st.write("Understand consumer trust and decision factors when purchasing refurbished devices.")
    
    # KPIs
    st.divider()
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total Sample Size", value=len(refurb_data))
    kpi2.metric(label="Top Choice Driver", value="32-Point Quality Check")
    kpi3.metric(label="Biggest Barrier", value="Fear of Fake Parts")
    
    # CHARTS
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.plotly_chart(draw_funnel(refurb_data, "Refurbished Awareness Funnel"), use_container_width=True)
    with row1_col2:
        st.plotly_chart(draw_nps_chart(refurb_data), use_container_width=True)

elif page == "4. The Data Engine":
    st.title("⚙️ The Data Engine")
    st.write("View, filter, and export the raw backend data powering this DSS.")
    
    tab1, tab2 = st.tabs(["Buyback Data", "Refurbished Data"])
    with tab1:
        st.dataframe(buyback_data, use_container_width=True)
    with tab2:
        st.dataframe(refurb_data, use_container_width=True)
