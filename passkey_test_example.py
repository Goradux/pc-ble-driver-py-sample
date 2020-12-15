from queue import Queue
from threading import Thread, Condition
import time
import random
import string
import logging

from pc_ble_driver_py.observers import BLEDriverObserver, BLEAdapterObserver
from driver_setup import Settings, setup_adapter

from pc_ble_driver_py.ble_driver import (
    BLEDriver,
    BLEEnableParams,
    BLEConfig,
    BLEConfigConnGatt,
    BLEAdvData,
    BLEGapIOCaps,
    BLEGapSecStatus,
    BLEGapSecParams,
    BLEGapSecKDist,
    util,
    driver
)

logger = logging.getLogger(__name__)
passkeyQueue = Queue()
authStatusQueue = Queue()

class Central(BLEDriverObserver, BLEAdapterObserver):
    def __init__(self, adapter):
        self.adapter = adapter
        logger.info("Central adapter is %d", self.adapter.driver.rpc_adapter.internal)
        self.conn_q = Queue()
        self.adapter.observer_register(self)
        self.adapter.driver.observer_register(self)
        self.conn_handle = None
        self.connecting = False

    def start(self, connect_with):
        self.connect_with = connect_with
        self.connecting = False
        logger.info("scan_start, trying to find %s", self.connect_with)
        self.adapter.driver.ble_gap_scan_start()
        self.conn_handle = self.conn_q.get(timeout=10)
        Thread(
            target=self.adapter.authenticate,
            args=(self.conn_handle, None),
            kwargs={"bond": True, "mitm": True, "io_caps": BLEGapIOCaps.keyboard_only},
        ).start()

    def stop(self):
        self.connecting = False

        if self.conn_handle:
            self.adapter.driver.ble_gap_disconnect(self.conn_handle)

    def on_gap_evt_adv_report(
        self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data
    ):
        if BLEAdvData.Types.complete_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.complete_local_name]
        elif BLEAdvData.Types.short_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.short_local_name]
        else:
            return

        dev_name = "".join(chr(e) for e in dev_name_list)

        if dev_name == self.connect_with and self.connecting == False:
            self.connecting = True
            address_string = "".join("{0:02X}".format(b) for b in peer_addr.addr)
            logger.info(
                "Trying to connect to peripheral advertising as %s, address: 0x%s",
                dev_name,
                address_string,
            )

            self.adapter.connect(peer_addr, tag=1)

    def on_gap_evt_connected(
        self, ble_driver, conn_handle, peer_addr, role, conn_params
    ):
        self.conn_q.put(conn_handle)

    def on_gap_evt_auth_key_request(
        self, ble_driver, conn_handle, **kwargs
    ):
        passkey = passkeyQueue.get(timeout=10)
        pk = util.list_to_uint8_array(passkey)

        driver.sd_ble_gap_auth_key_reply(
            ble_driver.rpc_adapter,
            conn_handle,
            kwargs['key_type'],
            pk.cast(),
        )




def setUp(self):
    settings = Settings.current()

    central = setup_adapter(
        settings.serial_ports[0],
        False,
        settings.baud_rate,
        settings.retransmission_interval,
        settings.response_timeout,
        settings.driver_log_level,
    )

    self.central = Central(central)

    # Advertising name used by peripheral and central
    # to find peripheral and connect with it

def test_passkey(self):
    self.peripheral.start('CAAQM')
    self.central.start("CAAQM")
    authStatus = authStatusQueue.get(timeout=200)
    self.assertTrue(authStatus == BLEGapSecStatus.success)
