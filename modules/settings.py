import os
import json
from argparse import Namespace
from .exceptions import BNCCritical, BNCExceptions


class Logfile:
    """
        Contains properties for one particular logs file.
        Is used to separate logs.
    """

    def __init__(self, logfile_dict: dict):
        self.name = os.path.basename(logfile_dict["file"])
        self.path = os.path.join(os.path.abspath(logfile_dict["directory"]), logfile_dict["file"])
        self.max_size = logfile_dict["size"]
        self.backup_count = logfile_dict["back"]

    def change_name(self, name: str):
        self.name = name

    def change_file(self, file: str):
        self.path = os.path.join(os.path.dirname(self.path), file)


class Api:
    """
        Contains properties for one particular API.
    """

    def __init__(self, api_name: str, api_dict: dict, is_testnet: bool):
        self.name = api_name
        self.key_api = api_dict["key_api"]
        self.key_secret = api_dict["key_secret"]
        if not is_testnet:
            self.permissions = api_dict["permissions"]
        self.is_testnet = is_testnet


class Settings:
    """
        Handle and store all settings passed to the
        script via every .json file in given dir.
    """

    def __init__(self, settings_dir: str, args: Namespace):
        settings_dir = os.path.abspath(settings_dir)

        ''' properties '''
        self.account_log = None
        self.price_log = None
        self.trader_log = dict()
        self.recv_window = None
        self.traders = dict()
        self.load_properties(settings_dir)

        ''' credentials '''
        self.api_demo = None
        self.load_credentials(settings_dir, args.api, args.testnet)

    def load_properties(self, settings_dir):
        """
            Handle properties file

            return: no
            raise: BNCCritical (INCORRECT_ARGS)
        """

        properties_file = "properties.json"
        properties_path = os.path.join(settings_dir, properties_file)
        properties_fd = open(properties_path, "r")
        properties_dict = json.load(properties_fd)

        ''' logging '''
        logging_dict = properties_dict["logging"]
        self.account_log = Logfile(logging_dict["account"])
        self.price_log = Logfile(logging_dict["price"])
        for key, value in logging_dict["trader"].items():
            self.trader_log[key] = Logfile(value)

        ''' requests '''
        logging_dict = properties_dict["requests"]
        self.recv_window = logging_dict["recv_window"]
        if self.recv_window > 60000:
            raise BNCCritical(BNCExceptions.INCORRECT_ARGS)

        ''' traders '''
        traders = properties_dict["traders"]
        for key, value in traders.items():
            self.traders[key] = value

    def load_credentials(self, settings_dir, api_name, is_testnet):
        credentials_file = "credentials.json"
        credentials_path = os.path.join(settings_dir, credentials_file)
        credentials_fd = open(credentials_path, "r")
        credentials_dict = json.load(credentials_fd)
        self.api_demo = Api(api_name, credentials_dict["api"][api_name], is_testnet)

