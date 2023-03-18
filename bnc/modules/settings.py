import os
import json


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


class Api:
    """
        Contains properties for one particular API.
    """

    def __init__(self, api_name: str, api_dict: dict):
        self.name = api_name
        self.key_api = api_dict["key_api"]
        self.key_secret = api_dict["key_secret"]
        self.permissions = api_dict["permissions"]


class Settings:
    """
        Handle and store all settings passed to the
        script via every .json file in given dir.
    """

    def __init__(self, settings_dir: str):
        settings_dir = os.path.abspath(settings_dir)
        ''' properties '''
        self.account_log = None
        self.price_log = None
        self.load_properties(settings_dir)
        ''' credentials '''
        self.api_demo = None
        self.load_credentials(settings_dir)

    def load_properties(self, settings_dir):
        properties_file = "properties.json"
        properties_path = os.path.join(settings_dir, properties_file)
        properties_fd = open(properties_path, "r")
        properties_dict = json.load(properties_fd)
        ''' logging '''
        logging_dict = properties_dict["logging"]
        self.account_log = Logfile(logging_dict["account"])
        self.price_log = Logfile(logging_dict["price"])

    def load_credentials(self, settings_dir):
        credentials_file = "credentials.json"
        credentials_path = os.path.join(settings_dir, credentials_file)
        credentials_fd = open(credentials_path, "r")
        credentials_dict = json.load(credentials_fd)
        self.api_demo = Api("demo", credentials_dict["api"]["demo"])

