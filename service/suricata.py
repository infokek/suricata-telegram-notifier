import os
import subprocess
from service.config import ServiceConfig as config

class Suricata:
    def __init__(self) -> None:
        self.suricata_command = f"suricata -c {config.SERVICE_CONFDIR}/suricata.yaml -l {config.SERVICE_LOGDIR} -s {config.SURICATA_RULES}"
        self._logger = config.logger


    def start_suricata(self) -> str | None:
        """Start suricata as subprocess.Popen"""
        for interface in config.INTERFACES:
            self.suricata_command = self.suricata_command + f" -i {interface}"
        suricata_process = subprocess.Popen(self.suricata_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._logger.info("Suricata started")
        return suricata_process
    

    def terminate_suricata(self, suricata_process: subprocess.Popen) -> None:
        """Terminate suricata by subprocess.Popen"""
        suricata_process.terminate()
        self._logger.info("Suricata terminated")
    

    def kill_suricata(self) -> None:
        """Kill suricata instance with pkill unix command"""
        os.system(f"pkill -9 -f '{self.suricata_command}'")
        self._logger.warning("Suricata killed")