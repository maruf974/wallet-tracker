import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
import os

# পেজ কনফিগারেশন & কাস্টম ডার্ক থিম
st.set_page_config(page_title="Portfolio Overview", page_icon="📈", layout="centered")

# কাস্টম CSS (ছবি অনুযায়ী লুক এন্ড ফিল দেওয়ার জন্য)
st.markdown("""
    <style>
    .main-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .total-title { color: #808495; font-size: 14px; margin-bottom: 4px; }
    .total-equity { color: #FFFFFF; font-size: 38px; font-weight: 700; }
    .change-down { color: #FF4B4B; font-size: 16px; font-weight: 500; }
    .change-up { color: #00CC96; font-size: 16px; font-weight: 500; }
    .wallet-card {
        background-color: #161A23;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Lighter API থেকে রিয়েল-টাইম ইকুইটি ফেচ করার ফাংশন
def get_lighter_equity(wallet_address):
    try:
        # Lighter Public API Endpoint
        url = f"https://api.lighter.xyz/v1/account?address={wallet_address}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Lighter response structured equity balance
            return float(data.get("equity", 0.0))
    except Exception as e:
        pass
    return 0.0

# Arcus API/RPC থেকে রিয়েল-টাইম ইকুইটি ফেচ করার ফাংশন
def get_arcus_equity(wallet_address):
    try:
        # Arcus Public API Endpoint
        url = f"https://api.arcus.exchange/v1/user/account?address={wallet_address}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("total_equity", 0.0))
    except Exception as e:
        pass
    return 0.0

# ওয়ালেট ফাইল সেভ ও লোড লজিক
DATA_FILE = "wallets_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"wallets": [], "deposits": 0.0, "yesterday_total": 0.0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# সাইডবার - ওয়ালেট অ্যাড্রেস এবং ডিপোজিট ম্যানেজমেন্ট
st.sidebar.title("⚙️ Manage Portfolio")

# নতুন ওয়ালেট যোগ করা
with st.sidebar.expander("➕ Add New Wallet", expanded=False):
    w_name = st.text_input("Wallet Name / Level", "Wallet 1")
    w_platform = st.selectbox("Platform", ["Lighter", "Arcus"])
    w_address = st.text_input("Wallet Address")
    
    if st.button("Save Wallet"):
        if w_address:
            # First fetch initial equity
            eq = get_lighter_equity(w_address) if w_platform == "Lighter" else get_arcus_equity(w_address)
            db["wallets"].append({
                "name": w_name,
                "platform": w_platform,
                "address": w_address,
                "initial_equity": eq,
                "last_equity": eq
            })
            save_data(db)
            st.success(f"Added {w_name} successfully!")
            st.rerun()

# নতুন ফান্ড ডিপোজিট যোগ করা
with st.sidebar.expander("💵 Add Deposit (নতুন ফান্ড জমা)", expanded=False):
    dep_amount = st.number_input("Deposit Amount ($)", min_value=0.0, value=0.0, step=10.0)
    if st.button("Record Deposit"):
        if dep_amount > 0:
            db["deposits"] += dep_amount
            save_data(db)
            st.success(f"Added ${dep_amount} to Total Capital!")
            st.rerun()

if st.sidebar.button("🗑️ Reset All Wallets"):
    db = {"wallets": [], "deposits": 0.0, "yesterday_total": 0.0}
    save_data(db)
    st.rerun()

# --- ড্যাশবোর্ড মেনু ও হেডলাইন ---

st.title("Portfolio Overview")
st.caption("All wallets · Total Perpetuals Equity")

# ওয়ালেট ডেটা ক্যালকুলেশন
total_current_equity = 0.0
total_initial_capital = db.get("deposits", 0.0)
wallet_results = []

for w in db["wallets"]:
    # Real-time API fetch
    if w["platform"] == "Lighter":
        current_eq = get_lighter_equity(w["address"])
    else:
        current_eq = get_arcus_equity(w["address"])
    
    # Fallback to test/stored equity if API is zero/offline
    if current_eq == 0.0 and w.get("last_equity", 0) > 0:
        current_eq = w["last_equity"]
    else:
        w["last_equity"] = current_eq

    total_current_equity += current_eq
    total_initial_capital += w.get("initial_equity", 0.0)
    
    # Per-wallet 24h change vs initial
    diff = current_eq - w.get("initial_equity", 0.0)
    wallet_results.append({
        "name": f"{w['platform']} — {w['name']}",
        "equity": current_eq,
        "diff": diff
    })

# Yesterday compare calculation
yesterday_total = db.get("yesterday_total", total_current_equity)
day_change = total_current_equity - yesterday_total

# ১. টোটাল পোর্টফোলিও কার্ড (ছবির মতো ডিজাইন)
st.markdown(f"""
    <div style="background-color: #0E1117; border: 1px solid #262730; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
        <div style="color: #8D96A0; font-size: 14px;">All wallets · Total Perpetuals Equity</div>
        <div style="color: #FFFFFF; font-size: 40px; font-weight: 700; margin: 8px 0;">${total_current_equity:,.2f}</div>
        <div class="{ 'change-down' if day_change < 0 else 'change-up' }">
            { '↓' if day_change < 0 else '↑' } ${abs(day_change):,.2f} compared with yesterday
        </div>
    </div>
""", unsafe_allow_html=True)

# রিফ্রেশ বাটনে ক্লিক করলে গতকালের হিসাব আপডেট হবে
col_ref, col_cost = st.columns([1, 2])
with col_ref:
    if st.button("🔄 Refresh Data & Set Daily Benchmark"):
        db["yesterday_total"] = total_current_equity
        save_data(db)
        st.success("Refreshed! Today's snapshot recorded.")
        st.rerun()

# ২. Farming Cost / Net PnL সেকশন
net_farming_cost = total_initial_capital - total_current_equity
st.markdown("---")
col_c1, col_c2 = st.columns(2)
col_c1.metric("Total Invested + Deposits", f"${total_initial_capital:,.2f}")
col_c2.metric("Total Farming Cost / Loss", f"${net_farming_cost:,.2f}", delta=f"-${net_farming_cost:,.2f}" if net_farming_cost > 0 else f"+${abs(net_farming_cost):,.2f}")

st.markdown("---")
st.subheader("Wallets Breakdown")

# ৩. ইন্ডিভিজুয়াল ওয়ালেট কার্ড ডিসপ্লে (আপনার দেওয়া লেআউট অনুযায়ী)
if not wallet_results:
    st.info("সাইডবার (Sidebar) থেকে আপনার Lighter ও Arcus ওয়ালেট অ্যাড্রেসগুলো যোগ করুন।")
else:
    for item in wallet_results:
        diff_text = f"+${item['diff']:,.2f}" if item['diff'] >= 0 else f"-${abs(item['diff']):,.2f}"
        diff_color = "#00CC96" if item['diff'] >= 0 else "#FF4B4B"
        
        st.markdown(f"""
            <div style="background-color: #161A23; border-radius: 8px; padding: 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="color: #FFFFFF; font-size: 16px; font-weight: 600;">{item['name']}</div>
                    <div style="color: #8D96A0; font-size: 12px;">Level/Sub account</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #FFFFFF; font-size: 18px; font-weight: 700;">${item['equity']:,.2f}</div>
                    <div style="color: {diff_color}; font-size: 13px;">{diff_text}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
