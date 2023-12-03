from service.suricata import Suricata
from service.checker import Checker

def main() -> None:
    suricata = Suricata()
    checker = Checker()
    try:
        # kill old suricata instance (if exists) to prevent fork bomb
        suricata.kill_suricata()
        suricata_process = suricata.start_suricata()
        checker.start_checker()        
    except KeyboardInterrupt:
        suricata.terminate_suricata(suricata_process=suricata_process)
        suricata.kill_suricata()
        exit()

if __name__ == "__main__":
    main()