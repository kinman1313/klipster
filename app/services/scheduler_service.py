import schedule
import time
import threading

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def schedule_upload(task, interval, unit):
    if unit == 'hours':
        schedule.every(interval).hours.do(task)
    elif unit == 'minutes': # for testing
        schedule.every(interval).minutes.do(task)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()
