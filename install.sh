function checkRoot {
  if [ "$EUID" -ne 0 ]
    then echo "[!] Please run as root or sudo"
    exit
  fi
}

SERVICE_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

function addService {
  echo "[Unit]
  Description=Suricata Telegram Notifier Service
  After=network.target

  [Service]
  Type=simple
  Restart=always
  RestartSec=3
  User=root
  ExecStart=$SERVICE_DIRECTORY/.venv/bin/python3 -m service
  WorkingDirectory=$SERVICE_DIRECTORY

  [Install]
  WantedBy=multi-user.target" > /etc/systemd/system/suricata-telegram-notifier.service
  systemctl daemon-reload
}

checkRoot
apt update
apt install python3-pip suricata python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
wget https://rules.emergingthreats.net/open/suricata-5.0/emerging-all.rules -O $SERVICE_DIRECTORY/rules/emerging-all.rules
addService
systemctl start suricata-telegram-notifier
systemctl status suricata-telegram-notifier