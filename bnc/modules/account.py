from .exceptions import bnc_lib_exc_str, BNCAttention, BNCExceptions, BNCCritical
from .settings import Api, Logfile
from .utilities import init_logger
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException, BinanceOrderException, \
    BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, \
    BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException
from enum import Enum


class OrderType(Enum):
    BUY_MARKET = 0
    BUY_LIMIT = 1
    SELL_MARKET = 2
    SELL_LIMIT = 3


class Order:
    """
        Contains full info about order
        which was:
            - initiated and
            - executed (filled) if was
    """

    # statuses
    REJECT = -1
    INITED = 0
    OPENED = 1
    CLOSED = 2

    def __init__(self, symbol: str, quantity: float, price: str):
        self.status = Order.INITED
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.id = None      # always corresponds to API "clientOrderId" field
        self.side = None    # differ buy and sell orders possibility

    def opened(self, response: dict):
        self.status = Order.OPENED
        self.side = response["side"]
        self.id = response["clientOrderId"]
        exec_quantity = float(response["executedQty"])
        if exec_quantity < self.quantity:
            pass
        self.quantity = exec_quantity
        return self


class Account:
    """
        Provide access to all necessary account actions, e.g.
        get account info, set and remove orders, etc.

        return: no
        raise: see invoked calls (get_client)
    """

    def __init__(self, api: Api, recv_window: int, logfile: Logfile):
        self.name = api.name
        self.logger = init_logger(logfile)
        self.recv_window = recv_window
        self.client = None
        self.get_client(api)
        self.balances = dict()          # current balance state
        self.placed_orders = list()     # placed but not executed orders

        '''
        self.buy_orders = dict()        # placed (not executed) orders
        self.sell_orders = dict()       # take profit (for both placed and executed buy orders)
        self.pair = 0                   # unique ID to be able to match buy-sell pairs
        '''

        self.logger.info(f"Account instance is created")

    def get_client(self, api: Api):
        """
            Initialize account data and prepare environment.

            return: no
            raise: see invoked calls (__check_permissions, __update_account_data)
        """
        self.logger.debug(f"get_client(api='{api.name}')")
        self.logger.debug(f"    key_api: '{api.key_api[:4:]}...{api.key_api[-4::]}'")
        self.logger.debug(f"    key_sec: '{api.key_secret[:2:]}.......{api.key_api[-2::]}'")
        self.logger.debug(f"    using testnet: {api.is_testnet}")
        self.client = Client(api.key_api, api.key_secret, testnet=api.is_testnet)
        if not api.is_testnet:
            self.check_permissions(api.permissions)
            self.update_account_data()

    def check_permissions(self, expected_permissions):
        """
            Check if expected API permissions correspond to actual

            return: no
            raise: BNCAttention (API_ACCESS, API_PERMISSIONS)
        """
        self.logger.debug(f"__check_permissions(expected_permissions={expected_permissions}")
        try:
            actual_permissions = self.client.get_account_api_permissions(recvWindow=self.recv_window)
        except BinanceAPIException as ex:
            raise BNCAttention(
                BNCExceptions.API_ACCESS,
                f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} \n\terror: {ex.code}"
            )

        # check if actual permissions are enough to satisfy required ones
        for perm in expected_permissions:
            if not actual_permissions[perm]:
                raise BNCAttention(
                    BNCExceptions.API_PERMISSIONS,
                    "Check expected permissions and actual ones: https://www.binance.com/ru/my/settings/api-management"
                )

    def update_account_data(self):
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
            account_info = self.client.get_account(recvWindow=self.recv_window)["balances"]
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
                f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
            )

        self.logger.info("Balance:")
        for key, value in self.balances.items():
            self.logger.info(f"    {key} = {value}")
        return self.balances

    def get_placed_orders(self, symbol: str):
        """
            Get all orders were placed on
            market but still weren't executed.

            return: self.placed_orders
            raise: BNCAttention (GET_ORDERS)
        """
        self.logger.debug(f"get_placed_orders(symbol='{symbol}')")
        try:
            self.placed_orders = self.client.get_open_orders(symbol=symbol, recvWindow=self.recv_window)
            return self.placed_orders
        except (BinanceAPIException, BinanceRequestException) as ex:
            error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
            raise BNCAttention(
                BNCExceptions.GET_ORDERS,
                f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
            )

    def get_single_price(self, symbol: str):
        """
            Get current market price for specified symbol.

            return: price
            raise: see invoked calls (binance.Client.get_symbol_ticker)
        """
        self.logger.debug(f"get_single_price(symbol='{symbol}')")
        price_list = self.client.get_symbol_ticker(symbol=symbol)
        self.logger.info(f"'{symbol}' = {price_list['price']}")
        return price_list['price']

    def buy_limit(self, order: Order, attempts: int = 3):
        """
            If order PRICE is GREATER than market price, the order
            will be executed by current market price.

            return: no
            raise: BNCAttention, BNCCritical (OPEN_ORDER)
        """
        try:
            order = self.place_order(OrderType.BUY_LIMIT, order, attempts)
            return order
        except Exception as ex:
            raise ex

    def sell_limit(self, order: Order, attempts: int = 3):
        """
            If order PRICE is LESS than market price, the order
            will be executed by current market price.

            return: no
            raise: BNCAttention, BNCCritical (TP_ORDER)
        """
        try:
            order = self.place_order(OrderType.SELL_LIMIT, order, attempts)
            return order
        except Exception as ex:
            raise ex

    def place_order(self, order_type: OrderType, order: Order, attempts: int):
        symbol = order.symbol
        price = order.price
        quantity = order.quantity
        self.logger.debug("place_order(order={}, symbol={}, price={}, quantity={}, attempts={}".format(
            order_type.name,
            symbol,
            price,
            quantity,
            attempts
        ))

        api = {
            OrderType.BUY_MARKET: None,
            OrderType.BUY_LIMIT: self.client.order_limit_buy,
            OrderType.SELL_MARKET: None,
            OrderType.SELL_LIMIT: self.client.order_limit_sell
        }

        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                response = api[order_type](symbol=symbol, price=price, quantity=quantity, newOrderRespType="RESULT")
                order = order.opened(response)
                self.logger.info("Order PLACED successfully. \n\tID: {} \n\tquantity: {}".format(
                    order.id,
                    order.quantity
                ))
                return order
            except (BinanceRequestException,
                    BinanceAPIException,
                    BinanceOrderException,
                    BinanceOrderInactiveSymbolException) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCCritical(
                    BNCExceptions.TP_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
                )
            except (BinanceOrderMinAmountException,
                    BinanceOrderMinPriceException,
                    BinanceOrderMinTotalException,
                    BinanceOrderUnknownSymbolException) as ex:
                raise BNCAttention(
                    BNCExceptions.TP_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message}"
                )

    def cancel_order(self, order: Order, attempts: int = 3):
        """
            Cansel order which was placed on
            market but still wasn't executed.

            return: no
            raise: BNCAttention (CANSEL_ORDER)
        """
        symbol = order.symbol
        order_id = order.id
        self.logger.debug(f"cancel_order(symbol='{symbol}', id={order_id})")
        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                self.client.cancel_order(symbol=symbol, origClientOrderId=order_id)
                self.logger.info(f"Order CANCELLED successfully. ID: {order.id}")
                break
            except (BinanceAPIException, BinanceRequestException) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCAttention(
                    BNCExceptions.CANSEL_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
                )
