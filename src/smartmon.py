#!/usr/bin/python
# Author: Yu-Jung Cheng
# Version: 1.3


import os, sys, time, json, socket, traceback, subprocess, thread
import logging.handlers

from ConfigParser import ConfigParser
from daemon import Daemon

from lib import Disk
from lib import Ceph


# Disk S.M.A.R.T. Monitoring Class
class SMARTMON(Daemon):

    SMART_CMD       = 'smartctl'
    CONFIG_PATH     = '/etc/smartmon.conf'
    CONFIG_IGNORE   = False
    DEFAULT_SECTION = 'default'
    LOGGER_NAME     = 'smartmon'
    LOG_DIRECTORY   = '/var/log/smartmon'
    LOG_MAXBYTES    = 209715200             # 200MB
    LOG_BACKUPCOUNT = 10
    LOG_DELAY       = 1
    LOG_LEVEL       = 'DEBUG'
    LOG_FORMAT      = '[%(asctime)s] [%(levelname)s] %(message)s'

    def run(self, smart_cmd=SMART_CMD,
                  config_path=CONFIG_PATH,
                  config_ignore=CONFIG_IGNORE,
                  default_section=DEFAULT_SECTION,
                  logger_name=LOGGER_NAME,
                  log_directory=LOG_DIRECTORY,
                  log_maxbytes=LOG_MAXBYTES,
                  log_backupcount=LOG_BACKUPCOUNT,
                  log_delay=LOG_DELAY,
                  log_level=LOG_LEVEL,
                  log_format=LOG_FORMAT):

        # ----------------------------------------
        # initialize smartmon daemon logging
        # ----------------------------------------
        os.system("mkdir -p %s" % log_directory)
        daemon_log_file = logger_name + ".log"
        daemon_log_path = os.path.join(log_directory,
                                       daemon_log_file)

        # create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # create handler for rotating file
        log_handler = logging.handlers.RotatingFileHandler(
                      daemon_log_path,
                      maxBytes=log_maxbytes,
                      backupCount=log_backupcount,
                      delay=log_delay)
        log_handler.setLevel(log_level)

        # create formatter
        formatter = logging.Formatter(log_format)

        # set formatter to handler and add handler to logger
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)

        # assign the logger to self.logger
        self.logger = logger

        # logging daemon start message.
        uptime_proc = subprocess.Popen("uptime --since",
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        uptime_out, err = uptime_proc.communicate()

        if len(uptime_out) == 0:
            uptime_out = err

        daemon_info_msg = "pid=%s, ignore config file=%s, " \
                          "system uptime since=%s" % (os.getpid(),
                                                      config_ignore,
                                                      uptime_out.strip())
        daemon_start_msg = "Start S.M.A.R.T. Monitor Daemon Logging. " \
                           "(%s)" % daemon_info_msg

        self.logger.info(daemon_start_msg)

        # ----------------------------------------
        # check smartctl command installed or not
        # ----------------------------------------
        # get return code
        smartctl_exist = subprocess.call("type %s" % smart_cmd, shell=True,
                                                                stdout=subprocess.PIPE,
                                                                stderr=subprocess.PIPE)
        if smartctl_exist != 0:
            self.logger.error("The smartctl command is not found " \
                              "or installed. Daemon stop!")
            sys.exit(2)

        # ----------------------------------------
        # parser SMART log setting from /etc/smartmon.conf
        # ----------------------------------------

        # set default values of SMART checking parameters
        self.logger.info("aaaa")
        try:
            disks               = Disk.list_device()
        except Exception as e:
            self.logger.info(e)
            exit(0)
        self.logger.info("bbbb")
        check_level         = 'DEBUG'
        passed_keyword      = 'PASSED'
        interval            = 60
        rotate_size         = 20971520
        rotate_count        = 10
        check_file          = os.path.join(log_directory, 'check.log')
        error_file          = os.path.join(log_directory, 'error.log')
        status_file         = None
        critical_attributes = [5, 10, 183, 184, 187, 196, 197,198, 201]  # critical id to detect potential failure of disk
        smart_xall          = False
        critical_threshold  = 0 # for attributes check
        system_cmds         = []
        system_interval     = 60

        if not config_ignore:
            try:
                cfg = ConfigParser()
                with open(config_path, 'rb') as fp:
                    cfg.readfp(fp, config_path)

                section = default_section
                hostname = socket.gethostname()

                if cfg.has_section(hostname):
                    section = hostname
                    self.logger.info("Read section %s from config file." % section)
                else:
                    self.logger.info("Read default section from config file. (%s)" % section)
                    if not cfg.has_section(section):
                        config_ignore = True
                        self.logger.warn("The default section not found in config file. Set ignore config to %s." % config_ignore)

            except Exception as e:
                self.logger.error("Read config file error! %s, Deamon stop!" % e)
                exc_type,exc_value,exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
                sys.exit(2)

        # to do, reuse this function when checking each option
        def check_option(cfg, section, option):
            if cfg.has_option(section, 'smart_check_disks'):
                disks_str = cfg.get(section, 'smart_check_disks')
                if disks_str == None:
                    self.logger.warn("No disks configured, use detected disk devices.")
                else:
                    disks = disks_str.replace(' ', '').split(',')
            else:
                self.logger.warn("No smart_check_disks option found in config file.")
            self.logger.info("Set SMART monitor to monitor disks %s" % (disks))

        if not config_ignore:
            try:
                if cfg.has_option(section, 'smart_check_disks'):
                    disks_str = cfg.get(section, 'smart_check_disks')
                    if disks_str == None:
                        self.logger.warn("No disks configured, use detected disk devices.")
                    else:
                        disks = disks_str.replace(' ', '').split(',')
                else:
                    self.logger.warn("No smart_check_disks option found in config file.")
                self.logger.info("Set SMART monitor to monitor disks %s" % (disks))

                if cfg.has_option(section, 'smart_log_level'):
                    level_str = cfg.get(section, 'smart_log_level')
                    if level_str in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        check_level = level_str
                    else:
                        self.logger.warn("Invalid smart_log_level value %s." % (level_str))
                else:
                    self.logger.warn("No smart_log_level option found in config file.")
                self.logger.info("Set SMART monitor log level to %s." % (check_level))

                if cfg.has_option(section, 'smart_passed_keyword'):
                    passed_keyword = cfg.get(section, 'smart_passed_keyword')
                else:
                    self.logger.warn("No smart_passed_keyword option found in config file.")
                self.logger.info("Set SMART monitor health status keyword to %s." % (passed_keyword))

                if cfg.has_option(section, 'smart_check_interval'):
                    interval_str = cfg.get(section, 'smart_check_interval')
                    if interval_str.isdigit():
                        if int(interval_str) < 1:
                            self.logger.error("Check SMART interval must at least 1 second.")
                        else:
                            interval = int(interval_str)
                    else:
                        self.logger.warn("Invalid check_interval value %s." % (interval_str))
                else:
                    self.logger.warn("No smart_check_interval option found in config file.")
                self.logger.info("Set SMART monitor interval to %s seconds." % (interval))

                if cfg.has_option(section, 'smart_file_rotate_size'):
                    size_str = cfg.get(section, 'smart_file_rotate_size')
                    if size_str.isdigit():
                        rotate_size = int(size_str)
                    else:
                        self.logger.warn("Invalid smart_file_rotate_size value %s." % (size_str))
                else:
                    self.logger.warn("No smart_file_rotate_size option found in config file")
                self.logger.info("Set SMART monitor rotating size of log file to %s bytes." % (rotate_size))

                if cfg.has_option(section, 'smart_file_rotate_count'):
                    count_str = cfg.get(section, 'smart_file_rotate_count')
                    if count_str.isdigit():
                        rotate_count = int(count_str)
                    else:
                         self.logger.warn("Invalid smart_file_rotate_count value %s." % (count_str))
                else:
                    self.logger.warn("No smart_file_rotate_count option found in config file")
                self.logger.info("Set SMART monitor file rotating count to %s" % (rotate_count))

                if cfg.has_option(section, 'smart_check_file'):
                    check_str = cfg.get(section, 'smart_check_file')
                    if os.path.isabs(check_str):
                        os.system("mkdir -p %s" % os.path.dirname(check_str))
                        check_file = check_str
                    else:
                        self.logger.warn("Invalid smart_check_file value %s" % (check_str))
                else:
                    self.logger.warn("No smart_check_file option found in config file")
                self.logger.info("Set SMART monitor check file to %s" % (check_file))

                if cfg.has_option(section, 'smart_error_file'):
                    error_str = cfg.get(section, 'smart_error_file')
                    if os.path.isabs(error_str):
                        os.system("mkdir -p %s" % os.path.dirname(error_str))
                        error_file = error_str
                    else:
                        self.logger.warn("Invalid smart_error_file value %s" % (error_str))
                else:
                    self.logger.warn("No smart_error_file option found in config file")
                self.logger.info("Set SMART monitor error file to %s" % (error_file))

                if cfg.has_option(section, 'smart_status_file'):
                    status_str = cfg.get(section, 'smart_status_file')
                    if os.path.isabs(status_str):
                        os.system("mkdir -p %s" % os.path.dirname(status_str))
                        status_file = status_str
                    else:
                        self.logger.warn("Invalid smart_status_file value %s" % (status_str))
                else:
                    self.logger.warn("No smart_status_file option found in config file")
                self.logger.info("Set SMART monitor status file to %s" % (status_file))

                if cfg.has_option(section, 'smart_critical_attribute_id'):
                    attribute_str = cfg.get(section, 'smart_critical_attribute_id')
                    if attribute_str == None:
                        critical_attributes = []
                    else:
                        critical_attributes = attribute_str.replace(' ', '').split(',')
                else:
                    self.logger.warn("No smart_critical_attribute_id option found in config file")
                self.logger.info("Set SMART monitor critical attributes to %s" % (critical_attributes))

                if cfg.has_option(section, 'smart_critical_threshold'):
                    threshold_str = cfg.get(section, 'smart_critical_threshold')
                    if threshold_str.isdigit():
                        critical_threshold = int(threshold_str)
                    elif threshold_str != "":
                        critical_threshold = {}
                        critical_thresholds = threshold_str.replace(' ', '').split(',')
                        for threshold in critical_thresholds:
                            if ':' in threshold:
                                threshold_set = threshold.split(':')
                                threshold_attr = threshold_set[0]
                                threshold_value = threshold_set[1]
                                critical_threshold[threshold_attr] = threshold_value
                            else:
                                self.logger.warn("Invalid smart_critical_threshold value %s." % (threshold_str))
                else:
                    self.logger.warn("No smart_critical_threshold option found in config file")
                self.logger.info("Set SMART monitor critical attribute threshold to %s" % (critical_threshold))

                if cfg.has_option(section, 'smart_xall_info'):
                    smart_xall_str = cfg.get(section, 'smart_xall_info')
                    if smart_xall_str == 'True':
                        smart_xall = True
                else:
                    self.logger.warn("No smart_xall_info option found in config file.")
                self.logger.info("Set SMART monitor xall output logging to %s." % (smart_xall))

                if cfg.has_option(section, 'smart_system_run_interval'):
                    system_run_interval_str = cfg.get(section, 'smart_system_run_interval')
                    if system_run_interval_str.isdigit():
                        if int(system_run_interval_str) < 1:
                            self.logger.warn("run system command interval must at least 1 second.")
                        else:
                            system_interval = int(system_run_interval_str)
                self.logger.info("Set SMART run system command interval to %s seconds." % system_interval)

                if cfg.has_option(section, 'smart_system_cmd'):
                    system_cmd_str = cfg.get(section, 'smart_system_cmd')
                    if ", " in system_cmd_str:
                        system_cmds = system_cmd_str.split(' , ')
                    else:
                        system_cmds.append(system_cmd_str)
                else:
                    self.logger.warn("No smart_system_cmd option found in config file.")
                self.logger.info("Set SMART run system command to %s" % (system_cmds))

            except Exception as e:
                self.logger.error("Parser config file error! %s" % e)
                exc_type,exc_value,exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
                #self.logger.error("Parser config file error! %s, %s, %s" % exc_type, exc_value, exc_traceback)
                sys.exit(2)

        else:

            #todo: change to better code and add collect system info option
            initial_values = "Use default config:\n"\
                             "Disks=%s\nCheck Level=%s\nPasswd Keyword=%s\nInterval=%s\nRotate Size=%s\n"\
                             "Rotate Count=%s\nCheck File=%s\nError File=%s\nStatus File=%s\n"\
                             "CriticalAttributes=%s\nCritical Threshold=%s\nXALL=%s" % (
                             disks, check_level, passed_keyword, interval, rotate_size, rotate_count,
                             check_file, error_file, status_file, critical_attributes, critical_threshold,
                             smart_xall)

            space_padding = "\n" + " " * 34
            default_config = initial_values.replace("\n", space_padding)
            self.logger.debug(default_config)

        # ----------------------------------------
        # run system command thread
        # ----------------------------------------
        try:
            if len(system_cmds) >= 1:
                self.logger.info("Create new thread for monitoring system status.")
                tid = thread.start_new_thread(self.run_system_command, (system_cmds, interval))
        except Exception as e:
            self.logger.error("Error, unable to start system command thread. %s" % e)

        # ----------------------------------------
        # initialize SMART logging
        # ----------------------------------------
        try:
            check_logger = logging.getLogger('check_logger')
            check_logger.setLevel(logging.DEBUG)
            error_logger = logging.getLogger('error_logger')
            error_logger.setLevel(logging.DEBUG)

            check_log_handler = logging.handlers.RotatingFileHandler(
                                check_file,
                                maxBytes=rotate_size,
                                backupCount=rotate_count)
            check_log_handler.setLevel(check_level)

            error_log_handler = logging.handlers.RotatingFileHandler(
                                error_file,
                                maxBytes=rotate_size,
                                backupCount=rotate_count)
            error_log_handler.setLevel(check_level)

            check_formatter = logging.Formatter(formatter)
            error_formatter = logging.Formatter(formatter)

            check_log_handler.setFormatter(formatter)
            error_log_handler.setFormatter(formatter)

            check_logger.addHandler(check_log_handler)
            error_logger.addHandler(error_log_handler)

            self.logger.info("SMART logger initialized.")

        except Exception as e:
            self.logger.error("Initialize SMART logging error! %s" % e)
            exc_type,exc_value,exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

        # ----------------------------------------
        # start SMART monitoring
        # ----------------------------------------
        monitor_counter = 0
        while True:
            # monitor disk s.m.a.r.t. status
            try:
                # for output status data to specific file
                all_disk_info = {}
                check_message = ""
                error_message = ""
                status_verify = True
                attribute_verify = True

                for disk in disks:

                    disk_type = "auto"  # default type in smartctl

                    if ":" in disk:
                        disk_options = disk.split(':')  # name:type:number

                        disk_name = disk_options[0]

                        disk_options_count =  len(disk_options)
                        if disk_options_count == 2:
                            disk_type = disk_options[1]
                        elif disk_options_count == 3:
                            disk_type = "%s,%s" % (disk_options[1], disk_options[2])
                    else:
                        disk_name = disk

                    if not os.path.exists('/dev/'+disk_name):
                        self.logger.warn("The disk device %s is not found in /dev/ directory." % disk_name)
                        continue

                    disk_info = {}
                    disk_info['check_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    disk_info['osd_id'] = Ceph.get_osd_id(disk_name)  # for ceph storage
                    disk_info['capacity'] = Disk.get_capacity(disk_name)

                    smart_enabled = Disk.is_smart_supported(disk_name, disk_type)
                    if not smart_enabled:
                        self.logger.warn("The SMART is not supported or enabled on disk '%s'." % disk)
                        all_disk_info[disk] = disk_info
                        continue

                    critical_status_check = passed_keyword
                    status, detail = Disk.get_smart_detail(disk_name, disk_type)

                    if status == None:
                        self.logger.error("Failed to get health status of %s, return status %s." % (disk, status))
                        status_verify = False
                        status = "Error"

                    if detail == {}:
                        self.logger.error("Failed to get smart attributes of %s, return attributes %s." % (disk, detail))
                        attribute_verify = False
                        critical_status_check = "Error"
                    else:
                        # check some SMART attributes, if those attribute value greater than 0, trigger logging
                        for attribute_id in critical_attributes:
                            if int(attribute_id) in detail:

                                attribute_value = detail[int(attribute_id)]
                                if attribute_value.isdigit():
                                    if isinstance(critical_threshold, dict) and str(attribute_id) in critical_threshold:
                                        attr_critical_shreshold = int(critical_threshold[attribute_id])
                                    else:
                                        attr_critical_shreshold = int(critical_threshold)

                                    if int(attribute_value) > attr_critical_shreshold:
                                        critical_status_check = "FAILED"
                                        self.logger.warn("Detected critical status, attributes id %s = %s on %s" % (attribute_id, attribute_value, disk))
                                else:
                                    self.logger.error("Invalid raw data in SMART attribute id %s, (Not an integer)" % attribute_value)

                    check_message = "[Disk_Name=%s, SMART_Health_Check=%s, Critical_Attribute_Check=%s" % (disk, status, critical_status_check)

                    # if failed to get both status and attribute value, skip check or error logging.
                    if status_verify != False and attribute_verify != False:
                        if status != passed_keyword or critical_status_check != passed_keyword:
                            error_message = check_message + ", SMART_Value=%s]" % (detail)
                            error_logger.critical(error_message)

                            if smart_xall:
                                disk_smart_xall_output = Disk.get_smart_xall(disk_name, disk_type)
                                error_logger.debug('Prints all SMART and non-SMART information about the device.\n'+disk_smart_xall_output)
                        else:
                            check_message += "]"
                            check_logger.info(check_message)

                    disk_info['smart_health_check'] = status
                    disk_info['smart_attributes_check'] = critical_status_check
                    all_disk_info[disk] = disk_info

                # write all disk status to file
                if status_file != None:
                    with open(status_file, 'w') as fp:
                        fp.write(json.dumps(all_disk_info))

                        monitor_counter += 1
                        self.logger.info("Write disk status to %s, count=%s" % (status_file, monitor_counter))

            except Exception as e:
                self.logger.error("Error occour during disk SMART check! %s" % e)
                exc_type,exc_value,exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

            time.sleep(interval)

    def run_system_command(self, system_cmds, interval):
        self.logger.info("Running system command, number of command=%s, interval=%s." % (len(system_cmds), interval))

        last_cmd_output = dict()
        while True:
            try:
                cmd_counter = 0
                space_padding = "\n" + " " * 33
                for cmd in system_cmds:
                    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = process.communicate()

                    cmd_counter += 1
                    if len(err) != 0:
                        self.logger.error("System command '%s' has error output, err = %s" % (cmd, err))
                    if len(out) == 0:
                        self.logger.error("System command '%s' has no standard output." % cmd)
                    else:

                        if str(cmd_counter) in last_cmd_output:
                            if last_cmd_output[str(cmd_counter)] == out:
                                # if the output is the same to the previous output, skip this output log.
                                #self.logger.info("Output of system command '%s' is not changed" % cmd)
                                continue

                        msg = "run system command '%s'\n" % cmd + out.strip()
                        log_msg = msg.replace("\n", space_padding)
                        self.logger.info("%s" % log_msg)

                    last_cmd_output[str(cmd_counter)] = out

            except Exception as e:
                self.logger.error("Error, fail to run system command! %s" % e)

            time.sleep(interval)


if __name__ == "__main__":

    pid_file = '/var/run/smartmon.pid'

    daemon = SMARTMON(pid_file)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            print("stopping daemon!!!")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknow Operation!"
            sys.exit(2)

    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
