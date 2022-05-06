# -*- encoding: utf-8 -*-
"""
@File    : easyr4.py
@Project : silicon_radar_easyr4
@Time    : 2022/5/6 14:24
@Author  : Jason Liu
@Email   : ltxvanessa4980@gmail.com
@Software: PyCharm
"""
"""
easyR4.wave_cfg = {
    'gain': 0,          # dB
    'ramp_time': 0,     # us
    'samples': 0,       # 
    'max_range': 0,     # m
    'setting_bw': 0,    # MHz
    'real_bw':0,        # MHz
    'update_rate':0,    # ms
    'base_freq':0,      # GHz
    'adc_clkdiv':0,     #
    'down_samp':0,      #
    'ramps':0,          #
}
"""
import numpy as np
import time
import json5
import threading

class EASYR4_IDENTIFIER_CODE():
    BEGINNING_CODE = '!'
    SYSTEM_CFG_CODE = 'S'
    RADAR_FRONTEND_CFG_CODE = 'F'
    PLL_CFG_CODE = 'P'
    BASEBAND_CFG_CODE = 'B'
    PROGRAMMING_MODE_CODE = 'W'
    GET_FULL_ERR_REPORT_CODE = 'E'
    GET_SYS_INFO_CODE = 'I'
    DO_FREQ_SCAN_CODE = 'J'
    SET_MAX_BW_CODE = 'K'
    SEND_PRE_TRIG_CODE = 'L'
    SEND_MAIN_TRIG_CODE = 'M'
    SEND_BOTH_TRIG_CODE = 'N'
    GET_VERSION_CODE = 'V'
    END_CODE = '\r\n'

class easyR4():
    def __init__(self, com_port , profile='config_profile.jsonc'):
        self.com_port = com_port
        self.profile = profile
        self.CLIPort = com_port
        self.wave_cfg = {
            'gain': 0,          # dB
            'ramp_time': 0,     # us
            'samples': 0,       #
            'max_range': 0,     # m
            'setting_bw': 0,    # MHz
            'real_bw':0,        # MHz
            'update_rate':0,    # ms
            'base_freq':0,      # GHz
            'adc_clkdiv':0,     #
            'down_samp':0,      #
            'ramps':0,          #
        }
        self.config_cmd = []

    def get_config(self):
        profile = open(self.profile)
        profile = json5.load(profile)['EasyR4Config']

        system_cfg_profile = profile['SystemCfg']
        system_cfg_profile['SelfTrigDelay'] = int(np.log2(system_cfg_profile['SelfTrigDelay']).astype(int))
        system_cfg = \
            format((system_cfg_profile['SelfTrigDelay'] << 1) + system_cfg_profile['CL'], 'X') + \
            format(
                (system_cfg_profile['LOG'] << 3) + (system_cfg_profile['FMT'] << 2) + (system_cfg_profile['LED']),
                'X') + \
            format(0, 'X') + \
            format((system_cfg_profile['Protocal'] << 2) + (system_cfg_profile['AGC'] << 1) + (
                        system_cfg_profile['Gain'] >> 2), 'X') + \
            format(((system_cfg_profile['Gain'] & 3) << 2) + (system_cfg_profile['SER1'] << 1) + (
            system_cfg_profile['SER2']), 'X') + \
            format((system_cfg_profile['ERR'] << 3) + (system_cfg_profile['ST'] << 2) + (
                        system_cfg_profile['TL'] << 1) + (system_cfg_profile['C']), 'X') + \
            format((system_cfg_profile['R'] << 3) + (system_cfg_profile['P'] << 2) + (
                        system_cfg_profile['CPL'] << 1) + (system_cfg_profile['RAW']), 'X') + \
            format((system_cfg_profile['SLF'] << 1) + (system_cfg_profile['PRE']), 'X')

        system_cfg = EASYR4_IDENTIFIER_CODE.BEGINNING_CODE + \
                     EASYR4_IDENTIFIER_CODE.SYSTEM_CFG_CODE + \
                     system_cfg + \
                     EASYR4_IDENTIFIER_CODE.END_CODE
        self.config_cmd.append(system_cfg)


        radar_frontend_cfg_profile = profile['RadarFrontendCfg']
        self.wave_cfg['base_freq'] = radar_frontend_cfg_profile['Base Frequency'] * 250 / 10e6

        radar_frontend_cfg = format(radar_frontend_cfg_profile['Base Frequency'], 'X').zfill(8)
        radar_frontend_cfg = EASYR4_IDENTIFIER_CODE.BEGINNING_CODE + \
                             EASYR4_IDENTIFIER_CODE.RADAR_FRONTEND_CFG_CODE + \
                             radar_frontend_cfg + \
                             EASYR4_IDENTIFIER_CODE.END_CODE
        self.config_cmd.append(radar_frontend_cfg)

        pll_cfg_profile = profile['PLLCfg']
        self.wave_cfg['setting_bw'] = pll_cfg_profile['Bandwidth'] * 2
        pll_cfg = format(pll_cfg_profile['Bandwidth'], 'X').zfill(8)
        pll_cfg = EASYR4_IDENTIFIER_CODE.BEGINNING_CODE + \
                  EASYR4_IDENTIFIER_CODE.PLL_CFG_CODE + \
                  pll_cfg + \
                  EASYR4_IDENTIFIER_CODE.END_CODE
        self.config_cmd.append(pll_cfg)

        baseband_cfg_profile = profile['BasebandCfg']
        self.wave_cfg['samples'] = baseband_cfg_profile['Samples']
        self.wave_cfg['adc_clkdiv'] = baseband_cfg_profile['ADC ClkDiv']
        self.wave_cfg['down_samp'] = baseband_cfg_profile['Downsampling']
        self.wave_cfg['ramps'] = baseband_cfg_profile['Ramps']


        baseband_cfg_profile['CFAR Thres'] = baseband_cfg_profile['CFAR Thres'] // 2
        baseband_cfg_profile['FFT Size'] = int(np.log2(baseband_cfg_profile['FFT Size']).astype(int)) - 5
        if not baseband_cfg_profile['Downsampling'] == 0:
            baseband_cfg_profile['Downsampling'] = int(
                np.log2(baseband_cfg_profile['Downsampling']).astype(int)) + 1
        baseband_cfg_profile['Ramps'] = int(np.log2(baseband_cfg_profile['Ramps']).astype(int))
        baseband_cfg_profile['Samples'] = int(np.log2(baseband_cfg_profile['Samples']).astype(int)) - 5

        baseband_cfg = \
            format((baseband_cfg_profile['WIN'] << 3) + (baseband_cfg_profile['FIR'] << 2) + (
                        baseband_cfg_profile['DC'] << 1) + (baseband_cfg_profile['CFAR'] >> 1), 'X') + \
            format(((baseband_cfg_profile['CFAR'] & 1) << 3) + (baseband_cfg_profile['CFAR Thres'] >> 1), 'X') + \
            format(((baseband_cfg_profile['CFAR Thres'] & 1) << 3) + (baseband_cfg_profile['CFAR Size'] >> 1),
                   'X') + \
            format(((baseband_cfg_profile['CFAR Size'] & 1) << 3) + (baseband_cfg_profile['CRAR Grd'] << 1) + (
                        baseband_cfg_profile['Average N'] >> 1), 'X') + \
            format(((baseband_cfg_profile['Average N'] & 1) << 3) + (baseband_cfg_profile['FFT Size']), 'X') + \
            format((baseband_cfg_profile['Downsampling'] << 1) + (baseband_cfg_profile['Ramps'] >> 2), 'X') + \
            format(((baseband_cfg_profile['Ramps'] & 3) << 2) + (baseband_cfg_profile['Samples'] >> 1), 'X') + \
            format(((baseband_cfg_profile['Samples'] & 1) << 3) + (baseband_cfg_profile['ADC ClkDiv']), 'X')

        baseband_cfg = EASYR4_IDENTIFIER_CODE.BEGINNING_CODE + \
                       EASYR4_IDENTIFIER_CODE.BASEBAND_CFG_CODE + \
                       baseband_cfg + \
                       EASYR4_IDENTIFIER_CODE.END_CODE
        self.config_cmd.append(baseband_cfg)


    def send_config(self):
        for cmd in self.config_cmd:
            self.CLIPort.write(cmd.encode())
            time.sleep(0.01)


    def get_system_status(self):

        self.get_config()

        self.CLIPort.write(self.config_cmd[1].encode())
        time.sleep(0.01)

        self.CLIPort.write(self.config_cmd[2].encode())
        time.sleep(0.01)

        self.CLIPort.write(self.config_cmd[3].encode())
        time.sleep(0.01)

        system_cfg = self.config_cmd[0]
        get_status_code = list(system_cfg)
        get_status_code[-5] = '4'
        get_status_code[-4] = '0'
        get_status_code = ''.join(get_status_code)

        self.CLIPort.write(get_status_code.encode())
        self.com_port.flushInput()
        time.sleep(1)
        bb = list(self.com_port.read_all())
        for i in range(len(bb)-23):
            if bb[i] == 170 and bb[i + 1] == 170 and bb[i + 2] == 187 and bb[i + 3] == 204:
                if bb[i + 4] == ord('U'):
                    size = bb[i + 5] * 256 + bb[i + 6]
                    cnt = bb[i + 7] * 256 + bb[i + 8]
                    format = bb[i + 9]
                    gain = bb[i + 10]
                    acc = bb[i + 11] * 256 + bb[i + 12]
                    ramp_time = bb[i + 13] * 256 + bb[i + 14]
                    max_range = bb[i + 15] * 256 + bb[i + 16]
                    real_bw = bb[i + 17] * 256 + bb[i + 18]
                    time_diff = bb[i + 19] * 256 + bb[i + 20]

                    self.wave_cfg['gain'] = gain
                    self.wave_cfg['ramp_time'] = ramp_time
                    self.wave_cfg['max_range'] = max_range
                    self.wave_cfg['real_bw'] = real_bw
                    self.wave_cfg['update_rate'] = time_diff / 100


                    print('Gain:', gain, 'dB')
                    print('Ramp Time:', ramp_time, 'us')
                    print('Max Range:', max_range, 'mm')
                    print('Real BW:', real_bw, 'MHz')
                    print('Updata Rate:', time_diff/100, 'ms')
                break

        self.CLIPort.flushInput()
        self.send_config()


    def sensor_stop(self):
        cmd = '!S110A3002\r\n'
        self.CLIPort.write(cmd.encode())



class easyR4_Read_Thread(threading.Thread):
    def __init__(self, com_port, samples, queue):
        threading.Thread.__init__(self)
        self.file = []
        self.com_port = com_port
        self.bb = []
        self.data_queue = queue
        time.sleep(0.01)

        self.com_port.close()
        self.com_port.open()
        self.com_port.flushInput()
        self.run_flag = True

        self.samples = samples
        # (header + indentifier + cnt + size + data + crlf)
        self.frame_len = (4 + 1 + 2 + 2 + samples * 2 + 2)

        self.first_frame = True

        self.dt = np.dtype(np.uint8)
        self.dt = self.dt.newbyteorder('<')
        self.adc_dt = np.dtype(np.uint16)

        self.adc_frame = np.zeros([2, self.samples], dtype=np.int16)

    def run(self):
        while self.run_flag:

            if self.com_port.in_waiting:
                aa = list(self.com_port.read_all())
                self.bb += aa

                if len(self.bb) >= self.frame_len:

                    for i in range(len(self.bb) - self.frame_len):
                        if self.bb[i] == 170 and self.bb[i+1] == 170 and self.bb[i+2] == 187 and self.bb[i+3] == 204:

                            if self.first_frame == True and self.bb[i+4] == ord('I'):

                                adc_data = self.bb[i + 9:i + self.frame_len - 2]
                                adc_data = np.array(adc_data, dtype=self.dt).view(self.adc_dt)
                                adc_data = adc_data.astype(np.int16) - 2048
                                self.adc_frame[0, :] = adc_data

                                self.bb = self.bb[i + self.frame_len:]
                                self.first_frame = False

                            elif self.first_frame == False:

                                adc_data = self.bb[i + 9:i + self.frame_len - 2]
                                adc_data = np.array(adc_data, dtype=self.dt).view(self.adc_dt)
                                adc_data = adc_data.astype(np.int16) - 2048

                                if self.bb[i+4] == ord('I'):
                                    self.adc_frame[0, :] = adc_data

                                elif self.bb[i+4] == ord('Q'):
                                    self.adc_frame[1, :] = adc_data
                                    self.data_queue.put(self.adc_frame)

                                self.bb = self.bb[i + self.frame_len:]

                            else:
                                self.bb = self.bb[i + self.frame_len:]

                            break

            time.sleep(0.005)


    def start_capture(self):
        self.com_port.flushInput()
        self.run_flag = True


    def close(self):
        self.run_flag = False
