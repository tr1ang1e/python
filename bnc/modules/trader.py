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

    def __init__(self, logfile: Logfile, parameters: dict):
        super().__init__(logfile)
        self.symbol = 'BTCUSDT'
        self.orders_step = parameters['orders_step']
        self.orders_max = parameters['orders_max']
        self.min_order_usdt = parameters['min_order_usdt']

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
        raw = round((self.min_order_usdt / price), 6)
        shift = 10000
        actual = (int(raw * shift) + 1) / shift
        return raw, actual

    def log_order(self, raw_quantity: float, order: Order):
        self.logger.info(f"Order PLACED:")
        self.logger.info(f"    type: {order.type.name}")
        self.logger.info(f"    price: {order.price}")
        self.logger.info(f"    quantity: raw={raw_quantity}, actual={order.quantity}")
        self.logger.info(f"    ID: '{order.id}'")

    def trade(self, msg: dict):
        price_current = msg['c']
        self.logger.debug(f"trade({price_current})")
        if self.flag:
            return

        self.flag = True
        try:
            # price_order = float(price_current) - 1000.00
            # raw_quantity, act_quantity = self.get_quantity(price_order)
            # order = Order(self.symbol, act_quantity, str(price_order))
            # order = self.account.sell_limit(order)
            # self.log_order(raw_quantity, order)
            pass
        except Exception as ex:
            raise ex
