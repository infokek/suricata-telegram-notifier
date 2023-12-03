function checkRoot {
  if [ "$EUID" -ne 0 ]
    then echo "[!] Please run as root or sudo"
    exit
  fi
}

systemctl stop suricata-telegram-notifier
systemctl disable suricata-telegram-notifier
rm /etc/systemd/system/suricata-telegram-notifier.service