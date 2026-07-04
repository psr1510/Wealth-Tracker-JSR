import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import datetime
import os

# ==========================================
# 0. CRITICAL FIX: INITIALIZE SESSION STATE
# ==========================================
if 'ui_date' not in st.session_state:
    st.session_state.ui_date = datetime.date.today()

# ==========================================
# 1. PAGE CONFIGURATION & FORMATTING
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

MEMBER_SORT_ORDER = {
    'ASR HUF': 1, 'ASR': 2, 'LR': 3, 'PSR HUF': 4, 'PSR': 5, 
    'VSR': 6, 'Aarvi': 7, 'Anjaney': 8, 'VSR Gift': 9
}

def get_member_sort_key(name):
    return MEMBER_SORT_ORDER.get(str(name), 99)

# ==========================================
# 2. DATA LOADER (NOW WITH ABSOLUTE PATH)
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    # Absolute path explicitly for Streamlit Cloud (Linux)
    db_path = os.path.join(os.getcwd(), "WealthDatabase.db")
    conn = sqlite3.connect(db_path)
    
    # Load Mutual Funds
    df = pd.read_sql_query("SELECT snapshot_date, name, folio, amc, asset_name, units, invested_amount, current_value, abs_return, xirr, nav FROM portfolio_snapshots ORDER BY snapshot_date ASC", conn)
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date']).dt.date
    
    # Load Transactions
    tx_df = pd.read_excel("TransactionsLatestCAS.xlsx", sheet_name="Transactions")
    tx_df['Date'] = pd.to_datetime(tx_df['Date']).dt.date
    
    # Load Stocks
    try:
        stocks_df = pd.read_sql_query("SELECT snapshot_date, entity, symbol, quantity, price, value FROM stock_snapshots ORDER BY snapshot_date ASC", conn)
        stocks_df['snapshot_date'] = pd.to_datetime(stocks_df['snapshot_date']).dt.date
    except Exception:
        stocks_df = pd.DataFrame(columns=['snapshot_date', 'entity', 'symbol', 'quantity', 'price', 'value'])
        
    conn.close()
    return df, tx_df, stocks_df

with st.spinner("Loading financial history..."):
    df, tx_df, stocks_df = load_data()

# Safe Date Boundaries for Time Machine 
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
picked_date = st.sidebar.date_input("Travel to Date:", value=st.session_state.ui_date, min_value=min_date, max_value=max_date)

if st.sidebar.button("📅 Jump to Today"):
    st.session_state.ui_date = max_date
    st.rerun()

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.session_state.ui_date = picked_date

# --- ROBUST EFFECTIVE DATE LOGIC (FORWARD FILLING) ---
# Mutual Funds
historical_df = df[df['snapshot_date'] <= st.session_state.ui_date]
if not historical_df.empty:
    historical_df = historical_df.sort_values('snapshot_date')
    latest_df = historical_df.groupby(['name', 'folio', 'amc', 'asset_name'], as_index=False).last()
    effective_date = latest_df['snapshot_date'].max()
else:
    latest_df = pd.DataFrame(columns=df.columns)
    effective_date = min_date

# Stocks
historical_stocks_df = stocks_df[stocks_df['snapshot_date'] <= st.session_state.ui_date]
if not historical_stocks_df.empty:
    historical_stocks_df = historical_stocks_df.sort_values('snapshot_date')
    latest_stocks_df = historical_stocks_df.groupby(['entity', 'symbol'], as_index=False).last()
else:
    latest_stocks_df = pd.DataFrame(columns=stocks_df.columns)

# ==========================================
# PAGE 1: GLOBAL DASHBOARD 
# ==========================================
if page == "📊 Global Dashboard":
    st.title("📈 JSR's Wealth Dashboard")
    if effective_date < max_date:
        st.warning(f"⚠️ Viewing historical portfolio state. Showing values from **{effective_date.strftime('%d %b %Y')}**.")

    total_invested_mf = latest_df['invested_amount'].sum()
    total_current_mf = latest_df['current_value'].sum()
    total_profit_mf = total_current_mf - total_invested_mf
    overall_return_mf = (total_profit_mf / total_invested_mf) * 100 if total_invested_mf > 0 else 0
    
    total_current_stocks = latest_stocks_df['value'].sum() if not latest_stocks_df.empty else 0
    grand_total_wealth = total_current_mf + total_current_stocks

    st.markdown("### 💎 Grand Total Net Worth")
    st.metric("Combined Value (MFs + Stocks)", f"₹ {inr_format(grand_total_wealth)}")
    st.markdown("---")

    st.markdown("### 🏦 Mutual Funds Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Value", f"₹ {inr_format(total_current_mf)}", f"₹ {inr_format(total_profit_mf)} Profit")
    col2.metric("Invested", f"₹ {inr_format(total_invested_mf)}")
    col3.metric("Absolute Return", f"{inr_format(overall_return_mf)} %")
    if total_current_mf > 0:
        weighted_xirr = (latest_df['xirr'] * latest_df['current_value']).sum() / total_current_mf
        col4.metric("Weighted XIRR", f"{inr_format(weighted_xirr)} %")
    else:
        col4.metric("Weighted XIRR", "0.00 %")
        
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
    history_df = pd.DataFrame({
        'snapshot_date': all_dates,
        'Invested (L)': inv_p.sum(axis=1) / 100000,
        'Value (L)': val_p.sum(axis=1) / 100000,
    })
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

        with tab1:
            if total_portfolio_baseline > 0:
                pie_mem = daily_df.groupby('name')['current_value'].sum().reset_index()
                pie_mem = pie_mem[pie_mem['current_value'] > 0]
                fig_mem = px.pie(pie_mem, values='current_value', names='name', title="Allocation by Family Member", hole=0.4)
                fig_mem.update_traces(textinfo='percent+label', textposition='inside')
                fig_mem.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=False, height=350)
                st.plotly_chart(fig_mem, use_container_width=True)
            
            st.write("") 
            
            members_present = sorted(daily_df['name'].unique(), key=get_member_sort_key)
            for member in members_present:
                mem_df = daily_df[daily_df['name'] == member]
                mem_inv = mem_df['invested_amount'].sum()
                mem_val = mem_df['current_value'].sum()
                mem_gains = mem_val - mem_inv
                mem_gains_pct = (mem_gains / mem_inv * 100) if mem_inv > 0 else 0
                mem_xirr = (mem_df['xirr'] * mem_df['current_value']).sum() / mem_val if mem_val > 0 else 0
                mem_weight = (mem_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                
                with st.expander(f"👤 **{member}** | Inv: ₹ {inr_format(mem_inv)} | Val: ₹ {inr_format(mem_val)} | Gains: ₹ {inr_format(mem_gains)} ({inr_format(mem_gains_pct)}%) | XIRR: {inr_format(mem_xirr)}% | Wgt: {inr_format(mem_weight)}%", expanded=False):
                    amcs_in_mem = [a for a in sorted_amcs if a in mem_df['amc'].unique()]
                    for amc in amcs_in_mem:
                        amc_df = mem_df[mem_df['amc'] == amc]
                        amc_inv = amc_df['invested_amount'].sum()
                        amc_val = amc_df['current_value'].sum()
                        amc_gains = amc_val - amc_inv
                        amc_gains_pct = (amc_gains / amc_inv * 100) if amc_inv > 0 else 0
                        amc_xirr = (amc_df['xirr'] * amc_df['current_value']).sum() / amc_val if amc_val > 0 else 0
                        amc_weight = (amc_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                        
                        with st.expander(f"🏢 **{amc}** | Inv: ₹ {inr_format(amc_inv)} | Val: ₹ {inr_format(amc_val)} | Gains: ₹ {inr_format(amc_gains)} ({inr_format(amc_gains_pct)}%) | XIRR: {inr_format(amc_xirr)}% | Wgt: {inr_format(amc_weight)}%", expanded=False):
                            funds_in_amc = amc_df.sort_values(by='current_value', ascending=False)['asset_name'].unique()
                            for fund in funds_in_amc:
                                fund_row = amc_df[amc_df['asset_name'] == fund].iloc[0]
                                fund_inv = fund_row['invested_amount']
                                fund_val = fund_row['current_value']
                                fund_gains = fund_val - fund_inv
                                fund_gains_pct = (fund_gains / fund_inv * 100) if fund_inv > 0 else 0
                                fund_xirr = fund_row['xirr']
                                fund_weight = (fund_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                                
                                with st.expander(f"📄 **{fund}** | Units: {fund_row['units']} | Inv: ₹ {inr_format(fund_inv)} | Val: ₹ {inr_format(fund_val)} | Gains: ₹ {inr_format(fund_gains)} ({inr_format(fund_gains_pct)}%) | XIRR: {inr_format(fund_xirr)}% | Wgt: {inr_format(fund_weight)}%", expanded=False):
                                    txns = tx_df[(tx_df['Name'] == member) & (tx_df['AMC / Equity Name'] == amc) & (tx_df['Asset Name / Scrip Code'] == fund)].copy()
                                    if not txns.empty:
                                        dtx = txns[['Date', 'Transaction Type (Buy / Sell)', 'Units', 'Total Amount']].copy()
                                        dtx.columns = ['Date', 'Type', 'Units', 'Amount (₹)']
                                        dtx['Date'] = dtx['Date'].apply(lambda x: x.strftime('%d-%b-%Y') if pd.notnull(x) else "")
                                        dtx['Amount (₹)'] = dtx['Amount (₹)'].apply(inr_format)
                                        st.dataframe(dtx, use_container_width=True, hide_index=True)

        with tab2:
            if total_portfolio_baseline > 0:
                pie_amc = daily_df.groupby('amc')['current_value'].sum().reset_index()
                pie_amc = pie_amc[pie_amc['current_value'] > (total_portfolio_baseline * 0.01)] 
                fig_amc = px.pie(pie_amc, values='current_value', names='amc', title="Allocation by Top AMCs (>1%)", hole=0.4)
                fig_amc.update_traces(textinfo='percent', textposition='inside')
                fig_amc.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=350)
                st.plotly_chart(fig_amc, use_container_width=True)

            st.write("") 

            for amc in sorted_amcs:
                amc_df = daily_df[daily_df['amc'] == amc]
                if amc_df.empty: continue
                amc_inv = amc_df['invested_amount'].sum()
                amc_val = amc_df['current_value'].sum()
                amc_gains = amc_val - amc_inv
                amc_gains_pct = (amc_gains / amc_inv * 100) if amc_inv > 0 else 0
                amc_xirr = (amc_df['xirr'] * amc_df['current_value']).sum() / amc_val if amc_val > 0 else 0
                amc_weight = (amc_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                
                with st.expander(f"🏢 **{amc}** | Inv: ₹ {inr_format(amc_inv)} | Val: ₹ {inr_format(amc_val)} | Gains: ₹ {inr_format(amc_gains)} ({inr_format(amc_gains_pct)}%) | XIRR: {inr_format(amc_xirr)}% | Wgt: {inr_format(amc_weight)}%", expanded=False):
                    funds_in_amc = amc_df.groupby('asset_name')['current_value'].sum().sort_values(ascending=False).index
                    for fund in funds_in_amc:
                        fund_df = amc_df[amc_df['asset_name'] == fund]
                        fund_inv = fund_df['invested_amount'].sum()
                        fund_val = fund_df['current_value'].sum()
                        fund_gains = fund_val - fund_inv
                        fund_gains_pct = (fund_gains / fund_inv * 100) if fund_inv > 0 else 0
                        fund_xirr = (fund_df['xirr'] * fund_df['current_value']).sum() / fund_val if fund_val > 0 else 0
                        fund_weight = (fund_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                        
                        with st.expander(f"📄 **{fund}** | Inv: ₹ {inr_format(fund_inv)} | Val: ₹ {inr_format(fund_val)} | Gains: ₹ {inr_format(fund_gains)} ({inr_format(fund_gains_pct)}%) | XIRR: {inr_format(fund_xirr)}% | Wgt: {inr_format(fund_weight)}%", expanded=False):
                            members_in_fund = sorted(fund_df['name'].unique(), key=get_member_sort_key)
                            for member in members_in_fund:
                                mem_row = fund_df[fund_df['name'] == member].iloc[0]
                                mem_inv = mem_row['invested_amount']
                                mem_val = mem_row['current_value']
                                mem_gains = mem_val - mem_inv
                                mem_gains_pct = (mem_gains / mem_inv * 100) if mem_inv > 0 else 0
                                mem_xirr = mem_row['xirr']
                                mem_weight = (mem_val / total_portfolio_baseline * 100) if total_portfolio_baseline > 0 else 0
                                
                                with st.expander(f"👤 **{member}** | Units: {mem_row['units']} | Inv: ₹ {inr_format(mem_inv)} | Val: ₹ {inr_format(mem_val)} | Gains: ₹ {inr_format(mem_gains)} ({inr_format(mem_gains_pct)}%) | XIRR: {inr_format(mem_xirr)}% | Wgt: {inr_format(mem_weight)}%", expanded=False):
                                    txns = tx_df[(tx_df['Name'] == member) & (tx_df['AMC / Equity Name'] == amc) & (tx_df['Asset Name / Scrip Code'] == fund)].copy()
                                    if not txns.empty:
                                        dtx = txns[['Date', 'Transaction Type (Buy / Sell)', 'Units', 'Total Amount']].copy()
                                        dtx.columns = ['Date', 'Type', 'Units', 'Amount (₹)']
                                        dtx['Date'] = dtx['Date'].apply(lambda x: x.strftime('%d-%b-%Y') if pd.notnull(x) else "")
                                        dtx['Amount (₹)'] = dtx['Amount (₹)'].apply(inr_format)
                                        st.dataframe(dtx, use_container_width=True, hide_index=True)

# ==========================================
# PAGE 3: DIRECT EQUITIES
# ==========================================
elif page == "📈 Direct Equities":
    st.title("📈 Direct Equities (Stocks)")

    if latest_stocks_df.empty:
        st.info("No stock data found. Ensure your Stock Catcher Bot has processed the NSE/BSE emails.")
    else:
        entities = ["All"] + list(latest_stocks_df['entity'].unique())
        selected_entity = st.selectbox("Filter by Entity:", entities)

        display_df = latest_stocks_df.copy()
        if selected_entity != "All":
            display_df = display_df[display_df['entity'] == selected_entity]

        total_stock_value = display_df['value'].sum()
        
        st.metric("Total Equity Value", f"₹ {inr_format(total_stock_value)}")
        st.markdown("---")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("### Holding Allocation")
            pie_stocks = display_df.groupby('symbol')['value'].sum().reset_index()
            fig_stocks = px.pie(pie_stocks, values='value', names='symbol', hole=0.4)
            fig_stocks.update_traces(textinfo='percent+label', textposition='inside')
            fig_stocks.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False, height=400)
            st.plotly_chart(fig_stocks, use_container_width=True)

        with col_b:
            st.markdown("### Ledger Details")
            clean_df = display_df[['entity', 'symbol', 'quantity', 'price', 'value']].copy()
            clean_df.columns = ['Entity', 'Ticker', 'Quantity', 'LTP (₹)', 'Total Value (₹)']
            clean_df['Quantity'] = clean_df['Quantity'].apply(lambda x: f"{x:,.0f}")
            clean_df['LTP (₹)'] = clean_df['LTP (₹)'].apply(inr_format)
            clean_df['Total Value (₹)'] = clean_df['Total Value (₹)'].apply(inr_format)
            st.dataframe(clean_df, use_container_width=True, hide_index=True)

# ==========================================
# PAGE 4: RECENT TRANSACTIONS
# ==========================================
elif page == "📜 Recent MF Transactions":
    st.title("📜 Recent Mutual Fund Transactions")
    st.write("Showing activity for the last 3 months.")

    selected_dt = pd.to_datetime(effective_date)
    start_date = (selected_dt - pd.DateOffset(months=3)).replace(day=1).date()

    past_tx = tx_df[(tx_df['Date'] <= effective_date) & (tx_df['Date'] >= start_date)].copy()

    if not past_tx.empty:
        recent_dates = sorted(past_tx['Date'].unique(), reverse=True)
        for r_date in recent_dates:
            date_df = past_tx[past_tx['Date'] == r_date]
            date_total = date_df['Total Amount'].sum()
            date_str = r_date.strftime('%d-%b-%Y')
            with st.expander(f"📅 **{date_str}** | Total Amount: ₹ {inr_format(date_total)}", expanded=False):
                members_on_date = sorted(date_df['Name'].unique(), key=get_member_sort_key)
                for member in members_on_date:
                    mem_df = date_df[date_df['Name'] == member]
                    mem_total = mem_df['Total Amount'].sum()
                    with st.expander(f"👤 **{member}** | Total Amount: ₹ {inr_format(mem_total)}", expanded=False):
                        dtx = mem_df[['AMC / Equity Name', 'Asset Name / Scrip Code', 'Transaction Type (Buy / Sell)', 'Units', 'Total Amount']].copy()
                        dtx.columns = ['AMC', 'Fund Name', 'Buy/Sell', 'Units', 'Amount (₹)']
                        dtx['Amount (₹)'] = dtx['Amount (₹)'].apply(inr_format)
                        st.dataframe(dtx, use_container_width=True, hide_index=True)
    else:
        st.info(f"No transactions occurred between {start_date.strftime('%b %Y')} and {effective_date.strftime('%b %Y')}.")

# ==========================================
# PAGE 5: RESEARCH HOLDINGS
# ==========================================
elif page == "🤖 Research Holdings":
    st.title("🤖 Ask Gemini")
    st.write("Click on any mutual fund below to securely compile your relative allocation history and analyze its performance.")

    if not latest_df.empty:
        fund_totals = latest_df.groupby('asset_name')['current_value'].sum().reset_index()
        total_portfolio_baseline = latest_df['current_value'].sum()
        fund_totals['Weightage'] = (fund_totals['current_value'] / total_portfolio_baseline) * 100
        fund_totals = fund_totals.sort_values('Weightage', ascending=False)
        
        for idx, row in enumerate(fund_totals.itertuples(), 1):
            fund_name = row.asset_name
            weight = row.Weightage
            
            with st.expander(f"**{idx}. {fund_name}** | Global Weight: {inr_format(weight)}%", expanded=False):
                fund_tx = tx_df[tx_df['Asset Name / Scrip Code'] == fund_name].sort_values('Date')
                total_invested_in_fund = fund_tx['Total Amount'].sum()
                
                history_lines = []
                for _, tx_row in fund_tx.iterrows():
                    action = tx_row['Transaction Type (Buy / Sell)']
                    dt = tx_row['Date'].strftime('%d-%b-%Y')
                    alloc_weight = (tx_row['Total Amount'] / total_invested_in_fund * 100) if total_invested_in_fund > 0 else 0
                    history_lines.append(f"- {dt}: {action} | Allocation Share: {alloc_weight:.2f}% of my total investment")
                    
                tx_history_str = "\n".join(history_lines)
                
                gemini_prompt = (
                    f"Act as an expert financial advisor. Analyze the mutual fund: '{fund_name}'.\n\n"
                    f"Here is a timeline of my allocation into this fund (by percentage share rather than absolute currency):\n{tx_history_str}\n\n"
                    f"Provide a comprehensive analysis including:\n"
                    f"1. Current health and market rating.\n"
                    f"2. A comparison of general market performance versus my specific entry points.\n"
                    f"3. Strategic advice on holding, buying, or re-allocating based on my relative position."
                )
                encoded_prompt = urllib.parse.quote(gemini_prompt)
                gemini_url = f"https://gemini.google.com/app?q={encoded_prompt}"
                
                st.markdown(
                    f"""
                    <a href="{gemini_url}" target="_blank">
                        <button style="
                            background-color: #1A73E8; 
                            color: white; 
                            border: none; 
                            padding: 10px 20px; 
                            border-radius: 8px; 
                            cursor: pointer;
                            font-weight: bold;
                            margin-bottom: 10px;
                            ">
                            ✨ Ask Gemini
                        </button>
                    </a>
                    """, 
                    unsafe_allow_html=True
                )
    else:
        st.info("No funds available for the selected date.")