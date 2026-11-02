"""
ProductPilot - Streamlit Application
=====================================
Main entry point for the ProductPilot analytics dashboard.
Provides a multi-page layout with sidebar navigation.
Premium SaaS Design — Light Mode
"""

import streamlit as st
import pandas as pd
import os
import sys
import json
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_scoring import compute_priority_scores, get_feature_explanation, validate_weights
from src.risk_scoring import compute_risk_scores, compute_release_risk, generate_recommendations
from src.bloom_filter import BloomFilter, evaluate_bloom_filter
from src.dgim import DGIM, run_dgim_demo
from src.custom_data_processor import (
    process_user_dataframe,
    process_excel_file,
    get_sample_custom_dataset,
    generate_csv_template,
    detect_column_mapping,
)

# --- Page config ---
st.set_page_config(
    page_title="ProductPilot | Analytics Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Premium CSS Theme ---
st.markdown("""
<style>
    /* ============================================================
       PRODUCTPILOT — PREMIUM LIGHT SAAS THEME
       Inspired by Linear, Notion, Vercel dashboards
       ============================================================ */

    /* Google Font — Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* === GLOBAL FOUNDATION === */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        color: #0f172a !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(226, 232, 240, 0.6);
    }

    /* === TYPOGRAPHY === */
    .stApp h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
        letter-spacing: -0.6px !important;
        font-size: 1.85rem !important;
        line-height: 1.2 !important;
        margin-bottom: 0.15rem !important;
    }
    .stApp h2 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.4px !important;
        font-size: 1.35rem !important;
    }
    .stApp h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
        font-size: 1.1rem !important;
    }
    .stApp p, .stApp span, .stApp label, .stApp li {
        color: #475569;
        line-height: 1.6;
    }
    .stApp .stCaption p {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }

    /* === PAGE TITLE ACCENT === */
    .page-title-container {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 6px;
    }
    .page-icon-badge {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }
    .page-icon-badge.blue { background: linear-gradient(135deg, #dbeafe, #bfdbfe); }
    .page-icon-badge.green { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
    .page-icon-badge.amber { background: linear-gradient(135deg, #fef3c7, #fde68a); }
    .page-icon-badge.red { background: linear-gradient(135deg, #ffe4e6, #fecdd3); }
    .page-icon-badge.purple { background: linear-gradient(135deg, #ede9fe, #ddd6fe); }
    .page-icon-badge.cyan { background: linear-gradient(135deg, #cffafe, #a5f3fc); }

    /* === SECTION HEADERS === */
    .section-header {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 20px 0 10px;
        margin: 16px 0 12px;
        border-bottom: none;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-header::before {
        content: '';
        width: 3px;
        height: 16px;
        border-radius: 3px;
        background: linear-gradient(180deg, #3b82f6, #06b6d4);
        display: inline-block;
    }

    /* === KPI METRIC CARDS === */
    .kpi-card {
        background: #ffffff !important;
        border-radius: 14px;
        padding: 20px 22px;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02) !important;
        margin-bottom: 8px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04) !important;
        border-color: #cbd5e1 !important;
    }
    .kpi-card .kpi-icon {
        font-size: 1.35rem;
        margin-bottom: 8px;
        display: block;
    }
    .kpi-card .kpi-label {
        font-size: 0.72rem;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .kpi-card .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a !important;
        line-height: 1.15;
        letter-spacing: -0.5px;
    }
    /* Color accent strips */
    .kpi-card.blue::after { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .kpi-card.green::after { background: linear-gradient(90deg, #10b981, #34d399); }
    .kpi-card.amber::after { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .kpi-card.red::after { background: linear-gradient(90deg, #ef4444, #f87171); }
    .kpi-card.purple::after { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
    .kpi-card.cyan::after { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
    .kpi-card.teal::after { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }

    /* === ALERT CARDS === */
    .alert-card {
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        line-height: 1.5;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        border: 1px solid;
        transition: all 0.15s ease;
    }
    .alert-card:hover {
        transform: translateX(3px);
    }
    .alert-high {
        background: #fff5f5 !important;
        border-color: #fed7d7 !important;
        color: #9b2c2c !important;
    }
    .alert-medium {
        background: #fffff0 !important;
        border-color: #fefcbf !important;
        color: #975a16 !important;
    }
    .alert-low {
        background: #f0fff4 !important;
        border-color: #c6f6d5 !important;
        color: #276749 !important;
    }

    /* ========================================================
       PREMIUM SIDEBAR DESIGN
       Clean minimal sidebar with icon navigation
       ======================================================== */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 1px 0 12px rgba(0,0,0,0.02) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        background: #ffffff !important;
        padding: 1rem 0.8rem 0 !important;
    }

    /* Sidebar text defaults */
    section[data-testid="stSidebar"] * {
        color: #475569;
    }
    section[data-testid="stSidebar"] p {
        font-size: 0.88rem !important;
    }

    /* Radio navigation group */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 2px !important;
    }

    /* Nav item base */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }

    /* Nav item hover */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: #f8fafc !important;
        border-color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover span {
        color: #0f172a !important;
    }

    /* Nav item text */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label span,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label div {
        color: #64748b !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        letter-spacing: -0.1px !important;
    }

    /* ACTIVE Nav item */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, #eff6ff, #f0f9ff) !important;
        border: 1px solid #bfdbfe !important;
        box-shadow: 0 1px 4px rgba(59, 130, 246, 0.06) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) span {
        color: #1d4ed8 !important;
        font-weight: 700 !important;
    }

    /* Radio dot accent */
    section[data-testid="stSidebar"] input[type="radio"] {
        accent-color: #3b82f6 !important;
    }

    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid #f1f5f9 !important;
        margin: 14px 0 !important;
    }

    /* === DATA TABLES === */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        overflow: hidden;
    }

    /* === FORM CONTROLS === */
    .stSelectbox label, .stSlider label, .stTextInput label, .stNumberInput label {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* Slider track */
    .stSlider [data-testid="stThumbValue"] {
        color: #3b82f6 !important;
        font-weight: 700 !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

    /* === STATUS BADGE === */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
    }
    .status-badge.online {
        background: #ecfdf5;
        color: #059669;
    }
    .status-badge.warning {
        background: #fffbeb;
        color: #d97706;
    }
    .status-badge.error {
        background: #fef2f2;
        color: #dc2626;
    }

    /* === INFO PANEL === */
    .info-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin: 8px 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #f1f5f9;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        color: #64748b !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }

    /* Expanders */
    .stExpander {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }

</style>
""", unsafe_allow_html=True)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def style_fig(fig, title=None):
    """Style Plotly figures with premium aesthetic."""
    layout_update = dict(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
        margin=dict(l=40, r=20, t=50, b=40),
        title_font=dict(size=15, color="#0f172a"),
    )
    if title:
        layout_update["title"] = title
    fig.update_layout(**layout_update)
    fig.update_xaxes(gridcolor="#f1f5f9", color="#475569", zerolinecolor="#e2e8f0", gridwidth=1)
    fig.update_yaxes(gridcolor="#f1f5f9", color="#475569", zerolinecolor="#e2e8f0", gridwidth=1)
    return fig


def kpi_card(label, value, color="blue", icon=""):
    """Render a premium KPI card."""
    icon_html = f'<span class="kpi-icon">{icon}</span>' if icon else ''
    return f"""
    <div class="kpi-card {color}">
        {icon_html}
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """


def section_header(text):
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def page_header(icon, title, subtitle, badge_color="blue"):
    """Render a premium page header with icon badge."""
    st.markdown(f"""
    <div class="page-title-container">
        <div class="page-icon-badge {badge_color}">{icon}</div>
        <div>
            <h1 style="margin:0 !important; padding:0 !important;">{title}</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(subtitle)


# ================================================================
# DATA LOADING & ACTIVE DATASET RESOLUTION
# ================================================================

@st.cache_data(ttl=300)
def load_processed_data():
    """Load processed Parquet files into pandas DataFrames."""
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    data = {}
    try:
        data["features"] = pd.read_parquet(os.path.join(processed_dir, "features"))
        data["requests"] = pd.read_parquet(os.path.join(processed_dir, "requests"))
        data["tasks"] = pd.read_parquet(os.path.join(processed_dir, "tasks"))
        data["releases"] = pd.read_parquet(os.path.join(processed_dir, "releases"))
        data["loaded"] = True
    except Exception as e:
        data["loaded"] = False
        data["error"] = str(e)
    return data

# Initialize Session State
if "active_data_source" not in st.session_state:
    st.session_state["active_data_source"] = "demo"
if "custom_dataset" not in st.session_state:
    st.session_state["custom_dataset"] = None

def get_active_data():
    """Resolve active datasets depending on whether custom user data or demo data is selected."""
    if st.session_state.get("active_data_source") == "custom" and st.session_state.get("custom_dataset") is not None:
        ds = st.session_state["custom_dataset"]
        return ds["features"], ds["requests"], ds["tasks"], ds["releases"], ds.get("name", "Custom Dataset"), True

    demo = load_processed_data()
    if not demo.get("loaded"):
        sample = get_sample_custom_dataset()
        return sample["features"], sample["requests"], sample["tasks"], sample["releases"], "Sample Dataset", False

    return demo["features"], demo["requests"], demo["tasks"], demo["releases"], "Big Data Pipeline Demo", False

features_df, requests_df, tasks_df, releases_df, active_dataset_name, is_custom_data = get_active_data()

def render_custom_data_banner():
    """Render a persistent banner across pages when user custom data is active."""
    if is_custom_data:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                    border: 1px solid #10b981; border-radius: 12px; padding: 12px 18px; margin-bottom: 20px;
                    display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(16,185,129,0.08);">
            <div>
                <span style="font-weight: 800; color: #065f46; font-size: 0.92rem;">✨ Active Dataset: {active_dataset_name}</span>
                <span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 700; margin-left: 8px;">USER DATA</span>
                <div style="font-size: 0.78rem; color: #047857; margin-top: 2px;">
                    {len(features_df):,} Features · {len(tasks_df):,} Tasks · {len(releases_df):,} Releases · {len(requests_df):,} Requests · Live analytical scoring active
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ================================================================
# SIDEBAR NAVIGATION
# ================================================================
with st.sidebar:
    # Brand Header with gradient icon
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; padding: 6px 6px 18px; border-bottom: 1px solid #f1f5f9; margin-bottom: 16px;">
        <div style="
            background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            width: 42px; height: 42px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; color: #fff;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
            flex-shrink: 0;
        ">🚀</div>
        <div>
            <div style="font-size: 1.12rem; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; line-height: 1.25;">ProductPilot</div>
            <div style="font-size: 0.68rem; font-weight: 600; color: #94a3b8; letter-spacing: 0.5px; text-transform: uppercase;">Analytics Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section label
    st.markdown('<div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #cbd5e1; margin: 4px 0 8px 8px;">Navigation</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation Menu",
        [
            "📊  Executive Overview",
            "⭐  Feature Prioritization",
            "⚠️  Delivery Risks",
            "🔬  Bloom Filter Lab",
            "📈  DGIM Streaming",
            "💡  Recommendations",
            "🔧  Pipeline & Evaluation",
            "📥  User Data Workspace",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Active Dataset Toggle
    st.markdown('<div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #cbd5e1; margin: 4px 0 8px 8px;">Active Dataset</div>', unsafe_allow_html=True)
    has_custom = st.session_state["custom_dataset"] is not None
    custom_radio_label = f"📂 My Custom Data ({len(features_df)} feats)" if has_custom else "📂 My Custom Data (Empty)"

    data_mode_choice = st.radio(
        "Select Active Data Mode",
        ["🚀 Big Data Demo", custom_radio_label],
        index=1 if (st.session_state.get("active_data_source") == "custom" and has_custom) else 0,
        label_visibility="collapsed"
    )

    if data_mode_choice.startswith("📂"):
        if not has_custom:
            st.info("💡 No custom dataset loaded yet. Go to **User Data Workspace** to upload or input data.")
            st.session_state["active_data_source"] = "demo"
        else:
            if st.session_state.get("active_data_source") != "custom":
                st.session_state["active_data_source"] = "custom"
                st.rerun()
    else:
        if st.session_state.get("active_data_source") != "demo":
            st.session_state["active_data_source"] = "demo"
            st.rerun()

    st.markdown("---")

    # Dynamic System Status Panel
    total_active_records = len(features_df) + len(tasks_df) + len(releases_df) + len(requests_df)
    engine_badge = "User Data Engine" if is_custom_data else "PySpark Pipeline"
    format_badge = "Custom Upload" if is_custom_data else "Parquet / Big Data"

    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-top: 4px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 10px;">
            <span style="font-size:0.7rem; font-weight:700; color:#1e293b; text-transform:uppercase; letter-spacing:0.6px;">System Status</span>
            <span class="status-badge online">● Active</span>
        </div>
        <div style="font-size: 0.76rem; color: #64748b; line-height: 1.5;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span>Engine</span>
                <span style="font-weight:600; color:#0f172a;">{engine_badge}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span>Format</span>
                <span style="font-weight:600; color:#0f172a;">{format_badge}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Records</span>
                <span style="font-weight:600; color:#0f172a;">{total_active_records:,}</span>
            </div>
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e2e8f0; font-size: 0.66rem; color: #94a3b8; text-align: center;">
            {active_dataset_name[:28]}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# PAGE: Executive Overview
# ================================================================
if page == "📊  Executive Overview":
    page_header("📊", "Executive Overview",
                "Real-time summary of product health and project delivery — all metrics computed from data",
                "blue")

    render_custom_data_banner()

    import plotly.express as px
    import plotly.graph_objects as go

    # KPI Row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_card("Total Requests", f"{len(requests_df):,}", "blue", "📋"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_card("Features Analyzed", f"{len(features_df):,}", "cyan", "⭐"), unsafe_allow_html=True)
    with col3:
        open_tasks = len(tasks_df[tasks_df["task_status"].isin(["Not Started", "In Progress", "Blocked"])])
        st.markdown(kpi_card("Open Tasks", f"{open_tasks:,}", "amber", "📝"), unsafe_allow_html=True)
    with col4:
        overdue_tasks = len(tasks_df[tasks_df["overdue_days"] > 0])
        st.markdown(kpi_card("Overdue Tasks", f"{overdue_tasks:,}", "red", "⏰"), unsafe_allow_html=True)

    # KPI Row 2
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        if "release_status" in releases_df.columns:
            delayed_rels = len(releases_df[releases_df["release_status"] == "Delayed"])
        else:
            delayed_rels = 0
        st.markdown(kpi_card("Delayed Releases", f"{delayed_rels}", "red", "🚩"), unsafe_allow_html=True)
    with col6:
        completed = len(tasks_df[tasks_df["task_status"] == "Completed"])
        total = len(tasks_df)
        rate = f"{completed/total*100:.0f}%" if total > 0 else "0%"
        st.markdown(kpi_card("Completion Rate", rate, "green", "✅"), unsafe_allow_html=True)
    with col7:
        blocked = len(tasks_df[tasks_df["task_status"] == "Blocked"])
        st.markdown(kpi_card("Blocked Tasks", f"{blocked:,}", "amber", "🚫"), unsafe_allow_html=True)
    with col8:
        released_count = len(releases_df[releases_df["release_status"] == "Released"])
        st.markdown(kpi_card("Releases Shipped", f"{released_count}", "green", "🚀"), unsafe_allow_html=True)

    st.markdown("")

    # Charts row
    section_header("Feature & Task Distribution")
    col_a, col_b = st.columns(2)

    with col_a:
        if "product" in features_df.columns:
            prod_counts = features_df["product"].value_counts().reset_index()
            prod_counts.columns = ["Product", "Count"]
            fig = px.bar(
                prod_counts, x="Product", y="Count",
                color="Count",
                color_continuous_scale=["#93c5fd", "#3b82f6", "#1e3a5f"],
                title="Features by Product"
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)

    with col_b:
        status_counts = tasks_df["task_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {
            "Completed": "#10b981", "In Progress": "#3b82f6",
            "Not Started": "#94a3b8", "Blocked": "#ef4444", "Cancelled": "#6b7280"
        }
        fig2 = px.pie(
            status_counts, names="Status", values="Count",
            color="Status", color_discrete_map=color_map,
            title="Task Status Distribution"
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    # Management alerts
    section_header("Management Alerts")
    has_alert = False
    if overdue_tasks > 0:
        has_alert = True
        st.markdown(
            f'<div class="alert-card alert-high">🔴 <strong>{overdue_tasks}</strong> task(s) are overdue. '
            f'Immediate review recommended.</div>', unsafe_allow_html=True
        )
    if blocked > 0:
        has_alert = True
        st.markdown(
            f'<div class="alert-card alert-high">🔴 <strong>{blocked}</strong> task(s) are blocked. '
            f'Investigate dependency chains.</div>', unsafe_allow_html=True
        )
    if delayed_rels > 0:
        has_alert = True
        st.markdown(
            f'<div class="alert-card alert-medium">🟡 <strong>{delayed_rels}</strong> release(s) are delayed. '
            f'Review estimation and scoping processes.</div>', unsafe_allow_html=True
        )
    if not has_alert:
        st.markdown(
            '<div class="alert-card alert-low">🟢 No critical alerts. Operations are within normal parameters.</div>',
            unsafe_allow_html=True
        )

    # Request volume trend
    section_header("Request Volume & Demand Trend")
    rendered_trend = False
    if "request_date" in requests_df.columns and len(requests_df) > 1:
        try:
            req_trend = requests_df.copy()
            req_trend["request_date"] = pd.to_datetime(req_trend["request_date"], errors="coerce")
            monthly = req_trend.groupby(req_trend["request_date"].dt.to_period("M")).size().reset_index()
            monthly.columns = ["Month", "Requests"]
            monthly["Month"] = monthly["Month"].astype(str)
            if len(monthly) > 1:
                fig3 = px.area(
                    monthly, x="Month", y="Requests",
                    title="Monthly Feature Requests",
                )
                fig3.update_traces(
                    line_color="#3b82f6",
                    fillcolor="rgba(59, 130, 246, 0.08)",
                    line_width=2.5
                )
                st.plotly_chart(style_fig(fig3), use_container_width=True)
                rendered_trend = True
        except Exception:
            rendered_trend = False

    if not rendered_trend and len(features_df) > 0:
        top_dem = features_df.sort_values("customer_demand", ascending=False).head(10)
        fig3 = px.bar(
            top_dem, x="feature_name", y="customer_demand",
            color="customer_demand",
            color_continuous_scale=["#93c5fd", "#3b82f6", "#1e3a5f"],
            title="Customer Demand by Feature (Top 10)"
        )
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig3), use_container_width=True)


# ================================================================
# PAGE: Feature Prioritization
# ================================================================
elif page == "⭐  Feature Prioritization":
    page_header("⭐", "Feature Prioritization",
                "Configurable weighted scoring to rank product features — scores are recommendations",
                "amber")

    render_custom_data_banner()

    import plotly.express as px
    import plotly.graph_objects as go

    # Weight configuration
    section_header("Scoring Weights")
    st.markdown("Adjust the weights below. They will be normalized to sum to 100%.")

    wcol1, wcol2, wcol3, wcol4, wcol5 = st.columns(5)
    with wcol1:
        w_demand = st.slider("Customer Demand", 0, 100, 30, key="w_demand")
    with wcol2:
        w_bv = st.slider("Business Value", 0, 100, 25, key="w_bv")
    with wcol3:
        w_urg = st.slider("Urgency", 0, 100, 20, key="w_urg")
    with wcol4:
        w_align = st.slider("Strategic Alignment", 0, 100, 15, key="w_align")
    with wcol5:
        w_eff = st.slider("Effort Efficiency", 0, 100, 10, key="w_eff")

    user_weights = {
        "customer_demand": w_demand,
        "business_value": w_bv,
        "urgency": w_urg,
        "strategic_alignment": w_align,
        "effort_efficiency": w_eff,
    }

    # Compute scores
    scored = compute_priority_scores(features_df, user_weights)

    # Filters
    section_header("Filters")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        products = ["All"] + sorted(scored["product"].dropna().unique().tolist())
        sel_product = st.selectbox("Product", products)
    with fcol2:
        categories = ["All"] + sorted(scored["category"].dropna().unique().tolist())
        sel_category = st.selectbox("Category", categories)
    with fcol3:
        statuses = ["All"] + sorted(scored["status"].dropna().unique().tolist())
        sel_status = st.selectbox("Status", statuses)
    with fcol4:
        priorities = ["All", "Critical", "High", "Medium", "Low"]
        sel_priority = st.selectbox("Priority", priorities)

    filtered = scored.copy()
    if sel_product != "All":
        filtered = filtered[filtered["product"] == sel_product]
    if sel_category != "All":
        filtered = filtered[filtered["category"] == sel_category]
    if sel_status != "All":
        filtered = filtered[filtered["status"] == sel_status]
    if sel_priority != "All":
        filtered = filtered[filtered["priority_category"] == sel_priority]

    # Summary KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("Features Shown", f"{len(filtered):,}", "blue", "📊"), unsafe_allow_html=True)
    with k2:
        avg_score = filtered["priority_score"].mean() if len(filtered) > 0 else 0
        st.markdown(kpi_card("Avg Priority Score", f"{avg_score:.1f}", "cyan", "📈"), unsafe_allow_html=True)
    with k3:
        crit_count = len(filtered[filtered["priority_category"] == "Critical"])
        st.markdown(kpi_card("Critical Features", f"{crit_count}", "red", "🔥"), unsafe_allow_html=True)
    with k4:
        high_count = len(filtered[filtered["priority_category"] == "High"])
        st.markdown(kpi_card("High Priority", f"{high_count}", "amber", "⚡"), unsafe_allow_html=True)

    # Charts
    chart1, chart2 = st.columns(2)
    with chart1:
        fig = px.histogram(
            filtered, x="priority_score", nbins=20,
            color_discrete_sequence=["#3b82f6"],
            title="Priority Score Distribution"
        )
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with chart2:
        if len(filtered) > 0:
            fig2 = px.scatter(
                filtered.head(50), x="estimated_effort_hours", y="priority_score",
                color="priority_category",
                color_discrete_map={"Critical": "#ef4444", "High": "#f59e0b",
                                    "Medium": "#3b82f6", "Low": "#94a3b8"},
                size="customer_demand" if "customer_demand" in filtered.columns else None,
                hover_name="feature_name",
                title="Priority vs Effort (Top 50)"
            )
            st.plotly_chart(style_fig(fig2), use_container_width=True)

    # Ranked table
    section_header("Ranked Features")
    display_cols = [
        "rank", "feature_id", "feature_name", "product", "priority_score",
        "priority_category", "customer_demand", "business_value",
        "estimated_effort_hours", "recommended_action"
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[available_cols].head(50),
        use_container_width=True,
        hide_index=True
    )

    # Feature detail
    section_header("Feature Detail")
    if len(filtered) > 0:
        feature_options = filtered["feature_id"].tolist()[:50]
        selected_feat = st.selectbox("Select a feature to see score explanation", feature_options)
        if selected_feat:
            row = filtered[filtered["feature_id"] == selected_feat].iloc[0]
            explanation = get_feature_explanation(row, user_weights)
            st.markdown(explanation)


# ================================================================
# PAGE: Project Delivery Risks
# ================================================================
elif page == "⚠️  Delivery Risks":
    page_header("⚠️", "Project Delivery Risks",
                "Transparent risk analysis for project tasks and releases",
                "red")

    render_custom_data_banner()

    import plotly.express as px

    # Compute risk scores
    tasks_scored = compute_risk_scores(tasks_df, releases_df)
    releases_scored = compute_release_risk(releases_df, tasks_scored)

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("Total Tasks", f"{len(tasks_scored):,}", "blue", "📋"), unsafe_allow_html=True)
    with k2:
        completed = len(tasks_scored[tasks_scored["task_status"] == "Completed"])
        st.markdown(kpi_card("Completed", f"{completed:,}", "green", "✅"), unsafe_allow_html=True)
    with k3:
        in_progress = len(tasks_scored[tasks_scored["task_status"] == "In Progress"])
        st.markdown(kpi_card("In Progress", f"{in_progress:,}", "cyan", "🔄"), unsafe_allow_html=True)
    with k4:
        overdue = len(tasks_scored[tasks_scored["overdue_days"] > 0])
        st.markdown(kpi_card("Overdue", f"{overdue:,}", "amber", "⏰"), unsafe_allow_html=True)
    with k5:
        high_risk = len(tasks_scored[tasks_scored["risk_category"] == "High"])
        st.markdown(kpi_card("High Risk", f"{high_risk:,}", "red", "🔥"), unsafe_allow_html=True)

    # Filters
    section_header("Filters")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        projects = ["All"] + sorted(tasks_scored["project_id"].dropna().unique().tolist())
        sel_project = st.selectbox("Project", projects)
    with fc2:
        rel_ids = ["All"] + sorted(tasks_scored["release_id"].dropna().unique().tolist())
        sel_release = st.selectbox("Release", rel_ids)
    with fc3:
        statuses = ["All"] + sorted(tasks_scored["task_status"].dropna().unique().tolist())
        sel_task_status = st.selectbox("Task Status", statuses)
    with fc4:
        risks = ["All", "High", "Medium", "Low"]
        sel_risk = st.selectbox("Risk Level", risks)

    tf = tasks_scored.copy()
    if sel_project != "All":
        tf = tf[tf["project_id"] == sel_project]
    if sel_release != "All":
        tf = tf[tf["release_id"] == sel_release]
    if sel_task_status != "All":
        tf = tf[tf["task_status"] == sel_task_status]
    if sel_risk != "All":
        tf = tf[tf["risk_category"] == sel_risk]

    # Charts
    ch1, ch2 = st.columns(2)
    with ch1:
        risk_dist = tf["risk_category"].value_counts().reset_index()
        risk_dist.columns = ["Risk Category", "Count"]
        fig = px.bar(
            risk_dist, x="Risk Category", y="Count",
            color="Risk Category",
            color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"},
            title="Risk Distribution"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with ch2:
        if "overdue_days" in tf.columns:
            overdue_data = tf[tf["overdue_days"] > 0]
            if len(overdue_data) > 0:
                fig2 = px.histogram(
                    overdue_data, x="overdue_days", nbins=20,
                    color_discrete_sequence=["#ef4444"],
                    title="Overdue Days Distribution"
                )
                st.plotly_chart(style_fig(fig2), use_container_width=True)
            else:
                st.info("No overdue tasks in the current filter selection.")

    # Release risk table
    section_header("Release Delivery Status")
    if not releases_scored.empty:
        rel_display_cols = ["release_id", "release_status", "planned_features",
                           "delivered_features", "delay_days",
                           "feature_delivery_rate", "release_risk"]
        available_rel = [c for c in rel_display_cols if c in releases_scored.columns]
        if available_rel:
            st.dataframe(
                releases_scored[available_rel].sort_values("delay_days", ascending=False).head(30),
                use_container_width=True, hide_index=True
            )

    # High risk tasks
    section_header("High Risk Tasks")
    task_display_cols = ["task_id", "project_id", "task_name", "task_status",
                        "overdue_days", "risk_score", "risk_category", "recommendation"]
    available_task = [c for c in task_display_cols if c in tf.columns]
    st.dataframe(
        tf[available_task].head(30),
        use_container_width=True, hide_index=True
    )


# ================================================================
# PAGE: Bloom Filter Lab
# ================================================================
elif page == "🔬  Bloom Filter Lab":
    page_header("🔬", "Bloom Filter Laboratory",
                "Interactive demonstration of the Bloom Filter probabilistic data structure",
                "purple")

    render_custom_data_banner()

    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("""
    <div class="info-panel">
        <strong>How it works:</strong> A Bloom Filter uses multiple hash functions to map items to positions
        in a bit array. It can tell you with certainty that an item is <strong>not</strong> in the set,
        but can only say an item <strong>might</strong> be in the set (possible false positives).<br><br>
        <strong>Use case:</strong> Efficiently screen incoming feature requests for potential duplicate request IDs
        before performing an expensive database lookup.
    </div>
    """, unsafe_allow_html=True)

    section_header("Configuration")
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        bf_size = st.slider("Bit Array Size", 100, 50000, 10000, step=100)
    with bc2:
        bf_hashes = st.slider("Number of Hash Functions", 1, 15, 5)
    with bc3:
        bf_test_count = st.slider("Test IDs to Check", 10, 5000, 500)

    # Use actual request IDs or feature IDs from active dataset
    if "request_id" in requests_df.columns and len(requests_df) > 0:
        all_request_ids = requests_df["request_id"].dropna().astype(str).tolist()
    else:
        all_request_ids = features_df["feature_id"].dropna().astype(str).tolist()

    half_len = max(1, len(all_request_ids) // 2)
    inserted_ids = all_request_ids[:half_len]
    test_existing = inserted_ids[:min(bf_test_count, len(inserted_ids))]
    test_new_count = max(200, min(bf_test_count, 1000))
    test_new = [f"NEW-REQ-{i:06d}" for i in range(test_new_count)]

    if st.button("🔬 Run Bloom Filter Evaluation", type="primary"):
        with st.spinner("Running evaluation..."):
            results = evaluate_bloom_filter(
                inserted_ids, test_existing, test_new,
                size=bf_size, num_hashes=bf_hashes
            )

        # Results
        section_header("Results")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.markdown(kpi_card("Items Inserted", f"{results['items_inserted']:,}", "blue", "📥"),
                        unsafe_allow_html=True)
        with r2:
            st.markdown(kpi_card("False Positives", f"{results['false_positives']}", "red", "❌"),
                        unsafe_allow_html=True)
        with r3:
            st.markdown(kpi_card("FP Rate (Measured)", f"{results['measured_fp_rate']:.4%}", "amber", "📏"),
                        unsafe_allow_html=True)
        with r4:
            st.markdown(kpi_card("FP Rate (Expected)", f"{results['expected_fp_rate']:.4%}", "cyan", "🎯"),
                        unsafe_allow_html=True)

        # Memory comparison
        section_header("Memory Comparison")
        mem1, mem2, mem3 = st.columns(3)
        with mem1:
            st.markdown(kpi_card("Bloom Filter", f"{results['bloom_memory_bytes']:.0f} bytes", "green", "💾"),
                        unsafe_allow_html=True)
        with mem2:
            st.markdown(kpi_card("Exact Set", f"{results['exact_set_memory_bytes']:,} bytes", "amber", "🗄️"),
                        unsafe_allow_html=True)
        with mem3:
            st.markdown(kpi_card("Memory Savings", f"{results['memory_ratio']:.1f}×", "green", "⚡"),
                        unsafe_allow_html=True)

        # Confusion matrix
        section_header("Accuracy Breakdown")
        conf_data = pd.DataFrame({
            "Category": ["True Positives", "False Negatives", "True Negatives", "False Positives"],
            "Count": [results["true_positives"], results["false_negatives"],
                      results["true_negatives"], results["false_positives"]],
            "Description": [
                "Known items correctly identified",
                "Known items missed (should be 0)",
                "Unknown items correctly rejected",
                "Unknown items falsely matched"
            ]
        })
        st.dataframe(conf_data, use_container_width=True, hide_index=True)

        # Bit array visualization
        section_header("Bit Array State")
        summary = results["bit_summary"]
        st.markdown(f"""
        - **Total bits:** {summary['total_bits']:,}
        - **Set bits (1s):** {summary['set_bits']:,}
        - **Unset bits (0s):** {summary['unset_bits']:,}
        - **Fill ratio:** {summary['fill_ratio']:.2%}
        """)

        # Visual of fill ratio
        fill_data = pd.DataFrame({
            "State": ["Set (1)", "Unset (0)"],
            "Bits": [summary["set_bits"], summary["unset_bits"]]
        })
        fig = px.pie(fill_data, names="State", values="Bits",
                     color="State",
                     color_discrete_map={"Set (1)": "#3b82f6", "Unset (0)": "#e2e8f0"},
                     title="Bit Array Fill Ratio")
        st.plotly_chart(style_fig(fig), use_container_width=True)

        # False positive rate vs size trade-off
        section_header("Trade-off: Bit Array Size vs False Positive Rate")
        tradeoff_data = []
        for test_size in [500, 1000, 2000, 5000, 10000, 20000, 50000]:
            test_result = evaluate_bloom_filter(
                inserted_ids[:500], inserted_ids[:100],
                test_new[:200], size=test_size, num_hashes=bf_hashes
            )
            tradeoff_data.append({
                "Bit Array Size": test_size,
                "FP Rate": test_result["measured_fp_rate"],
                "Memory (bytes)": test_result["bloom_memory_bytes"]
            })
        td = pd.DataFrame(tradeoff_data)
        fig_t = px.line(td, x="Bit Array Size", y="FP Rate",
                        markers=True, title="False Positive Rate vs Bit Array Size")
        fig_t.update_traces(line_color="#3b82f6", marker_color="#1e3a5f")
        st.plotly_chart(style_fig(fig_t), use_container_width=True)

    # Interactive lookup
    section_header("Interactive Lookup")
    st.markdown("Enter a request ID to check if it might already exist:")
    lookup_id = st.text_input("Request ID", placeholder="e.g., REQ-000001 or NEW-REQ-999999")
    if lookup_id:
        bf = BloomFilter(size=bf_size, num_hashes=bf_hashes)
        for rid in inserted_ids[:1000]:
            bf.insert(rid)

        result = bf.lookup(lookup_id)
        if result:
            st.warning(
                f"⚠️ **'{lookup_id}' MIGHT exist** in the database (possible false positive). "
                f"Verify against the exact database before discarding."
            )
        else:
            st.success(f"✅ **'{lookup_id}' DEFINITELY does not exist** in the database.")


# ================================================================
# PAGE: DGIM Streaming
# ================================================================
elif page == "📈  DGIM Streaming":
    page_header("📈", "DGIM Streaming Analytics",
                "Approximate event counting in a sliding window using the DGIM algorithm",
                "green")

    render_custom_data_banner()

    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("""
    <div class="info-panel">
        <strong>DGIM (Datar-Gionis-Indyk-Motwani)</strong> counts 1-bits in a sliding window using
        logarithmic memory instead of storing every event. The oldest bucket is estimated
        at half its size, introducing bounded approximation error (≤50% of the true count
        in the worst case, typically much less).<br><br>
        <strong>Use case:</strong> Monitor incoming event streams (feature requests, blocker reports,
        incidents) and detect volume spikes without storing every individual event.
    </div>
    """, unsafe_allow_html=True)

    section_header("Configuration")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        window_size = st.slider("Window Size", 50, 2000, 500, step=50)
    with dc2:
        stream_length = st.slider("Stream Length", 100, 10000, 2000, step=100)
    with dc3:
        event_probability = st.slider("Event Probability", 0.1, 0.9, 0.4, step=0.05)

    dc4, dc5 = st.columns(2)
    with dc4:
        stream_patterns = ["Random", "Bursty", "All Ones", "All Zeros", "Alternating"]
        if len(tasks_df) > 0:
            stream_patterns.insert(0, "From Active Dataset Tasks (Completed=1, Open/Blocked=0)")
        stream_type = st.selectbox("Stream Pattern", stream_patterns)
    with dc5:
        alert_threshold = st.number_input("Alert Threshold (0 = no alerts)", 0, 5000, 0, step=10)

    if st.button("📈 Run DGIM Simulation", type="primary"):
        import random
        random.seed(42)

        # Generate stream based on pattern
        if stream_type.startswith("From Active Dataset"):
            base_stream = [1 if s == "Completed" else 0 for s in tasks_df["task_status"]]
            if not base_stream:
                base_stream = [1, 0, 1, 0]
            stream = (base_stream * ((stream_length // len(base_stream)) + 1))[:stream_length]
        elif stream_type == "Random":
            stream = [1 if random.random() < event_probability else 0 for _ in range(stream_length)]
        elif stream_type == "Bursty":
            stream = []
            for i in range(stream_length):
                if (i // 100) % 3 == 0:
                    stream.append(1 if random.random() < 0.8 else 0)
                else:
                    stream.append(1 if random.random() < 0.2 else 0)
        elif stream_type == "All Ones":
            stream = [1] * stream_length
        elif stream_type == "All Zeros":
            stream = [0] * stream_length
        else:  # Alternating
            stream = [i % 2 for i in range(stream_length)]

        with st.spinner("Processing stream..."):
            results = run_dgim_demo(
                stream, window_size=window_size,
                alert_threshold=alert_threshold if alert_threshold > 0 else None
            )

        # Results KPIs
        err = results["final_error"]
        mem = results["memory"]
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.markdown(kpi_card("Approx Count", f"{err['approximate_count']}", "blue", "🔢"), unsafe_allow_html=True)
        with r2:
            st.markdown(kpi_card("Exact Count", f"{err['exact_count']}", "green", "✓"), unsafe_allow_html=True)
        with r3:
            st.markdown(kpi_card("Error", f"{err['relative_error_pct']}%", "amber", "📊"), unsafe_allow_html=True)
        with r4:
            st.markdown(kpi_card("Memory Savings", f"{mem['memory_ratio']}×", "green", "⚡"), unsafe_allow_html=True)

        # Snapshots chart
        section_header("Accuracy Over Time")
        snap_df = pd.DataFrame(results["snapshots"])
        if len(snap_df) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=snap_df["position"], y=snap_df["exact_count"],
                name="Exact Count", line=dict(color="#10b981", width=2.5)
            ))
            fig.add_trace(go.Scatter(
                x=snap_df["position"], y=snap_df["approximate_count"],
                name="DGIM Estimate", line=dict(color="#3b82f6", width=2.5, dash="dash")
            ))
            fig.update_layout(
                title="DGIM Estimate vs Exact Count Over Stream",
                xaxis_title="Stream Position",
                yaxis_title="Count in Window",
                legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.8)")
            )
            st.plotly_chart(style_fig(fig), use_container_width=True)

        # Error chart
        if len(snap_df) > 0 and "relative_error_pct" in snap_df.columns:
            fig_err = px.line(
                snap_df, x="position", y="relative_error_pct",
                title="Relative Error Over Time (%)",
                markers=True
            )
            fig_err.update_traces(line_color="#f59e0b")
            fig_err.add_hline(y=50, line_dash="dash", line_color="#ef4444",
                              annotation_text="DGIM worst-case bound (50%)")
            st.plotly_chart(style_fig(fig_err), use_container_width=True)

        # Bucket visualization
        section_header("Current Bucket State")
        buckets = results["buckets"]
        if buckets:
            bucket_df = pd.DataFrame(buckets)
            fig_b = px.bar(
                bucket_df, x="timestamp", y="size",
                color="size",
                color_continuous_scale=["#93c5fd", "#3b82f6", "#1e3a5f"],
                title="DGIM Buckets (Position vs Size)"
            )
            fig_b.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_fig(fig_b), use_container_width=True)

            st.markdown(f"**Total buckets:** {len(buckets)} (vs {window_size} bits in exact storage)")
        else:
            st.info("No buckets — no 1-bits were observed in the current window.")

        # Memory comparison
        section_header("Memory Usage Comparison")
        mem_df = pd.DataFrame({
            "Method": ["DGIM Buckets", "Exact Storage"],
            "Entries": [mem["dgim_entries"], mem["exact_entries"]],
            "Approx Bytes": [mem["dgim_bytes_approx"], mem["exact_bytes_approx"]]
        })
        st.dataframe(mem_df, use_container_width=True, hide_index=True)

        # Alerts
        if results["alerts"]:
            section_header(f"Alerts ({len(results['alerts'])} triggered)")
            for alert in results["alerts"][:10]:
                st.markdown(
                    f'<div class="alert-card alert-high">🔔 {alert["message"]}</div>',
                    unsafe_allow_html=True
                )


# ================================================================
# PAGE: Recommendations
# ================================================================
elif page == "💡  Recommendations":
    page_header("💡", "Management Recommendations",
                "Actionable insights derived from computed analytics — not hardcoded",
                "cyan")

    render_custom_data_banner()

    import plotly.express as px

    # Compute risk data
    tasks_scored = compute_risk_scores(tasks_df, releases_df)
    releases_scored = compute_release_risk(releases_df, tasks_scored)

    recs = generate_recommendations(tasks_scored, releases_scored)

    if not recs:
        st.success("✅ No critical recommendations at this time. All metrics are within acceptable ranges.")
    else:
        for i, rec in enumerate(recs):
            severity_class = f"alert-{rec['severity'].lower()}"
            emoji = "🔴" if rec["severity"] == "High" else ("🟡" if rec["severity"] == "Medium" else "🟢")
            st.markdown(f"""
            <div class="alert-card {severity_class}">
                <strong>{emoji} {rec['type']}</strong> ({rec['count']} items)<br>
                {rec['message']}<br><br>
                <strong>Recommended Action:</strong> {rec['action']}
            </div>
            """, unsafe_allow_html=True)

    # Feature priority recommendations
    section_header("Top Priority Features")
    scored = compute_priority_scores(features_df)
    top_features = scored.head(10)
    if len(top_features) > 0:
        st.markdown("Features recommended for immediate attention based on default scoring weights:")
        display_cols = ["rank", "feature_name", "product", "priority_score",
                       "priority_category", "recommended_action"]
        available = [c for c in display_cols if c in top_features.columns]
        st.dataframe(top_features[available], use_container_width=True, hide_index=True)

    # Release attention
    section_header("Releases Requiring Attention")
    if "release_risk" in releases_scored.columns:
        attention_releases = releases_scored[releases_scored["release_risk"].isin(["High", "Medium"])]
        if len(attention_releases) > 0:
            rel_cols = ["release_id", "release_status", "delay_days",
                       "feature_delivery_rate", "release_risk"]
            available_rel = [c for c in rel_cols if c in attention_releases.columns]
            st.dataframe(
                attention_releases[available_rel].sort_values("delay_days", ascending=False).head(15),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No releases currently require special attention.")

    st.markdown("---")
    st.markdown(
        "*All recommendations are computed from the processed data. They should inform "
        "management decisions but do not replace human judgment.*"
    )


# ================================================================
# PAGE: Pipeline & Evaluation
# ================================================================
elif page == "🔧  Pipeline & Evaluation":
    page_header("🔧", "Data Pipeline & Evaluation",
                "Processing details, data validation, and algorithm evaluation metrics",
                "purple")

    render_custom_data_banner()

    import plotly.express as px

    # Record counts
    section_header("Dataset Record Counts")
    counts_data = {
        "Dataset": ["Feature Requests", "Features", "Tasks", "Releases"],
        "Records": [len(requests_df), len(features_df), len(tasks_df), len(releases_df)],
    }
    counts_df = pd.DataFrame(counts_data)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(counts_df, use_container_width=True, hide_index=True)
    with c2:
        fig = px.bar(counts_df, x="Dataset", y="Records",
                     color_discrete_sequence=["#3b82f6"],
                     title="Records per Dataset")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    # Data quality
    section_header("Data Quality Summary")
    for name, df in [("Features", features_df), ("Requests", requests_df),
                     ("Tasks", tasks_df), ("Releases", releases_df)]:
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        total_cells = df.shape[0] * df.shape[1]
        completeness = (1 - total_nulls / total_cells) * 100 if total_cells > 0 else 100
        st.markdown(f"**{name}**: {df.shape[0]:,} rows × {df.shape[1]} columns | "
                    f"Completeness: {completeness:.1f}%")

    # Spark processing info
    section_header("Spark Processing Details")
    pipeline_info_file = os.path.join(PROJECT_ROOT, "data", "processed", "pipeline_metadata.json")
    if os.path.exists(pipeline_info_file):
        with open(pipeline_info_file) as f:
            pipeline_meta = json.load(f)
        st.json(pipeline_meta)
    else:
        st.info("Pipeline metadata will appear here after running: `python src/spark_pipeline.py`")
        st.markdown("""
        **Spark Configuration:**
        - Mode: `local[*]` (uses all available CPU cores)
        - Driver memory: 2 GB
        - Input format: CSV
        - Output format: Parquet (columnar, compressed)
        """)

    # Bloom Filter evaluation
    section_header("Bloom Filter Evaluation")
    all_ids = requests_df["request_id"].tolist()
    bf_eval = evaluate_bloom_filter(
        all_ids[:2000], all_ids[:500],
        [f"FAKE-{i}" for i in range(500)],
        size=20000, num_hashes=5
    )
    bf_metrics = pd.DataFrame([{
        "Metric": k.replace("_", " ").title(),
        "Value": str(v)
    } for k, v in bf_eval.items() if k not in ("bloom_filter", "bit_summary")])
    st.dataframe(bf_metrics, use_container_width=True, hide_index=True)

    # DGIM evaluation
    section_header("DGIM Accuracy Evaluation")
    import random
    random.seed(42)
    test_stream = [1 if random.random() < 0.4 else 0 for _ in range(2000)]
    dgim_eval = run_dgim_demo(test_stream, window_size=500)
    dgim_error = dgim_eval["final_error"]
    dgim_mem = dgim_eval["memory"]

    dgim_df = pd.DataFrame([
        {"Metric": "Approximate Count", "Value": str(dgim_error["approximate_count"])},
        {"Metric": "Exact Count", "Value": str(dgim_error["exact_count"])},
        {"Metric": "Absolute Error", "Value": str(dgim_error["absolute_error"])},
        {"Metric": "Relative Error %", "Value": f"{dgim_error['relative_error_pct']}%"},
        {"Metric": "DGIM Buckets", "Value": str(dgim_mem["dgim_entries"])},
        {"Metric": "Exact Storage Entries", "Value": str(dgim_mem["exact_entries"])},
        {"Metric": "Memory Savings Ratio", "Value": f"{dgim_mem['memory_ratio']}×"},
    ])
    st.dataframe(dgim_df, use_container_width=True, hide_index=True)

    # Known limitations
    section_header("Known Limitations")
    st.markdown("""
    - **All data is synthetic** — generated with a fixed seed for reproducibility.
    - **Spark runs in local mode** — not a distributed cluster deployment.
    - **Feature scores are heuristic** — based on configurable weighted averages, not predictive models.
    - **Risk scores are rule-based** — transparent but not ML-predicted.
    - **Bloom Filter** produces false positives by design — never use it to automatically discard requests.
    - **DGIM** has bounded approximation error (≤50%) — the oldest bucket is partially estimated.
    - **No real-time streaming** — DGIM demonstration uses simulated streams, not live data.
    """)


# ================================================================
# PAGE: User Data Workspace
# ================================================================
elif page == "📥  User Data Workspace":
    page_header("📥", "User Data Workspace",
                "Input your own product and project data via file upload, interactive forms, or spreadsheet editing — all ProductPilot analytical features run directly on your data",
                "green")

    # Quick Action Bar
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("🚀 Load 1-Click Sample Custom Data", use_container_width=True, type="primary"):
            st.session_state["custom_dataset"] = get_sample_custom_dataset()
            st.session_state["active_data_source"] = "custom"
            st.toast("✅ Loaded 1-click SaaS sample dataset (10 features, 10 tasks, 3 releases)!")
            st.rerun()
    with q2:
        template_csv = generate_csv_template()
        st.download_button(
            "⬇️ Download CSV Template",
            template_csv,
            file_name="productpilot_features_tasks_template.csv",
            mime="text/csv",
            use_container_width=True
        )
    with q3:
        excel_path = os.path.join(PROJECT_ROOT, "ProductPilot_Dataset.xlsx")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                excel_bytes = f.read()
            st.download_button(
                "⬇️ Download Full Excel Dataset",
                excel_bytes,
                file_name="ProductPilot_Dataset.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button("⬇️ Full Excel Dataset", disabled=True, use_container_width=True)
    with q4:
        if st.button("🗑️ Reset to Big Data Demo", use_container_width=True):
            st.session_state["custom_dataset"] = None
            st.session_state["active_data_source"] = "demo"
            st.info("Reset to default Big Data Pipeline dataset.")
            st.rerun()

    st.markdown("")

    # Workspace Tabs
    tab_upload, tab_form, tab_editor, tab_preview = st.tabs([
        "📁 File Upload (CSV & Excel)",
        "✍️ Interactive Form Input",
        "📊 Live Spreadsheet Editor",
        "🔍 Active Data Diagnostics"
    ])

    with tab_upload:
        section_header("Upload Dataset File")
        st.markdown(
            "Upload any CSV file or Excel workbook (.xlsx/.xls). ProductPilot automatically detects columns, "
            "cleanses and normalizes values, auto-generates associated tasks if needed, and computes WSJF prioritization, "
            "delivery risks, Bloom Filter index, and DGIM sliding-window streams."
        )

        up_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="workspace_file_uploader",
            help="Upload your product features, backlog, or combined project delivery tasks"
        )

        if up_file is not None:
            try:
                # Preview Raw Content
                if up_file.name.lower().endswith((".xlsx", ".xls")):
                    xls = pd.ExcelFile(up_file)
                    st.info(f"📊 Excel file uploaded: **{up_file.name}** with sheet(s): {', '.join(xls.sheet_names)}")
                    parsed_df = pd.read_excel(xls, sheet_name=0)
                else:
                    parsed_df = pd.read_csv(up_file)

                st.markdown(f"**Preview of Uploaded Data:** ({len(parsed_df):,} rows × {len(parsed_df.columns)} columns)")
                st.dataframe(parsed_df.head(5), use_container_width=True, hide_index=True)

                # Column Mapping Auto-detection
                detected = detect_column_mapping(parsed_df.columns.tolist())
                section_header("Detected Semantic Mapping")
                
                m_cols = st.columns(3)
                mapped_items = list(detected.items())
                for i, (canonical, actual) in enumerate(mapped_items):
                    with m_cols[i % 3]:
                        st.markdown(f"**{canonical.replace('_', ' ').title()}:** `{actual}`")

                # Optional Custom Mapping Override
                with st.expander("⚙️ Customize Column Mappings (Optional)"):
                    st.markdown("Override any detected column mapping below if your headers differ:")
                    all_cols = ["(Not Mapped)"] + parsed_df.columns.tolist()
                    overrides = {}
                    ov1, ov2 = st.columns(2)
                    with ov1:
                        f_name_col = st.selectbox("Feature Name Column", all_cols, index=all_cols.index(detected.get("feature_name", "(Not Mapped)")) if detected.get("feature_name") in all_cols else 0)
                        if f_name_col != "(Not Mapped)": overrides["feature_name"] = f_name_col
                        
                        dem_col = st.selectbox("Customer Demand / Votes Column", all_cols, index=all_cols.index(detected.get("customer_demand", "(Not Mapped)")) if detected.get("customer_demand") in all_cols else 0)
                        if dem_col != "(Not Mapped)": overrides["customer_demand"] = dem_col

                        bv_col = st.selectbox("Business Value Column", all_cols, index=all_cols.index(detected.get("business_value", "(Not Mapped)")) if detected.get("business_value") in all_cols else 0)
                        if bv_col != "(Not Mapped)": overrides["business_value"] = bv_col

                    with ov2:
                        urg_col = st.selectbox("Urgency / Priority Column", all_cols, index=all_cols.index(detected.get("urgency", "(Not Mapped)")) if detected.get("urgency") in all_cols else 0)
                        if urg_col != "(Not Mapped)": overrides["urgency"] = urg_col

                        eff_col = st.selectbox("Dev Effort / Hours Column", all_cols, index=all_cols.index(detected.get("estimated_effort_hours", "(Not Mapped)")) if detected.get("estimated_effort_hours") in all_cols else 0)
                        if eff_col != "(Not Mapped)": overrides["estimated_effort_hours"] = eff_col

                        status_col = st.selectbox("Status / Task Status Column", all_cols, index=all_cols.index(detected.get("task_status", "(Not Mapped)")) if detected.get("task_status") in all_cols else 0)
                        if status_col != "(Not Mapped)": overrides["task_status"] = status_col

                if st.button("⚡ Apply & Compute All ProductPilot Analytics", type="primary", use_container_width=True):
                    with st.spinner("Processing custom dataset and computing analytics..."):
                        if up_file.name.lower().endswith((".xlsx", ".xls")):
                            up_file.seek(0)
                            processed = process_excel_file(up_file, filename=up_file.name)
                        else:
                            processed = process_user_dataframe(parsed_df, custom_mapping=overrides, dataset_name=up_file.name)

                        st.session_state["custom_dataset"] = processed
                        st.session_state["active_data_source"] = "custom"

                    st.success(f"🎉 Successfully loaded and processed '{up_file.name}'!")
                    st.balloons()
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")

    with tab_form:
        section_header("Quick-Add a Feature to Active Dataset")
        st.markdown(
            "Manually enter details for a feature, customer demand, and its engineering delivery task. "
            "It will immediately be added to your active workspace and scored by the analytics engine."
        )

        with st.form("quick_add_feature_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                in_name = st.text_input("Feature Name *", placeholder="e.g., Automated Stripe Invoicing", value="")
                in_prod = st.text_input("Product / App", value="Core Web App")
                in_cat = st.selectbox("Category", ["Core Feature", "Integration", "Security", "UX / UI", "Reporting", "Performance"])
                in_demand = st.slider("Customer Demand (Signals / Votes)", 1, 100, 75)
                in_bv = st.slider("Business Value (1 - 10)", 1.0, 10.0, 8.0, step=0.5)

            with col_f2:
                in_urg = st.selectbox("Urgency", ["Critical", "High", "Medium", "Low"], index=1)
                in_align = st.slider("Strategic Alignment (1 - 10)", 1.0, 10.0, 7.5, step=0.5)
                in_effort = st.slider("Estimated Dev Effort (Hours)", 5, 200, 40, step=5)
                in_proj = st.text_input("Project / Team", value="PROJ-Core")
                in_rel = st.text_input("Target Release ID", value="REL-v2.0")
                in_tstatus = st.selectbox("Task Status", ["Not Started", "In Progress", "Blocked", "Completed"], index=1)

            submit_btn = st.form_submit_button("➕ Add Feature & Recalculate All Features", type="primary", use_container_width=True)

            if submit_btn:
                if not in_name.strip():
                    st.warning("Please provide a feature name.")
                else:
                    new_row = {
                        "feature_id": f"FEAT-{len(features_df)+1:04d}",
                        "feature_name": in_name.strip(),
                        "product": in_prod.strip(),
                        "category": in_cat,
                        "customer_demand": in_demand,
                        "business_value": in_bv,
                        "urgency": in_urg,
                        "strategic_alignment": in_align,
                        "estimated_effort_hours": in_effort,
                        "task_id": f"TASK-{len(tasks_df)+1:05d}",
                        "task_name": f"Implement {in_name.strip()}",
                        "project_id": in_proj.strip(),
                        "task_status": in_tstatus,
                        "planned_date": (datetime.date.today() + datetime.timedelta(days=14)).isoformat(),
                        "release_id": in_rel.strip()
                    }

                    # Append to current features or initialize
                    if st.session_state.get("custom_dataset") is not None:
                        current_f = st.session_state["custom_dataset"]["features"]
                        # Convert to DataFrame
                        combined_df = pd.concat([current_f, pd.DataFrame([new_row])], ignore_index=True)
                        processed = process_user_dataframe(combined_df, dataset_name=st.session_state["custom_dataset"].get("name", "Custom Dataset"))
                    else:
                        processed = process_user_dataframe(pd.DataFrame([new_row]), dataset_name="Interactive User Backlog")

                    st.session_state["custom_dataset"] = processed
                    st.session_state["active_data_source"] = "custom"
                    st.toast(f"✅ Added '{in_name}' to dataset!")
                    st.rerun()

    with tab_editor:
        section_header("Live Spreadsheet Editor")
        st.markdown(
            "Directly edit, add, or delete features in the grid below. "
            "Click **Save Changes & Recompute** to update the entire ProductPilot analytics platform."
        )

        display_editable = features_df[[c for c in [
            "feature_id", "feature_name", "product", "category",
            "customer_demand", "business_value", "urgency", "strategic_alignment",
            "estimated_effort_hours", "status", "release_id"
        ] if c in features_df.columns]].copy()

        edited_df = st.data_editor(
            display_editable,
            num_rows="dynamic",
            use_container_width=True,
            key="workspace_live_features_editor"
        )

        if st.button("💾 Save Changes & Recompute All Analytics", type="primary", use_container_width=True):
            if not edited_df.empty:
                processed = process_user_dataframe(edited_df, dataset_name="User Spreadsheet Edited Dataset")
                st.session_state["custom_dataset"] = processed
                st.session_state["active_data_source"] = "custom"
                st.toast("✅ Saved changes and recomputed all analytics!")
                st.rerun()

    with tab_preview:
        section_header("Active Dataset Diagnostics & Schema")
        st.markdown(f"**Active Mode:** `{active_dataset_name}` ({'Custom User Data' if is_custom_data else 'Big Data Demo'})")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(kpi_card("Features", f"{len(features_df):,}", "blue", "⭐"), unsafe_allow_html=True)
        with d2:
            st.markdown(kpi_card("Tasks", f"{len(tasks_df):,}", "cyan", "📋"), unsafe_allow_html=True)
        with d3:
            st.markdown(kpi_card("Releases", f"{len(releases_df):,}", "green", "🚀"), unsafe_allow_html=True)
        with d4:
            st.markdown(kpi_card("Requests (Bloom)", f"{len(requests_df):,}", "purple", "🔬"), unsafe_allow_html=True)

        st.markdown("")
        preview_choice = st.radio("Inspect Table:", ["Features", "Tasks", "Releases", "Requests"], horizontal=True)

        if preview_choice == "Features":
            st.dataframe(features_df, use_container_width=True, hide_index=True)
        elif preview_choice == "Tasks":
            st.dataframe(tasks_df, use_container_width=True, hide_index=True)
        elif preview_choice == "Releases":
            st.dataframe(releases_df, use_container_width=True, hide_index=True)
        elif preview_choice == "Requests":
            st.dataframe(requests_df.head(100), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 🚀 Jump to Analytics:")
        j1, j2, j3, j4 = st.columns(4)
        with j1:
            st.markdown("👉 **Executive Overview** to see overall KPIs, completion rate & product distributions")
        with j2:
            st.markdown("👉 **Feature Prioritization** to adjust WSJF weights and see ranked priorities")
        with j3:
            st.markdown("👉 **Delivery Risks** to analyze overdue tasks, release risk & recommendations")
        with j4:
            st.markdown("👉 **Bloom Filter Lab & DGIM** to test duplicate queries and sliding-window event counting")
