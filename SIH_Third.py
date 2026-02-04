#SIH_Third.py
import streamlit as st
import pandas as pd
import os
from streamlit_autorefresh import st_autorefresh

LOG_CSV = "detections_log.csv"

st.set_page_config(page_title="Space Debris Dashboard", layout="wide")
st.title("🛰️ Space Debris Monitor — Live Dashboard")

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="refresh_dashboard")

if os.path.exists(LOG_CSV):
    try:
        # Try to read the CSV with error handling
        df = pd.read_csv(LOG_CSV, on_bad_lines='skip', engine='python')

        if df.empty:
            st.warning("Log file is empty. Run detection script to generate data.")
        else:
            st.subheader("📄 Recent Track Entries (last 50)")
            # Ensure required columns exist
            required_cols = ["frame", "time"]
            if all(col in df.columns for col in required_cols):
                latest = df.sort_values(required_cols, ascending=[False, False]).head(50)
            else:
                latest = df.head(50)
            st.dataframe(latest)

            # Simple computed risk metric (for demo)
            if "speed_px_per_s" in df.columns and "area" in df.columns:
                df["risk"] = (df["speed_px_per_s"] / df["speed_px_per_s"].max() +
                              df["area"] / df["area"].max()) / 2

                st.subheader("⚠️ Risk Summary (last 500 entries)")
                st.write(df.tail(500)["risk"].describe())

                st.subheader("📊 Risk Distribution")
                st.bar_chart(df.tail(500)["risk"])
            else:
                st.warning("Missing required columns for risk calculation (speed_px_per_s, area)")
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        st.info("The log file may be corrupted. Try running the detection script again to generate fresh logs.")
else:
    st.info("Log file not found yet. Run your detection script to generate logs.")
    
#streamlit run SIH_Third.py

