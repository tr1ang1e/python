from .exceptions import bnc_lib_exc_str, BNCAttention, BNCExceptions, BNCCritical
from .settings import Api, Logfile
from .utilities import init_logger
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException, BinanceOrderException, \
    BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, \
    BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException


class Symbol:
    """
        Contains information about symbol
    """

    def __init__(self, info: dict):
        self.symbol = info['symbol']
        self.base_asset = info['baseAsset']
        self.quote_asset = info['quoteAsset']
        self.order_types = info['orderTypes']
        self.min_notional = None    # minimal order size in quote asset
        self.max_limit_orders = None
        self.max_stop_orders = None

        for f in info['filters']:
            for key, value in f.items():
                if key == 'filterType':
                    if value == 'MIN_NOTIONAL':
                        self.min_notional = float(f['minNotional'])
                    if value == 'MAX_NUM_ORDERS':
                        self.max_num_orders = int(f['maxNumOrders'])
                    if value == 'MAX_NUM_ALGO_ORDERS':
                        self.max_algo_orders = int(f['maxNumAlgoOrders'])


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

    def __init__(self, symbol: str, side: str = None, order_type: str = None,
                 price: str = "0.0", quantity: float = 0.0,
                 stop_price: str = None, unique_id: str = None):
        """
            Every order action requires symbol to be specified.
            Other parameters depend on particular API function.
        """

        self.status = Order.INITED
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.price = price
        self.quantity = quantity
        self.stop_price = stop_price
        self.unique_id = unique_id      # always corresponds to API "clientOrderId" field

    def opened(self, response: dict):
        self.status = Order.OPENED
        self.unique_id = response["clientOrderId"]
        exec_quantity = float(response["executedQty"])
        if exec_quantity and (exec_quantity < self.quantity):
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
        self.balances = dict()  # current balance state
        self.placed_orders = list()  # placed but not executed orders
        self.logger.info(f"Account instance is created")

    def get_client(self, api: Api):
        """
            Initialize account data and prepare environment.

            return: no
            raise: see invoked calls (check_permissions, update_account_data)
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
        self.logger.debug(f"check_permissions(expected_permissions={expected_permissions}")
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
            TODO: make connecting to account process safe
                - update balance
                - synchronize opened orders
        """
        pass

    def get_balance(self, assets=("btc", "usdt"), base_asset="usdt"):
        """
            Get account balance according to the passed assets list.
            Total balance is given in base_asset.

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

    def get_symbol_info(self, symbol: str):
        """
            Get information about specified symbol.
            Not all information is printed. See 'class Symbol'.

            return: class Symbol
            raise: BNCAttention (SYMBOL_INFO)
        """
        self.logger.debug(f"get_symbol_info(symbol='{symbol}')")

        try:
            symbol = Symbol(self.client.get_symbol_info(symbol=symbol))
            return symbol
        except (BinanceAPIException, BinanceRequestException) as ex:
            error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
            raise BNCAttention(
                BNCExceptions.SYMBOL_INFO,
                f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
            )

    def get_placed_orders(self, symbol: str):
        """
            Get all orders were placed on
            market but still weren't executed.

            return: list of Order instances
            raise: BNCAttention (GET_ORDERS)
        """
        self.logger.debug(f"get_placed_orders(symbol='{symbol}')")
        try:
            placed_orders = self.client.get_open_orders(symbol=symbol, recvWindow=self.recv_window)
            self.placed_orders = list()
            for o in placed_orders:
                order = Order(
                    symbol=o["symbol"],
                    side=o["side"],
                    order_type=o["type"],
                    price=o["price"],
                    quantity=o["origQty"],
                    stop_price=o["stopPrice"],
                    unique_id=o["clientOrderId"]
                )
                self.placed_orders.append(order)
            return self.placed_orders
        except (BinanceAPIException, BinanceRequestException) as ex:
            error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
            raise BNCAttention(
                BNCExceptions.GET_ORDERS,
                f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
            )

    def buy_limit(self, order: Order, attempts: int = 3):
        """
            If order PRICE is GREATER than market price, the order
            will be executed by current market price.

            Must be filled:
                - Order.symbol
                - Order.price
                - Order.quantity

            return: class Order (all fields are filled)
            raise: see invoked calls (place order)
        """
        try:
            order.side = Client.SIDE_BUY
            order.order_type = Client.ORDER_TYPE_LIMIT
            order = self.place_order(order, attempts)
            return order
        except Exception as ex:
            raise ex

    def sell_limit(self, order: Order, attempts: int = 3):
        """
            If order PRICE is LESS than market price, the order
            will be executed by current market price.

            Must be filled:
                - Order.symbol
                - Order.price
                - Order.quantity

            return: class Order (all fields are filled)
            raise: see invoked calls (place order)
        """
        try:
            order.side = Client.SIDE_SELL
            order.order_type = Client.ORDER_TYPE_LIMIT
            order = self.place_order(order, attempts)
            return order
        except Exception as ex:
            raise ex

    def place_order(self, order: Order, attempts: int = 3):
        """
            Generic function for placing orders.

            Mandatory fields if Order.order_type is:
                Client.ORDER_TYPE_LIMIT                     symbol, price, side, type, quantity
                Client.ORDER_TYPE_STOP_LOSS_LIMIT           .ORDER_TYPE_LIMIT + stopPrice
            Auto added inside this function                 timeInForce, newOrderRespType


                                STOP_LOSS       TAKE_PROFIT
            price above               BUY              SELL
            price below              SELL               BUY


            return: class Order
            raise: BNCAttention, BNCCritical (PLACE_ORDER)
        """
        self.logger.debug("place_order(symbol={}, side/type={}/{} price={}, quantity={}, attempts={})".format(
            order.symbol,
            order.side, order.order_type,
            order.price,
            order.quantity,
            attempts
        ))

        stop_price_required = [Client.ORDER_TYPE_STOP_LOSS_LIMIT]

        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")

                ''' prepare arguments '''

                # always required
                args = {
                    "symbol": order.symbol,
                    "side": order.side,
                    "type": order.order_type,
                    "price": order.price,
                    "quantity": order.quantity,
                    "timeInForce": Client.TIME_IN_FORCE_GTC,    # always required
                    "newOrderRespType": "RESULT"                # most convenient
                }

                # not always required
                if order.order_type in stop_price_required:
                    args['stopPrice'] = order.stop_price

                ''' place order '''

                response = self.client.create_order(**args)
                order = order.opened(response)

                ''' log result '''

                self.logger.info(f"Order PLACED:")
                self.logger.info(f"    ID: '{order.unique_id}'")
                self.logger.info(f"    symbol: {order.symbol}, side/type: {order.order_type}/{order.side}")
                self.logger.info(f"    price: {order.price}")
                if order.order_type in stop_price_required:
                    self.logger.info(f"    stop price: {order.stop_price}")
                self.logger.info(f"    quantity: {order.quantity}")

                return order
            except (BinanceRequestException,
                    BinanceAPIException,
                    BinanceOrderException,
                    BinanceOrderInactiveSymbolException) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCCritical(
                    BNCExceptions.PLACE_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
                )
            except (BinanceOrderMinAmountException,
                    BinanceOrderMinPriceException,
                    BinanceOrderMinTotalException,
                    BinanceOrderUnknownSymbolException) as ex:
                raise BNCAttention(
                    BNCExceptions.PLACE_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message}"
                )

    def cancel_order(self, order: Order, attempts: int = 3):
        """
            Cansel order which was placed on
            market but still wasn't executed.

            return: class Order
            raise: BNCAttention (CANSEL_ORDER)
        """
        symbol = order.symbol
        unique_id = order.unique_id
        self.logger.debug(f"cancel_order(symbol='{symbol}', unique_id={unique_id})")
        for attempt in range(attempts):
            try:
                self.logger.debug(f"    attempt {attempt + 1} of {attempts}")
                self.client.cancel_order(symbol=symbol, origClientOrderId=unique_id)
                self.logger.info(f"Order CANCELLED, ID: '{order.unique_id}'")
                break
            except (BinanceAPIException, BinanceRequestException) as ex:
                if (attempt + 1) < attempts:
                    continue
                error = f"\n\terror: {ex.code}" if hasattr(ex, "error") else ""
                raise BNCAttention(
                    BNCExceptions.CANSEL_ORDER,
                    f"{bnc_lib_exc_str} \n\ttype: {type(ex)} \n\tmessage: {ex.message} {error}"
                )

    def cansel_all_orders(self, symbols: list):
        self.logger.debug(f"cansel_all_orders(symbols={symbols})")
        for symbol in symbols:
            orders = self.get_placed_orders(symbol)
            for o in orders:
                order = Order(symbol=symbol, unique_id=o.unique_id)
                self.cancel_order(order)
