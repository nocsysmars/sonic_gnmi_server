#
# oc_dispatcher.py
#
# OpenConfig Dispatcher
#

from oc_binding.oc_if_binding import openconfig_interfaces
from oc_binding.oc_lldp_binding import openconfig_lldp
from oc_binding.oc_platform_binding import openconfig_platform
from pyangbind.lib.xpathhelper import YANGPathHelper
from grpc import StatusCode
import subprocess
import pdb
import json

# Dispatch table for openconfig class and info function
ocTable = {
    "interfaces" : { "cls"   : openconfig_interfaces,
                     "info_f": "interface_get_info"    },
    "lldp"       : { "cls"   : openconfig_lldp,
                     "info_f": "lldp_get_info"         },
    "components" : { "cls"   : openconfig_platform,
                     "info_f": "platform_get_info"     },
}

#
# tag_str : "Manufacture Date"
def platform_get_syseeprom_output_val(sys_output, tag_str, pos):
    ret_val = None

    for idx in range(len(sys_output)):
        if tag_str in sys_output[idx]:
            ret_val = sys_output[idx].split()[pos]

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
    #       Manufacture Date     0x25  19 06/16/2016 14:01:49           7
    #       Diag Version         0x2E   7 2.0.1.4
    #       Label Revision       0x27   4 R01J
    #       Manufacturer         0x2B   6 Accton                        10
    #       Manufacture Country  0x2C   2 TW
    #       Base MAC Address     0x24   6 CC:37:AB:EC:D9:B2
    #       Serial Number        0x23  14 571254X1625041                13
    #       Part Number          0x22  13 FP1ZZ5654002A                 14
    #       Product Name         0x21  15 5712-54X-O-AC-B               15
    #       MAC Addresses        0x2A   2 74
    #       Vendor Name          0x2D   8 Edgecore
    #       Platform Name        0x28  27 x86_64-accton_as5712_54x-r0   18
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
                    comp.state._set_type('CHASSIS')
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


# input : '7 days, 22:55:53' / '0 day, 00:00:11'
# ret   : xxx
def lldp_cnv_age_to_secs(age_str):
    days = age_str.split(',')
    days_secs = 0
    if len (days) > 1:
        hours = days[1]
        days = days[0].split(' ')
        days_secs = int(days[0]) * 24 * 60 * 60
    else:
        hours = days[0]

    hours = hours.split(":")
    hours_secs = 0
    for k in hours:
        hours_secs = hours_secs * 60 + int(k)

    return (days_secs + hours_secs)

# for set lldp chassis/port
def lldp_set_id_field(obj, fld_str, fld_dict):
    attr_key_type = "_set_%s_id_type" % fld_str
    attr_key_id   = "_set_%s_id" % fld_str

    # refer to _set_xxx_id_type in lldp_binding
    if "id" in fld_dict[fld_str]:
        id_dict = fld_dict[fld_str]["id"]
    else:
        for k, v in fld_dict[fld_str].items():
            id_dict = fld_dict[fld_str][k]["id"]
            if fld_str == "chassis":
                obj._set_system_name(k)
                obj._set_system_description(fld_dict[fld_str][k]["descr"])

    # TODO: type mapping
    #  CHASSIS_COMPONENT/INTERFACE_ALIAS/PORT_COMPONENT/MAC_ADDRESS
    #  NETWORK_ADDRESS/INTERFACE_NAME/LOCAL
    if id_dict["type"] == "mac":
        type_value = "MAC_ADDRESS"

        set_type_fun = getattr(obj, attr_key_type)
        if set_type_fun:
            set_type_fun(type_value)

    set_id_fun = getattr(obj, attr_key_id)
    if set_id_fun:
        set_id_fun(id_dict["value"])

# fill lldp info for one interface
# input : inf - "eth0"
#         val - {"age": ..., "chassis": ... }
def lldp_get_info_interface(lldp_yph, inf, val):
    infs = lldp_yph.get("/interfaces")[0]
    # bcz /lldp/interfaces/interface ref to oc-if:base-interface-ref
    # need to create oc-if's interface for lldp's operation
    if inf not in infs.interface:
        infs.interface.add(inf)

    lldp_infs = lldp_yph.get("/lldp")[0].interfaces
    if inf not in lldp_infs.interface:
        lldp_inf = lldp_infs.interface.add(inf)
    else:
        lldp_inf = lldp_infs.interface[inf]

    # val key: ppvid, via, age, vlan, chassis, rid, pi, port
    #pdb.set_trace()

    nbr = lldp_inf.neighbors.neighbor.add(val["rid"])
    nbr.state._set_age(lldp_cnv_age_to_secs(val["age"]))
    lldp_set_id_field(nbr.state, "chassis", val)
    lldp_set_id_field(nbr.state, "port", val)

def lldp_del_all_inf_neighbors(lldp_yph, inf):
    lldp_infs = lldp_yph.get("/lldp")[0].interfaces
    if inf in lldp_infs.interface:
        lldp_inf = lldp_infs.interface[inf]
        lldp_inf._unset_neighbors()

# fill DUT's current lldp info into lldp_yph
# key_ar [0] : interface name e.g. "eth0"
# ret        : True/False
def lldp_get_info(lldp_yph, key_ar):
    """
    use 'lldpctl -f xml' command to gather local lldp detailed information
    """
    lldp_cmd = 'lldpctl -f json'
    ret_val = False

    #pdb.set_trace()
    p = subprocess.Popen(lldp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    lldp_root = lldp_yph.get("/lldp")[0]
    if returncode == 0:
        lldp_root.config.enabled = True
        lldp_root.config.enabled._mchanged = True

        lldp_info = json.loads(output)

        if "interface" in lldp_info["lldp"]:
            if isinstance(lldp_info["lldp"]["interface"], list):
                for k in lldp_info["lldp"]["interface"]:
                    for inf, val in k.items():
                        if key_ar and inf != key_ar[0]:
                            continue
                        lldp_del_all_inf_neighbors(lldp_yph, inf)
                        # TODO: more than one neighbor ???
                        lldp_get_info_interface(lldp_yph, inf, val)

            if isinstance(lldp_info["lldp"]["interface"], dict):
                for inf, val in lldp_info["lldp"]["interface"].items():
                    if key_ar and inf != key_ar[0]:
                        continue
                    lldp_del_all_inf_neighbors(lldp_yph, inf)
                    lldp_get_info_interface(lldp_yph, inf, val)

        ret_val = True
    else:
        if 'Error response from daemon' in err:
            lldp_root.config.enabled = False
            lldp_root._unset_interfaces()
            ret_val = True

    return ret_val


def interface_get_vlan_output():
    """
    use 'show vlan config' command to gather interface counters information
    """
    cmd = 'show vlan config'

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()
    ret_output = []

    if returncode == 0:
        output = output.splitlines()
        for idx in range(len(output)):
            ret_output.append(output[idx].split())

    return ret_output

def interface_get_info_vlan(oc_inf, key_ar, vlan_output):
    oc_inf.ethernet.switched_vlan._unset_config()

    #pdb.set_trace()
    t_vlan = []
    u_vlan = []
    for idx in range(len(vlan_output)):
        # skip element 0/1, refer to output of show vlan config
        if idx <= 1: continue

        ldata = vlan_output[idx]
        #                Name       VID    Member       Mode
        # ex of ldata : ['Vlan400', '400', 'Ethernet6', 'untagged']
        if ldata [2] == key_ar[0]:
            if ldata [3] == 'tagged':
                t_vlan.append(int(ldata[1]))
            else:
                u_vlan.append(int(ldata[1]))

    if len(t_vlan) > 0:
        # trunk mode
        oc_inf.ethernet.switched_vlan.config.interface_mode = 'TRUNK'
        oc_inf.ethernet.switched_vlan.config.trunk_vlans = t_vlan

        if len(u_vlan) > 0: # TODO: what to do if > 1 ???
            oc_inf.ethernet.switched_vlan.config.native_vlan = u_vlan[0]
    elif len(u_vlan) > 0: # TODO: what to do if > 1 ???
        # access mode
        oc_inf.ethernet.switched_vlan.config.interface_mode = 'ACCESS'
        oc_inf.ethernet.switched_vlan.config.access_vlan = u_vlan [0]

# fill DUT's interface info into inf_yph
# key_ar [0] : interface name e.g. "eth0"
def interface_get_info(inf_yph, key_ar):
    """
    use 'portstat -j' command to gather interface counters information
    """
    # 1. fill interface statistics
    pstat_cmd = 'portstat -j'
    ret_val = False
    vlan_output = interface_get_vlan_output()

    #pdb.set_trace()
    p = subprocess.Popen(pstat_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode == 0:
        pstat_info = json.loads(output)

        oc_infs = inf_yph.get("/interfaces")[0]
        for inf, val in pstat_info.items():
            if key_ar and inf != key_ar[0]:
                continue

            dir_dict = {"in" : "RX", "out" : "TX"}
            cnt_dict = {"octets": "OK", "discards" : "DRP", "errors" : "ERR"}

            if inf not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(inf)
            else:
                oc_inf = oc_infs.interface[inf]
                oc_inf._unset_state()

            interface_get_info_vlan(oc_inf, [inf], vlan_output)

            for d, dv in dir_dict.items():
                for c, cv in cnt_dict.items():
                    set_fun = getattr(oc_inf.state.counters, "_set_%s_%s" % (d, c))
                    if set_fun: set_fun(val["%s_%s" % (dv, cv)])

        ret_val = True

    # 2. fill admin/oper status/mtu
    inf_status_cmd = 'intfutil status'
    p = subprocess.Popen(inf_status_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode == 0:
        output = output.splitlines()
        for idx in range(len(output)):
            # skip element 0/1, refer to output of intfutil status
            if idx <= 1: continue

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if key_ar and key_ar[0] != ldata[0]: continue
            oc_inf = inf_yph.get_unique("/interfaces/interface[name=%s]" % ldata[0])

            if oc_inf:
                key_map = {"admin_status": 6, "oper_status" :5, "mtu": 3,}
                for k, v in key_map.items():
                    #if k == "mtu":
                    #    set_fun = getattr(oc_inf.config, "_set_%s" % (k))
                    #else:
                    set_fun = getattr(oc_inf.state, "_set_%s" % (k))
                    if set_fun:
                        val = ldata [v]
                        if k == "mtu": val = int(val)
                        else: val = val.upper()
                        set_fun(val)

        ret_val = True
    #pdb.set_trace()

    return ret_val


class ocDispatcher:
    """ Open Config Dispatcher that dispatch requests to
        other openconfig binding modules """
    def __init__(self):
        # create the full yang tree
        # for performance, only update the tree node requested
        self.oc_yph = YANGPathHelper()
        for k in ocTable.keys():
            ocTable[k]["cls"](path_helper= self.oc_yph)

    def GetRequestYph(self, path_ar, key_ar):
        # TODO: not support "/"
        if len(path_ar) < 1:
            #print "Invalid request"
            return StatusCode.INVALID_ARGUMENT

        if path_ar[0] not in ocTable:
            oc_yph = StatusCode.INVALID_ARGUMENT
        else:
            oc_yph = self.oc_yph
            # suppose key_ar [0] is interface name e.g. "eth0"
            ret_val = eval(ocTable[path_ar[0]]["info_f"])(oc_yph, key_ar)
            if not ret_val: oc_yph = StatusCode.INTERNAL

        return oc_yph


