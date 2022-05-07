# -*- encoding: utf-8 -*-
"""
@File    : qt_main.py
@Time    : 2021/12/26 20:55
@Author  : Jason Liu
@Email   : ltxvanessa4980@gmail.com
@Software: PyCharm
"""
import time
import PyQt6
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QWidget
import numpy as np
from scipy import signal
from .ui_main_window import UI_Main_Window
from scipy.io import savemat

class QT_Main(QWidget):
    def __init__(self, capture_cnt, adc_data_queue, radar_config):
        super(QT_Main, self).__init__()

        self.ui = UI_Main_Window()
        self.ui.setupUi(self)

        self.label1 = self.ui.label1

        self.capbtn = self.ui.pushButton
        self.capbtn.clicked.connect(self.Start_Capture)

        self.plot_hrrp_view = self.ui.plot_hrrp.addPlot()
        self.plot_hrrp_view.setLabel('bottom', 'HRRP')
        self.plot_hrrp_view.showGrid(x=True, y=True)

        self.capture_cnt = radar_config['cap_time'] * 1e3 // radar_config['update_rate']
        self.save_path = radar_config['save_path']
        self.save_format = radar_config['save_format']

        self.data_queue = adc_data_queue

        self.capture_cnt_last = 0

        self.ppg_length = 0
        self.ppg_data = []
        self.rp_length = 0
        self.rp_data = []
        self.ptr5 = 0
        self.radar_cfg = radar_config
        self.win = signal.windows.hann(self.radar_cfg['samples'])

        self.capture = False
        self.cap_now = 0
        self.cap_temp = []

    def Start_Capture(self):
        self.capbtn.setEnabled(False)
        self.capture = True

    def Start_Timer(self):

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(1)


    def Display_Setting(self):
        self.label1.setText("Gain       : " + str(self.radar_cfg['gain']) + 'dB' + "\n" +
                            "Ramp Time  : " + str(self.radar_cfg['ramp_time']) + 'us'  + "\n" +
                            "Samples    : " + str(self.radar_cfg['samples']) + "\n" +
                            "Max Range  : " + str(self.radar_cfg['max_range']) + 'mm'  + "\n" +
                            "Setting BW : " + str(self.radar_cfg['setting_bw']) + 'MHz'  + "\n" +
                            "Real BW    : " + str(self.radar_cfg['real_bw']) + 'MHz'  + "\n" +
                            "Update Rate: " + str(self.radar_cfg['update_rate']) + 'ms'  + "\n" +
                            "Base Freq  : " + str(self.radar_cfg['base_freq']) + 'GHz'  + "\n" +
                            "ADC CLKDIV : " + str(self.radar_cfg['adc_clkdiv']) + "\n" +
                            "Downsamp   : " + str(self.radar_cfg['down_samp']) + "\n" +
                            "Ramps      : " + str(self.radar_cfg['ramps']) + "\n" +
                            "Cap Time   : " + str(self.radar_cfg['cap_time']) + "\n" +
                            "Save Path  : " + str(self.radar_cfg['save_path']) + "\n"
                            )

    def updateData(self):
        if self.data_queue.qsize() >= 1:
            adc_data = self.data_queue.get()

            adc = adc_data[0, :] + 1j * adc_data[1, :]

            adc_fft = np.fft.fft(adc * self.win, 512)
            fft_abs = np.abs(adc_fft)
            fft_log = np.log10(fft_abs)
            self.plot_hrrp_view.plot(fft_abs[10:256], clear=True, pen=pg.mkPen('g', width=3))

            if self.capture == True:
                self.cap_now += 1
                self.cap_temp.append(adc_data)
                prec = int(self.cap_now / self.capture_cnt * 100)
                self.ui.progressBar.setValue(prec)

                if self.cap_now == self.capture_cnt:
                    self.capture = False
                    self.capbtn.setEnabled(True)
                    file_name = self.save_path + time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
                    if self.save_format == 0:
                        np.save(file_name, self.cap_temp)
                    elif self.save_format == 1:
                        savemat(file_name + '.mat', {'adc_data': self.cap_temp})
                    self.cap_temp = []