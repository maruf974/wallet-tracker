import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
import os

# Page Configuration
st.set_page_config(page_title="Perpetual Farming Portfolio", page_icon="⚡", layout="centered")

# Custom Styling (Dark UI like professional dashboards)
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

DATA_FILE = "wallets_data.json"

# Data Load & Save functions (Local JSON storage yate refresh korle data muche na jay)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"wallets": [], "deposits": 0.0, "yesterday_total": 0.0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# Lighter & Arcus Public API Fetch Function
def fetch_equity(address, platform):
    try:
        if platform == "Lighter":
            url = f"https://api.lighter.xyz/v1/account?address={address}"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                return float(res.json().get("equity", 0.0))
        elif platform == "Arcus":
            url = f"https://api.arcus.exchange/v1/user/account?address={address}"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                return float(res.json().get("total_equity", 0.0))
    except:
        pass
    return None

st.title("⚡ Perpetual Farming Portfolio Tracker")
st.markdown("Lighter & Arcus wallet tracking, daily PnL, and farming cost calculator.")

# Sidebar for managing wallets and deposits
st.sidebar.header("⚙️ Wallet & Fund Setup")

with st.sidebar.expander("➕ Add New Wallet", expanded=True):
    w_name = st.text_input("Wallet Name / Level", "Level 1 Main")
    w_platform = st.selectbox("Platform", ["Lighter", "Arcus"])
    w_address = st.text_input("Wallet Address (0x...)")
    
    if st.button("Add Wallet & Record Initial Balance"):
        if w_address.startswith("0x") and len(w_address) > 10:
            live_eq = fetch_equity(w_address, w_platform)
            initial_val = live_eq if live_eq is not None and live_eq > 0 else 1000.0
            
            db["wallets"].append({
                "name": w_name,
                "platform": w_platform,
                "address": w_address,
                "initial_equity": initial_val,
                "last_equity": initial_val
            })
            save_data(db)
            st.sidebar.success("Wallet added successfully!")
            st.rerun()
        else:
            st.sidebar.error("Sothik wallet address din (0x... diye shuru hobe)")

with st.sidebar.expander("💵 Add New Deposit (Extra Fund)", expanded=False):
    deposit_val = st.number_input("Deposit Amount ($)", min_value=0.0, value=0.0, step=10.0)
    if st.button("Record Deposit"):
        if deposit_val > 0:
            db["deposits"] = db.get("deposits", 0.0) + deposit_val
            save_data(db)
            st.sidebar.success(f"Added ${deposit_val} to total capital!")
            st.rerun()

if st.sidebar.button("🗑️ Reset All Data"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.rerun()

# Calculations
total_current_equity = 0.0
total_initial_capital = db.get("deposits", 0.0)
wallet_results = []

for w in db["wallets"]:
    live_eq = fetch_equity(w["address"], w["platform"])
    if live_eq is not None and live_eq > 0:
        current_eq = live_eq
        w["last_equity"] = live_eq
    else:
        current_eq = w.get("last_equity", 1000.0)
    
    total_current_equity += current_eq
    total_initial_capital += w.get("initial_equity", 0.0)
    
    diff = current_eq - w.get("initial_equity", 0.0)
    wallet_results.append({
        "name": w["name"],
        "platform": w["platform"],
        "address": w["address"][:6] + "..." + w["address"][-4:],
        "equity": current_eq,
        "diff": diff
    })

save_data(db)

yesterday_total = db.get("yesterday_total", total_current_equity)
day_change = total_current_equity - yesterday_total

# Top Overview Card
st.markdown(f"""
    <div class="card">
        <div class="metric-title">All wallets · Total Perpetuals Equity</div>
        <div class="metric-value">${total_current_equity:,.2f}</div>
        <div class="{'change-down' if day_change < 0 else 'change-up'}">
            {'↓' if day_change < 0 else '↑'} ${abs(day_change):,.2f} compared with yesterday
        </div>
    </div>
""", unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔄 Refresh Data & Save Daily Snapshot"):
        db["yesterday_total"] = total_current_equity
        save_data(db)
        st.success("Snapshot saved as yesterday baseline!")
        st.rerun()

# Cost / Loss Calculation
# Formula: (Initial Capital + New Deposits) - Current Total Equity = Net Cost/Loss
farming_cost = total_initial_capital - total_current_equity

st.markdown("---")
c1, c2 = st.columns(2)
c1.metric("Total Invested Capital (Initial + Deposits)", f"${total_initial_capital:,.2f}")
c2.metric("Total Farming Cost / Loss", f"${farming_cost:,.2f}", delta=f"-${farming_cost:,.2f}" if farming_cost > 0 else f"+${abs(farming_cost):,.2f}", delta_inverse=True)

st.markdown("---")
st.subheader("📋 Connected Wallets Breakdown")

if not wallet_results:
    st.info("Sidebar theke apnar Lighter ba Arcus wallet add korun.")
else:
    for item in wallet_results:
        d_text = f"+${item['diff']:,.2f}" if item['diff'] >= 0 else f"-${abs(item['diff']):,.2f}"
        d_color = "#00CC96" if item['diff'] >= 0 else "#FF4B4B"
        st.markdown(f"""
            <div style="background-color: #161A23; border: 1px solid #262730; border-radius: 8px; padding: 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="color: #FFFFFF; font-size: 16px; font-weight: 600;">{item['platform']} — {item['name']}</div>
                    <div style="color: #8D96A0; font-size: 12px;">{item['address']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #FFFFFF; font-size: 18px; font-weight: 700;">${item['equity']:,.2f}</div>
                    <div style="color: {d_color}; font-size: 13px;">{d_text}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
