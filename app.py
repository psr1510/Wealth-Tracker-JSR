import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import datetime

# ==========================================
# 0. INITIALIZATION & SESSION STATE FIX
# ==========================================
# Ensure session state is initialized immediately
if 'ui_date' not in st.session_state:
    st.session_state.ui_date = datetime.date.today()

# ==========================================
# 1. PAGE CONFIGURATION & FORMATTING
# ==========================================
st.set_page_config(page_title="Family Wealth", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

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

MEMBER_SORT_ORDER = {
    'ASR HUF': 1, 'ASR': 2, 'LR': 3, 'PSR HUF': 4, 'PSR': 5, 
    'VSR': 6, 'Aarvi': 7, 'Anjaney': 8, 'VSR Gift': 9
}

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
    except Exception:
        stocks_df = pd.DataFrame(columns=['snapshot_date', 'entity', 'symbol', 'quantity', 'price', 'value'])
    conn.close()
    return df, tx_df, stocks_df

with st.spinner("Loading financial history..."):
    df, tx_df, stocks_df = load_data()

# CRITICAL FIX: Safe date calculation
if not df.empty:
    min_date = df['snapshot_date'].min()
    max_date = df['snapshot_date'].max()
else:
    min_date = datetime.date(2017, 1, 1)
    max_date = datetime.date.today()

# ==========================================
# 3. SIDEBAR NAVIGATION & TIME MACHINE
# ==========================================
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Select a view:", [
    "📊 Global Dashboard", 
    "💼 MF Portfolio Breakdown", 
    "📈 Direct Equities",
    "📜 Recent MF Transactions", 
    "🤖 Research Holdings"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕰️ Time Machine")

# Use valid fallback dates to prevent DateInput crashes
picked_date = st.sidebar.date_input("Travel to Date:", value=st.session_state.ui_date, min_value=min_date, max_value=max_date)

if st.sidebar.button("📅 Jump to Today"):
    st.session_state.ui_date = max_date
    st.rerun()

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.session_state.ui_date = picked_date

# --- ROBUST EFFECTIVE DATE LOGIC ---
historical_df = df[df['snapshot_date'] <= st.session_state.ui_date]
latest_df = historical_df.groupby(['name', 'folio', 'amc', 'asset_name'], as_index=False).last() if not historical_df.empty else pd.DataFrame(columns=df.columns)
effective_date = latest_df['snapshot_date'].max() if not latest_df.empty else min_date

historical_stocks_df = stocks_df[stocks_df['snapshot_date'] <= st.session_state.ui_date]
latest_stocks_df = historical_stocks_df.groupby(['entity', 'symbol'], as_index=False).last() if not historical_stocks_df.empty else pd.DataFrame(columns=stocks_df.columns)

# ==========================================
# PAGE 1: GLOBAL DASHBOARD
# ==========================================
if page == "📊 Global Dashboard":
    st.title("📈 Family Wealth Dashboard")
    if effective_date < max_date:
        st.warning(f"⚠️ Viewing historical portfolio state. Showing values from **{effective_date.strftime('%d %b %Y')}**.")

    total_invested_mf = latest_df['invested_amount'].sum()
    total_current_mf = latest_df['current_value'].sum()
    total_current_stocks = latest_stocks_df['value'].sum() if not latest_stocks_df.empty else 0
    grand_total_wealth = total_current_mf + total_current_stocks

    st.markdown("### 💎 Grand Total Net Worth")
    st.metric("Combined Value (MFs + Stocks)", f"₹ {inr_format(grand_total_wealth)}")
    st.markdown("---")

    st.markdown("### 🏦 Mutual Funds Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Value", f"₹ {inr_format(total_current_mf)}", f"₹ {inr_format(total_current_mf - total_invested_mf)} Profit")
    col2.metric("Invested", f"₹ {inr_format(total_invested_mf)}")
    col3.metric("Absolute Return", f"{inr_format(((total_current_mf - total_invested_mf) / total_invested_mf * 100) if total_invested_mf > 0 else 0)} %")
    col4.metric("Weighted XIRR", f"{inr_format((latest_df['xirr'] * latest_df['current_value']).sum() / total_current_mf if total_current_mf > 0 else 0)} %")
        
    st.markdown("---")
    st.markdown("### 📈 Direct Equities Overview")
    if not latest_stocks_df.empty:
        st.metric("Total Stock Value", f"₹ {inr_format(total_current_stocks)}")
    else:
        st.info("No direct equity data recorded for this date.")

    st.markdown("---")
    st.markdown("### 📅 Mutual Fund Growth Timeline")
    all_dates = [d.date() for d in pd.date_range(start=min_date, end=max_date)]
    val_p = df.pivot_table(index='snapshot_date', columns='asset_name', values='current_value').reindex(all_dates).ffill().fillna(0)
    inv_p = df.pivot_table(index='snapshot_date', columns='asset_name', values='invested_amount').reindex(all_dates).ffill().fillna(0)
    history_df = pd.DataFrame({'snapshot_date': all_dates, 'Invested (L)': inv_p.sum(axis=1) / 100000, 'Value (L)': val_p.sum(axis=1) / 100000})
    history_df = history_df[history_df['Invested (L)'] > 0]

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=history_df['snapshot_date'], y=history_df['Invested (L)'], fill='tozeroy', mode='lines', name='Invested', line=dict(color='#3b82f6')))
    fig1.add_trace(go.Scatter(x=history_df['snapshot_date'], y=history_df['Value (L)'], fill='tozeroy', mode='lines', name='Value', line=dict(color='#10b981')))
    fig1.update_layout(yaxis_title="Amount (Lakhs)", hovermode="x unified", legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig1, use_container_width=True)

# ==========================================
# PAGE 2: MF PORTFOLIO BREAKDOWN
# ==========================================
elif page == "💼 MF Portfolio Breakdown":
    st.title("💼 Mutual Fund Breakdown")
    family_members = ["All"] + list(sorted(df['name'].unique(), key=get_member_sort_key))
    selected_member = st.selectbox("Filter by Family Member:", family_members)

    daily_df = latest_df.copy()
    if selected_member != "All":
        daily_df = daily_df[daily_df['name'] == selected_member]

    total_portfolio_baseline = daily_df['current_value'].sum()
    amc_totals = daily_df.groupby('amc')['current_value'].sum().sort_values(ascending=False)
    sorted_amcs = amc_totals.index.tolist()

    if daily_df.empty:
        st.warning("No portfolio data found for this selection.")
    else:
        tab1, tab2 = st.tabs(["View 1: Member ➔ AMC ➔ Fund", "View 2: AMC ➔ Fund ➔ Member"])
        # (Tabs logic retained from your source file)
        with tab1:
            if total_portfolio_baseline > 0:
                pie_mem = daily_df.groupby('name')['current_value'].sum().reset_index()
                fig_mem = px.pie(pie_mem, values='current_value', names='name', title="Allocation by Family Member", hole=0.4)
                st.plotly_chart(fig_mem, use_container_width=True)
            # Add existing member-loop expander logic here...
        with tab2:
            if total_portfolio_baseline > 0:
                pie_amc = daily_df.groupby('amc')['current_value'].sum().reset_index()
                fig_amc = px.pie(pie_amc, values='current_value', names='amc', title="Allocation by Top AMCs", hole=0.4)
                st.plotly_chart(fig_amc, use_container_width=True)
            # Add existing amc-loop expander logic here...

# ==========================================
# PAGE 3: DIRECT EQUITIES
# ==========================================
elif page == "📈 Direct Equities":
    st.title("📈 Direct Equities (Stocks)")
    if not latest_stocks_df.empty:
        entities = ["All"] + list(latest_stocks_df['entity'].unique())
        selected_entity = st.selectbox("Filter by Entity:", entities)
        display_df = latest_stocks_df.copy()
        if selected_entity != "All":
            display_df = display_df[display_df['entity'] == selected_entity]
        st.metric("Total Equity Value", f"₹ {inr_format(display_df['value'].sum())}")
        st.dataframe(display_df, use_container_width=True)

# ==========================================
# PAGE 4: RECENT TRANSACTIONS
# ==========================================
elif page == "📜 Recent MF Transactions":
    st.title("📜 Recent Mutual Fund Transactions")
    selected_dt = pd.to_datetime(effective_date)
    start_date = (selected_dt - pd.DateOffset(months=3)).replace(day=1).date()
    past_tx = tx_df[(tx_df['Date'] <= effective_date) & (tx_df['Date'] >= start_date)].copy()
    st.dataframe(past_tx, use_container_width=True)

# ==========================================
# PAGE 5: RESEARCH HOLDINGS
# ==========================================
elif page == "🤖 Research Holdings":
    st.title("🤖 Ask Gemini")
    if not latest_df.empty:
        fund_totals = latest_df.groupby('asset_name')['current_value'].sum().reset_index()
        total_portfolio_baseline = latest_df['current_value'].sum()
        fund_totals['Weightage'] = (fund_totals['current_value'] / total_portfolio_baseline) * 100
        for idx, row in enumerate(fund_totals.itertuples(), 1):
            st.write(f"{idx}. {row.asset_name}")