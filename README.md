# disk_smart_monitor_tools
monitor disk smart status and attributes

# check disk list
```
root@CH-CephOsd01:/home/chadmin# fdisk -l 2>/dev/null | grep "^Disk /dev/sd[a-z]: "
Disk /dev/sda: 120.0 GB, 120034123776 bytes
Disk /dev/sdb: 120.0 GB, 120034123776 bytes
Disk /dev/sdd: 120.0 GB, 120034123776 bytes
Disk /dev/sdc: 120.0 GB, 120034123776 bytes
Disk /dev/sde: 120.0 GB, 120034123776 bytes
Disk /dev/sdl: 199.4 GB, 199447543808 bytes
Disk /dev/sdf: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdi: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdj: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdk: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdg: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdh: 8001.6 GB, 8001563222016 bytes
Disk /dev/sdm: 120.0 GB, 120034123776 bytes
```

