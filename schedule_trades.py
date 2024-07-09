# Code to schedule the trader.py file to run during trading hours
import schedule
import time
import subprocess

START = "08:30"
END = "15:00"
file_name = "trader.py"

def trade():
    print("Trading has started")
    try:
        result = subprocess.run(["python", file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"Error generated while runnning {file_name}: {e}")

# Schedule to run during trading hours
schedule.every().day.at(START).do(trade)
schedule.every().day.at(END).do(trade)

while True:
    schedule.run_pending()
    time.sleep(5)