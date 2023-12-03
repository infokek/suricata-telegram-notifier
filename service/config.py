import os
import sys
from pathlib import Path
import configparser
import logging
import json

class ServiceConfig():
    PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    SERVICE_LOGDIR = f"{PROJECT_DIR.parent}/logs"
    SERVICE_CONFDIR = f"{PROJECT_DIR.parent}/configs"


    file_handler = logging.FileHandler(filename=f"{SERVICE_LOGDIR}/service.log", mode="a")
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(level=logging.DEBUG,
                             format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S',
                                handlers=handlers)
    logger = logging.getLogger('service')


    config = configparser.ConfigParser()
    config.read(f"{SERVICE_CONFDIR}/service.ini")


    BOT_TOKEN = config["Telegram"]["BOT_TOKEN"]
    CHAT_ID = config["Telegram"]["CHAT_ID"]


    SURICATA_RULES = f"{PROJECT_DIR.parent}/rules/emerging-all.rules"
    INTERFACES = json.loads(config["Suricata"]["INTERFACES"])
    BLACKLIST_SIDS = config["Suricata"]["BLACKLIST_SIDS"]