import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os

# --- 1. CONFIGURATION ---
FAMOUS_STOCKS = {
    "NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", 
    "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL", 
    "Meta": "META", "Netflix": "NFLX", "AMD": "AMD", "Reliance": "RELIANCE.NS"
}

# --- 2. DATA PERSISTENCE ---
def log_sentiment_data(ticker, avg_sentiment):
    log_file = "market_history.csv"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[timestamp, ticker, avg_sentiment]], columns=['Timestamp', 'Ticker', 'Sentiment'])
    if not os.path.isfile(log_file): new_entry.to_csv(log_file, index=False)
    else: new_entry.to_csv(log_file, mode='a', header=False, index=False)
    return pd.read_csv(log_file)

# --- 3. THE SCRAPER ---
def get_live_news_elite(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_table = soup.find(id='news-table')
        if not news_table: return None
        headlines = []
        for row in news_table.find_all('tr')[:20]:
            a_tag = row.find('a')
            if not a_tag: continue
            text = a_tag.get_text()
            score = TextBlob(text).sentiment.polarity
            headlines.append([text, score])
        return pd.DataFrame(headlines, columns=['Headline', 'Sentiment'])
    except: return None

# --- 4. UI SETUP ---
st.set_page_config(page_title="Market Mood AI", layout="wide")
st.title("📈 Market Mood AI: Predictive Sentiment Engine")

# --- NEW USER GUIDE (STRATEGIC INTERPRETATION) ---
with st.expander("🎓 NEW USER GUIDE: How to read the Sentiment Score"):
    st.markdown("""
    ### 🧠 Sentiment Score Logic
    The score ranges from **-1.0 (Panic)** to **+1.0 (Euphoria)**.
    
    | Score Range | Market State | Example Headline |
    | :--- | :--- | :--- |
    | **+0.5 to +1.0** | 🚀 **Extreme Greed** | *"NVIDIA profits triple as AI demand explodes"* |
    | **+0.1 to +0.5** | 📈 **Bullish** | *"Apple launches innovative new feature"* |
    | **-0.1 to +0.1** | ⚖️ **Neutral** | *"Tesla releases monthly production report"* |
    | **-0.5 to -0.1** | 📉 **Bearish** | *"Microsoft faces minor supply chain delay"* |
    | **-1.0 to -0.5** | 📉 **Extreme Fear** | *"Major lawsuit filed against Meta; shares plummet"* |
    """)

# SIDEBAR
st.sidebar.header("Control Panel")
choice = st.sidebar.selectbox("Select Target Stock:", list(FAMOUS_STOCKS.keys()))
target_ticker = FAMOUS_STOCKS[choice]

if st.sidebar.button("Run Mission"):
    df = get_live_news_elite(target_ticker)
    
    if df is not None:
        avg_score = df['Sentiment'].mean()
        history_df = log_sentiment_data(target_ticker, avg_score)
        
        # --- DYNAMIC MOOD ALERTS ---
        if avg_score >= 0.15:
            st.success(f"🔥 **MARKET MOOD: BULLISH** ({avg_score:.2f}) - Buying pressure is high.")
        elif avg_score <= -0.15:
            st.error(f"⚠️ **MARKET MOOD: BEARISH** ({avg_score:.2f}) - Selling pressure is rising.")
        else:
            st.warning(f"⚖️ **MARKET MOOD: NEUTRAL** ({avg_score:.2f}) - Market is indecisive.")

        col1, col2 = st.columns(2)
        with col1:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = avg_score,
                title = {'text': f"{choice} Sentiment Gauge"},
                gauge = {
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': "white"},
                    'steps': [
                        {'range': [-1, -0.15], 'color': "#ff4b4b"},
                        {'range': [-0.15, 0.15], 'color': "#3d3d3d"},
                        {'range': [0.15, 1], 'color': "#00f2fe"}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col2:
            st.subheader("📊 Historical Sentiment Trend")
            ticker_history = history_df[history_df['Ticker'] == target_ticker]
            st.line_chart(ticker_history.set_index('Timestamp')['Sentiment'])

        st.subheader("Latest Headlines (Sorted by Impact)")
        st.dataframe(df.sort_values(by='Sentiment', ascending=False), use_container_width=True)
    else:
        st.error("Connection lost. Try again.")
