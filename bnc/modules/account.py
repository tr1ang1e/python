from .exceptions import bnc_lib_exc_str, BNCAttention, BNCExceptions, BNCCritical
from .price import Price
from .settings import Api, Logfile
from .utilities import init_logger
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException, BinanceOrderException, \
    BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, \
    BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException


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

        return: no
        raise: see invoked calls (get_client)
    """

    def __init__(self, api: Api, logfile: Logfile, price: Price = None):
        self.client = None
        self.price = price
        self.get_client(api)
        self.balances = dict()          # current balance state
        self.buy_orders = dict()        # placed (not executed) orders
        self.sell_orders = dict()       # take profit (for both placed and executed buy orders)
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
            raise: BNCAttention (API_ACCESS, API_PERMISSIONS)
        """
        try:
            actual_permissions = self.client.get_account_api_permissions()
        except BinanceAPIException as ex:
            raise BNCAttention(
                BNCExceptions.API_ACCESS,
                f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message} \n\terror: {ex.code}"
            )

        # check if actual permissions are enough to satisfy required ones
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

            return: self.balances
            raise: BNCCritical (API_ACCESS)
        """
        self.logger.debug(f"get_balance(assets={assets}, base_asset='{base_asset}')")
        balances = dict()
        try:
            account_info = self.client.get_account()["balances"]
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
            self.balances = balances
        except (BinanceAPIException, BinanceRequestException) as ex:
            error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
            raise BNCCritical(
                BNCExceptions.API_ACCESS,
                f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message} {error}"
            )

        self.logger.info("Balance:")
        for key, value in self.balances.items():
            self.logger.info(f"      {key} = {value}")
        return self.balances

    def get_placed_orders(self):
        """
            Get all orders were placed on
            market but still weren't executed.
        """
        self.logger.debug(f"get_placed_orders()")
        pass

    def get_single_price(self, symbol: str):
        """
            Get current market price for specified symbol.

            return: price
            raise: see invoked calls (binance.Client.get_symbol_ticker)
        """
        self.logger.debug(f"get_single_price(symbol='{symbol}')")
        price_list = self.client.get_symbol_ticker(symbol=symbol)
        self.logger.info(f"      price={price_list['price']}")
        return price_list['price']

    def set_open_order(self, symbol, buy_price, quantity, attempts: int = 3):
        """
            Function implements OPEN position logic (long-trading).
            If order PRICE is GREATER than market price, the order
            will be executed by current market price.

            return: no
            raise: BNCAttention, BNCCritical (OPEN_ORDER)
        """
        self.logger.debug(f"set_open_order(symbol='{symbol}', buy_price={buy_price}, quantity={quantity})")
        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                response = self.client.order_limit_buy(
                    symbol=symbol,
                    price=buy_price,
                    quantity=quantity,
                    newOrderRespType="FULL"
                )
                self.logger.info("OPEN order placed successfully")
                self.buy_orders[response["newClientOrderId"]] = Order(response)
            except (BinanceRequestException,
                    BinanceAPIException,
                    BinanceOrderException,
                    BinanceOrderInactiveSymbolException
                    ) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCCritical(
                    BNCExceptions.OPEN_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message} {error}"
                )
            except (BinanceOrderMinAmountException,
                    BinanceOrderMinPriceException,
                    BinanceOrderMinTotalException,
                    BinanceOrderUnknownSymbolException,
                    ) as ex:
                raise BNCAttention(
                    BNCExceptions.OPEN_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message}"
                )

    def set_order_tp(self, symbol, sell_price, quantity, attempts: int = 3):
        """
            Function implements CLOSE position logic (long-trading).
            If order PRICE is LESS than market price, the order
            will be executed by current market price.

            return: no
            raise: BNCAttention, BNCCritical (TP_ORDER)
        """
        self.logger.debug(f"set_close_order(symbol='{symbol}', sell_price={sell_price}, quantity={quantity})")
        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                response = self.client.order_limit_sell(
                    symbol=symbol,
                    price=sell_price,
                    quantity=quantity,
                    newOrderRespType="FULL"
                )
                self.logger.info("TAKE PROFIT order placed successfully")
                self.sell_orders[response["newClientOrderId"]] = Order(response)
            except (BinanceRequestException,
                    BinanceAPIException,
                    BinanceOrderException,
                    BinanceOrderInactiveSymbolException
                    ) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCCritical(
                    BNCExceptions.TP_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message} {error}"
                )
            except (BinanceOrderMinAmountException,
                    BinanceOrderMinPriceException,
                    BinanceOrderMinTotalException,
                    BinanceOrderUnknownSymbolException,
                    ) as ex:
                raise BNCAttention(
                    BNCExceptions.TP_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message}"
                )

    def cancel_order(self, symbol: str, order_id: str, attempts: int = 3):
        """
            Cansel order which was placed on
            market but still wasn't executed.

            return: no
            raise: BNCAttention (CANSEL_ORDER)
        """
        self.logger.debug(f"cancel_order(symbol='{symbol}', order_id='{order_id}')")
        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                self.client.cancel_order(symbol=symbol, origClientOrderId=order_id)
            except (BinanceAPIException, BinanceRequestException) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCAttention(
                    BNCExceptions.CANSEL_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {ex} \n\tmessage: {ex.message} {error}"
                )
