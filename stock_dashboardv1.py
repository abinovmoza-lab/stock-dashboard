import yfinance as yf #Python library that fetches financial market data from Yahoo Finance.
import pandas as pd #Used for working with tabular data (DataFrames).
import streamlit as st #Builds the interactive web dashboard easily from Python code
import time

# --- Streamlit Dashboard Config ---
st.set_page_config(page_title="Stock Dashboard", layout="wide") #defines the app’s browser tab title and sets the page layout to wide for more space.
st.title("📊 Live Stock Dashboard") # displays a big title at the top of the app page.

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Settings")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 10, 300, 10) #Lets you choose how often (10–300 seconds) the dashboard refreshes. Default = 60 sec
st.sidebar.write(f"⏱ Dashboard refreshes every {refresh_rate} seconds")

default_codes = "VAS.AX, AX1.AX, SPK.AX, BOQ.AX, BEN.AX, EDV.AX" # defines default stock codes to show initially
stock_input = st.text_input("Enter stock codes separated by commas:", default_codes) # creates a text box for the user to type stock codes
stock_codes = [code.strip().upper() for code in stock_input.split(",")]
# stock_input.split(",") → splits the input string wherever there’s a comma, turning it into a list.
# [code.strip().upper() ...] → trims spaces and converts all codes to uppercase for consistency.

# --- Function to Fetch Data ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="2d")
        if len(data) < 2:
            return None
        current_price = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[-2]
        change = current_price - previous_close
        pct_change = (change / previous_close) * 100
        return {
            'Symbol': ticker,
            'Current Price': round(current_price, 2),
            'Previous Close': round(previous_close, 2),
            'Change': round(change, 2),
            'Change (%)': round(pct_change, 2)
        }
    except Exception as e:
        return {'Symbol': ticker, 'Error': str(e)}


# --- Placeholder for Live Updating ---
placeholder = st.empty() #Creates an “empty box” where we’ll continuously update the stock data table.

# --- Live Update Loop ---
while True: #Runs indefinitely, fetching new prices each cycle. Sleeps for the user-defined interval before fetching again.
    data_list = []
    for code in stock_codes:
        stock_data = get_stock_data(code)
        if stock_data:
            data_list.append(stock_data)

    df = pd.DataFrame(data_list)

    with placeholder.container(): #Every loop replaces the old dashboard with fresh data — without restarting Streamlit.
        if not df.empty:
            st.subheader("📈 Live Stock Summary")


            def highlight_changes(val):
                color = 'green' if val > 0 else 'red'
                return f'color: {color}'


            st.dataframe(
                df.style.format({
                    'Current Price': '${:.2f}',
                    'Previous Close': '${:.2f}',
                    'Change': '${:.2f}',
                    'Change (%)': '{:.2f}%'
                }).applymap(highlight_changes, subset=['Change', 'Change (%)'])
            )
            # --- Add Timestamp Below ---
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            st.caption(f"🕒 Last updated: {current_time}")

        else:
            st.warning("No valid data retrieved. Check the stock codes and try again.")

        st.caption(f"Data source: Yahoo Finance | Updated every {refresh_rate} seconds")

    time.sleep(refresh_rate)
