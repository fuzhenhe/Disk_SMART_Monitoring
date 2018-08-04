#!/usr/bin/python
# Author: Yu-Jung Cheng
# Version: 1.3

import os, re, subprocess


class Disk:
    @staticmethod
    def list_device(dev_prefix='sd'):
        ''' The /sys/class/ directory contains representations
        of all device that is registered with the
        kernel. A device class describes a functional
        type of device.
            Disk naming: sd, hd, fd
        '''
        try:
            class_path='/sys/class/block/'
            device_list = list()
            file_name_list = os.listdir(class_path)
            for file_name in file_name_list:
                if file_name.startswith(dev_prefix):
                    if file_name[-1].isdigit():
                        continue
                    real_path = os.readlink(class_path + file_name)
                    if real_path.find("usb") > 0:
                        continue
                    device_list.append(file_name)
            return device_list
        except Exception as e:
            print("Error, %s." % e)

    @staticmethod
    def get_capacity(device_name, unit='MB'):
        ''' unit: MB, GB, PB '''
        class_path='/sys/class/block/'
        path = os.path.join(class_path, device_name, "size")
        with open(path, "r") as f:
            sector_count = f.readline()

        if str(sector_count).isdigit():
            total_bytes = int(sector_count) * 512
            if unit == 'MB':
                return total_bytes / 1048576
            elif unit == 'GB':
                return total_bytes / 1073741824
            elif unit == 'PB':
                return total_bytes / 1099511627776

    @staticmethod
    def is_smart_supported(device_name, device_type="auto"):
        smart_is_available = False
        smart_is_enabled = False

        if not str(device_name).startswith("/dev/"):
            device_name = "/dev/" + device_name

        smartctl_cmd = ['smartctl', '-i', '-d', device_type, device_name]

        process = subprocess.Popen(smartctl_cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        lines = out.split("\n")
        pattern0 = re.compile("SMART support is:")
        pattern1 = re.compile("Available - device has SMART capability.")
        pattern2 = re.compile("Enabled")

        for line in lines:
            result0 = pattern0.search(line)
            result1 = pattern1.search(line)
            result2 = pattern2.search(line)
            if not result0 == None:
                if not result1 == None:
                    smart_is_available = True
                if not result2 == None:
                    smart_is_enabled = True

        if smart_is_available and smart_is_enabled:
            return True
        return False

    @staticmethod
    def get_smart_detail(device_name, device_type="auto"):
        found = False
        health_result = None
        smart = dict()

        if not str(device_name).startswith("/dev/"):
            device_name = "/dev/" + device_name

        smartctl_cmd = ['smartctl', '-HA', '-d', device_type, device_name]

        process = subprocess.Popen(smartctl_cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        lines = out.split("\n")
        pattern = re.compile("test result: +([A-Za-z]+)")
        pattern2 = re.compile("(^[0-9 ]{1,3})")
        for line in lines:
            if found == True:
                result = pattern2.search(line)
                if not result == None:
                    x = result.group(1)
                    x = x.strip()
                    if len(x) > 0:
                        id = int(result.group(1))
                        value = line[87:]
                        smart[id] = value
            else:
                result = pattern.search(line)
                if not result == None:
                    found = True
                    health_result = result.group(1)

        return health_result, smart

    @staticmethod
    def get_smart_xall(device_name, device_type="auto"):
        out = None

        if not str(device_name).startswith("/dev/"):
            device_name = "/dev/" + device_name

        smartctl_cmd = ['smartctl', '--xall', '-d', device_type, device_name]

        process = subprocess.Popen(smartctl_cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        return out


class System:
    @staticmethod
    def exec_cmd(cmd, shell=False,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE):
        process = subprocess.Popen(cmd,
                                   shell=shell,
                                   stdout=stdout,
                                   stderr=stderr)
        out, err = process.communicate()
        if len(err) != 0:
            return None
        if len(out) == 0:
            return None
        return out

    @staticmethod
    def get_uptime(option='--since'):
        system_cmd = ['uptime', option]
        output = System.exec_cmd(system_cmd)
        return output.strip()

    @staticmethod
    def get_diskstats(path='/proc/diskstats'):
        system_cmd = ['grep', '-v', 'loop', path]
        return SysFunc.exec_cmd(system_cmd)

    @staticmethod
    def get_sysblock(path="/sys/block/sd*"):
        system_cmd = "ls -l %s" % path
        return SysFunc.exec_cmd(system_cmd, shell=True)

    @staticmethod
    def get_mounts(path='/proc/mounts', grep_key='/dev/sd'):
        system_cmd = "cat %s | %s " % (path, grep_key)
        return SysFunc.exec_cmd(system_cmd, shell=True)

    @staticmethod
    def get_last_x(grep_key='shutdown\|reboot'):
        system_cmd = "last -x | grep " + grep_key
        return SysFunc.exec_cmd(system_cmd, shell=True)


class Ceph():
    @staticmethod
    def get_osd_id(device_name):
        if not str(device_name).startswith("/dev/"):
            device_name = "/dev/" + device_name
        with open("/proc/mounts", "r") as f:
            contents = f.readlines()
        for line in contents:
            if line.find("/var/lib/ceph/osd/ceph") > 0:
                if line.startswith(device_name):
                    parms = line.split(" ")
                    paramss = parms[1].split("-")
                    return paramss[1]
        return 'Unknow'

    def get_status():
        return
