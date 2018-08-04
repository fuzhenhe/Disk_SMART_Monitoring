#!/bin/bash

echo "Start installing S.M.A.R.T monitor service."
install_path="/opt/smartmon/"

#apt-get install smartmontools python

echo "- create dir ${install_path}"
mkdir -p ${install_path}

echo "- copy source code to ${install_path}"
cp -afpR ./src/* ${install_path}

echo "- copy smartmon.conf to /etc/"
cp -afpR ./smartmon.conf /etc/

echo "- copy smartmon.service to /lib/systemd/system/"
cp -afpR ./smartmon.service /lib/systemd/system/

echo "- enable smartmon service"
systemctl enable smartmon.service

echo "- installation completed. The smartmon service will be started automatically at boot."

echo ""
echo "To start, stop or get status of smartmon service by issuing following command"
echo "  systemctl start smartmon.service"
echo "  systemctl stop smartmon.service"
echo "  systemctl status smartmon.service"
echo ""
echo "Please config /etc/smartmon.conf before you start S.M.A.R.T. monitoring service."
