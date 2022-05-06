# -*- encoding: utf-8 -*-
"""
@File    : test.py
@Project : py_easyR4
@Time    : 2022/5/4 18:59
@Author  : Jason Liu
@Email   : ltxvanessa4980@gmail.com
@Software: PyCharm
"""
import serial
import numpy as np
import time
import os
import sys
from matplotlib import pyplot as plt
import json5

EASYR4_PORT = '/dev/tty.usbserial-323240'
BAUDRATE = 1 * 1000 * 1000

SETTING = '!S110A3C02\r\n'
if __name__ == '__main__':
    CLIPort = serial.Serial(EASYR4_PORT, baudrate=BAUDRATE, timeout=0.01)
    CLIPort.write(SETTING.encode())
    time.sleep(0.1)
    for i in range(100):
        print(CLIPort.readline().hex())
    print('aa')
