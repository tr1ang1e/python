from .utilities import init_logger
from binance import ThreadedWebsocketManager as WebSock


class Price:
    """
        Access to actual market prices
        Access is processed via: https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-ticker-streams
            API = Individual Symbol Ticker Streams
            description = 24-hour rolling window
            update = 1000 ms
            ticker = <symbol>@ticker
    """

    tickers = list()

    def __init__(self):
        self.socket = WebSock()
        self.socket.start()

    def start_ticker(self, symbol: str, callback):
        """
            Must be called at least once for binance library
            ThreadedWebsocketManager proper work.
        """
        ticker = symbol.lower() + "@ticker"
        if not (ticker in self.tickers):
            # callback will be invoked every time WebSocket proceed packet exchange
            new_ticker = self.socket.start_symbol_ticker_socket(callback=callback, symbol=symbol.upper())
            self.tickers.append(new_ticker)

    # safe even if __init__ wasn't successful
    def stop(self):
        self.socket.stop()

    def __del__(self):
        self.stop()
