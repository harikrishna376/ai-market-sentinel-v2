import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os
from google import genai

# --- CONFIG ---
STOCKS = {"NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", "Reliance": "RELIANCE.NS"}

def get_news(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.google.com/'}
    try:
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        news_table = soup.find(id='news-table')
        data = []
        for row in news_table.find_all('tr')[:15]:
            a_tag = row.find('a')
            if not a_tag: continue
            text = a_tag.get_text()
            score = TextBlob(text).sentiment.polarity
            data.append([text, score])
        return pd.DataFrame(data, columns=['Headline', 'Sentiment'])
    except: return None

st.set_page_config(page_title="Market Mood AI", layout="wide")
st.title("🤖 AI Market Sentinel")

st.sidebar.header("🔑 Authentication")
user_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
choice = st.sidebar.selectbox("Select Stock:", list(STOCKS.keys()))

if st.sidebar.button("Execute Analysis"):
    if not user_key:
        st.sidebar.error("Enter Key!")
    else:
        with st.spinner("Analyzing..."):
            df = get_news(STOCKS[choice])
            if df is not None:
                avg_s = df['Sentiment'].mean()
                
                # Visuals
                fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_s, 
                      title={'text': f"{choice} Sentiment"}, gauge={'axis':{'range':[-1,1]}}))
                st.plotly_chart(fig)
                
                # AI ANALYSIS (The clean 2026 syntax)
                st.subheader("🕵️ Chief Analyst Insight")
                try:
                    client = genai.Client(api_key=user_key)
                    context = "\n".join(df['Headline'].head(10).tolist())
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Analyze these headlines for {choice}: {context}. Give 3 ruthless bullet points on risk, drivers, and 24h outlook."
                    )
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
                
                st.dataframe(df)
