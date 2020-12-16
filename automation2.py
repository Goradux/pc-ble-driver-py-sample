# 1. resize window
# 2. position it top left
# 3. get its coordinates
# 4. Do the shenanigans
#

# https://pypi.org/project/PyGetWindow/
import pygetwindow
# https://pypi.org/project/PyAutoGUI/
import pyautogui
import time
import os
import sys

REGION = (0, 0, 1000, 1000)
FULL_PATH = None
FOLDER = None
FILE = None

def check_args(path):
    if os.path.exists(path):
        global FULL_PATH, FOLDER, FILE
        FULL_PATH = os.path.abspath(path)
        FOLDER = os.path.dirname(FULL_PATH)
        FILE = os.path.basename(FULL_PATH)
    else:
        raise ValueError('Bad .zip path.')


def prepare_window():
    window = pygetwindow.getWindowsWithTitle('nRF Connect v3.6.1 - Bluetooth Low Energy')[0]
    window.resizeTo(1000, 800)
    window.moveTo(0, 0)
    window.activate()

def choose_adapter():
    SELECT_DEVICE = (150, 50)
    pyautogui.moveTo(SELECT_DEVICE)
    pyautogui.click()
    SELECT_ADAPTER = (150, 120)
    pyautogui.moveTo(SELECT_ADAPTER)
    pyautogui.click()

def filter_device(mac: str):
    def open_options():
        OPTIONS = (775, 170)
        pyautogui.moveTo(OPTIONS)
        pyautogui.click()

    try:
        position = pyautogui.locateOnScreen('images/scan_options_extended.png', region=REGION)
        if position == None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError) as e:
        print(e)
        print('exception raised')
        open_options()

    FILTER = (850, 220)
    pyautogui.moveTo(FILTER)
    pyautogui.click()
    pyautogui.hotkey('ctrl', 'a')
    # pyautogui.press('backspace')
    pyautogui.write(mac, interval=0.01)

def discover_devices():
    START_SCAN = (800, 140)
    pyautogui.moveTo(START_SCAN)
    pyautogui.click()
    time.sleep(5)
    pyautogui.click()

def connect_AQM():
    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()

    try:
        position = pyautogui.locateOnScreen('images/error_device_disconnected.png', region=REGION)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError) as e:
        print(e)
        print('exception raised')
        ERROR_CLOSE = (750, 220)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        connect_AQM()
        return

def disconnect_AQM():
    COG = (575, 230)
    pyautogui.moveTo(COG)
    pyautogui.click()
    DISCONNECT = (610, 440)
    pyautogui.moveTo(DISCONNECT)
    pyautogui.click()

def pair(passkey: str):
    COG = (575, 230)
    pyautogui.moveTo(COG)
    pyautogui.click()
    PAIR = (585, 395)
    pyautogui.moveTo(PAIR)
    pyautogui.click()
    PAIR_2 = (695, 535)
    pyautogui.moveTo(PAIR_2)
    pyautogui.click()
    time.sleep(0.5)
    try:
        position = pyautogui.locateOnScreen('images/error_pairing_timeout.png', region=REGION)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError) as e:
        print(e)
        print('exception raised')
        ERROR_CLOSE = (750, 250)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        ERROR_CLOSE = (755, 210)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        return -1
    time.sleep(2)
    PASSKEY = (560, 190)
    pyautogui.moveTo(PASSKEY)
    pyautogui.click()
    pyautogui.write(passkey, interval=0.01)
    SUBMIT_PASSKEY = (690, 250)
    pyautogui.moveTo(SUBMIT_PASSKEY)
    pyautogui.click()
    time.sleep(7)
    CLOSE = (755, 265)
    pyautogui.moveTo(CLOSE)
    pyautogui.click()
    return 0

def write_request():
    UART_OVER_BLE = (390, 425)
    pyautogui.moveTo(UART_OVER_BLE)
    pyautogui.click()
    time.sleep(5)
    TEXTFIELD = (390, 495)
    pyautogui.moveTo(TEXTFIELD)
    pyautogui.click()
    time.sleep(0.5)
    # insert error_write_gatt_operation_in_progress here
    try:
        position = pyautogui.locateOnScreen('images/error_write_gatt_operation_in_progress.png', region=REGION)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError) as e:
        print(e)
        print('exception raised')
    pyautogui.write('F00A')
    CONFIRM = (590, 490)
    time.sleep(0.5)
    pyautogui.moveTo(CONFIRM)
    pyautogui.click()


def connect_DfuTarg():
    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()
    # this can throw a bunch of errors

def start_secure_DFU():
    DFU_BUTTON = (540, 225)
    pyautogui.moveTo(DFU_BUTTON)
    pyautogui.click()

def choose_zip_file():
    CHOOSE_BUTTON = (750, 150)
    pyautogui.moveTo(CHOOSE_BUTTON)
    pyautogui.click()
    time.sleep(0.25)
    pyautogui.hotkey('ctrl' ,'l')
    pyautogui.press('backspace')
    pyautogui.write(FOLDER)
    for _ in range(6):
        pyautogui.press('tab')
    pyautogui.write(FILE)
    pyautogui.press('enter')



if __name__ == "__main__":
    prepare_window()
    choose_adapter()
    time.sleep(3)
    filter_device('E9:1E:3D:7D:08:F4')
    discover_devices()
    connect_AQM()
    while True:
        if pair('111111') == -1:
            disconnect_AQM()
            connect_AQM()
        else:
            break
    write_request()
    time.sleep(5)
    filter_device('DfuTarg')
    discover_devices()
    connect_DfuTarg()
    start_secure_DFU()
    choose_zip_file()