import datetime

timestamp = "12/02/2023-13:19:51"

#alert_time = int(datetime.datetime.strptime(timestamp, '%d/%m/%Y-%H:%M:%S'))
now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
print( now)