#!/bin/bash

echo "Uninstalling S.M.A.R.T monitor service."
install_path="/opt/smartmon/"

systemctl stop smartmon.service
systemctl disable smartmon.service

rm -rf /opt/smartmon
rm /etc/smartmon.conf
rm /lib/systemd/system/smartmon.service


echo "Uninstall completed."
