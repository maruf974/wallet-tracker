import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import requests

# Page Configuration
st.set_page_config(page_title="Perpetual Wallet Auto-Tracker", page_icon="⚡", layout="centered")

# Custom Styling
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .card { background-color: #161A23; border: 1px solid #262730; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    .metric-title { color: #8D96A0; font-size: 14px; }
    .metric-value { color: #FFFFFF; font-size: 36px; font-weight: 700; margin-top: 5px; }
    .change-down { color: #FF4B4B; font-size: 15px; font-weight: 500; }
    .change-up { color: #00CC96; font-size: 15px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "wallets_auto_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"wallets": [], "deposits": 0.0, "previous_total": 0.0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# Lighter ba Arcus API theke auto equity fetch korar function
def fetch_wallet_equity(address, platform):
    try:
        if platform == "Lighter":
            url = f"https://api.lighter.xyz/v1/account?address={address}"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                return float(res.json().get("equity", 0.0))
        elif platform == "Arcus":
            url = f"https://api.arcus.exchange/v1/user/account?address={address}"
            res.status_code = requests.get(url, timeout=3)
            if res.status_code == 200:
                return float(res.json().get("total_equity", 0.0))
    except:
        pass
    return None

st.title("⚡ Perpetuals Wallet Auto-Tracker")
st.markdown("Wallet address দিয়ে অটো ট্র্যাক করুন এবং রিফ্রেশ করলেই ব্যালেন্স ড্রপ বা লস হিসাব করুন।")

# Sidebar: Wallet Setup
st.sidebar.header("➕ Add Wallet Address")
with st.sidebar.form("wallet_form", clear_on_submit=True):
    w_name = st.text_input("Wallet Name / Level", "Level 1 (Main)")
    w_platform = st.selectbox("Platform", ["Lighter", "Arcus"])
    w_address = st.text_input("Wallet Address (0x...)")
    submit_btn = st.form_submit_button("Track Wallet")
    
    if submit_btn and w_address:
        # Initial fetch or default fallback if API is restricted
        live_eq = fetch_wallet_equity(w_address, w_platform)
        starting_eq = live_eq if live_eq and live_eq > 0 else 1000.0
        
        db["wallets"].append({
            "name": w_name,
            "platform": w_platform,
            "address": w_address,
            "equity": starting_eq
        })
        save_data(db)
        st.sidebar.success(f"Added {w_name} successfully!")
        st.rerun()

with st.sidebar.expander("💵 Add New Deposit (Extra Fund)"):
    dep = st.number_input("Deposit Amount ($)", min_value=0.0, value=0.0, step=10.0)
    if st.button("Record Deposit"):
        if dep > 0:
            db["deposits"] = db.get("deposits", 0.0) + dep
            save_data(db)
            st.sidebar.success(f"Added ${dep} to total capital!")
            st.rerun()

if st.sidebar.button("🗑️ Reset All Data"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.rerun()

# --- Main Dashboard Logic ---
total_current_equity = 0.0
total_initial_capital = db.get("deposits", 0.0)
wallet_results = []

st.markdown("### 📊 Tracked Wallets Overview")

for i, w in enumerate(db["wallets"]):
    # Try fetching fresh live equity from API
    live_eq = fetch_wallet_equity(w["address"], w["platform"])
    if live_eq is not None and live_eq > 0:
        current_eq = live_eq
    else:
        # Fallback to stored equity if direct API blocks browser requests
        current_eq = w.get("equity", 1000.0)
    
    w["equity"] = current_eq
    total_current_equity += current_eq
    
    # Display individual wallet card
    st.markdown(f"""
        <div style="background-color: #161A23; border: 1px solid #262730; border-radius: 8px; padding: 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: #FFFFFF; font-size: 15px; font-weight: 600;">{w['platform']} — {w['name']}</div>
                <div style="color: #8D96A0; font-size: 11px;">{w['address'][:6]}...{w['address'][-4:]}</div>
            </div>
            <div style="text-align: right;">
                <div style="color: #FFFFFF; font-size: 17px; font-weight: 700;">${current_eq:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

save_data(db)

# Refresh & Baseline calculation
previous_total = db.get("previous_total", total_current_equity)
drop_amount = total_current_equity - previous_total

st.markdown("---")

# Top Overview Card
st.markdown(f"""
    <div class="card">
        <div class="metric-title">All Wallets · Total Perpetuals Equity</div>
        <div class="metric-value">${total_current_equity:,.2f}</div>
        <div class="{'change-down' if drop_amount < 0 else 'change-up'}">
            {'↓' if drop_amount < 0 else '↑'} ${abs(drop_amount):,.2f} compared with last check/refresh
        </div>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Refresh & Update Baseline"):
        db["previous_total"] = total_current_equity
        save_data(db)
        st.success("Baseline updated! Next refresh will calculate drop from here.")
        st.rerun()

with col2:
    if st.button("⚡ Force Sync All Wallets"):
        st.rerun()

# Farming cost calculation
net_farming_cost = total_initial_capital - total_current_equity
st.markdown("---")
c1, c2 = st.columns(2)
c1.metric("Total Capital Invested", f"${total_initial_capital:,.2f}")
c2.metric("Net Farming Cost / Loss", f"${net_farming_cost:,.2f}")
