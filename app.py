import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os

# --- 1. CONFIGURATION ---
STOCKS = {
    "NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", 
    "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL", 
    "Meta": "META", "Netflix": "NFLX", "AMD": "AMD", "Reliance": "RELIANCE.NS"
}

# --- 2. DATA PERSISTENCE (THE MEMORY) ---
def log_sentiment_data(ticker, avg_sentiment):
    log_file = "market_history.csv"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = pd.DataFrame([[timestamp, ticker, avg_sentiment]], 
                             columns=['Timestamp', 'Ticker', 'Sentiment'])
    
    if not os.path.isfile(log_file):
        new_entry.to_csv(log_file, index=False)
    else:
        new_entry.to_csv(log_file, mode='a', header=False, index=False)
    
    return pd.read_csv(log_file)

# --- 3. SCRAPER ENGINE ---
def get_news(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }
    try:
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        news_table = soup.find(id='news-table')
        if not news_table: return None
        
        data = []
        for row in news_table.find_all('tr')[:15]:
            a_tag = row.find('a')
            if not a_tag: continue
            text = a_tag.get_text()
            # NLP Logic: TextBlob calculates the Polarity
            score = TextBlob(text).sentiment.polarity
            data.append([text, score])
        return pd.DataFrame(data, columns=['Headline', 'Sentiment'])
    except:
        return None

# --- 4. UI SETUP ---
st.set_page_config(page_title="Market Mood Tracker", layout="wide")
st.title("📈 Market Mood Tracker (Direction 1)")

# Sidebar selection
choice = st.sidebar.selectbox("Select Target Stock:", list(STOCKS.keys()))
target_ticker = STOCKS[choice]

if st.sidebar.button("Analyze Sentiment"):
    with st.spinner(f"Infiltrating {choice} news..."):
        df = get_news(target_ticker)
        
        if df is not None:
            avg_s = df['Sentiment'].mean()
            
            # Interpretation Logic
            if avg_s >= 0.5: mood = "🚀 EXTREME BULLISH (GREED)"
            elif avg_s >= 0.1: mood = "📈 BULLISH"
            elif avg_s <= -0.5: mood = "📉 EXTREME BEARISH (FEAR)"
            elif avg_s <= -0.1: mood = "📉 BEARISH"
            else: mood = "⚖️ NEUTRAL / SIDEWAYS"
            
            # Save and Load History
            history_df = log_sentiment_data(target_ticker, avg_s)
            
            # Visuals
            st.metric(label=f"Current {choice} Mood", value=mood, delta=round(avg_s, 3))
            
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=avg_s,
                    title={'text': "Sentiment Score (-1 to 1)"},
                    gauge={
                        'axis': {'range': [-1, 1]},
                        'steps': [
                            {'range': [-1, -0.1], 'color': "#ff4b4b"}, # Red
                            {'range': [-0.1, 0.1], 'color': "gray"},    # Neutral
                            {'range': [0.1, 1], 'color': "#00f2fe"}    # Blue/Green
                        ],
                        'bar': {'color': "white"}
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📊 Historical Trend")
                ticker_hist = history_df[history_df['Ticker'] == target_ticker]
                st.line_chart(ticker_hist.set_index('Timestamp')['Sentiment'])
            
            st.subheader("Latest Headlines Scraped")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Connection Error: Finviz is blocking the cloud server. Try again in 5 minutes.")
