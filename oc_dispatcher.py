#
# oc_dispatcher.py
#
# OpenConfig Dispatcher
#

from oc_binding.oc_if_binding import openconfig_interfaces
from oc_binding.oc_lldp_binding import openconfig_lldp
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
}

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

    # bcz /lldp/interfaces/interface ref to oc-if:base-interface-ref
    # need to create oc-if's interface for lldp's operation
    #ocTable["interfaces"]["cls"](path_helper= lldp_yph)

    lldp_cmd = 'lldpctl -f json'
    ret_val = False

    #pdb.set_trace()
    p = subprocess.Popen(lldp_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return returncode ##
    returncode = p.wait()
    ### if no error, get the lldpctl result

    if returncode == 0:
        lldp_info = json.loads(output)

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

    return ret_val

def interface_get_vlan_output():
    """
    use 'show vlan config' command to gather interface counters information
    """
    cmd = 'show vlan config'

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return returncode ##
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
    ## Wait for end of command. Get return returncode ##
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
    ## Wait for end of command. Get return returncode ##
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


