import sys
import time
import logging
# from queue import Queue, Empty
import queue
from pc_ble_driver_py.observers import BLEDriverObserver, BLEAdapterObserver

COM_PORT = 'COM5'
NRF_ADAPTER = 'NRF52'
TARGET_DEV_NAME = "CAAQM"
TARGET_DEV_MAC = 'E9:1E:3D:7D:08:F4'
CONNECTIONS = 1
CFG_TAG = 1

from pc_ble_driver_py import config

config.__conn_ic_id__ = NRF_ADAPTER
from pc_ble_driver_py.ble_driver import BLEDriver, BLEAdvData, BLEEvtID, BLEEnableParams, BLEGapTimeoutSrc, BLEUUID, BLEGapScanParams, BLEConfigCommon, BLEConfig, BLEConfigConnGatt, util, driver, BLEGattsHVXParams, BLEGattsCharHandles
from pc_ble_driver_py.ble_adapter import BLEAdapter

nrf_sd_ble_api_ver = config.sd_api_ver_get()


def print_with_gaps(*args, **kwargs):
    print()
    print()
    print()
    print(*args, **kwargs)
    print()
    print()
    print()


class HRCollector(BLEDriverObserver, BLEAdapterObserver):
    def __init__(self, adapter):
        # super(HRCollector, self).__init__()
        super().__init__()
        self.adapter = adapter
        self.connection_queue = queue.Queue()
        self.adapter.observer_register(self)
        self.adapter.driver.observer_register(self)
        self.adapter.default_mtu = 250

    def open(self):
        self.adapter.driver.open()
        if str(config.__conn_ic_id__).upper() == "NRF52":
            gatt_config = BLEConfigConnGatt()
            gatt_config.att_mtu = self.adapter.default_mtu
            # gatt_config.tag = CFG_TAG # ? mb they had an error?
            gatt_config.conn_cfg_tag = CFG_TAG
            self.adapter.driver.ble_cfg_set(BLEConfig.conn_gatt, gatt_config)

            self.adapter.driver.ble_enable()

    def close(self):
        self.adapter.driver.close()

    def connect_and_discover(self):
        scan_duration = 5
        params = BLEGapScanParams(interval_ms=200, window_ms=150, timeout_s=scan_duration)

        self.adapter.driver.ble_gap_scan_start(scan_params=params)

        try:
            # before and after this line changes a lot!!!
            new_connection = self.connection_queue.get(timeout=scan_duration)
            print_with_gaps('IN CONNECT AND DISCOVER')
            self.adapter.service_discovery(new_connection)
            print_with_gaps('AFTER DISCOVERY')
            tx_channel = BLEUUID(0x0003)
            # somehow this happens before the "AFTER DISCOVERY" printout
            # self.adapter.enable_notification(
            #     # new_connection, BLEUUID(BLEUUID.Standard.battery_level)
            #     new_connection, BLEUUID(0x0003)
            # )

            # status, data = self.adapter.read_req(new_connection,BLEUUID(BLEUUID.Standard.battery_level))
            # status, data = self.adapter.read_req(new_connection, tx_channel)
            # print('Battery level read value = {} status = {}'.format(data,status))
            return new_connection
        except queue.Empty:
            print(f"No advertising {TARGET_DEV_NAME} found.")
            return None

    def on_gap_evt_connected(self, ble_driver, conn_handle, peer_addr, role, conn_params):
        print_with_gaps("New connection: {}".format(conn_handle))
        self.connection_queue.put(conn_handle)

    def on_gap_evt_disconnected(self, ble_driver, conn_handle, reason):
        print("Disconnected: {} {}".format(conn_handle, reason))

    # useless?
    # def on_gap_evt_passkey_display(self, ble_driver, conn_handle, passkey):
    #     # TODO: implement
    #     print("Passkey display request: {} {}".format(conn_handle, passkey))

    def on_gap_evt_auth_key_request(self, ble_driver, conn_handle, **kwargs):
        passkey = '111111'  # must be a string or a list
        pk = util.list_to_uint8_array(passkey)

        driver.sd_ble_gap_auth_key_reply(
            ble_driver.rpc_adapter,
            conn_handle,
            kwargs['key_type'],
            pk.cast(),
        )


    def on_gap_evt_adv_report(self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data):
        if BLEAdvData.Types.complete_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.complete_local_name]

        elif BLEAdvData.Types.short_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.short_local_name]

        else:
            return

        dev_name = "".join(chr(e) for e in dev_name_list)
        address_string = "".join("{0:02X}".format(b) for b in peer_addr.addr)
        print(
            "Received advertisment report, address: 0x{}, device_name: {}".format(
                address_string, dev_name
            )
        )

        custom_address_string = ":".join(hex(i)[2:].rjust(2, '0').upper() for i in peer_addr.addr)
        if dev_name == TARGET_DEV_NAME:
            self.adapter.connect(peer_addr, tag=CFG_TAG)
            # print_with_gaps('Connected')
            # result = self.adapter.authenticate(conn_handle, None, bond=True)
            # print_with_gaps('Authenticated')
            # print_with_gaps(result)
            print('Connected to {}'.format(custom_address_string))
            print_with_gaps('In the if statement')

    def on_notification(self, ble_adapter, conn_handle, uuid, data):
        if len(data) > 32:
            data = "({}...)".format(data[0:10])
        print("Connection: {}, {} = {}".format(conn_handle, uuid, data))


def main(selected_serial_port):
    print("Serial port used: {}".format(selected_serial_port))
    print_with_gaps()
    driver = BLEDriver(
        serial_port=selected_serial_port, auto_flash=False, baud_rate=1000000, log_severity_level="info"
    )

    adapter = BLEAdapter(driver)
    collector = HRCollector(adapter)
    collector.open()
    conn = collector.connect_and_discover()

    if conn is not None:
        time.sleep(10)

    collector.close()

    # set up settings

    # set up central adapter
    # assign central

    # set up peripheral adapter ???
    # assign peripheral

    # start the test:
    # start the peripheral ???
    # start the central



if __name__ == "__main__":
    logging.basicConfig(
        level="DEBUG",
        format="%(asctime)s [%(thread)d/%(threadName)s] %(message)s",
    )
    serial_port = COM_PORT
    if len(sys.argv) > 1:
        serial_port = sys.argv[1]
    main(serial_port)
    quit()