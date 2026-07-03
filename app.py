import streamlit as st
import pandas as pd
import datetime

# --- CRITICAL FIX: INITIALIZE SESSION STATE ---
if 'ui_date' not in st.session_state:
    st.session_state.ui_date = datetime.date.today()

# --- Load Data ---
# Note: Ensure these files are in the same folder as app.py
try:
    tx_df = pd.read_excel("TransactionsLatestCAS.xlsx", sheet_name="Transactions")
    # Add your logic for your database/warehouse here
except Exception as e:
    st.error(f"Data loading error: {e}")

# --- Sidebar Logic ---
st.sidebar.header("Navigation")
# Define your dates
min_date = datetime.date(2017, 1, 1)
max_date = datetime.date.today()

# Now this will work because st.session_state.ui_date is guaranteed to exist
picked_date = st.sidebar.date_input(
    "Travel to Date:", 
    value=st.session_state.ui_date, 
    min_value=min_date, 
    max_value=max_date
)

# --- Rest of your app logic ---
st.title("JSR Wealth Tracker")
st.write(f"Selected Date: {picked_date}")