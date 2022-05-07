# -*- encoding: utf-8 -*-
"""
@File    : main.py
@Project : py_easyR4
@Time    : 2022/5/4 18:59
@Author  : Jason Liu
@Email   : ltxvanessa4980@gmail.com
@Software: PyCharm
"""
import queue
import threading
import time

import json5
import numpy as np
import pyqtgraph as pg
import serial
from pyqtgraph.Qt import QtWidgets
from scipy import signal
from easyr4 import easyR4, easyR4_Read_Thread
from ui import QT_Main
import sys
EASYR4_PORT = '/dev/tty.usbserial-32310'
BAUDRATE = 1 * 1000 * 1000

PROFILE = 'config_profile.jsonc'

def update():
    global data_queue, view, win
    if data_queue.qsize() >= 1:
        adc_data = data_queue.get()

        adc = adc_data[0, :] + 1j * adc_data[1, :]

        adc_fft = np.fft.fft(adc * win, 512)
        fft_abs = np.abs(adc_fft)
        fft_log = np.log10(fft_abs)
        view.plot(fft_abs[10:256], clear=True, pen=pg.mkPen('g', width=3))

captime = 5

if __name__ == '__main__':
    data_queue = queue.Queue()


    radar = easyR4()
    radar.get_config()
    radar.sensor_stop()
    time.sleep(1)

    win = signal.windows.hann(radar.radar_cfg['samples'])
    radar.get_system_status()

    cap_cnt = captime * 1e3 // radar.radar_cfg['update_rate']

    rp_read = easyR4_Read_Thread(com_port=radar.com_port, samples=radar.radar_cfg['samples'], queue=data_queue)
    rp_read.start()

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QT_Main(capture_cnt=cap_cnt, adc_data_queue=data_queue, radar_config=radar.radar_cfg)
    MainWindow.show()
    MainWindow.Display_Setting()
    MainWindow.Start_Timer()
    app.instance().exec()
    rp_read.close()