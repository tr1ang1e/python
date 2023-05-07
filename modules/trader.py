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

        ORDERS_MAX =
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
        self.orders_step = float(parameters['orders_step'])
        self.min_price_offset = parameters['min_price_offset']
        self.orders_max = parameters['orders_max']
        self.order_usdt = parameters['order_usdt']

        # store buy-limit order which:
        #   closest to current price
        #   placed during the last iteration
        #   without tp is placed
        # TODO: assumption that only one buy-limit order
        #       might be executed between two prices are got
        self.placed_last = Order(symbol="BTCUSDT", price="0.0", side="BUY", order_type="LIMIT")

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
        return float(enter_price), float(tp_price)

    def log_order(self, raw_quantity: float, order: Order):
        self.logger.info(f"Order PLACED:")
        self.logger.info(f"    ID: '{order.unique_id}'")
        self.logger.info(f"    symbol: {order.symbol}, side/type: {order.order_type}/{order.side}")
        self.logger.info(f"    price: {order.price}")
        self.logger.info(f"    quantity: raw={raw_quantity}, actual={order.quantity}")

    def trade(self, msg: dict):
        place_new = list()          # potential prices for new buy-limit orders
        tp_new = list()             # potential prices for new sell-limit orders

        # get all potential orders prices
        current_price = float(msg['c'])
        closest_place, closest_tp = self.get_orders_prices(current_price)
        for i in range(self.orders_max):
            place_new.append(closest_place - self.orders_step * i)
            tp_new.append(closest_tp - self.orders_step * i)

        # to handle from price closest to current
        place_new.sort(reverse=True)
        tp_new.sort(reverse=True)

        try:

            # debug
            print(current_price)
            self.logger.debug(current_price)

            orders = self.account.get_placed_orders(self.symbol)
            place_act = [float(o.price) for o in orders if o.side == "BUY"].sort(reverse=True)
            tp_act = [float(o.price) for o in orders if o.side == "SELL"].sort()

            # debug
            self.logger.debug(f"PLACED LAST: {float(self.placed_last.price)}")
            self.logger.debug(f"PLACED ORDERS:")
            self.logger.debug(f"    LIMIT/SELL ... {tp_act}")
            self.logger.debug(f"    LIMIT/BUY .... {place_act}")

            # inspect if tp for self.placed_last is placed
            is_last_tp_placed = (float(self.placed_last.price) + self.orders_step) in tp_act

            for i in range(self.orders_max):

                ''' TAKE PROFIT '''

                if tp_new[i] in tp_act:
                    # state: TP PLACED - CURRENT PRICE - BUY EXECUTED
                    # buy order executed, tp placed: nothing to do
                    continue

                if (place_new[i] < float(self.placed_last.price)) \
                        and not (float(self.placed_last.price) in place_act) \
                        and not is_last_tp_placed:
                    # state: TP NOT PLACED - BUY EXECUTED - CURRENT PRICE
                    # last buy order is executed, place tp
                    order_price = float(self.placed_last.price) + self.orders_step
                    raw_quantity, act_quantity = self.get_quantity(order_price)
                    order = Order(
                        symbol=self.symbol,
                        price=str(order_price),
                        quantity=act_quantity
                    )
                    order = self.account.sell_limit(order)
                    self.log_order(raw_quantity, order)
                    is_last_tp_placed = True

                ''' BUY LIMIT '''

                if place_new[i] not in place_act:
                    # state: CURRENT PRICE - BUY NOT PLACED
                    # buy order not placed, place buy order
                    order_price = place_new[i]
                    raw_quantity, act_quantity = self.get_quantity(order_price)
                    order = Order(
                        symbol=self.symbol,
                        price=str(order_price),
                        quantity=act_quantity
                    )
                    order = self.account.buy_limit(order)
                    self.log_order(raw_quantity, order)

            # update closest price
            self.placed_last.price = str(closest_place)

            # debug
            # print(f"closest_price: {self.placed_last.price}")

        except Exception as ex:
            raise ex
