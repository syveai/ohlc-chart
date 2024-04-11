import requests
import json
import time


def fetch_ohlc_price(
    token_address="0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
    pool_address="all",
    interval="1h",
    from_timestamp=0,
    until_timestamp=None,
    price_type="price_token_usd_robust_tick_1",
    skip_null=True,
    fill=True,
    max_size=100,
    order="desc",
    open_method="prev_close",
    chain="matic",
    key=None,
):
    if key is None:
        raise ValueError("API key is required")
    if until_timestamp is None:
        until_timestamp = int(time.time())

    url = "https://api.syve.ai/v1/price/historical/ohlc"
    params = {
        "token_address": token_address,
        "pool_address": pool_address,
        "interval": interval,
        "from_timestamp": from_timestamp,
        "until_timestamp": until_timestamp,
        "price_type": price_type,
        "chain": chain,
        "skip_null": skip_null,
        "fill": fill,
        "max_size": max_size,
        "order": order,
        "open_method": open_method,
        "key": key,
    }
    res = requests.get(url, params=params)
    data = res.json()
    return data


if __name__ == "__main__":
    data = fetch_ohlc_price(max_size=10)
    print(json.dumps(data, indent=2))
