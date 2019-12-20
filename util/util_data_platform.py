# coding=utf-8
import random
import util_utl

show_platform_psustatus = " " \
                          "PSU    Status\n" \
                          "-----  --------\n" \
                          "PSU 1  OK\n" \
                          "PSU 2  OK\n"

show_environment = " " \
                   "coretemp-isa-0000\n" \
                   "Adapter: ISA adapter\n" \
                   "Physical id 0:  +40.0 C  (high = +82.0 C, crit = +104.0 C)\n" \
                   "Core 0:         +40.0 C  (high = +82.0 C, crit = +104.0 C)\n" \
                   "Core 1:         +40.0 C  (high = +82.0 C, crit = +104.0 C)\n" \
                   "Core 2:         +40.0 C  (high = +82.0 C, crit = +104.0 C)\n" \
                   "Core 3:         +40.0 C  (high = +82.0 C, crit = +104.0 C)\n" \
                   "as6712_54x_fan-i2c-1-63\n" \
                   "_fan-i2c-1-63\n" \
                   "Adapter: i2c-0-mux (chan_id 0)\n" \
                   "front fan 1: 11700 RPM\n" \
                   "front fan 2: 11850 RPM\n" \
                   "front fan 3: 11700 RPM\n" \
                   "front fan 4: 11700 RPM\n" \
                   "front fan 5: 11700 RPM\n" \
                   "rear fan 1:  9900 RPM\n" \
                   "rear fan 2:  9750 RPM\n" \
                   "rear fan 3:  9900 RPM\n" \
                   "rear fan 4:  9750 RPM\n" \
                   "rear fan 5:  9900 RPM\n" \
                   "lm75-i2c-17-4b\n" \
                   "Adapter: i2c-1-mux (chan_id 0)\n" \
                   "temp1:        +32.5 C  (high = +80.0 C, hyst = +75.0 C)\n" \
                   "lm75-i2c-19-49\n" \
                   "Adapter: i2c-1-mux (chan_id 2)\n" \
                   "temp2:        +33.5 C  (high = +80.0 C, hyst = +75.0 C)\n" \
                   "lm75-i2c-20-4a\n" \
                   "Adapter: i2c-1-mux (chan_id 3)\n" \
                   "temp3:        +30.5 C  (high = +80.0 C, hyst = +75.0 C)\n"

# "Serial Number        0x23  14 571254X1625041\n"
# "Base MAC Address     0x24   6 02:42:ac:11:00:06\n"
show_platform_syseeprom = " " \
                          "TlvInfo Header:\n" \
                          "  Id String:    TlvInfo\n" \
                          "   Version:      1\n" \
                          "   Total Length: 527\n" \
                          "TLV Name             Code Len Value\n" \
                          "-------------------- ---- --- -----\n" \
                          "Product Name         0x21  15 as6712\n" \
                          "Part Number          0x22  20 as6712-54x\n" \
                          "Serial Number        0x23  14 671254X16%s\n" \
                          "Base MAC Address     0x24   6 %s\n" \
                          "Manufacture Date     0x25  19 05/28/2018 23:56:02\n" \
                          "Device Version       0x26   1 16\n" \
                          "MAC Addresses        0x2A   2 128\n" \
                          "Manufacturer         0x2B   6 Edgecore Networks\n" \
                          "Vendor Extension     0xFD  36\n" \
                          "Vendor Extension     0xFD 164\n" \
                          "Vendor Extension     0xFD  36\n" \
                          "Vendor Extension     0xFD  36\n" \
                          "Vendor Extension     0xFD  36\n" \
                          "Platform Name        0x28  18 x86_64-accton_as6712_54x-r0\n" \
                          "ONIE Version         0x29  21 2018.08-5.2.0006-9600\n" \
                          "CRC-32               0xFE   4 0x11C017E1\n"

show_version = " " \
               "SONiC Software Version: SONiC.HEAD.128-c07ae3b1\n" \
               "Distribution: Debian 9.8\n" \
               "Kernel: 4.9.0-8-amd64\n" \
               "Build commit: c07ae3b1\n" \
               "Build date: Fri Mar 22 01:55:48 UTC 2019\n" \
               "Built by: support@edge-core.com\n" \
               " \n" \
               "Docker images:\n" \
               "REPOSITORY                 TAG                 IMAGE ID            SIZE\n" \
               "docker-syncd-brcm          HEAD.32-21ea29a     434240daff6e        362MB\n" \
               "docker-syncd-brcm          latest              434240daff6e        362MB\n" \
               "docker-orchagent-brcm      HEAD.32-21ea29a     e4f9c4631025        287MB\n" \
               "docker-orchagent-brcm      latest              e4f9c4631025        287MB\n" \
               "docker-lldp-sv2            HEAD.32-21ea29a     9681bbfea3ac        275MB\n" \
               "docker-lldp-sv2            latest              9681bbfea3ac        275MB\n" \
               "docker-dhcp-relay          HEAD.32-21ea29a     2db34c7bc6f4        257MB\n" \
               "docker-dhcp-relay          latest              2db34c7bc6f4        257MB\n" \
               "docker-database            HEAD.32-21ea29a     badc6fc84cdb        256MB\n" \
               "docker-database            latest              badc6fc84cdb        256MB\n" \
               "docker-snmp-sv2            HEAD.32-21ea29a     e2776e2a30b7        295MB\n" \
               "docker-snmp-sv2            latest              e2776e2a30b7        295MB\n" \
               "docker-teamd               HEAD.32-21ea29a     caf957cd2ad1        275MB\n" \
               "docker-teamd               latest              caf957cd2ad1        275MB\n" \
               "docker-router-advertiser   HEAD.32-21ea29a     b1a62023958c        255MB\n" \
               "docker-router-advertiser   latest              b1a62023958c        255MB\n" \
               "docker-platform-monitor    HEAD.32-21ea29a     40b40a4b2164        287MB\n" \
               "docker-platform-monitor    latest              40b40a4b2164        287MB\n" \
               "docker-fpm-quagga          HEAD.32-21ea29a     546036fe6838        282MB\n" \
               "docker-fpm-quagga          latest              546036fe6838        282MB\n"

cmd_output = {}
cmd_output['show platform psustatus'] = show_platform_psustatus
cmd_output['show environment'] = show_environment
cmd_output['show platform syseeprom'] = show_platform_syseeprom
cmd_output['show version'] = show_version

def get_serial_number():
    ret = ""
    for i in range(5):
        num = random.randint(0, 9)
        ret += str(num)
    return ret

def get_show_platform_syseeprom( cmd_output ):
    (is_mac_ok, mac_output) = util_utl.utl_get_execute_cmd_output("cat /sys/class/net/eth0/address")
    if is_mac_ok:
        return cmd_output % (get_serial_number(), mac_output)
    else:
        return cmd_output % (get_serial_number(), "FF:FF:FF:FF:FF:FF")

def docker_get_execute_cmd_test_output( cmd_str ):
    if cmd_str == "show platform syseeprom":
        return (True, get_show_platform_syseeprom(cmd_output[cmd_str]).strip())
    else:
        return (True, cmd_output[cmd_str].strip())
