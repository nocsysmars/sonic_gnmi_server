#
# util_platform.py
#
# APIs for processing platform info.
#

import subprocess, json, re, pdb, util_utl

OLD_COMP_LST = []

#
# tag_str : "Manufacture Date"
def platform_get_syseeprom_output_val(sys_output, tag_str, pos):
    ret_val = None

    for idx in range(len(sys_output)):
        if tag_str in sys_output[idx]:
            ret_val = sys_output[idx].split()[pos]
            break

    return ret_val

def platform_get_info_psu(oc_comps):
    """
    root@switch1:/home/admin# show platform psustatus
    PSU    Status
    -----  --------
    PSU 1  NOT OK
    PSU 2  OK
    """
    global OLD_COMP_LST
    exec_cmd = 'show platform psustatus'
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        output = output.splitlines()
        #pdb.set_trace()
        psu_beg = False
        for idx in range(len(output)):
            if output[idx] == '': continue

            if psu_beg:
                psu_line = output[idx].split("  ")
                psu_name = psu_line[0].replace(" ", "_")
                oc_comp = oc_comps.component.add(psu_name)
                OLD_COMP_LST.append(psu_name)
                oc_comp.state._set_type('POWER_SUPPLY')
                oc_comp.power_supply.state._set_enabled(
                    True if "OK" == psu_line[1] else False)
                oc_comp.power_supply.state.enabled._mchanged = True
            else:
                if '-----' in output[idx]:
                    psu_beg = True

def platform_get_info_fan(oc_comps):
    """
    root@switch1:/home/admin# show environment
    coretemp-isa-0000
    Adapter: ISA adapter
    Physical id 0:  +40.0 C  (high = +82.0 C, crit = +104.0 C)
    Core 0:         +40.0 C  (high = +82.0 C, crit = +104.0 C)
    Core 1:         +40.0 C  (high = +82.0 C, crit = +104.0 C)
    Core 2:         +40.0 C  (high = +82.0 C, crit = +104.0 C)
    Core 3:         +40.0 C  (high = +82.0 C, crit = +104.0 C)

    as7116_54x_fan-i2c-1-63
    Adapter: i2c-0-mux (chan_id 0)
    front fan 1: 11700 RPM
    front fan 2: 11850 RPM
    front fan 3: 11700 RPM
    front fan 4: 11700 RPM
    front fan 5: 11700 RPM
    rear fan 1:  9900 RPM
    rear fan 2:  9750 RPM
    rear fan 3:  9900 RPM
    rear fan 4:  9750 RPM
    rear fan 5:  9900 RPM

    lm75-i2c-17-4b
    Adapter: i2c-1-mux (chan_id 0)
    temp1:        +32.5 C  (high = +80.0 C, hyst = +75.0 C)

    lm75-i2c-19-49
    Adapter: i2c-1-mux (chan_id 2)
    temp1:        +33.5 C  (high = +80.0 C, hyst = +75.0 C)

    lm75-i2c-20-4a
    Adapter: i2c-1-mux (chan_id 3)
    temp1:        +30.5 C  (high = +80.0 C, hyst = +75.0 C)
    """
    exec_cmd = 'show environment'
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        output = output.splitlines()

        # step 1 name
        # step 2 Adapter
        # step 3 component
        beg_id = 1 if 'Command:' in output[0] else 0

        step = 1
        for idx in range(beg_id, len(output)):
            if step == 1:
                comp_name = output[idx]
                step = step + 1
            elif step == 2:
                step = step + 1
            elif step == 3:
                if output[idx] == '':
                    step = 1 # begin for next component
                else:
                    m = re.match(r'([^:]*):([^(]*)(.*)', output[idx])
                    if m:
                        is_fan = True if 'RPM' in m.group(2) else False
                        is_tem = True if 'C' in m.group(2) else False

                        if is_fan or is_tem:
                            sub_comp_name = comp_name + '_' + m.group(1).replace(' ', '_')
                            oc_comp = oc_comps.component.add(sub_comp_name)
                            OLD_COMP_LST.append(sub_comp_name)

                            if is_fan:
                                # fan
                                oc_comp.state._set_type('FAN')
                                value = int(m.group(2).split(" RPM")[0])
                                oc_comp.fan.state._set_speed(value)
                            else:
                                # temperature
                                oc_comp.state._set_type('SENSOR')
                                value = float(m.group(2).split(" C")[0].replace('+', ' '))
                                oc_comp.state.temperature._set_instant(value)

def platform_get_info(pf_yph, path_ar, key_ar, disp_args):
    global OLD_COMP_LST

    oc_comps = pf_yph.get("/components")[0]

    # remove old entries
    for old_comp in OLD_COMP_LST:
        oc_comps.component.delete(old_comp)
    OLD_COMP_LST = []

    # get info for psu
    platform_get_info_psu(oc_comps)

    # get info for fan/sensor
    platform_get_info_fan(oc_comps)

    # show platform syseeprom
    #  ex:  Command: sudo decode-syseeprom
    #       TlvInfo Header:
    #          Id String:    TlvInfo
    #          Version:      1
    #          Total Length: 169
    #       TLV Name             Code Len Value
    #       -------------------- ---- --- -----
    #       Manufacture Date     0x25  19 06/16/2016 14:01:49
    #       Diag Version         0x2E   7 2.0.1.4
    #       Label Revision       0x27   4 R01J
    #       Manufacturer         0x2B   6 Accton
    #       Manufacture Country  0x2C   2 TW
    #       Base MAC Address     0x24   6 CC:37:AB:EC:D9:B2
    #       Serial Number        0x23  14 571254X1625041
    #       Part Number          0x22  13 FP1ZZ5654002A
    #       Product Name         0x21  15 5712-54X-O-AC-B
    #       MAC Addresses        0x2A   2 74
    #       Vendor Name          0x2D   8 Edgecore
    #       Platform Name        0x28  27 x86_64-accton_as5712_54x-r0
    #       ONIE Version         0x29  14 20170619-debug
    #       CRC-32               0xFE   4 0x5B1B4944
    show_cmd_pf = 'show platform syseeprom'
    oc_comp = None
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(show_cmd_pf)
    if is_ok:
        output = output.splitlines()
        fld_map = [ {"fld" : "pd",               "tag" : "Product",          "pos" : 4 },
                    {"fld" : "hardware_version", "tag" : "Platform",         "pos" : 4 },
                    {"fld" : "serial_no",        "tag" : "Serial",           "pos" : 4 },
                    {"fld" : "part_no",          "tag" : "Part",             "pos" : 4 },
                    {"fld" : "mfg_name",         "tag" : "Manufacturer",     "pos" : 3 },
                    {"fld" : "mfg_date",         "tag" : "Manufacture Date", "pos" : 4 } ]

        for idx in range(len(fld_map)):
            val = platform_get_syseeprom_output_val(output, fld_map[idx]["tag"], fld_map[idx]["pos"])
            if val:
                if idx == 0:
                    oc_comp =oc_comps.component.add(val)
                    OLD_COMP_LST.append(val)
                    oc_comp.state._set_type('FABRIC')

                    (is_mac_ok, mac_output) = util_utl.utl_get_execute_cmd_output("cat /sys/class/net/eth0/address")
                    if is_mac_ok:
                        oc_prop = oc_comp.properties.property_.add('ETH0_MAC')
                        oc_prop.state._set_value(mac_output.replace('\n', '').upper())
                else:
                    if idx == 5:
                        val = val.split('/')
                        val = val[2] + '-' + val[0] + '-' + val[1]

                    set_fun = getattr(oc_comp.state, "_set_%s" % fld_map[idx]["fld"])
                    if set_fun:
                        set_fun(val)
            else:
                if idx == 0:
                    break

    # show version
    #  ex: SONiC Software Version: SONiC.HEAD.434-dirty-20171220.093901
    #      Distribution: Debian 8.1
    #      Kernel: 3.16.0-4-amd64
    #      Build commit: ab2d066
    #      Build date: Wed Dec 20 09:44:56 UTC 2017
    #      Built by: johnar@jenkins-worker-3
    show_cmd_ver = 'show version'
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(show_cmd_ver)
    if is_ok:
        if oc_comp:
            output = output.splitlines()
            oc_comp.state._set_software_version(output[0].split(': ')[1])

    return True if OLD_COMP_LST else False

