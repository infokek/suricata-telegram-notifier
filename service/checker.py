import os
import re
import requests
import time
from service.config import ServiceConfig as config


class Checker():
    def __init__(self) -> None:
        self._logger = config.logger
        self._alert_regex = re.compile(r"(.*)\.[0-9]{6}  \[\*\*\] \[(.*)\] (.*) \[\*\*\] \[Classification\: (.*)\] \[Priority: (.*)\] {(.*)} ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):([0-9]{1,5}) -> ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):([0-9]{1,5})")
        self._sid_regex = re.compile(r"\[[0-9]:(.*):[0-9]\]")
        self._cached_stamp = 0


    def _send_message(self, message) -> str | None:
        """Send message to telegram bot"""
        response = requests.get(url=f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage?chat_id={config.CHAT_ID}&text={message}&parse_mode=HTML').json()
        return response


    def _watch_events(self) -> str | None:
        """Returns last event from fast.log"""
        try:
            stamp = os.stat(f"{config.SERVICE_LOGDIR}/fast.log").st_mtime
            if stamp != self._cached_stamp:
                self._cached_stamp = stamp
                self._logger.debug(f"File {config.SERVICE_LOGDIR}/fast.log modified")
                with open(f"{config.SERVICE_LOGDIR}/fast.log", 'r') as f:
                    try:
                        last_line = f.readlines()[-1]
                        return last_line
                    except IndexError:
                        self._logger.warning("No lines in fast.log")
        except FileNotFoundError:
            self._logger.warning("fast.log not found")
            time.sleep(3)


    def _format_message(self, event) -> str | None:
        """Formats message for telegram"""
        parsed = self._alert_regex.findall(event)[0]
        #('12/02/2023-13:19:51', '1:2013028:7', 'ET POLICY curl User-Agent Outbound',
        # 'Attempted Information Leak', '2', 'TCP', '10.8.0.3', '54052', '195.201.201.35', '80')
        formatted_message = f'⚠️ {parsed[0]}\n<b>Alert:</b> {parsed[2]}\n<b>Sid:</b> {parsed[1]}\n<b>Type:</b> {parsed[3]} {parsed[4]}\n<b>Proto:</b> {parsed[5]}\n<b>Source:</b> <a href="https://www.virustotal.com/gui/ip-address/{parsed[6]}/detection">{parsed[6]}</a>:{parsed[7]}\n<b>Destination:</b> <a href="https://www.virustotal.com/gui/ip-address/{parsed[8]}/detection">{parsed[8]}</a>:{parsed[9]}'
        return formatted_message


    def start_checker(self) -> None:
        """Start checking eve.json for alerts and send messages to telegram bot on alert"""
        self._logger.info("Starting checker")
        while True:
            if last_event := self._watch_events():
                self._logger.debug(f'Got event: {last_event[:46]}')
                alert_sid = self._sid_regex.findall(last_event)[0]
                if alert_sid not in config.BLACKLIST_SIDS:
                    response = self._send_message(message=self._format_message(event=last_event))
                    if response["ok"] == "false":
                        self._logger.error(f'Got response: {response["error_code"]}, {response["description"]}')                        
                else:
                    self._logger.info(f'Got sid from blacklist: {alert_sid}')