from .account import Account
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


class Demo2(Trader):

    def __init__(self, logfile: Logfile):
        super().__init__(logfile)

    def add_account(self, account: Account):
        """
            Algorithm requires to be the only trader on a specified account.
            The responsibility is on a user. See 'trade' method description.

            return: no
            raise: no
        """
        self.logger.debug(f"add_account(account='{account.name}')")
        self.account = account

    def trade(self, msg: dict):
        self.logger.debug(f"trade({msg['c']})")
