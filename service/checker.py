import os
import re
import requests
import time
import datetime
import json
from service.config import ServiceConfig as config
from service.models import Alert


class Checker():
    def __init__(self) -> None:
        self._logger = config.logger
        self._alert_regex = re.compile(r"(.*)\.[0-9]{6}  \[\*\*\] \[(.*)\] (.*) \[\*\*\] \[Classification\: (.*)\] \[Priority: (.*)\] {(.*)} ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):([0-9]{1,5}) -> ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):([0-9]{1,5})")
        self._sid_regex = re.compile(r"\[[0-9]:(.*):[0-9]{1,2}\]")
        self._cached_stamp: int = 0
        self._spamming_alerts: list[Alert] = []
        self._last_alert: Alert = None


    def _send_message(self, message: str) -> str | None:
        """Send message to Telegram Bot API"""
        response = requests.get(url=f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage?chat_id={config.CHAT_ID}&text={message}&parse_mode=HTML').json()
        response = json.dumps(response)
        response = json.loads(response)
        self._logger.debug(f'Got response: {response}')
        if response["ok"] == "false":
            self._logger.error(f'Got response: {response["error_code"]}, {response["description"]}')
            return None        
        else:
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

    def _parse_event(self, event: str) -> Alert | None:
        """Parse event from fast.log format and create Alert dataclass object"""
        event = self._alert_regex.findall(event)[0]
        #  ('12/02/2023-13:19:51', '1:2013028:7', 'ET POLICY curl User-Agent Outbound',
        # 'Attempted Information Leak', '2', 'TCP', '10.8.0.3', '54052', '195.201.201.35', '80')
        return Alert(
            timestamp=event[0], sid_and_rev=event[1], message=event[2],
            classification=event[3], priority=event[4], protocol=event[5],
            src_ip=event[6], src_port=event[7],
            dst_ip=event[8], dst_port=event[9],
            count=1
        )


    def _format_message(self, alert: Alert) -> str | None:
        """Formats message for telegram"""
        formatted_message = f'⚠️ {alert.timestamp}\n'\
            f'<b>Alert:</b> {alert.message}\n' \
            f'<b>Sid:</b> {alert.sid_and_rev}\n' \
            f'<b>Type:</b> {alert.classification} {alert.priority}\n' \
            f'<b>Proto:</b> {alert.protocol}\n' \
            f'<b>Source:</b> <a href="https://www.virustotal.com/gui/ip-address/{alert.src_ip}/detection">{alert.src_ip}</a>:{alert.src_port}\n' \
            f'<b>Destination:</b> <a href="https://www.virustotal.com/gui/ip-address/{alert.dst_ip}/detection">{alert.dst_ip}</a>:{alert.dst_port}'
        return formatted_message
    

    def _check_lastaalert_similarity(self, alert: Alert) -> bool | None:
        if alert.sid_and_rev == self._last_alert.sid_and_rev \
            and alert.dst_ip == self._last_alert.dst_ip \
                and alert.dst_port == self._last_alert.dst_port:
                    return True
        else:
            return False
    

    def _format_and_send_message(self, alert: Alert) -> None:
        """Format and send message to Telegram Bot API"""
        if self._send_message(message=self._format_message(alert=alert)):
            self._last_alert = alert
            self._logger.debug(f'Last alert {self._last_alert.sid_and_rev}')
        else:
            self._logger.error(f'Telegram error occurred, sleeping...')
            time.sleep(10)        


    def start_checker(self) -> None:
        """Start checking eve.json for alerts and send messages to telegram bot on alert"""
        self._logger.info("Starting checker")
        while True:
            if last_event := self._watch_events():
                self._logger.debug(f'Got event: {last_event[:46]}')
                alert_sid = self._sid_regex.findall(last_event)[0]
                # check sids blacklist
                if alert_sid not in config.BLACKLIST_SIDS:
                    alert = self._parse_event(event=last_event)
                    # check alert in spam list
                    self._logger.debug(f'There are {len(self._spamming_alerts)} spamming alerts')
                    for spamming_alert in self._spamming_alerts:
                        if self._check_lastaalert_similarity(alert=spamming_alert):
                            alert_time = datetime.datetime.strptime(alert.timestamp, '%d/%m/%Y-%H:%M:%S')
                            now = datetime.datetime.now()
                            self._logger.debug(f'Разница: {now - alert_time}')
                            if now - alert_time > datetime.datetime.hour():
                                self._logger.info(f'Anti-Spam: {alert_sid} not repeated last hour. Sending to telegram...')
                                self._spamming_alerts.remove(alert)
                                self._format_and_send_message(alert=alert)
                            else:
                                self._logger.info(f'Anti-Spam: {alert_sid} repeated {alert.count} times for last hour')
                                alert.count += 1
                    else:
                        if self._last_alert:
                            if self._check_lastaalert_similarity(alert=alert):
                                self._logger.info(f'Anti-Spam: {alert_sid} repeated firstly, adding to spamming alerts')
                                alert.count += 1
                                self._spamming_alerts.append(alert)
                        self._format_and_send_message(alert=alert)
                else:
                    self._logger.info(f'Got sid from blacklist: {alert_sid}')