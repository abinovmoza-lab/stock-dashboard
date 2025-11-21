# share_dashboardv1.3.py

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Share Price Tracker + Watchlist/Portfolio",
    page_icon="📈",
    layout="wide"
)

# ------------------------------------------------
# AUTO-REFRESH (no external packages)
# ------------------------------------------------
def auto_refresh(interval_seconds: int):
    """Simple, safe refresh using session_state + st.rerun()"""
    last = st.session_state.get("last_refresh_time", 0)
    now = time.time()
    if now - last > interval_seconds:
        st.session_state.last_refresh_time = now
        st.rerun()

# ------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# ------------------------------------------------
# FETCHING FUNCTIONS
# ------------------------------------------------
@st.cache_data(ttl=30)
def fetch_price_for_symbol(symbol: str):
    """Robust price fetch with fallbacks."""
    try:
        t = yf.Ticker(symbol)
        info = t.info

        current = info.get("currentPrice") or info.get("regularMarketPrice")
        prev = info.get("previousClose") or info.get("regularMarketPreviousClose")

        if current is None or prev is None:
            hist = t.history(period="2d")
            if hist.shape[0] >= 2:
                prev = hist["Close"].iloc[-2]
                current = hist["Close"].iloc[-1]

        return (
            float(current) if current is not None else None,
            float(prev) if prev is not None else None
        )
    except Exception:
        return (None, None)

@st.cache_data(ttl=30)
def fetch_prices_for_list(symbols: list):
    return {s: fetch_price_for_symbol(s) for s in symbols}

# ------------------------------------------------
# HEADER
# ------------------------------------------------
st.title("📊 Live Share Price Tracker")
st.markdown("Track live prices, maintain a watchlist, and manage a simple portfolio.")

# ------------------------------------------------
# SIDEBAR - CONTROLS
# ------------------------------------------------
st.sidebar.header("Controls")

# --- Watchlist —
with st.sidebar.expander("Watchlist Controls", expanded=True):
    new_symbol = st.text_input("Add symbol (e.g. AAPL, BHP.AX):")

    if st.button("Add to Watchlist"):
        sym = new_symbol.strip().upper()
        if sym and sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(sym)
            st.success(f"Added {sym}")
        elif not sym:
            st.warning("Enter a symbol first")
        else:
            st.info(f"{sym} already exists")

    if st.session_state.watchlist:
        remove_sym = st.selectbox("Remove from watchlist:", [""] + st.session_state.watchlist)
        if st.button("Remove selected"):
            if remove_sym in st.session_state.watchlist:
                st.session_state.watchlist.remove(remove_sym)
                st.success(f"Removed {remove_sym}")
    else:
        st.write("Watchlist empty")

# --- Portfolio —
with st.sidebar.expander("Portfolio Controls", expanded=False):
    p_sym = st.text_input("Symbol:", key="pf_sym")
    p_qty = st.number_input("Quantity:", min_value=0.0, step=1.0, key="pf_qty")
    p_buy = st.number_input("Buy Price:", min_value=0.0, step=0.01, key="pf_buy")

    if st.button("Add to Portfolio"):
        sym = p_sym.strip().upper()
        if sym and p_qty > 0:
            st.session_state.portfolio.append(
                {"Symbol": sym, "Quantity": p_qty, "Buy Price": p_buy}
            )
            st.success(f"Added {sym}")
        else:
            st.warning("Enter valid symbol & quantity")

# --- Auto-refresh slider (seconds) —
refresh_interval = st.sidebar.slider("Auto-refresh (seconds)", 5, 300, 30, 5)

# ------------------------------------------------
# FETCH SYMBOLS
# ------------------------------------------------
symbols_to_fetch = list(dict.fromkeys(
    st.session_state.watchlist + [p["Symbol"] for p in st.session_state.portfolio]
))

prices_map = fetch_prices_for_list(symbols_to_fetch) if symbols_to_fetch else {}

# ------------------------------------------------
# TABS
# ------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Watchlist", "Portfolio", "All Symbols"])

# ------------------------------------------------
# WATCHLIST TAB
# ------------------------------------------------
with tab1:
    st.header("🔖 Watchlist")

    if not st.session_state.watchlist:
        st.info("Your watchlist is empty.")
    else:
        rows = []

        for s in st.session_state.watchlist:
            current, prev = prices_map.get(s, (None, None))
            change = None if current is None or prev is None else current - prev
            pct = None if change is None or prev == 0 else (change / prev) * 100

            rows.append({
                "Symbol": s,
                "Current Price": None if current is None else round(current, 2),
                "Previous Close": None if prev is None else round(prev, 2),
                "Change": None if change is None else round(change, 2),
                "% Change": None if pct is None else round(pct, 2)
            })

        df = pd.DataFrame(rows)
        df.insert(0, "Id", range(1, len(df) + 1))

        def gain_loss(v):
            if v is None:
                return ""
            return "color: green;" if v > 0 else "color: red;" if v < 0 else ""

        styled_df = df.style.format("{:.2f}", subset=["Current Price", "Previous Close", "Change", "% Change"]) \
            .applymap(gain_loss, subset=["Change", "% Change"])

        st.dataframe(styled_df)


    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ------------------------------------------------
# PORTFOLIO TAB
# ------------------------------------------------
with tab2:
    st.header("💼 Portfolio")

    if not st.session_state.portfolio:
        st.info("No holdings yet.")
    else:
        rows = []
        total_invested = 0
        total_current = 0

        for h in st.session_state.portfolio:
            sym = h["Symbol"]
            qty = h["Quantity"]
            buy = h["Buy Price"]

            current, _ = prices_map.get(sym, (None, None))

            invested = buy * qty
            current_value = None if current is None else current * qty
            pl = None if current_value is None else current_value - invested
            pl_pct = None if pl is None or invested == 0 else (pl / invested) * 100

            total_invested += invested
            if current_value:
                total_current += current_value

            rows.append({
                "Symbol": sym,
                "Quantity": qty,
                "Buy Price": round(buy, 2),
                "Invested": round(invested, 2),
                "Current Price": None if current is None else round(current, 2),
                "Current Value": None if current_value is None else round(current_value, 2),
                "P/L": None if pl is None else round(pl, 2),
                "P/L %": None if pl_pct is None else round(pl_pct, 2)
            })

        dfp = pd.DataFrame(rows)
        dfp.insert(0, "ID", range(1, len(dfp) + 1))


        def pl_style(v):
            if v is None:
                return ""
            return "color: green;" if v > 0 else "color: red;" if v < 0 else ""

        styled_portfolio = (
            dfp.style
            .format("{:.2f}", subset=[
                "Buy Price", "Invested", "Current Price", "Current Value",
                "P/L", "P/L %"
            ])
            .applymap(pl_style, subset=["P/L", "P/L %"])
        )

        st.dataframe(styled_portfolio)


        st.markdown("### Summary")
        total_pl = total_current - total_invested
        pl_pct = (total_pl / total_invested * 100) if total_invested else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Invested", f"${total_invested:,.2f}")
        c2.metric("Current Value", f"${total_current:,.2f}")
        c3.metric("Total P/L", f"${total_pl:,.2f}", f"{pl_pct:.2f}%")

# ------------------------------------------------
# ALL SYMBOLS TAB
# ------------------------------------------------
with tab3:
    st.header("All Symbol Data (Raw)")
    raw = [{"Symbol": k, "Current": v[0], "Previous": v[1]} for k, v in prices_map.items()]
    st.dataframe(pd.DataFrame(raw))

# ------------------------------------------------
# PERFORM AUTO-REFRESH (LAST LINE)
# ------------------------------------------------
auto_refresh(refresh_interval)


