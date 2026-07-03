import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import datetime

# ==========================================
# 0. INITIALIZATION
# ==========================================
if 'ui_date' not in st.session_state:
    st.session_state.ui_date = datetime.date.today()

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="JSR's Wealth", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

def inr_format(n):
    if pd.isna(n) or n is None: return "0.00"
    try:
        is_neg = float(n) < 0
        n = abs(float(n))
        num_str = f"{n:.2f}"
        int_part, dec_part = num_str.split('.')
        if len(int_part) > 3:
            last_3 = int_part[-3:]
            remaining = int_part[:-3]
            remaining = ','.join([remaining[max(i-2, 0):i] for i in range(len(remaining), 0, -2)][::-1])
            int_part = remaining + ',' + last_3
        res = f"{int_part}.{dec_part}"
        return f"-{res}" if is_neg else res
    except Exception:
        return "0.00"

MEMBER_SORT_ORDER = {'ASR HUF': 1, 'ASR': 2, 'LR': 3, 'PSR HUF': 4, 'PSR': 5, 'VSR': 6, 'Aarvi': 7, 'Anjaney': 8, 'VSR Gift': 9}

def get_member_sort_key(name):
    return MEMBER_SORT_ORDER.get(str(name), 99)

# ==========================================
# 2. DATA LOADER
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    conn = sqlite3.connect("WealthDatabase.db")
    df = pd.read_sql_query("SELECT snapshot_date, name, folio, amc, asset_name, units, invested_amount, current_value, abs_return, xirr, nav FROM portfolio_snapshots ORDER BY snapshot_date ASC", conn)
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date']).dt.date
    
    tx_df = pd.read_excel("TransactionsLatestCAS.xlsx", sheet_name="Transactions")
    tx_df['Date'] = pd.to_datetime(tx_df['Date']).dt.date
    
    try:
        stocks_df = pd.read_sql_query("SELECT snapshot_date, entity, symbol, quantity, price, value FROM stock_snapshots ORDER BY snapshot_date ASC", conn)
        stocks_df['snapshot_date'] = pd.to_datetime(stocks_df['snapshot_date']).dt.date
    except:
        stocks_df = pd.DataFrame(columns=['snapshot_date', 'entity', 'symbol', 'quantity', 'price', 'value'])
    conn.close()
    return df, tx_df, stocks_df

with st.spinner("Loading financial history..."):
    df, tx_df, stocks_df = load_data()

# Date fallbacks
if not df.empty:
    min_date = df['snapshot_date'].min()
    max_date = df['snapshot_date'].max()
else:
    min_date = datetime.date(2017, 1, 1)
    max_date = datetime.date.today()

# ==========================================
# 3. SIDEBAR & NAVIGATION
# ==========================================
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Select a view:", ["📊 Global Dashboard", "💼 MF Portfolio Breakdown", "📈 Direct Equities", "📜 Recent MF Transactions", "🤖 Research Holdings"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕰️ Time Machine")
picked_date = st.sidebar.date_input("Travel to Date:", value=st.session_state.ui_date, min_value=min_date, max_value=max_date)
if st.sidebar.button("📅 Jump to Today"):
    st.session_state.ui_date = max_date
    st.rerun()
st.session_state.ui_date = picked_date

# --- DATA PROCESSING ---
latest_df = df[df['snapshot_date'] <= st.session_state.ui_date].groupby(['name', 'folio', 'amc', 'asset_name'], as_index=False).last() if not df.empty else pd.DataFrame(columns=df.columns)
latest_stocks_df = stocks_df[stocks_df['snapshot_date'] <= st.session_state.ui_date].groupby(['entity', 'symbol'], as_index=False).last() if not stocks_df.empty else pd.DataFrame(columns=stocks_df.columns)

# ==========================================
# PAGE 1: GLOBAL DASHBOARD
# ==========================================
if page == "📊 Global Dashboard":
    st.title("📈 JSR's Wealth Dashboard")
    # Add your original dashboard charts/metrics here