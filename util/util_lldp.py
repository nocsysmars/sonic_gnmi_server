#
# util_lldp.py
#
# APIs for processing lldp info.
#

import subprocess
import json
import pdb

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
    old_nbrs = [ x for x in lldp_inf.neighbors.neighbor ]

    # TODO: more than one neighbor ???
    if val["rid"] in lldp_inf.neighbors.neighbor:
        nbr = lldp_inf.neighbors.neighbor[val["rid"]]
        old_nbrs.remove(val["rid"])
    else:
        nbr = lldp_inf.neighbors.neighbor.add(val["rid"])

    nbr.state._set_age(lldp_cnv_age_to_secs(val["age"]))
    lldp_set_id_field(nbr.state, "chassis", val)
    lldp_set_id_field(nbr.state, "port", val)

    # remove neighbours not used
    for old_nbr in old_nbrs:
        lldp_inf.neighbors.neighbor.delete(old_nbr)

def lldp_add_one_inf(lldp_yph, key_ar, lldp_info, old_infs):
    for inf, val in lldp_info.items():
        if key_ar and inf != key_ar[0]:
            continue

        if inf in old_infs: old_infs.remove(inf)

        lldp_get_info_interface(lldp_yph, inf, val)

# fill DUT's current lldp info into lldp_yph
# key_ar [0] : interface name e.g. "eth0"
# ret        : True/False
def lldp_get_info(lldp_yph, path_ar, key_ar, disp_args):
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
    old_infs = [ x for x in lldp_root.interfaces.interface ]

    if returncode == 0:
        lldp_root.config.enabled = True
        lldp_root.config.enabled._mchanged = True

        lldp_info = json.loads(output)

        if "interface" in lldp_info["lldp"]:
            if isinstance(lldp_info["lldp"]["interface"], list):
                for k in lldp_info["lldp"]["interface"]:
                    lldp_add_one_inf(lldp_yph, key_ar, k, old_infs)

            if isinstance(lldp_info["lldp"]["interface"], dict):
                lldp_add_one_inf(lldp_yph, key_ar, lldp_info["lldp"]["interface"], old_infs)

        ret_val = True
    else:
        if 'Error response from daemon' in err:
            lldp_root.config.enabled = False
            ret_val = True

    # remove interfaces not used
    for inf in old_infs:
        lldp_root.interfaces.interface.delete(inf)

    return ret_val

