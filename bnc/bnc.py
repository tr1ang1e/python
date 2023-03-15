import os
import json
import logging
import logging.config
from logging.handlers import RotatingFileHandler
# from time import sleep

import binance.exceptions
from binance.client import Client
from binance import ThreadedWebsocketManager as WebSock


"""
TODO:
    - decide which information should be permanently shown
    - implement multithread logic
"""


class Logfile:
    """
        Contains properties for one particular
        logs file. Is used to separate logs.
    """

    def __init__(self, logfile_dict: dict):
        self.name = os.path.basename(logfile_dict["file"])
        self.path = os.path.join(os.path.abspath(logfile_dict["directory"]), logfile_dict["file"])
        self.max_size = logfile_dict["size"]
        self.backup_count = logfile_dict["back"]


class Api:
    """
        Contains properties for one particular API
    """

    def __init__(self, name: str, key_api: str, key_secret: str):
        self.name = name
        self.key_api = key_api
        self.key_secret = key_secret


class Settings:
    """
        Contains all settings passed to the
        script via every .json file in given dir
    """

    def __init__(self, settings_dir: str):
        settings_dir = os.path.abspath(settings_dir)
        ''' properties '''
        self.account_log = None
        self.price_log = None
        self.load_properties(settings_dir)
        ''' credentials '''
        self.api_demo = None
        self.load_credentials(settings_dir)

    def load_properties(self, settings_dir):
        properties_file = "properties.json"
        properties_path = os.path.join(settings_dir, properties_file)
        properties_fd = open(properties_path, "r")
        properties_dict = json.load(properties_fd)
        ''' logging '''
        logging_dict = properties_dict["logging"]
        self.account_log = Logfile(logging_dict["account"])
        self.price_log = Logfile(logging_dict["price"])

    def load_credentials(self, settings_dir):
        credentials_file = "credentials.json"
        credentials_path = os.path.join(settings_dir, credentials_file)
        credentials_fd = open(credentials_path, "r")
        credentials_dict = json.load(credentials_fd)
        api_dict = credentials_dict["api"]
        api_name = "demo"
        self.api_demo = Api(api_name, api_dict[api_name]["key_api"], api_dict[api_name]["key_secret"])


class Price:
    """
        Access to actual market prices
        Access is processed via: https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-ticker-streams
            API = Individual Symbol Ticker Streams
            description = 24-hour rolling window
            update = 1000 ms
            ticker = <symbol>@ticker
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


class Order:
    """
        Contains full info about order
        which was placed on the market

        TODO: parse response for convenient access
    """

    def __init__(self, api_response):
        self.info = api_response


class Account:
    """
        Provide access to all necessary account actions, e.g.
        get account info, set and remove orders, etc.

        TODO:
            - active orders storage
            - def get_active_orders(...)
            - def cansel_order(...)
    """

    buy_orders = dict()
    sell_orders = dict()

    def __init__(self, api: Api, logfile: Logfile):
        self.client = Client(api.key_api, api.key_secret)
        self.logger = init_logger(logfile)

    def get_balance(self, assets=("btc", "usdt"), base_asset="usdt"):
        """
            Slow operation. Bad to call in WebSocket callback function.
            TODO: Implement two thread logic
                1 = WebSocket communication
                2 = trading logic
        """
        self.logger.debug(f"get_balance(assets={assets}, base_asset='{base_asset}')")
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

        self.logger.info("Balance:")
        for key, value in balances.items():
            self.logger.info(f"      {key} = {value}")
        return balances

    def get_placed_orders(self):
        """
            Get all orders were placed on
            market but still weren't executed

            TODO: implement
        """
        self.logger.debug(f"get_placed_orders()")
        pass

    def get_single_price(self, symbol: str):
        self.logger.debug(f"get_single_price(symbol='{symbol}')")
        price_list = self.client.get_symbol_ticker(symbol=symbol)
        self.logger.info(f"      price={price_list['price']}")
        return price_list['price']

    def set_open_order(self, symbol, buy_price, quantity):
        """
            Function implements OPEN position logic (long-trading).
            If order PRICE is GREATER than market price, the order
            will be executed by current market price.

            TODO: information for logging
        """
        self.logger.debug(f"set_open_order(symbol='{symbol}', buy_price={buy_price}, quantity={quantity})")
        result = False
        try:
            response = self.client.order_limit_buy(
                symbol=symbol,
                price=buy_price,
                quantity=quantity,
                newOrderRespType="FULL"
            )
            self.logger.info("OPEN order placed successfully")
            self.buy_orders[response["newClientOrderId"]] = Order(response)
            result = True
        except binance.exceptions.BinanceAPIException as api_exception:
            self.logger.error("APIException: {}. {}".format(api_exception.code, api_exception.message))
            pass
        except Exception as default_exception:
            self.logger.warning("Not specified exception case:")
            self.logger.error(default_exception)
        return result

    def set_close_order(self, symbol, sell_price, quantity):
        """
            Function implements CLOSE position logic (long-trading).
            If order PRICE is LESS than market price, the order
            will be executed by current market price.

            TODO: information for logging
        """
        self.logger.debug(f"set_close_order(symbol='{symbol}', sell_price={sell_price}, quantity={quantity})")
        result = False
        try:
            response = self.client.order_limit_sell(
                symbol=symbol,
                price=sell_price,
                quantity=quantity,
                newOrderRespType="FULL"
            )
            self.logger.info("CLOSE order placed successfully")
            self.sell_orders[response["newClientOrderId"]] = Order(response)
            result = True
        except binance.exceptions.BinanceAPIException as api_exception:
            self.logger.error("APIException: {}. {}".format(api_exception.code, api_exception.message))
            pass
        except Exception as default_exception:
            self.logger.warning("Not specified exception case:")
            self.logger.error(default_exception)
        return result

    def cancel_order(self, order_id: str):
        """
            Cansel order which was placed on
            market but still wasn't executed

            TODO: implement
        """
        self.logger.debug(f"cancel_order(order_id={order_id})")
        pass


def carriage_return():
    print("\r")


def init_logger(logfile: Logfile):
    pass
    ''' formatter '''
    base_format = f"%(asctime)s.%(msecs)03d   | %(threadName)-11s  | %(filename)s:%(lineno)-4d  | %(levelname)-8s   >  %(message)s"
    timestamp_format = "%H:%M:%S"
    formatter = logging.Formatter(base_format, timestamp_format)
    ''' configure file logs '''
    file_handler = RotatingFileHandler(logfile.path, maxBytes=logfile.max_size, backupCount=logfile.backup_count)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    ''' configure console logs '''
    # probably not necessary
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(formatter)

    ''' configure logger itself '''
    logger = logging.getLogger(logfile.name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)
    return logger


def handle_price_msg(msg):
    """
        main business logic function
        TODO: implement two thread logic
    """
    print(msg["c"])   # "c" = last price
    return


if __name__ == "__main__":
    btc = None
    price = None
    try:
        settings = Settings("./settings")
        account = Account(settings.api_demo, settings.account_log)
        account.get_balance()
        account.set_open_order('BTCUSDT', 26000, 0.00062)

        # price = Price()
        # price.start_ticker("BTCUSDT", handle_price_msg)
        # sleep(4)
        # price.stop()

    except Exception as e:
        print(e)
        if price:
            # price.stop()
            pass
