import os
import sys
import threading
from libs import ControlCAN_lib
from libs.ControlCAN_lib import *
from libs.LoadFile import CanFrame
from libs.LoadFile import can_obj

rev = can_obj.TVCI_CAN_OBJ()


class CanPlayBack:
    def __init__(self, baud_rate=1):
        self.recv_thread = None
        self.loop_enable = 0
        self.target = 0
        self.index = 0
        self.start_time = 0
        self.last_time = 0
        self.file_data_list = []
        self.switch_list = None
        self.init_obj = ControlCAN_lib.create_init_config(can_obj, baud_rate)

    def open_device(self):
        if ControlCAN_lib.vci_open_device(can_obj, 3, 0, 0) == 1:
            print("打开设备成功")
        else:
            print('打开设备失败，退出程序')
            self.end()

        if ControlCAN_lib.vci_init_can(can_obj, 3, 0, 0, self.init_obj) == 1:
            print("初始化成功")
        else:
            print('初始化失败，退出程序')
            self.end()

        if ControlCAN_lib.vci_start_can(can_obj, 3, 0, 0) == 1:
            print('启动设备成功')
        else:
            print('启动设备失败，退出程序')
            self.end()

        if ControlCAN_lib.vci_clear_buffer(can_obj, 3, 0, 0) == 1:
            print('清空缓存区成功')
        else:
            print('清空缓存区失败，退出程序')
            self.end()
        time.sleep(1)
        self.recv_thread = threading.Thread(target=self.recv_run)
        pass

    def load_file(self):
        print('请选择需要回放的文件，以空格相隔')
        idx = 0
        file_dir = {}
        self.file_data_list = []
        for file in os.listdir('../doc'):
            print(idx, file)
            file_dir[idx] = file
            idx += 1
        print(file_dir)
        switch_str = input('请输入您的选择：')
        self.switch_list = switch_str.split()
        for switch in self.switch_list:
            try:
                self.do_load_file(file_dir[int(switch)])
            except KeyError:
                print('未知选项 %d ，已忽略' % int(switch))
        while True:
            try:
                self.loop_enable = int(input('请选择是否循环回放（0/1）：'))
            except ValueError:
                pass
            else:
                if self.loop_enable == 0:
                    print('循环回放关闭')
                    break
                elif self.loop_enable == 1:
                    print('循环回放开启')
                    break
                else:
                    print('输入错误，请输入0或1')
                    pass
        pass

    def do_load_file(self, file_name: str):
        full_file_name = '../doc/' + file_name
        file_format = full_file_name.split('.')[-1]
        # print(file_format)
        can_list = []
        file_p = open(full_file_name, mode='r')
        for lines in file_p:
            frame_obj = CanFrame(file_format, lines)
            can_list.append(frame_obj)
            pass
        self.file_data_list.append(can_list)
        pass

    def print_file(self):
        print('file_data_list len:', len(self.file_data_list))
        for can_list in self.file_data_list:
            print('can_list len:', len(can_list))
            for can_data in can_list:
                if can_data.enable:
                    print("%x %s" % (can_data.can_id, can_data.data))

    def run(self):

        if self.loop_enable:
            while True:
                self.start()
        else:
            self.start()

    def recv_run(self):
        curr_time_s = time.localtime(time.time())
        fp = open('总线报文%04d/%02d/%02d_%02d;%02d;%02d.txt' % (curr_time_s.tm_year, curr_time_s.tm_mon,
                                                                 curr_time_s.tm_mday, curr_time_s.tm_hour,
                                                                 curr_time_s.tm_min, curr_time_s.tm_sec), mode='w')
        res = ControlCAN_lib.vci_receive(can_obj, 3, 0, 0, rev, 1, 2000)
        if res == 1:
            curr_time_s = time.localtime(time.time())
            time_s = '%04d/%02d/%02d %02d:%02d:%02d.txt' % (curr_time_s.tm_year, curr_time_s.tm_mon,
                                                            curr_time_s.tm_mday, curr_time_s.tm_hour,
                                                            curr_time_s.tm_min, curr_time_s.tm_sec)
            id_hex = "0x%08X" % rev.ID
            data_hex = " ".join(list(rev.Data))
            fp.write("%s %s %s" % (time_s, id_hex, data_hex))

        pass

    def start(self):
        try:
            print('file_data_list len:', len(self.file_data_list))
            for can_list in self.file_data_list:
                print('can_list len:', len(can_list))
                if len(can_list) > 0:

                    self.index = 0
                    self.target = len(can_list)
                    start = time.time()
                    time_s = time.localtime(start)
                    print('start time %04d/%02d/%02d %02d:%02d:%02d' % (time_s.tm_year, time_s.tm_mon, time_s.tm_mday,
                                                                        time_s.tm_hour, time_s.tm_min, time_s.tm_sec))
                    while self.index < self.target:
                        curr_time = time.time()
                        if not can_list[self.index].enable:
                            self.index += 1
                        else:
                            if self.start_time == 0:
                                self.start_time = curr_time - can_list[self.index].time
                                print("%d 0x%08x %s" % (self.index, can_list[self.index].can_id, can_list[self.index].data))
                                can_list[self.index].send()
                                self.index += 1
                            elif self.start_time + can_list[self.index].time <= curr_time:
                                print("%d 0x%08x %s" % (self.index, can_list[self.index].can_id, can_list[self.index].data))
                                can_list[self.index].send()
                                self.index += 1
                        # time.sleep(0.5)
                        # res = ControlCAN_lib.vci_receive(can_obj, 3, 0, 0, rev, 1, 2000)
                        # print(res)
                        # ControlCAN_lib.vci_transmit(can_obj, 3, 0, 0, trans, 100)
                    self.start_time = 0
                    end = time.time()
                    time_s = time.localtime(end)
                    print('end time %04d/%02d/%02d %02d:%02d:%02d' % (time_s.tm_year, time_s.tm_mon, time_s.tm_mday,
                                                                      time_s.tm_hour, time_s.tm_min, time_s.tm_sec))
                    print('spend time:', end - start)

        except KeyboardInterrupt:
            print("关闭设备%d" % (ControlCAN_lib.vci_close_device(can_obj, 3, 0)))
        pass

    @staticmethod
    def end():
        print("关闭设备%d" % (ControlCAN_lib.vci_close_device(can_obj, 3, 0)))
        sys.exit(0)


if __name__ == '__main__':
    CAN500k = 0
    CAN250k = 1
    obj = CanPlayBack(CAN250k)
    obj.open_device()
    obj.load_file()
    obj.run()
    input("Press Enter to exit...")


