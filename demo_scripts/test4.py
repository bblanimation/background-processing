# this script will time out
import time
for i in range(200):
    time.sleep(0.1)
    progress = i / 200
    update_job_progress(progress)
