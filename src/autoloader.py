import os
import time

original_edit_time = os.path.getmtime("./run_config.json")

def check_for_config_update():
    global original_edit_time

    new_time = os.path.getmtime("./run_config.json")
    if new_time != original_edit_time:
        print("File modified")
        os.system("python3 dactyl_manuform.py")
        original_edit_time = new_time

while True:
    check_for_config_update()
    time.sleep(1)