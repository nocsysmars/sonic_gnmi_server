#
# util_platform.py
#
# APIs for processing platform info.
#

import subprocess
import json
import pdb

#
# tag_str : "Manufacture Date"
def platform_get_syseeprom_output_val(sys_output, tag_str, pos):
    ret_val = None

    for idx in range(len(sys_output)):
        if tag_str in sys_output[idx]:
            ret_val = sys_output[idx].split()[pos]
            break

    return ret_val

def platform_get_info(pf_yph, key_ar):
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
    comp = None

    p = subprocess.Popen(show_cmd_pf, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    #pdb.set_trace()

    if returncode == 0:
        comps = pf_yph.get("/components")[0]
        comps._unset_component()

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
                    comp = comps.component.add(val)
                    comp.state._set_type('FABRIC')
                else:
                    if idx == 5:
                        val = val.split('/')
                        val = val[2] + '-' + val[0] + '-' + val[1]

                    set_fun = getattr(comp.state, "_set_%s" % fld_map[idx]["fld"])
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

    p = subprocess.Popen(show_cmd_ver, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()
    ### if no error, get the result
    if returncode == 0:
        if comp:
            output = output.splitlines()
            comp.state._set_software_version(output[0].split(': ')[1])

    return True if comp else False

