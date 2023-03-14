import os
import json
from time import sleep
from binance.client import Client
from binance import ThreadedWebsocketManager as WebSock


def carriage_return():
    print("\r")


def get_credentials(credentials_file: str):
    credentials_file = open(credentials_file, "r")
    credentials_dict = json.load(credentials_file)
    return credentials_dict


def handle_price_msg(msg):
    """
        main business logic function
        TODO: Implement two thread logic
    """
    print(msg["c"])   # "c" = last price
    return


class Price:
    """
        Access to actual market prices
        Access is processed via: https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-ticker-streams
            API = Individual Symbol Ticker Streams
            description = 24-hour rolling window
            update = 1000 ms
            ticker = <symbol@>ticker
    """

    tickers = list()

    def __init__(self):
        self.socket = WebSock()
        self.socket.start()

    def start_ticker(self, symbol: str, callback):
        """
            Must be called at least once
        """
        ticker = symbol.lower() + "@ticker"
        if not (ticker in self.tickers):
            # callback will be invoked every time WebSocket proceed packet exchange
            new_ticker = self.socket.start_symbol_ticker_socket(callback=callback, symbol=symbol.upper())
            self.tickers.append(new_ticker)

    # safe even if __init__ wasn't successful
    def stop(self):
        self.socket.stop()

    def __del__(self):
        self.stop()


class Account:

    def __init__(self, credentials_file: str):
        credentials_dict = get_credentials(credentials_file)
        credentials_api = credentials_dict["api"]
        self.credentials_account = credentials_dict["account"]
        self.api_demo = credentials_api["demo"]
        self.client = Client(self.api_demo["key_api"], self.api_demo["key_secret"])

    def get_balance(self, assets=("btc", "usdt"), base_asset="usdt"):
        """
            Slow operation. Bad to call in WebSocket callback function.
            TODO: Implement two thread logic
                1 = WebSocket communication
                2 = trading logic
        """
        account_info = self.client.get_account()["balances"]
        balances = dict()
        balances["total"] = [base_asset, 0]
        for asset in assets:
            balances[asset] = dict()
            for asset_info in account_info:
                if asset_info["asset"].lower() == asset.lower():
                    balances[asset]["free"] = float(asset_info["free"])
                    balances[asset]["locked"] = float(asset_info["locked"])
                    asset_total = balances[asset]["free"] + balances[asset]["locked"]
                    if asset != base_asset:
                        symbol = (asset + base_asset).upper()
                        current_price = float(self.get_single_price(symbol))
                        balances["total"][1] += current_price * asset_total
                    else:
                        balances["total"][1] += asset_total
        balances["total"][1] = round(balances["total"][1], 8)
        return balances

    def get_single_price(self, symbol: str):
        price_list = self.client.get_symbol_ticker(symbol=symbol)
        return price_list['price']

    def set_sell_limit_order(self, symbol, price, quantity):
        print(self.client.order_limit_sell(symbol=symbol, price=price, quantity=quantity))
        return


if __name__ == "__main__":
    btc = None
    price = None
    try:
        account = Account("./credentials.json")
        price = Price()
        price.start_ticker("BTCUSDT", handle_price_msg)
        sleep(4)
        # account.set_sell_limit_order('BTCUSDT', 26700, 0.0006)
        # sleep(2)
        price.stop()
    except Exception as e:
        print(e)
        if price:
            price.stop()
