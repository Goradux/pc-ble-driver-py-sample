import sys
import time
import logging
import queue
from pc_ble_driver_py.observers import BLEDriverObserver, BLEAdapterObserver
import threading

COM_PORT = 'COM5'
NRF_ADAPTER = 'NRF52'
TARGET_DEV_NAME = "CAAQM"
TARGET_DEV_MAC = 'E9:1E:3D:7D:08:F4'
CONNECTIONS = 1
CFG_TAG = 1

from pc_ble_driver_py import config

config.__conn_ic_id__ = NRF_ADAPTER
from pc_ble_driver_py.ble_driver import BLEDriver, BLEAdvData, BLEEvtID, BLEEnableParams, BLEGapTimeoutSrc, BLEUUID, BLEGapScanParams, BLEConfigCommon, BLEConfig, BLEConfigConnGatt, util, driver, BLEGattsHVXParams, BLEGattsCharHandles, BLEGapIOCaps
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
        self.conn_handle = None
        self.connecting = False


    def start(self, connect_with):
        self.connect_with = connect_with
        self.connecting = False
        
        self.adapter.driver.open()
        gatt_config = BLEConfigConnGatt()
        gatt_config.att_mtu = self.adapter.default_mtu
        gatt_config.conn_cfg_tag = 1
        self.adapter.driver.ble_cfg_set(BLEConfig.conn_gatt, gatt_config)
        self.adapter.driver.ble_enable()

        
        print_with_gaps(f'scan_start, trying to find {self.connect_with}')
        self.adapter.driver.ble_gap_scan_start()
        self.conn_handle = self.connection_queue.get(timeout=10)

        def toDo(adapter: BLEAdapter, handle):
            print_with_gaps('Before auth')
            # adapter.authenticate(handle, None, bond=True, mitm=True, io_caps=BLEGapIOCaps.keyboard_display)
            adapter.authenticate(handle, None, bond=True, mitm=True)
            print_with_gaps('After auth')
            # self.adapter.service_discovery(handle)
            # time.sleep(10)
            # print_with_gaps('before notification')
            # ok mb this is not necessary actually
            # adapter.enable_notification(handle, BLEUUID(0x0003))
            # print_with_gaps('after notification')

            # just write instead
            data = [0x22, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
            adapter.write_req(handle, BLEUUID(0x0002), data, 37)
            # adapter.write_req(handle, BLEUUID(0x0002), data)


        # data len = 0xF4 224


        # threading.Thread(
        #     target=self.adapter.authenticate,
        #     args=(self.conn_handle, None),
        #     # kwargs={"bond": True, "mitm": True, "io_caps": BLEGapIOCaps.keyboard_only},
        #     # kwargs={"bond": True, "mitm": True, "io_caps": BLEGapIOCaps.display_only},
        #     # kwargs={"bond": True, "mitm": True},
        #     kwargs={"bond": True},
        # ).start()

        threading.Thread(
            target=toDo,
            args=(self.adapter, self.conn_handle)
        ).start()

        # def notific():
        #     print_with_gaps('Before sleep')
        #     # time.sleep(15)
        #     print_with_gaps('After sleep')
        #     self.adapter.enable_notification(
        #         self.conn_handle, BLEUUID(0x0003)
        #     )
        #     print_with_gaps('After notifications')
        # threading .Thread(
        #     target=notific
        # ).start()


    def stop(self):
        self.connecting = False
        if self.conn_handle:
            self.adapter.driver.ble_gap_disconnect(self.conn_handle)

    

    def on_gap_evt_connected(self, ble_driver, conn_handle, peer_addr, role, conn_params):
        print_with_gaps("New connection: {}".format(conn_handle))
        self.connection_queue.put(conn_handle)

    def on_gap_evt_disconnected(self, ble_driver, conn_handle, reason):
        print("Disconnected: {} {}".format(conn_handle, reason))

    def on_gap_evt_auth_key_request(self, ble_driver, conn_handle, **kwargs):
        passkey = '111111'  # must be a string or a list
        pk = util.list_to_uint8_array(passkey)
        print_with_gaps('Got the AUTH request!')
        driver.sd_ble_gap_auth_key_reply(
            ble_driver.rpc_adapter,
            conn_handle,
            kwargs['key_type'],
            pk.cast(),
        )
        print_with_gaps('Replied to the AUTH request!')


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
        if dev_name == self.connect_with and self.connecting == False:
            self.connecting = True
            self.adapter.connect(peer_addr, tag=CFG_TAG)
            # self.adapter.authenticate()
            print('Connected to {}'.format(custom_address_string))
            print_with_gaps('In the if statement')

    def on_notification(self, ble_adapter, conn_handle, uuid, data):
        if len(data) > 32:
            data = "({}...)".format(data[0:10])
        print("Connection: {}, {} = {}".format(conn_handle, uuid, data))

    
    def on_gap_evt_auth_status(self, ble_driver, conn_handle, error_src, bonded, sm1_levels, sm2_levels, kdist_own, kdist_peer, auth_status):
        print_with_gaps('ON_GAP_EVT_AUTH_STATUS received!')
        return super().on_gap_evt_auth_status(ble_driver, conn_handle, error_src, bonded, sm1_levels, sm2_levels, kdist_own, kdist_peer, auth_status)

    def on_gap_evt_conn_param_update(self, ble_driver, conn_handle, conn_params):
        print_with_gaps('ON_GAP_EVT_CONN_PARAM_UPDATE request received!')




def main(selected_serial_port):
    print("Serial port used: {}".format(selected_serial_port))
    print_with_gaps()
    driver = BLEDriver(
        serial_port=selected_serial_port, auto_flash=False, baud_rate=1000000, log_severity_level="info"
    )

    adapter = BLEAdapter(driver)
    collector = HRCollector(adapter)
    # collector.open()
    # conn = collector.connect_and_discover()
    # if conn is not None:
    #     time.sleep(10)
    # collector.close()

    collector.start(TARGET_DEV_NAME)


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