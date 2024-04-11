from functools import partial
import json
import time
from utils.common import interval_to_seconds, is_valid_syve_api_key, round_price
from utils.fetch import fetch_ohlc_price
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone
from datetime import timedelta
import pandas as pd
import sys
import os
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


def get_config():
    config_path = "data/config.json"
    key = None
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        key = config["syve_api_key"]
        if is_valid_syve_api_key(key):
            print(f"Started app with key = {key}")
            return config
    except Exception:
        pass
    if key is None:
        key = input("Enter Syve API Key: ")
        if is_valid_syve_api_key(key) is False:
            print(f"Provided Syve API key (= {key}) is invalid. Exited.", file=sys.stderr)
            os._exit(1)
        else:
            print(f"Started app with key = {key}")
    config = {"syve_api_key": key}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config


config = get_config()
syve_api_key = config["syve_api_key"]


st.set_page_config(page_title="Token Price Data Downloader | Syve", page_icon=":bar_chart:", layout="wide")
ctx = get_script_run_ctx()
session_id = ctx.session_id


class Colors:
    JUNGLE_GREEN = "#29a329"
    CARNATION = "#ff5050"


class ChartSettings:
    PRICE_TEMPLATE = "plotly_white"


def render_chart(df_price_ohlcv):
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.3)

    ohlcv_trace = go.Candlestick(
        x=df_price_ohlcv["date_open"],
        open=df_price_ohlcv["price_open"],
        high=df_price_ohlcv["price_high"],
        low=df_price_ohlcv["price_low"],
        close=df_price_ohlcv["price_close"],
        name="Price",
        increasing=dict(fillcolor=Colors.JUNGLE_GREEN, line=dict(color=Colors.JUNGLE_GREEN)),
        decreasing=dict(fillcolor=Colors.CARNATION, line=dict(color=Colors.CARNATION))
    )

    fig.add_trace(ohlcv_trace, row=1, col=1)
    fig.update_layout(
        template=ChartSettings.PRICE_TEMPLATE,
        xaxis_rangeslider_visible=False,
        yaxis=dict(fixedrange=True),
        margin=dict(l=100, r=20, t=20, b=100),
        height=700,
    )
    fig.update_traces(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def round_until_timestamp(until_timestamp, interval="1h"):
    curr_timestmap = int(time.time())
    if until_timestamp > curr_timestmap:
        interval_in_secs = interval_to_seconds(interval)
        until_timestamp = (curr_timestmap // interval_in_secs) * interval_in_secs + interval_in_secs
    return until_timestamp


def parse_user_inputs(user_token_address, user_from_date, user_until_date, user_interval):
    from_timestamp = int(datetime.strptime(user_from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    until_timestamp = int(datetime.strptime(user_until_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())    
    until_timestamp = (until_timestamp // 86400) * 86400 + 86400 - 1
    until_timestamp = round_until_timestamp(until_timestamp, interval=user_interval)
    output = {
        "token_address": user_token_address.lower(),
        "from_timestamp": from_timestamp,
        "until_timestamp": until_timestamp,
    }
    return output


def create_df(
    token_address,
    from_timestamp,
    until_timestamp,
    price_type="price_token_usd_robust_total_1h",
    interval="1h",
    skip_null=True,
    fill=False,
    precision="5g",
    order="asc",
    max_size=100,
    open_method="first_trade",
    pool_address="all",
    chain="eth",
    key=None,
):
    pool_address = pool_address.lower()
    until_timestamp = round_until_timestamp(until_timestamp, interval=interval)
    try:
        data = fetch_ohlc_price(
            token_address=token_address,
            pool_address=pool_address,
            interval=interval,
            from_timestamp=from_timestamp,
            until_timestamp=until_timestamp,
            price_type=price_type,
            skip_null=skip_null,
            fill=fill,
            max_size=max_size,
            order=order,
            open_method=open_method,
            chain=chain,
            key=key,
        )
        if not data:
            df = pd.DataFrame(
                {
                    "date_open": [-1],
                    "price_open": [-1],
                    "price_high": [-1],
                    "price_low": [-1],
                    "price_close": [-1],
                    "volume": [-1],
                }
            )
            return df
        records = data["data"]
        df = pd.DataFrame(records)
        round_func = partial(round_price, precision=precision)
        df['price_open'] = df['price_open'].apply(round_func).astype(str)
        df['price_high'] = df['price_high'].apply(round_func).astype(str)
        df['price_low'] = df['price_low'].apply(round_func).astype(str)
        df['price_close'] = df['price_close'].apply(round_func).astype(str)
        return df
    except Exception as e:
        return {"error": "Something went wrong"}


default_token_address = "0x6982508145454ce325ddbe47a25d4ec3d2311933"
default_chain = "eth"
default_until_timestamp = (int(time.time()) // 86400) * 86400 + 86400
default_until_timestamp = round_until_timestamp(default_until_timestamp, interval="1h")
default_until_date = datetime.utcfromtimestamp(default_until_timestamp)
default_from_date = default_until_date - timedelta(days=7)


with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


_, body, _ = st.columns([1, 8, 1])
with body:
    st.title("Token Price Data Downloader")
    st.info(
        "**Data:** https://syve.readme.io/reference/price_historical_ohlc",
        icon="💡",
    )

    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        token_address = st.text_input(label="**Token Address**", value=default_token_address)
    with d2:
        pool_address = st.text_input(label="**Pool Address**", value="all")
    with d3:
        user_chain = st.selectbox(
            "**Chain**",
            ("eth", "matic", "base"),
            index=0,
        )

    d21, d22, d23, d24 = st.columns([1, 1, 1, 1])
    with d21:
        user_price_type = st.selectbox(
            "**Price Type**",
            ("price_token_usd_robust_tick_1", "price_token_usd_tick_1"),
            index=0,
        )
    with d22:
        user_interval = st.selectbox(
            "**Interval**",
            ("1m", "5m", "15m", "30m", "1h", "4h", "1d"),
            index=4,
        )
    with d23:
        user_from_date = st.date_input(label="**From Date**", value=default_from_date)
    with d24:
        user_until_date = st.date_input(label="**Until Date**", value=default_until_date)

    d31, d32, d33, d34 = st.columns([1, 1, 1, 1])

    with d31:
        user_precision = st.selectbox(
            "**Precision**",
            ("2g", "3g", "4g", "5g", "6g"),
            index=2,
        )
    with d32:
        user_fill = st.selectbox(
            "**Fill**",
            ("True", "False"),
            index=0,
        )
    with d33:
        user_order = st.selectbox(
            "**Order**",
            ("Ascending", "Descending"),
            index=1,
        )
    with d34:
        user_max_size = st.selectbox(
            "**Max Size**",
            (100, 150, 200, 250, 1000),
            index=2,
        )

    if st.button("Apply"):
        log_msg = {
            "action": "apply_button_clicked",
            "timestamp": int(datetime.now().timestamp()),
            "session_id": session_id,
            "metadata": {
                "token_address": token_address,
                "from_date": str(user_from_date),
                "until_date": str(user_until_date),
            },
        }

        user_inputs = parse_user_inputs(
            user_token_address=token_address,
            user_from_date=str(user_from_date),
            user_until_date=str(user_until_date),
            user_interval=user_interval,
        )
        if user_inputs is None:
            err_msg = "**Invalid input**. Please check your input and try again.\n"
            st.error(err_msg)
        else:
            df = create_df(
                token_address=user_inputs["token_address"],
                from_timestamp=user_inputs["from_timestamp"],
                until_timestamp=user_inputs["until_timestamp"],
                price_type=user_price_type,
                interval=user_interval,
                skip_null=True,
                fill=user_fill == "True",
                precision=user_precision,
                order="asc" if user_order == "Ascending" else "desc",
                max_size=int(user_max_size),
                open_method="prev_close",
                pool_address=pool_address,
                chain=user_chain,
                key=syve_api_key,
            )
            render_chart(df)

        file_name = f"price_ohlc_{token_address}_{str(user_from_date)}_{str(user_until_date)}.csv"

        with st.expander("**View and Download**", expanded=True):
            df_height = min(50, len(df)) * 35
            st.dataframe(df, use_container_width=True, height=df_height)
            st.download_button(
                label="Download CSV!",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=file_name,
                mime="text/csv",
            )

    e1, e2 = st.columns([1, 1])
    with e1:
        st.info(
            "**Twitter:** [@syve_ai](https://twitter.com/syve_ai)",
            icon="💡",
        )
    with e2:
        st.info(
            "**Discord:** https://discord.com/invite/rs5GPAZ7tG",
            icon="🧠",
        )
