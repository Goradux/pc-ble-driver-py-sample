# 1. resize window
# 2. position it top left
# 3. get its coordinates
# 4. Do the shenanigans
#

import time
import os
import sys
import re
import logging
from datetime import datetime

# https://pypi.org/project/PyGetWindow/
try:
    import pygetwindow
except ImportError:
    print('Install pygetwindow with: pip install pygetwindow')
    sys.exit()
# https://pypi.org/project/PyAutoGUI/
try:
    import pyautogui
except:
    print('Install pyautogui with: pip install pyautogui')
    sys.exit()
try:
    import cv2
except ImportError:
    print('Install cv2 with: pip install opencv-python')
    sys.exit()


REGION = (0, 0, 1000, 1000)

# default values for testing:
PATH = '.\\test_fw\\download_AQM_v112t_20201126.zip'
NRF_VERSION = '3.6.1'
MAC = 'E9:1E:3D:7D:08:F4'
PASSKEY = '111111'
AQMS_LIST = 'lists/AQMs.txt'

FULL_PATH = None
FOLDER = None
FILE = None
AQMS = []


def parse_args():
    print('Parsing args.')
    try:
        global NRF_VERSION
        NRF_VERSION = sys.argv[1]
    except:
        print(f'The required CLI arguments are: nrf_version aqm_list_path zip_path')
        sys.exit()
    
    # try:
    #     global MAC
    #     MAC = sys.argv[2]
    # except:
    #     print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
    #     sys.exit()

    # try:
    #     global PASSKEY
    #     PASSKEY = sys.argv[3]
    # except:
    #     print(f'The CLI format is: python {sys.argv[0]} nrf_version MAC_address passkey zip_path')
    #     sys.exit()

    try:
        global AQMS_LIST
        AQMS_LIST = sys.argv[2]
    except:
        print(f'The required CLI arguments are: nrf_version aqm_list_path zip_path')
        sys.exit()

    try:
        global PATH 
        PATH = sys.argv[3]
    except:
        print(f'The required CLI arguments are: nrf_version aqm_list_path zip_path')
        sys.exit()


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


def prepare_nrf_connect_window():
    print('Preparing nRF Connect window.')
    try:
        old_ble_window = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION} - Bluetooth Low Energy')[0]
        old_ble_window.close()
    except:
        pass
    time.sleep(1)
    try:
        window = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION}')[0]
    except IndexError:
        print(f'No nRF Connect v{NRF_VERSION} found.')
        sys.exit()
    window.resizeTo(768, 500)
    window.moveTo(0, 0)
    window.activate()
    BLE_OPEN = (610, 210)
    pyautogui.moveTo(BLE_OPEN)
    pyautogui.click()
    time.sleep(5)


def prepare_nrf_connect_ble_window():
    print('Preparing nRF Connect BLE window.')
    # window = pygetwindow.getWindowsWithTitle('nRF Connect v3.6.1 - Bluetooth Low Energy')[0]
    try:
        window = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION} - Bluetooth Low Energy')[0]
    except IndexError:
        print(f'No nRF Connect Bluetooth Low Energy with version {NRF_VERSION} found.')
        sys.exit()
    window.resizeTo(1000, 800)
    window.moveTo(0, 0)
    window.activate()


def restart_nrf_connect_ble_window():
    nrf_connect_ble = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION} - Bluetooth Low Energy')[0]
    nrf_connect_ble.close()
    time.sleep(1)
    nrf_connect = pygetwindow.getWindowsWithTitle(f'nRF Connect v{NRF_VERSION}')[0]
    nrf_connect.activate()
    BLE_OPEN = (610, 210)
    pyautogui.moveTo(BLE_OPEN)
    pyautogui.click()
    time.sleep(5)


def close_choose_file_window():
    choose_file = pygetwindow.getWindowsWithTitle('Choose file')[0]
    choose_file.close()


def get_DFU_MAC(mac: str) -> str:
    dfu_mac = ''

    temp = hex(int(mac.replace(':', ''), base=16) + 1)[2:].upper()
    dfu_mac = ':'.join(temp[i:i+2] for i in range(0, len(temp), 2))

    return dfu_mac


def choose_adapter():
    print('Selecting the adapter.')
    SELECT_DEVICE = (150, 50)
    pyautogui.moveTo(SELECT_DEVICE)
    pyautogui.click()
    try:
        img = cv2.imread('images/select_device_USB_nrf52.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
        if position == None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('No nRF52 dongle found.')
        logging.error(f'No nRF52 dongle found.')
        sys.exit()
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
        img = cv2.imread('images/scan_options_extended.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
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


connect_AQM_retry_counter = 0
def connect_AQM():
    print(f'Connecting to AQM at {MAC}.')
    global connect_AQM_retry_counter
    if connect_AQM_retry_counter > 3:
        connect_AQM_retry_counter = 0
        logging.exception(f'{MAC} - Connect AQM limit reached. Skipping this device.')
        return -1

    try:
        img = cv2.imread('images/button_connect.png')
        position = pyautogui.locateCenterOnScreen(img, region=REGION, confidence=0.95)
        if position == None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print(f'  Error received. No AQM at {MAC} found.')
        connect_AQM_retry_counter = 0
        logging.error(f'{MAC} - No AQM with such MAC found.')
        return -1    

    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()
    time.sleep(1)

    try:
        img = cv2.imread('images/error_device_disconnected.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
        if position != None:
            raise ValueError
        connect_AQM_retry_counter = 0
        return 0
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error received. Device has been disconnected.')
        print('  Trying to connect again.')
        logging.exception(f'{MAC} - Device has been disconnected. Trying again.')
        ERROR_CLOSE = (750, 220)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        connect_AQM_retry_counter += 1
        connect_AQM()


def disconnect_AQM():
    print(f'Disconnecting from AQM at {MAC}.')
    COG = (575, 230)
    pyautogui.moveTo(COG)
    pyautogui.click()
    time.sleep(1)
    DISCONNECT = (610, 440)
    pyautogui.moveTo(DISCONNECT)
    pyautogui.click()


def pair():
    print(f'Pairing to the AQM at {MAC} with {PASSKEY}.')
    time.sleep(1)
    COG = (575, 225)
    pyautogui.moveTo(COG)
    pyautogui.click()
    time.sleep(0.5)
    PAIR = (585, 395)
    pyautogui.moveTo(PAIR)
    pyautogui.click()
    time.sleep(0.5)
    PAIR_2 = (695, 535)
    pyautogui.moveTo(PAIR_2)
    pyautogui.click()
    time.sleep(0.5)
    try:
        img = cv2.imread('images/error_pairing_timeout.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error when pairing: Timeout.')
        logging.exception(f'{MAC} - Pairing timeout. Trying again.')
        ERROR_CLOSE = (750, 250)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        ERROR_CLOSE = (755, 210)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        return 1
    time.sleep(2)
    PASSKEY_FIELD = (560, 190)
    pyautogui.moveTo(PASSKEY_FIELD)
    pyautogui.click()
    pyautogui.write(PASSKEY, interval=0.01)
    time.sleep(0.25)
    SUBMIT_PASSKEY = (690, 250)
    pyautogui.moveTo(SUBMIT_PASSKEY)
    pyautogui.click()
    time.sleep(7)

    # bad passkey
    try:
        img = cv2.imread('images/error_bad_passkey.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.9)
        if position != None:
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error when pairing: Bad passkey.')
        logging.error(f'{MAC} - Bad passkey.')
        ERROR_CLOSE = (755, 265)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        return -1

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
        img = cv2.imread('images/error_write_gatt_operation_in_progress.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
        if position != None:
            ERROR_CLOSE = (755, 235)
            pyautogui.moveTo(ERROR_CLOSE)
            pyautogui.click()
            pyautogui.moveTo(UART_OVER_BLE)
            pyautogui.click()
            raise ValueError
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error writing: GATT operation already in progress.')
        logging.exception(f'{MAC} - GATT operation already in progress. Trying again.')
        return -1
    return 0


connect_DfuTarg_retry_counter = 0
def connect_DfuTarg():
    print('Connecting to DfuTarg.')
    global connect_DfuTarg_retry_counter
    if connect_DfuTarg_retry_counter > 3:
        connect_DfuTarg_retry_counter = 0
        logging.exception(f'{MAC} - Connect DfuTarg limit reached. Skipping this device.')
        return -1

    CONNECT_BUTTON = (950, 275)
    pyautogui.moveTo(CONNECT_BUTTON)
    pyautogui.click()
    time.sleep(0.5)
    # this can throw a bunch of errors
    try:
        img = cv2.imread('images/error_device_disconnected.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.75)
        if position != None:
            raise ValueError
        connect_DfuTarg_retry_counter = 0
        return 0
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error received. DfuTarg has been disconnected.')
        print('  Trying to connect again.')
        logging.exception(f'{MAC} - DfuTarg has been disconnected. Trying again.')
        ERROR_CLOSE = (750, 220)
        pyautogui.moveTo(ERROR_CLOSE)
        pyautogui.click()
        connect_DfuTarg_retry_counter += 1
        connect_DfuTarg()


def start_secure_DFU():
    print('Starting secure DFU.')
    DFU_BUTTON = (540, 225)
    pyautogui.moveTo(DFU_BUTTON)
    pyautogui.click()
    time.sleep(0.5)


def choose_zip_file():
    print(f'Choosing the zip file at {FULL_PATH}')
    CHOOSE_BUTTON = (750, 150)
    pyautogui.moveTo(CHOOSE_BUTTON)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.hotkey('ctrl' ,'l')
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    time.sleep(0.5)
    pyautogui.write(FOLDER)
    pyautogui.press('enter')
    # print(FOLDER)
    # Have to wait long after first tab, then its fine
    pyautogui.press('tab')
    time.sleep(0.5)
    for _ in range(5):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.write(FILE, interval=0.01)
    pyautogui.press('enter')
    time.sleep(1)

    try:
        img = cv2.imread('images/choose_zip_file_success.png')
        position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.9)
        if position == None:
            raise ValueError
        return 0
    except (pyautogui.ImageNotFoundException, ValueError):
        print('  Error received. Choosing zip file has failed.')
        logging.error(f'{MAC} - Choosing zip file has failed. Skipping.')
        try:
            close_choose_file_window()
        except Exception as e:
            print(e)
        # restart_nrf_connect_ble_window()
        return -1


def start_DFU_upload():
    print('Starting DFU upload.')
    # TODO: replace hardcoded buttons to button searches via pyautogui.locateCenterOnScreen()
    time.sleep(0.5)
    START_DFU_BUTTON = (735, 300)
    pyautogui.moveTo(START_DFU_BUTTON)
    pyautogui.click()


def check_DFU() -> int:
    print('Checking DFU progress.')
    start = time.time()
    while True:
        try:
            img = cv2.imread('images/dfu_completed.png')
            position = pyautogui.locateOnScreen(img, region=REGION, confidence=0.95)
            if position == None:
                raise ValueError
            CLOSE_BUTTON = (755, 395)
            pyautogui.moveTo(CLOSE_BUTTON)
            pyautogui.click()
            # add successful return
            # add timeout if it is never reached
            # break
            return 0
        except (pyautogui.ImageNotFoundException, ValueError):
            time_elapsed = round(time.time() - start, 3)
            print(f'  DFU is still in progress. Time elapsed: {time_elapsed} seconds.')
            if (time_elapsed) > 90:
                print('90 seconds exceeded. Stopping the execution.')
                print('Please restart nRF Connect and the script.')
                logging.error(f'{MAC} - Uploading taking too long (> 90 sec). Skipping.')
                return -1
        time.sleep(5)


def cleanup():
    raise NotImplementedError


def validate_mac(mac: str) -> bool:
    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
        return True
    else:
        return False


def validate_passkey(passkey: str) -> bool:
    try:
        if len(passkey) == 6:
            int(passkey)
            return True
        else:
            raise ValueError
    except ValueError:
        return False


def read_list(aqm_list: str):
    aqms = []
    try:
        with open(aqm_list) as f:
            lines = f.read().splitlines()
            index = 1
            for line in lines:
                mac, passkey = line.split(' ')
                if validate_mac(mac) and validate_passkey(passkey):
                    aqms.append({'mac': mac, 'passkey': passkey})
                else:
                    print(f'Bad data at line {index}:', mac, passkey)
                    raise ValueError
                index += 1
    except FileNotFoundError:
        print('Bad AQM list specified. Exiting.')
        sys.exit()
    except ValueError:
        print('Please check data correctness and try again. Exiting.')
        sys.exit()
    global AQMS
    AQMS = aqms


def init():
    print('Initializing the program.')
    parse_args()
    prepare_path()
    prepare_nrf_connect_window()
    prepare_nrf_connect_ble_window()
    read_list(AQMS_LIST)
    init_results_folder()
    init_logger()


def AQM_update_main():
    print()
    print(f'Updating AQM at {MAC}')
    logging.info(f'{MAC} - started.')
    try:
        choose_adapter()
        time.sleep(3)
        filter_device(MAC)
        discover_devices()
        if connect_AQM() == -1:
            raise RuntimeError
        while True:
            pair_attempt = 0
            if pair_attempt > 2:
                raise RuntimeError
            pair_code = pair()
            if pair_code == 1:
                disconnect_AQM()
                connect_AQM()
            elif pair_code == -1:
                raise RuntimeError
            else:
                break
            pair_attempt += 1
        while True:
            time.sleep(0.5)
            write_attempt = 0
            if write_attempt > 3:
                raise RuntimeError
            if write_request() == 0:
                break
            write_attempt += 1
        time.sleep(7)
        filter_device(get_DFU_MAC(MAC))
        discover_devices()
        if connect_DfuTarg() == -1:
            raise RuntimeError
        start_secure_DFU()
        if choose_zip_file() == -1:
            raise RuntimeError
        start_DFU_upload()
        if check_DFU() == 0:
            # success
            print(f'Update of AQM at {MAC} is successful!')
            logging.info(f'{MAC} - Success.')
            return 0
        else:
            # failure
            raise RuntimeError
    except RuntimeError:
        # mb restart nRF here for safety
        restart_nrf_connect_ble_window()
        print(f'Error while updating AQM at {MAC}. Skipping this device.')
        logging.error(f'{MAC} - RuntimeError raised. Skipping this device.')
        return -1


def init_results_folder():
    try:
        os.mkdir('results')
    except:
        pass
    

def log_success():
    with open('results/successes.txt', 'a') as f:
        f.write(f'{MAC} {PASSKEY}\n')


def log_failure():
    with open('results/failures.txt', 'a') as f:
        f.write(f'{MAC} {PASSKEY}\n')


def init_logger():
    try:
        os.mkdir('logs')
    except:
        pass
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logging.basicConfig(
        filename=f'logs/Log_{now}.txt',
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
        )


if __name__ == "__main__":
    init()
    for aqm in AQMS:
        MAC = aqm['mac']
        PASSKEY = aqm['passkey']
        result = AQM_update_main()
        if result == 0:
            log_success()
        else:
            log_failure()
        time.sleep(3)
    print('Program is finished. Press ENTER to exit.')
    input()

# command for compiling:
# pyinstaller --onefile automation2.py --add-data="images;images"
