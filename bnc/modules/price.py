from .utilities import init_logger
from .exceptions import BNCExceptions, BNCAttention
from .settings import Logfile
from binance import ThreadedWebsocketManager as WebSock


class Price:
    """
        Access to actual market prices:
            - subscribe to stream and ...
            - ... invoke given callback for every data update
        Current implementation uses:
            https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-mini-ticker-stream
            API             = Individual Symbol Ticker Streams
            description     = 24-hour rolling window
            update          = 1000 ms
            ticker          = <symbol>@miniTicker
    """

    suffix = "@miniTicker"
    tickers = list()

    def __init__(self, logfile: Logfile):
        self.socket = WebSock()
        self.socket.start()
        self.logger = init_logger(logfile)
        self.logger.info("Price instance is created")

    def create_ticker(self, symbol: str):
        self.logger.debug(f"create_ticker(symbol='{symbol}')")
        ticker = symbol.lower() + self.suffix
        self.logger.info(f"Result ticker: '{ticker}'")
        return ticker

    def start_ticker(self, symbol: str, callback):
        """
            Must be called at least once for binance library
            ThreadedWebsocketManager proper work.

            return: result ticker name
            raise: BNCAttention
        """
        self.logger.debug(f"start_ticker(symbol='{symbol}', callback='{callback.__name__}')")
        ticker_expected = self.create_ticker(symbol)
        if not (ticker_expected in self.tickers):
            # callback will be invoked every time WebSocket proceed packet exchange
            ticker_actual = self.socket.start_symbol_miniticker_socket(callback=callback, symbol=symbol.upper())
            if ticker_expected != ticker_expected:
                raise BNCAttention(
                    BNCExceptions.TICKER_START,
                    "Ticker name creation rule doesn't correspond to WebSocket Market Stream API\n\
                    See 'https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams'"
                )
            self.tickers.append(ticker_actual)
        self.logger.info(f"Ticker '{ticker_expected}' is started")
        return ticker_expected

    def stop_ticker(self, symbol: str):
        """
            Stop ticker. Protected from passing symbols
            which ticker was not started yet for.

            return: no
            raise: no
        """
        self.logger.debug(f"stop_ticker(symbol='{symbol}')")
        ticker = self.create_ticker(symbol)
        if ticker in self.tickers:
            self.socket.stop_socket(ticker)
        self.logger.info(f"Ticker '{ticker}' is stopped")

    def replace_callback(self, symbol: str, callback):
        """
            Stop and start ticker again with another callback.
            If ticker wasn't started yet, it will be done here.

            return: result ticker name
            raise: no
        """
        self.logger.debug(f"replace_callback(symbol='{symbol}', callback='{callback.__name__}')")
        ticker = self.create_ticker(symbol)
        ticker_exists = False
        if ticker in self.tickers:
            ticker_exists = True
            self.socket.stop_socket(ticker)
        if not ticker_exists:
            self.logger.info(f"Ticker doesn't exist. Starting.")
        ticker = self.start_ticker(symbol, callback)
        if ticker_exists:
            self.logger.info(f"New callback is set")
        return ticker

    def stop(self):
        """
            Safe even if __init__ wasn't successful.

            return: no
            raise: no
        """
        self.logger.debug(f"stop()")
        self.socket.stop()

    def __del__(self):
        self.stop()
