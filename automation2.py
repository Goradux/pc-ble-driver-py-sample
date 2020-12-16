# 1. resize window
# 2. position it top left
# 3. get its coordinates
# 4. Do the shenanigans
#

# https://pypi.org/project/PyGetWindow/
try:
    import pygetwindow
except ImportError:
    print('Install pygetwindow with: pip install pygetwindow')
# https://pypi.org/project/PyAutoGUI/
try:
    import pyautogui
except:
    print('Install pyautogui with: pip install pyautogui')
try:
    import cv2
except ImportError:
    print('Install cv2 with: pip install opencv-python')
import time
import os
import sys

REGION = (0, 0, 1000, 1000)

# default values for testing:
PATH = 'C:\\ex_hex\\OTA\\download_AQM_v112t_20201126.zip'
NRF_VERSION = '3.6.1'
MAC = 'E9:1E:3D:7D:08:F4'
PASSKEY = '111111'

FULL_PATH = None
FOLDER = None
FILE = None


def parse_args():
    print('Parsing args.')
    try:
        global NRF_VERSION
        NRF_VERSION = sys.argv[1]
    except:
        print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
        exit()
    
    try:
        global MAC
        MAC = sys.argv[2]
    except:
        print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
        exit()

    try:
        global PASSKEY
        PASSKEY = sys.argv[3]
    except:
        print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
        exit()

    try:
        global PATH 
        PATH = sys.argv[4]
    except:
        print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
        exit()


def prepare_path():
    print('Checking zip file path.')
    global PATH
    if os.path.exists(PATH):
        global FULL_PATH, FOLDER, FILE
        FULL_PATH = os.path.abspath(PATH)
        FOLDER = os.path.dirname(FULL_PATH)
        FILE = os.path.basename(FULL_PATH)
    else:
        raise ValueError('Bad .zip path.')


def prepare_window():
    print('Preparing the window.')
    # window = pygetwindow.getWindowsWithTitle('nRF Connect v3.6.1 - Bluetooth Low Energy')[0]
    try:
        window = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION} - Bluetooth Low Energy')[0]
    except IndexError:
        print(f'No nRF Connect Bluetooth Low Energy with version {NRF_VERSION} found.')
        exit()
    window.resizeTo(1000, 800)
    window.moveTo(0, 0)
    window.activate()


def choose_adapter():
    print('Selecting the adapter.')
    SELECT_DEVICE = (150, 50)
    pyautogui.moveTo(SELECT_DEVICE)
    pyautogui.click()
    try:
        position = pyautogui.locateOnScreen('images/select_device_USB_nrf52.png', region=REGION, confidence=0.75)
        if position == None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('No nRF52 dongle found.')
        exit()
    SELECT_ADAPTER = (150, 120)
    pyautogui.moveTo(SELECT_ADAPTER)
    pyautogui.click()


def filter_device(mac: str):
    print(f'Filtering out a device with MAC {mac}.')
    def open_options():
        OPTIONS = (775, 170)
        pyautogui.moveTo(OPTIONS)
        pyautogui.click()

    try:
        position = pyautogui.locateOnScreen('images/scan_options_extended.png', region=REGION, confidence=0.75)
        if position == None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        # print(e)
        print('  The options is not extended.')
        print('  Extending the options menu.')
        open_options()

    FILTER = (850, 220)
    pyautogui.moveTo(FILTER)
    pyautogui.click()
    pyautogui.hotkey('ctrl', 'a')
    # pyautogui.press('backspace')
    pyautogui.write(mac, interval=0.01)


def discover_devices():
    print('Discovering devices.')
    START_SCAN = (800, 140)
    pyautogui.moveTo(START_SCAN)
    pyautogui.click()
    time.sleep(5)
    pyautogui.click()


def connect_AQM():
    print(f'Connecting to AQM at {MAC}.')
    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()

    try:
        position = pyautogui.locateOnScreen('images/error_device_disconnected.png', region=REGION, confidence=0.75)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error received. Device has been disconnected.')
        ERROR_CLOSE = (750, 220)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        connect_AQM()
        return


def disconnect_AQM():
    print(f'Disconnecting from AQM at {MAC}.')
    COG = (575, 230)
    pyautogui.moveTo(COG)
    pyautogui.click()
    DISCONNECT = (610, 440)
    pyautogui.moveTo(DISCONNECT)
    pyautogui.click()


def pair():
    print(f'Pairing to the AQM at {MAC} with {PASSKEY}.')
    time.sleep(0.5)
    COG = (575, 225)
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
        position = pyautogui.locateOnScreen('images/error_pairing_timeout.png', region=REGION, confidence=0.75)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error when pairing: Timeout.')
        ERROR_CLOSE = (750, 250)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        ERROR_CLOSE = (755, 210)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        return -1
    time.sleep(2)
    PASSKEY_FIELD = (560, 190)
    pyautogui.moveTo(PASSKEY_FIELD)
    pyautogui.click()
    pyautogui.write(PASSKEY, interval=0.01)
    SUBMIT_PASSKEY = (690, 250)
    pyautogui.moveTo(SUBMIT_PASSKEY)
    pyautogui.click()
    time.sleep(7)
    CLOSE = (755, 265)
    pyautogui.moveTo(CLOSE)
    pyautogui.click()
    return 0


def write_request():
    print('Activating DfuTarg with 0xF00A write request.')
    UART_OVER_BLE = (390, 425)
    pyautogui.moveTo(UART_OVER_BLE)
    pyautogui.click()
    time.sleep(5)
    TEXTFIELD = (390, 495)
    pyautogui.moveTo(TEXTFIELD)
    pyautogui.click()
    pyautogui.write('F00A')
    CONFIRM = (590, 490)
    time.sleep(0.5)
    pyautogui.moveTo(CONFIRM)
    pyautogui.click()
    time.sleep(1)
    # insert error_write_gatt_operation_in_progress here
    try:
        position = pyautogui.locateOnScreen('images/error_write_gatt_operation_in_progress.png', region=REGION, confidence=0.75)
        if position != None:
            ERROR_CLOSE = (755, 235)
            pyautogui.moveTo(ERROR_CLOSE)
            pyautogui.click()
            pyautogui.moveTo(UART_OVER_BLE)
            pyautogui.click()
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error writing: GATT operation already in progress.')
        return -1
    return 0


def connect_DfuTarg():
    print('Connecting to DfuTarg.')
    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()
    # this can throw a bunch of errors


def start_secure_DFU():
    print('Starting secure DFU.')
    DFU_BUTTON = (540, 225)
    pyautogui.moveTo(DFU_BUTTON)
    pyautogui.click()


def choose_zip_file():
    print(f'Choosing the zip file at {FULL_PATH}')
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


def start_DFU_upload():
    print('Starting DFU upload.')
    # TODO: replace hardcoded buttons to button searches via pyautogui.locateCenterOnScreen()
    START_DFU_BUTTON = (735, 300)
    pyautogui.moveTo(START_DFU_BUTTON)
    pyautogui.click()


def check_DFU():
    print('Checking DFU progress.')
    while True:
        try:
            position = pyautogui.locateOnScreen('images/dfu_completed.png', region=REGION, confidence=0.75)
            print(position)
            if position != None:
                raise ValueError
            CLOSE_BUTTON = (755, 395)
            pyautogui.moveTo(CLOSE_BUTTON)
            pyautogui.click()
        except (pyautogui.ImageNotFoundException, ValueError):
            print('  DFU is still in progress.')
        time.sleep(5)


if __name__ == "__main__":
    parse_args()
    prepare_path()
    prepare_window()
    choose_adapter()
    time.sleep(3)
    filter_device(MAC)
    discover_devices()
    connect_AQM()
    while True:
        if pair() == -1:
            disconnect_AQM()
            connect_AQM()
        else:
            break
    ## THERE IS A BUG HERE: the program needs to detect whether there CAAQM has
    ## not connected properly
    while True:
        time.sleep(0.5)
        if write_request() == 0:
            break
    time.sleep(7)
    filter_device('DfuTarg')
    discover_devices()
    connect_DfuTarg()
    start_secure_DFU()
    choose_zip_file()
    start_DFU_upload()
    check_DFU()