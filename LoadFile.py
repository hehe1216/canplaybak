import ControlCAN_lib
from ControlCAN_lib import *


can_obj = ControlCAN_lib.control_can()

class CanFrame:
    def __init__(self, data_format, data_str):
        self.enable = False
        self.time = 0
        self.frame_format = 1
        self.can_id = 0
        self.data = ""
        self.data_len = 0
        self.bus_no = 0;
        self.trans = None
        if data_format == 'txt':
            if self.deal_txt(data_str):
                self.enable = True
        elif data_format == 'asc':
            if self.deal_asc(data_str):
                self.enable = True
        elif data_format == 'csv':
            if self.deal_csv(data_str):
                self.enable = True
        if self.enable:
            print("是否扩展帧：%d %f 0x%x %d %s" % (self.frame_format, self.time, self.can_id, self.data_len, self.data))

    def deal_txt(self, data_str: str):
        data_list = data_str.split()
        self.bus_no = data_list[0]
        try:
            self.can_id = int(data_list[3], 16)
            self.time = float(data_list[2][6:12])
        except ValueError:
            print('deal_txt 非法字符串，已忽略', data_str.replace('\n', ''))
            return False

        if data_list[5] == '扩展帧':
            self.frame_format = 1
        else:
            self.frame_format = 0
        self.data_len = int(data_list[6], 16)
        self.data = "".join(data_list[7:])
        # for i in range(self.data_len, 8, 1):  # 不足8个字节，以0xFF补齐
        #     self.data += 'FF'
        self.trans = ControlCAN_lib.create_vci_obj(can_obj, self.can_id, self.frame_format,
                                                   self.data_len, self.data)
        return True

    def deal_asc(self, data_str: str):
        # print(data_str)
        data_list = data_str.split()
        try:
            self.time = float(data_list[0])
        except ValueError:
            print('deal_asc 非法字符串，已忽略', data_str.replace('\n', ''))
            return False
        # print("time", self.time)
        self.bus_no = int(data_list[1])
        # print("bus no", self.bus_no)
        can_id_str = data_list[2]
        # print("id", can_id_str)
        if can_id_str[-1] == 'x':
            can_id_str = can_id_str[:-1]
        self.can_id = int(can_id_str, 16)
        # print('%x' % self.can_id)
        self.data_len = int(data_list[5])
        for byte in data_list[6:14]:
            self.data += byte
        self.trans = ControlCAN_lib.create_vci_obj(can_obj, self.can_id, self.frame_format,
                                                   self.data_len, self.data)
        # print(self.data)
        return True

    def deal_csv(self, data_str: str):
        data_list = data_str.split(',')
        try:
            self.time = float(data_list[2].split(':')[-1][:-2])
        except ValueError:
            print('deal_csv 非法字符串，已忽略', data_str.replace('\n', ''))
            return False
        # print("time", self.time)
        # self.bus_no = int(data_list[1])
        # print("bus no", self.bus_no)
        can_id_str = data_list[3]
        # print("id", can_id_str)
        self.can_id = int(can_id_str, 16)
        # print('0x%x' % self.can_id)
        if data_list[4] == '扩展帧':
            self.frame_format = 1
        else:
            self.frame_format = 0
        self.data_len = int(data_list[6], 16)
        self.data = data_list[7].replace(' ', '')
        self.trans = ControlCAN_lib.create_vci_obj(can_obj, self.can_id, self.frame_format,
                                                   self.data_len, self.data)
        # print(self.data)
        return True

    def send(self):
        ControlCAN_lib.vci_transmit(can_obj, 3, 0, 0, self.trans, 1)


