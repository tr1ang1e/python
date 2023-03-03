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


class Price:

    msg_total = 0

    def __init__(self, symbol: str):
        self.socket = WebSock()
        self.socket.start()
        # print(self.socket.start_symbol_ticker_socket(callback=self.btc_handle_msg, symbol=symbol))                # 24h statistics / interval = 1000ms
        # print(self.socket.start_depth_socket(callback=self.btc_handle_msg, symbol=symbol, interval=100))          # current depth  / interval = 100 or 1000ms
        print(self.socket.start_symbol_book_ticker_socket(callback=self.btc_handle_msg, symbol=symbol))             # realtime bid and ask

    def btc_handle_msg(self, msg):
        self.msg_total += 1
        # print(msg)
        return

    def stop(self):
        self.socket.stop()


class Account:
    def __init__(self, credentials_file: str):
        credentials_dict = get_credentials(credentials_file)
        credentials_api = credentials_dict["api"]
        self.credentials_account = credentials_dict["account"]
        self.api_demo = credentials_api["demo"]
        self.client = Client(self.api_demo["key_api"], self.api_demo["key_secret"])

    # use Client.get_account() to avoid separate calls and reduce time costs
    def print_spot_balance(self, assets: list):
        print("Balance")
        for asset in assets:
            balance_info = self.client.get_asset_balance(asset)
            total_balance = float(balance_info['free']) + float(balance_info['locked'])
            print("  {}: {}".format(asset, total_balance))

    def get_single_price(self, symbol: str):
        price = self.client.get_symbol_ticker(symbol=symbol)
        return price['price']


if __name__ == "__main__":
    btc = None
    try:
        account = Account("./credentials.json")
        account.print_spot_balance(['BTC', 'LTC', 'ETH'])
        btc = Price('BTCUSDT')
        sleep(6)
        btc.stop()
        print(btc.msg_total)
    except KeyboardInterrupt:
        btc.stop()
