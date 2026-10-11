import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="Perpetual Farming Wallet Tracker",
    page_icon="📊",
    layout="wide"
)

st.title("⚡ Lighter & Arcus Perpetual Wallet Tracker")
st.markdown("আপনার ওয়ালেট অ্যানালাইসিস এবং ২৪ ঘণ্টার ইকুইটি পরিবর্তন অটোমেটিক ট্র্যাক করুন।")

# ওয়ালেট অ্যাড্রেস ইনপুট সেকশন
st.sidebar.header("⚙️ Wallet Setup")
st.sidebar.write("এখানে আপনার ওয়ালেট অ্যাড্রেসগুলো লিখুন:")

wallet_1 = st.sidebar.text_input("Wallet 1 Address (Level 1)", "0x1234567890abcdef1234567890abcdef12345678")
platform_1 = st.sidebar.selectbox("Platform 1", ["Lighter", "Arcus"], index=0)

wallet_2 = st.sidebar.text_input("Wallet 2 Address (Level 2)", "0xabcdef1234567890abcdef1234567890abcdef12")
platform_2 = st.sidebar.selectbox("Platform 2", ["Lighter", "Arcus"], index=1)

# API থেকে ডেটা ফেচ করার ফাংশন
def fetch_wallet_data(address, platform):
    # এটি লাইভ ড্যাশবোর্ড লেআউটের জন্য রিয়েল-টাইম স্টেট হিসাব করবে
    # Lighter/Arcus API Endpoints ইন্টিগ্রেশন
    try:
        if platform == "Lighter":
            # API Call placeholder
            equity = 12450.80
            yesterday_equity = 12110.55
        else:
            equity = 5120.00
            yesterday_equity = 5205.50
            
        change = equity - yesterday_equity
        percent_change = (change / yesterday_equity) * 100
        return equity, change, percent_change
    except Exception as e:
        return 0.0, 0.0, 0.0

# রিফ্রেশ বাটন
if st.button("🔄 Refresh Data"):
    st.rerun()

# সময় ট্র্যাকিং
last_refresh = datetime.now().strftime("%b %d, %Y - %I:%M:%S %p")

# ডেটা প্রসেসিং
w1_eq, w1_ch, w1_pct = fetch_wallet_data(wallet_1, platform_1)
w2_eq, w2_ch, w2_pct = fetch_wallet_data(wallet_2, platform_2)

# ড্যাশবোর্ড ডিসপ্লে টেবিল
data = [
    {
        "Wallet Name / Level": "Alpha Farm (Level 1)",
        "Platform": platform_1,
        "Wallet Address": wallet_1[:6] + "..." + wallet_1[-4:],
        "Current Perpetuals Equity": f"${w1_eq:,.2f}",
        "24h Change ($)": f"{'+' if w1_ch >= 0 else ''}${w1_ch:,.2f} ({w1_pct:+.2f}%)",
        "Last Refresh Time": last_refresh
    },
    {
        "Wallet Name / Level": "Secondary Hedge (Level 2)",
        "Platform": platform_2,
        "Wallet Address": wallet_2[:6] + "..." + wallet_2[-4:],
        "Current Perpetuals Equity": f"${w2_eq:,.2f}",
        "24h Change ($)": f"{'+' if w2_ch >= 0 else ''}${w2_ch:,.2f} ({w2_pct:+.2f}%)",
        "Last Refresh Time": last_refresh
    }
]

df = pd.DataFrame(data)

# মেট্রিক কার্ডস
col1, col2, col3 = st.columns(3)
col1.metric("Total Equity", f"${(w1_eq + w2_eq):,.2f}")
col2.metric("Total 24h Change", f"${(w1_ch + w2_ch):,.2f}")
col3.metric("Tracked Wallets", len(data))

st.markdown("---")
st.subheader("📋 Detailed Wallet Overview")
st.dataframe(df, use_container_width=True)