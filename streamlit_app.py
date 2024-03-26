import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import ccxt
import datetime as dt


@st.cache_data(ttl=600)
def fetch_all_funding_rate(exchange_name: str) -> dict:
    ex = getattr(ccxt, exchange_name)()
    info = ex.load_markets()
    perp = [p for p in info if info[p]["linear"]]
    fr_d = {}
    for p in perp:
        try:
            fr_d[p] = ex.fetch_funding_rate(p)["fundingRate"]
        except ccxt.ExchangeError:
            continue  # Consider logging this error
    return fr_d


@st.cache_data(ttl=600)
def fetch_funding_rate_history(exchange_name: str, symbol: str) -> tuple:
    ex = getattr(ccxt, exchange_name)()
    funding_history_dict = ex.fetch_funding_rate_history(symbol=symbol)
    funding_time = [dt.datetime.fromtimestamp(
        d["timestamp"] * 0.001) for d in funding_history_dict]
    funding_rate = [d["fundingRate"] * 100 for d in funding_history_dict]
    return funding_time, funding_rate


# exchange = 'bybit'
# Allow the user to select an exchange
exchange_options = ['bybit', 'mexc']
exchange_name = st.selectbox("Select Exchange", options=exchange_options)


res_all_funding_rate = fetch_all_funding_rate(exchange_name=exchange_name)

res_all_funding_rate_sorted = sorted(
    res_all_funding_rate.items(), key=lambda x: x[1], reverse=True)

symbols, rates = zip(*res_all_funding_rate_sorted[:20])
symbols = list(symbols)  # Convert symbols to a list of strings

df = pd.DataFrame({'Symbol': symbols, 'Funding Rate': rates})

st.title("Funding Rate for Symbols")
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('Symbol:N', sort='-y'),
    y='Funding Rate:Q',
    tooltip=['Symbol', 'Funding Rate']
).properties(width=800, height=400)
st.altair_chart(chart, use_container_width=True)


# Loop through each symbol, fetch its funding rate history, and plot individually
for symbol in symbols:
    funding_time, funding_rate = fetch_funding_rate_history(
        exchange=exchange_name, symbol=symbol)
    if funding_rate:  # Check if there's data to plot
        df = pd.DataFrame({
            'Date': pd.to_datetime(funding_time),
            'Funding Rate': funding_rate
        })

        # Plot using Altair
        chart = alt.Chart(df).mark_line().encode(
            x='Date:T',
            y=alt.Y('Funding Rate:Q', axis=alt.Axis(title='Funding Rate (%)')),
            tooltip=['Date:T', 'Funding Rate:Q']
        ).properties(width=800, height=400, title=f'Funding Rate for {symbol}').interactive()

        st.altair_chart(chart, use_container_width=True)
    else:
        st.write(f"No data available for {symbol}.")
