import requests
from datetime import datetime


def round_price(number, precision="5g"):
    format_string = "{:." + precision + "}"
    return format_string.format(number)


def to_date(ts):
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def interval_to_seconds(interval):
    amount = int(interval[:-1])
    freq = interval[-1]
    if freq == "s":
        return amount
    elif freq == "m":
        return amount * 60
    elif freq == "h":
        return amount * 3600
    elif freq == "d":
        return amount * 86400
    else:
        raise ValueError("Invalid frequency in interval: '{}'".format(freq))


def is_valid_syve_api_key(syve_api_key: str) -> bool:
    """
    Check if the Syve API key is valid by making a request to the Syve API.
    """
    url = "https://api.syve.ai/v1/check-usage"
    params = {"key": syve_api_key}
    res = requests.get(url, params=params)
    data = res.json()
    if "error" in data:
        return False
    return True
