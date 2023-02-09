
import sched
import time
import subprocess

def run_app():
    # Code for the function you want to schedule
    subprocess.call(["python3", "getmikrotik.py"])
    print("Running the job...")

s = sched.scheduler(time.time, time.sleep)

while True:
    s.enter(21600, 1, run_app)
    s.run()
