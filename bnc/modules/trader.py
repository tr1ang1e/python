from binance.client import Client
from .account import Account, Order
from .settings import Logfile
from .utilities import init_logger


class Trader:
    """
        Base class for trading algorithms
    """

    def __init__(self, logfile: Logfile):
        self.logger = init_logger(logfile)
        self.account = None

    def add_account(self, account: Account):
        """
            A rule how to link Trader and Account instances
            See subclass implementation
        """
        raise NotImplementedError

    def trade(self, msg: dict):
        """
            Trading algorithm
            See subclass implementation
        """
        raise NotImplementedError


class Eleven(Trader):
    """
        --------------------------------------------------------------------
        ---------------------------- Parameters ----------------------------

        ORDERS_STEP =
            distance between two co-directional orders
            valid: [ x ]
                possible values are theoretically any. Current algorithm
                implementation assumes that parameter also specifies
                distance between placed order and corresponding Take Profit,
                so be aware of commission (is taken for both order and TP).

        MIN_PRICE_OFFSET =
            minimal (current_price - order_price) distance
            valid: [0...inf]
                no direct platform restrictions. The reason is to achieve
                precise execution in cases when current_price is too close
                to order_prise and net connection might affect.

        ORDERS_MAX
            number of orders PAIRS are placed in market simultaneously.
            valid: [1...5]
                currently stop-limit orders are used to provide Take Profit
                functionality, so max pairs number is limited by either
                limit orders or stop-limit orders allowed number. Platform
                allows 200 limit and 5 stop-limit orders, therefore parameter
                value is in the range from 1 to 5.

        ORDER_USDT =
            order size in USDT to be placed
            valid: [10...inf]
                currently minimal quantity is allowed by platform
                is 10 USDT, therefore parameter value can't be less.
    """

    def __init__(self, logfile: Logfile, parameters: dict):
        super().__init__(logfile)
        self.symbol = 'BTCUSDT'
        self.orders_step = parameters['orders_step']
        self.min_price_offset = parameters['min_price_offset']
        self.orders_max = parameters['orders_max']
        self.order_usdt = parameters['order_usdt']

        # debug
        self.flag = False

    def add_account(self, account: Account):
        """
            Algorithm requires to be the only trader on a specified account.
            The responsibility is on a user. See 'trade' method description.

            return: no
            raise: no
        """
        self.logger.debug(f"add_account(account='{account.name}')")
        self.account = account

    def get_quantity(self, price):
        raw = round((self.order_usdt / price), 6)
        shift = 10000
        actual = (int(raw * shift) + 1) / shift
        return raw, actual

    def get_orders_prices(self, current_price):
        enter_price = (current_price // self.orders_step) * self.orders_step
        if enter_price >= (current_price + self.min_price_offset):
            enter_price -= self.orders_step
        tp_price = enter_price + self.orders_step
        return enter_price, tp_price

    def log_order(self, raw_quantity: float, order: Order):
        self.logger.info(f"Order PLACED:")
        self.logger.info(f"    ID: '{order.unique_id}'")
        self.logger.info(f"    symbol: {order.symbol}, side/type: {order.order_type}/{order.side}")
        self.logger.info(f"    quantity: raw={raw_quantity}, actual={order.quantity}")

    def trade(self, msg: dict):
        price_current = msg['c']
        self.logger.debug(f"trade({price_current})")
        if self.flag:
            return

        self.flag = True
        try:
            price_order = float(price_current) + 1000.00
            raw_quantity, act_quantity = self.get_quantity(price_order)

            order = Order(
                symbol=self.symbol,
                quantity=act_quantity,
                price=str(price_order),
                side=Client.SIDE_SELL,
                order_type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
            )

            order = self.account.place_order(order)
            self.log_order(raw_quantity, order)
        except Exception as ex:
            raise ex
