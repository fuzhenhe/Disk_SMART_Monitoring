#!/bin/bash

smartmon_status="/run/shm/smartmon_status"
disk_name=$1

if [[ "$#" -ne 1 ]]; then
    eceho "Please give an device name as argument."
else
    python_script="import sys,json; data=json.loads(sys.stdin.read()); print json.dumps(data[\"$disk_name\"])"
    cat $smartmon_status | python -c "$python_script"
fi

