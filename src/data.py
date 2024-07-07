import glob
import json
import os
import pickle
import time

import pandas as pd
import requests
from pycoingecko import CoinGeckoAPI
from tqdm import tqdm

cg = CoinGeckoAPI()


class BinanceClient(object):
    # https://github.com/AlchemyHub/A1chemy/blob/master/a1chemy/data_source/binance.py
    def __init__(self) -> None:
        self.headers = {
            "authority": "www.binance.com",
            "x-trace-id": "c829406a-6c1f-45b6-a55a-cec1bb858ad1",
            "csrftoken": "d41d8cd98f00b204e9800998ecf8427e",
            "x-ui-request-trace": "c829406a-6c1f-45b6-a55a-cec1bb858ad1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "content-type": "application/json",
            "lang": "zh-CN",
            "fvideo-id": "31b3fe32b4dba62987d3203e5ad881d76b6fef2a",
            "sec-ch-ua-mobile": "?0",
            "device-info": "eyJzY3JlZW5fcmVzb2x1dGlvbiI6IjI1NjAsMTQ0MCIsImF2YWlsYWJsZV9zY3JlZW5fcmVzb2x1dGlvbiI6IjI1NjAsMTM1MiIsInN5c3RlbV92ZXJzaW9uIjoiTWFjIE9TIDEwLjE1LjciLCJicmFuZF9tb2RlbCI6InVua25vd24iLCJzeXN0ZW1fbGFuZyI6ImVuIiwidGltZXpvbmUiOiJHTVQrOCIsInRpbWV6b25lT2Zmc2V0IjotNDgwLCJ1c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTVfNykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzkyLjAuNDUxNS4xNTkgU2FmYXJpLzUzNy4zNiIsImxpc3RfcGx1Z2luIjoiQ2hyb21lIFBERiBQbHVnaW4sQ2hyb21lIFBERiBWaWV3ZXIsTmF0aXZlIENsaWVudCIsImNhbnZhc19jb2RlIjoiYTMxMWNjZTEiLCJ3ZWJnbF92ZW5kb3IiOiJJbnRlbCBJbmMuIiwid2ViZ2xfcmVuZGVyZXIiOiJJbnRlbCBJcmlzIFBybyBPcGVuR0wgRW5naW5lIiwiYXVkaW8iOiIxMjQuMDQzNDc2NTc4MDgxMDMiLCJwbGF0Zm9ybSI6Ik1hY0ludGVsIiwid2ViX3RpbWV6b25lIjoiQXNpYS9TaGFuZ2hhaSIsImRldmljZV9uYW1lIjoiQ2hyb21lIFY5Mi4wLjQ1MTUuMTU5IChNYWMgT1MpIiwiZmluZ2VycHJpbnQiOiIxYjJlNDcxMmQ0MTE2MjMyNzRmM2JmY2UyZWYwNDkwNSIsImRldmljZV9pZCI6IiIsInJlbGF0ZWRfZGV2aWNlX2lkcyI6IiJ9",
            "bnc-uuid": "bde6dfb0-cafa-4be3-988d-9cc313cddf26",
            "clienttype": "web",
            "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            "accept": "*/*",
            "origin": "https://www.binance.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en",
        }
        main_page_response = requests.get(
            "https://www.binance.com/", headers=self.headers
        )
        self.cookies = main_page_response.cookies

    def fund_rating(self, symbol: str, rows: int = 100):
        data = {"symbol": symbol, "page": 1, "rows": rows}  # can do 10_000 max
        response = requests.post(
            "https://www.binance.com/bapi/futures/v1/public/future/common/get-funding-rate-history",
            headers=self.headers,
            cookies=self.cookies,
            data=json.dumps(data),
        )
        df = pd.DataFrame(response.json()["data"])

        if df.empty:
            print(f"No data found for {symbol}")
            return df

        # Convert timestamp to datetime
        df["calcTime"] = pd.to_datetime(df["calcTime"], unit="ms")

        return df


def get_top_vol_coins(NUM_COINS) -> list:

    CACHE_FILE = "data/top_vol_coins_cache.pkl"
    CACHE_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds
    # List of symbols to exclude
    STABLE_COINS = [
        "OKBUSDT",
        "DAIUSDT",
        "USDTUSDT",
        "USDCUSDT",
        "BUSDUSDT",
        "TUSDUSDT",
        "PAXUSDT",
        "EURUSDT",
        "GBPUSDT",
        "CETHUSDT",
        "WBTCUSDT",
    ]

    # Check if the cache file exists and is not expired
    os.makedirs(CACHE_FILE.split("/")[0], exist_ok=True)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            cache_data = pickle.load(f)
            cache_time = cache_data["timestamp"]
            if time.time() - cache_time < CACHE_EXPIRATION:
                # Return the cached data if it's not expired
                print("Using cached top volume coins")
                return cache_data["data"][:NUM_COINS]

    # Fetch fresh data if the cache is missing or expired
    df = pd.DataFrame(cg.get_coins_markets("usd"))["symbol"].str.upper() + "USDT"

    sorted_volume = df[~df.isin(STABLE_COINS)]
    top_vol_coins = sorted_volume.tolist()

    # Save the result to the cache
    with open(CACHE_FILE, "wb") as f:
        pickle.dump({"timestamp": time.time(), "data": top_vol_coins}, f)

    return top_vol_coins[:NUM_COINS]


def get_all_funding_rates(NUM_COINS: int = 30):
    # TODO: Check if there is new data and save it
    b = BinanceClient()
    symbols = get_top_vol_coins(NUM_COINS=NUM_COINS)

    os.makedirs("data/funding_rate", exist_ok=True)

    for symbol in tqdm(symbols, desc="Processing symbols"):
        tqdm.write(f"Processing symbol: {symbol}")
        df = b.fund_rating(symbol, rows=10_000)
        # Save the df in data/funding_rate/symbol.csv
        if not df.empty:
            df.to_csv(f"data/funding_rate/{symbol}.csv", index=False)


def load_funding_rate_data(directory):
    all_files = glob.glob(os.path.join(directory, "*.csv"))

    if all_files == []:
        print("No data found. Fetching new data.")
        get_all_funding_rates()
        all_files = glob.glob(os.path.join(directory, "*.csv"))

    df_list = []

    for file in all_files:
        df = pd.read_csv(file, parse_dates=["calcTime"])

        # Get the latest date of the data
        latest_date = df["calcTime"].max()

        # If the data is older than 12 hours, fetch new data
        if pd.Timestamp.now() - latest_date > pd.Timedelta(hours=12):
            print(f"Fetching new data for {file}")
            symbol = file.split("/")[-1].split(".")[0]
            symbol = symbol.split("\\")[-1]
            b = BinanceClient()
            # Get the new data
            new_df = b.fund_rating(symbol, rows=10_000)
            # If it is not empty, save it to the file
            if not new_df.empty:
                new_df.to_csv(file, index=False)
                df = pd.read_csv(file, parse_dates=["calcTime"])

        df_list.append(df)

    all_data = pd.concat(df_list, ignore_index=True)
    return all_data


def prepare_heatmap_data(df, NUM_DAYS: int) -> pd.DataFrame:

    # Filter data for the last NUM_DAYS days
    last_n_days = df["calcTime"].max() - pd.Timedelta(days=NUM_DAYS)
    df = df[df["calcTime"] >= last_n_days]

    # Multiply funding rate with 100 to get percentage
    df.loc[:, "lastFundingRate"] = df["lastFundingRate"].multiply(100)

    # Pivot the data to create a matrix for the heatmap
    heatmap_data = df.pivot(
        index="symbol", columns="calcTime", values="lastFundingRate"
    )

    # Forward fill to handle NaN values
    heatmap_data = heatmap_data.ffill(axis=1)
    # Also do a backward fill to handle NaN values at the start
    heatmap_data = heatmap_data.bfill(axis=1)
    return heatmap_data
