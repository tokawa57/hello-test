import streamlit as st
import pandas as pd
import altair as alt
import ccxt
from datetime import datetime, timedelta


@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_funding_rate(exchange_name: str) -> dict:
    exchange = getattr(ccxt, exchange_name)()
    markets = exchange.load_markets()
    funding_rates = {}
    for symbol, market in markets.items():
        if market.get("linear"):  # 線形契約に限定
            try:
                funding_rate = exchange.fetch_funding_rate(
                    symbol)["fundingRate"] * 100  # パーセンテージに変換
                funding_rates[symbol] = funding_rate
            except ccxt.ExchangeError:
                continue  # エラーハンドリングを考慮
    return funding_rates


@st.cache_data(ttl=600, show_spinner=False)
def fetch_funding_rate_history(exchange_name: str, symbol: str) -> pd.DataFrame:
    exchange = getattr(ccxt, exchange_name)()
    history = exchange.fetch_funding_rate_history(symbol)
    timestamps = [datetime.fromtimestamp(
        item['timestamp'] / 1000) for item in history]
    rates = [item['fundingRate'] * 100 for item in history]  # パーセンテージに変換
    return pd.DataFrame({'Date': timestamps, 'Funding Rate': rates})


def display_funding_rates(exchange_name, top_n):
    with st.spinner('Fetching funding rates...'):
        rates = fetch_all_funding_rate(exchange_name)
    # rates = fetch_all_funding_rate(exchange_name)
    rates_sorted = sorted(
        rates.items(), key=lambda x: x[1], reverse=True)[:top_n]
    symbols, rates = zip(*rates_sorted)

    df = pd.DataFrame({'Symbol': symbols, 'Funding Rate': rates})
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Symbol:N', sort='-y'),
        y='Funding Rate:Q',
        tooltip=['Symbol', 'Funding Rate']
    ).properties(width=800, height=400, title=f"Top {top_n} Funding Rates [%]")

    st.altair_chart(chart, use_container_width=True)


def display_funding_rate_history(exchange_name, symbol, start_date):
    df = fetch_funding_rate_history(exchange_name, symbol)
    if not df.empty:
        start_datetime = pd.to_datetime(start_date)
        # 指定された日付より後のデータのみフィルタリング
        df_filtered = df[df['Date'] > start_datetime]

        chart = alt.Chart(df_filtered).mark_line().encode(
            x='Date:T',
            y=alt.Y('Funding Rate:Q', axis=alt.Axis(title='Funding Rate [%]')),
            tooltip=['Date:T', 'Funding Rate:Q']
        ).properties(width=800, height=400, title=f'Funding Rate History for {symbol}').interactive()

        st.altair_chart(chart, use_container_width=True)
    else:
        st.write(f"No data available for {symbol}.")


def main():
    st.title("Funding Rate Dashboard")
    exchange_options = [('MEXC', 'mexc'),
                        ('OKX', 'okx'), ('Binance', 'binance'), ('Bybit(only in local)', 'bybit'),]
    selected_exchange = st.sidebar.selectbox(
        "Select Exchange", options=exchange_options, format_func=lambda x: x[0])
    # exchange_options = ['bybit', 'mexc', 'okx']
    # selected_exchange = st.sidebar.selectbox(
    #     "Select Exchange", exchange_options)
    top_n = st.sidebar.slider("Select Top N Symbols",
                              min_value=1, max_value=50, value=20)

    default_start_date = datetime.now().date() - timedelta(days=10)
    start_date = st.sidebar.date_input("Start Date", value=default_start_date)

    st.header("Funding Rate Overview")
    display_funding_rates(selected_exchange[1], top_n)

    st.header("Detailed Funding Rate History")

    # 資金調達率が高い順にシンボルを取得
    rates = fetch_all_funding_rate(selected_exchange[1])
    rates_sorted = sorted(rates.items(), key=lambda x: x[1], reverse=True)
    top_symbols = [symbol for symbol, rate in rates_sorted[:top_n]]
    # ソートされたシンボルのリストを用いて詳細な履歴を表示
    for symbol in top_symbols:
        display_funding_rate_history(selected_exchange[1], symbol, start_date)


if __name__ == "__main__":
    main()
