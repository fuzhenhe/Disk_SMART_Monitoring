#!/usr/bin/python

import sys, json

# define constant
STATUS_FILE           = "/dev/shm/smartmon_status"
STATUS_ATTR_KEY       = 'smart_attributes_check'
STATUS_HEAL_KEY       = 'smart_health_check'
STATUS_PASSED_KEYWORD = 'PASSED'
STATUS_FAILED_KEYWORD = 'FAILED'
STATUS_UNAVAILABLE    = 'UNAVAILABLE'


# initial variable
status_data       = None
return_code       = 0
passed_list       = list()
failed_list       = list()
unavailable_list  = list()


with open(STATUS_FILE) as fp:
    status_data = json.load(fp)


#print json.dumps(status_data)
#print status_data

if status_data != None:
    for disk_name, disk_data in status_data.iteritems():
        if STATUS_ATTR_KEY in disk_data and STATUS_HEAL_KEY in disk_data:
            if disk_data[STATUS_ATTR_KEY] == STATUS_PASSED_KEYWORD and disk_data[STATUS_HEAL_KEY] == STATUS_PASSED_KEYWORD:
                passed_list.append(disk_name)
            else:
                failed_list.append(disk_name)
                return_code = 1
        else:
            unavailable_list.append(disk_name)
            return_code = 1

else:
    print("Error, fail to open file %s" % STATUS_FILE)
    sys.exit(2)


print("PASSED = %s, FAILED = %s, UNAVAILABLE = %s" %(len(passed_list), len(failed_list), len(unavailable_list)))
print("STATUS PASSED      = %s" % ", ".join(passed_list))
print("STATUS FAILED      = %s" % ", ".join(failed_list))
print("STATUS UNAVAILABLE = %s" % ", ".join(unavailable_list))
    
sys.exit(return_code)

