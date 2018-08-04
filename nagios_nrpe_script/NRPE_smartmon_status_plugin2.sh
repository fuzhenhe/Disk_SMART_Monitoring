
#!/bin/bash

smartmon_status="/run/shm/smartmon_status"
passed_keyword='PASSED'
failed_keyword='FAILED'
smart_attr_key='smart_attributes_check'
smart_heal_key='smart_health_check'
status_result='Unknown'
return_code=0

declare -A DISK_STATUS


# convert json string to bash associate array
if [[ "$#" -ne 1 ]]; then
    echo "Please give an device name as argument."
    exit 1 
else
    disk_name=$1

    python_script="import sys,json; data=json.loads(sys.stdin.read()); print json.dumps(data[\"$disk_name\"])"

    disk_raw_data=`cat $smartmon_status | python -c "$python_script"`
    
    disk_data1=${disk_raw_data//[\{\}]/}
    disk_data2=${disk_data1//\"/} 
    disk_info=`echo $disk_data2 | sed -e 's/,/\n/g' | sed -e 's/ //g'`

    readarray -t disk_array <<<"$disk_info"

    for item in "${disk_array[@]}"
    do
        key=${item%%:*}
        value=${item##*:}
        DISK_STATUS[${key}]=${value}
    done
fi


# check status of disk
if [[ -z "${DISK_STATUS[${smart_attr_key}]}" ]] && [[ -z "${DISK_STATUS[${smart_heal_key}]}" ]]; then
    status_result="No S.M.A.R.T. available!"
    return_code=1
else
    if [[ "${DISK_STATUS[${smart_attr_key}]}" == "${passed_keyword}" ]] && [[ "${DISK_STATUS[${smart_heal_key}]}" == "${passed_keyword}" ]]; then
        status_result=${passed_keyword}
    else
        status_result=${failed_keyword}
        return_code=1
    fi
fi


# output status of disk
echo ${status_result}

# output detail of disk 
for status_key in "${!DISK_STATUS[@]}"
do
    echo ${status_key} = ${DISK_STATUS[${status_key}]}
done

# exit with return code
exit ${return_code}

