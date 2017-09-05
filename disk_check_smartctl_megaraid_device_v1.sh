#!/bin/bash


# argument process
if [[ "$#" -ne 3 ]]; then
    begin_num=0
    last_num=31
    dev_name='sda'
    echo "Usage: first argument as begin number, second argument as last number, third argument as disk name"
    echo " - use default begin number 0, last number 31, device name sda"

else
    begin_num=$1
    last_num=$2
    dev_name=$3
    if [[ "${begin_num}" -gt "${last_num}" ]]; then
        echo "Error, begin number should greater than last number."
        exit
    fi

fi



# smartctl process
for i in `seq ${begin_num} ${last_num}`; do 

    capacity=`smartctl -i -d megaraid,${i} /dev/${dev_name} | grep "User Capacity:"`
    model=`   smartctl -i -d megaraid,${i} /dev/${dev_name} | grep "Device Model:"`
    echo "${i}: ${model}, ${capacity}"

done
