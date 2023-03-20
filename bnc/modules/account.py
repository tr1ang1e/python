from .exceptions import BNCAttention, BNCExceptions, BNCCritical
from .price import Price
from .settings import Api, Logfile
from .utilities import init_logger
from binance.client import Client
from binance.exceptions import BinanceAPIException


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
    """

    buy_orders = dict()
    sell_orders = dict()

    def __init__(self, api: Api, logfile: Logfile, price: Price = None):
        self.client = None
        self.price = price
        self.get_client(api)
        self.logger = init_logger(logfile)
        self.logger.info(f"Account instance is created, key_api: '{api.key_api[:4:]}...{api.key_api[-4::]}'")

    def get_client(self, api: Api):
        """
            Initialize account data and prepare environment.

            return: no
            raise: see invoked calls (__check_permissions, __update_account_data)
        """
        self.client = Client(api.key_api, api.key_secret)
        self.__check_permissions(api.permissions)
        self.__update_account_data()

    def __check_permissions(self, expected_permissions):
        """
            Check if expected API permissions correspond to actual

            return: no
            raise: BNCAttention (UNSPECIFIED, API_ACCESS, API_PERMISSIONS)
        """
        try:
            actual_permissions = self.client.get_account_api_permissions()
        except BinanceAPIException as ex:
            raise BNCAttention(
                BNCExceptions.API_ACCESS,
                f"BinanceAPIException: \n\terror: {ex.code} \n\tmessage: {ex.message}"
            )
        except Exception as ex:
            raise BNCAttention(
                BNCExceptions.UNSPECIFIED,
                f"Unspecified exception: \n\ttype: {type(ex)} \n\tmessage: {ex}"
            )
        for perm in expected_permissions:
            if not actual_permissions[perm]:
                raise BNCAttention(
                    BNCExceptions.API_PERMISSIONS,
                    "Check expected permissions and actual ones: https://www.binance.com/ru/my/settings/api-management"
                )

    def __update_account_data(self):
        """
            TODO: make connecting to account safe
                - update balance
                - synchronize opened orders
        """
        pass

    def get_balance(self, assets=("btc", "usdt"), base_asset="usdt"):
        """
            Slow operation. Reimplement logic.
            (bad to call in WebSocket callback function)
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
        except BinanceAPIException as api_exception:
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
        except BinanceAPIException as api_exception:
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
        """
        self.logger.debug(f"cancel_order(order_id={order_id})")
        pass
