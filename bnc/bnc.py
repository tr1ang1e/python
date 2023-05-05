"""
TODO, long:

    1. simple trading logic
    2. convenient parameters setting:
        - money management
    3. telegram notifications
    4. better multithread logic: split websocket callback and trading logic
        - "CANCEL read_loop" error: https://github.com/sammchardy/python-binance/issues/1169
    5. test on historical data
        - api: get historical data
        - class Tester
    6. reimplement in C

TODO, current (1. simple trading logic):

    - bnc.py:handle_price_msg - exceptions handling
    - decide which information should be permanently shown if any
    - trader.py:Eleven - assumption that only one order might be executed
                         during one iteration. Implement orders accounting

"""
import traceback
from time import sleep

from modules import Account
from modules import BNCAttention, BNCCritical
from modules import Price
from modules import Settings
from modules import Eleven
from modules import parse_arguments


"""
    There is no way to change callback signature, and therefore 
    the global storage of 'class Trader' instances should be used
"""
traders = list()


def handle_price_msg(msg):
    """
        Callback function: just iterates over
        all registered accounts and calls trade
    """
    global traders
    try:
        for tr in traders:
            tr.trade(msg)
    except Exception as e:
        # TODO: all important exceptions are here
        print("EXCEPTION in HANDLE_PRICE_MSG()")
        print(e)
        print(traceback.format_exc())


if __name__ == "__main__":
    btc = None
    account = None
    price = None
    args = parse_arguments()

    try:
        settings = Settings("./settings", args)

        """
            All 'Account' and 'Trader' instances must be created 
            before Price one, because callback, used by Price class, 
            involves 'Trader' class to proceed business logic
        """

        # Account
        account = Account(settings.api_demo, settings.recv_window, settings.account_log)
        account.get_balance()
        account.get_symbol_info("BTCUSDT")

        # Trader
        name = 'eleven'
        trader = Eleven(settings.trader_log[name], settings.traders[name])
        trader.add_account(account)
        traders.append(trader)

        """
            Price class is responsible for 
                - getting data using WebSocket connection
                - calling callback function for new data
                
            Executed in parallel thread
        """

        # debug
        flag = 1
        if flag:
            price = Price(settings.price_log)
            price.start_ticker("BTCUSDT", handle_price_msg)
            sleep(12)
            price.stop()

        # debug
        if not flag:
            print("CANCEL ORDERS")
            account.cansel_all_orders(['BTCUSDT'])

        # debug
        flag = 1
        if flag:
            print("PLACED ORDERS")
            for o in account.get_placed_orders('BTCUSDT'):
                print(f"{o.unique_id} = {o.symbol}, {o.side}/{o.order_type}, {o.price}, {o.quantity}")

        """
            This thread is used to initialization and to
            starting the work. So no exceptions require
            handling due to business logic thread
            is started by the last instruction above.
        """

    except IOError as ex:
        print("Failed to get settings")
        ex_string = traceback.format_exc()
        print(ex_string)
    except (BNCAttention, BNCCritical) as ex:
        ex_string = traceback.format_exc()
        print(ex_string)
    except Exception as ex:
        print("Unknown EXCEPTION type raised")
        ex_string = traceback.format_exc()
        print(ex_string)
        # if price is not None:
        #    price.stop()
