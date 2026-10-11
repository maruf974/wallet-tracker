import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Page Configuration
st.set_page_config(page_title="Perpetual Farming Portfolio", page_icon="⚡", layout="centered")

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

DATA_FILE = "wallets_data.json"

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

st.title("⚡ Perpetual Farming Portfolio Tracker")
st.markdown("Lighter & Arcus wallet tracking, daily PnL, and farming cost calculator.")

# Sidebar for managing wallets and deposits
st.sidebar.header("⚙️ Wallet & Fund Setup")

with st.sidebar.expander("➕ Add New Wallet", expanded=True):
    w_name = st.text_input("Wallet Name / Level", "Level 1 Main")
    w_platform = st.selectbox("Platform", ["Lighter", "Arcus"])
    w_address = st.text_input("Wallet Address (0x...)")
    initial_eq_input = st.number_input("Current/Initial Equity ($)", min_value=0.0, value=1000.0, step50.0)
    
    if st.button("Add Wallet"):
        if w_address:
            db["wallets"].append({
                "name": w_name,
                "platform": w_platform,
                "address": w_address,
                "initial_equity": initial_eq_input,
                "current_equity": initial_eq_input
            })
            save_data(db)
            st.sidebar.success("Wallet added successfully!")
            st.rerun()

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

# --- Main Dashboard ---
st.markdown("### Update Today's Equity for Each Wallet")
st.markdown("Protidin website-e giye apnar wallet-er current live equity golo nicher box-golo te update kore din.")

total_current_equity = 0.0
total_initial_capital = db.get("deposits", 0.0)
wallet_results = []

for i, w in enumerate(db["wallets"]):
    cols = st.columns([3, 2, 2])
    with cols[0]:
        st.write(f"**{w['platform']} — {w['name']}**")
        st.caption(f"{w['address'][:6]}...{w['address'][-4:]}")
    with cols[1]:
        # Live equity update input field for each wallet
        new_eq = st.number_input(f"Equity ($) {i}", min_value=0.0, value=float(w.get("current_equity", 1000.0)), step=10.0, key=f"eq_{i}")
        w["current_equity"] = new_eq
    with cols[2]:
        diff = new_eq - w.get("initial_equity", new_eq)
        d_text = f"+${diff:,.2f}" if diff >= 0 else f"-${abs(diff):,.2f}"
        st.metric("Change", d_text)
    
    total_current_equity += new_eq
    total_initial_capital += w.get("initial_equity", 0.0)
    wallet_results.append({
        "name": w["name"],
        "platform": w["platform"],
        "equity": new_eq,
        "diff": diff
    })

save_data(db)

yesterday_total = db.get("yesterday_total", total_current_equity)
day_change = total_current_equity - yesterday_total

st.markdown("---")

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
    if st.button("🔄 Save Today's Snapshot (Set Baseline for Tomorrow)"):
        db["yesterday_total"] = total_current_equity
        save_data(db)
        st.success("Snapshot saved successfully!")
        st.rerun()

# Farming Cost / Loss Calculation
# Formula: (Initial Capital + New Deposits) - Current Total Equity = Net Cost/Loss
farming_cost = total_initial_capital - total_current_equity

st.markdown("---")
c1, c2 = st.columns(2)
c1.metric("Total Invested Capital (Initial + Deposits)", f"${total_initial_capital:,.2f}")
c2.metric("Total Farming Cost / Loss", f"${farming_cost:,.2f}", delta=f"-${farming_cost:,.2f}" if farming_cost > 0 else f"+${abs(farming_cost):,.2f}", delta_inverse=True)
