from .settings import Logfile, Api
from .utilities import init_logger
from binance.client import Client
import binance.exceptions


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
            - def get_active_orders(...)
            - def cansel_order(...)
    """

    buy_orders = dict()
    sell_orders = dict()

    def __init__(self, api: Api, logfile: Logfile):
        self.client = Client(api.key_api, api.key_secret)
        self.check_permissions(api.permissions)
        self.logger = init_logger(logfile)

    def check_permissions(self, expected_permissions):
        actual_permissions = self.client.get_account_api_permissions()
        for perm in expected_permissions:
            if not actual_permissions[perm]:
                # TODO: exception
                pass

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
