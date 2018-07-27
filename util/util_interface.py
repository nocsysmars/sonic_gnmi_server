#
# util_interface.py
#
# APIs for processing interface info.
#

import subprocess
import json
import pdb

# inf list needed to clear the old agg id setting
old_agg_id_lst = []

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

def interface_get_info_vlan(oc_inf, inf_name, vlan_output):
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
        if ldata [2] == inf_name:
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

def interface_get_pc_info(inf_yph, is_fill_info, vlan_output):
    #root@switch1:/home/admin# teamshow
    #Flags: A - active, I - inactive, Up - up, Dw - Down, N/A - not available, S - selected, D - deselected
    #  No.  Team Dev          Protocol        Ports
    #-----  ----------------  --------------  -------------------------
    #    2  PortChannel2      ROUNDROBIN(Up)  Ethernet2(S) Ethernet4(S)
    #    3  PortChannel3      ROUNDROBIN(Dw)  N/A
    # PortChannel...
    #pdb.set_trace()
    global old_agg_id_lst

    # 1. clear all port's aggregate-id info
    oc_infs = inf_yph.get("/interfaces")[0]
    if is_fill_info:
        for inf in old_agg_id_lst:
            inf.ethernet.config._unset_aggregate_id()
        old_agg_id_lst = []

    ret_val = False
    teamshow_cmd = 'teamshow'
    p = subprocess.Popen(teamshow_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode == 0:
        output = output.splitlines()
        for idx in range(len(output)):
            # skip element 0/1/2, refer to output of teamshow
            if idx <= 2: continue

            ldata = output[idx].split()
            #                No.  Team Dev        Protocol          Ports
            # ex of ldata : ['2', 'PortChannel2', 'ROUNDROBIN(Up)', 'Ethernet2(S)', 'Ethernet4(S)']
            if ldata[1] not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(ldata[1])
            else:
                oc_inf = oc_infs.interface[ldata[1]]
                oc_inf._unset_aggregation()

            if is_fill_info:
                interface_get_info_vlan(oc_inf, ldata[1], vlan_output)

                if 'Up' in ldata[2]:
                    oc_inf.state._set_oper_status('UP')
                else:
                    oc_inf.state._set_oper_status('DOWN')

                if 'LACP' in ldata[2]:
                    oc_inf.aggregation.state._set_lag_type('LACP')
                else:
                    oc_inf.aggregation.state._set_lag_type('STATIC')
                    ldata_len = len(ldata)
                    idx = 3
                    while idx < ldata_len:
                        ptmp = ldata[idx].split('(')[0]
                        if 'Ethernet' in ptmp:
                            oc_inf.aggregation.state.member.append(ptmp)
                            oc_infs.interface[ptmp].ethernet.config._set_aggregate_id(ldata[1])
                            old_agg_id_lst.append(oc_infs.interface[ptmp])
                        idx = idx +1

        ret_val = True

    return ret_val

def interface_get_port_info(inf_yph, key_ar, vlan_output):
    # 1. fill interface statistics
    # use 'portstat -j' command to gather interface counters information
    pstat_cmd = 'portstat -j'

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

            interface_get_info_vlan(oc_inf, inf, vlan_output)

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

                #pdb.set_trace()
                if ldata[2] !=  'N/A':
                    oc_inf.ethernet.state._set_port_speed("SPEED_%sB" % ldata[2])

        ret_val = True

    return ret_val

# fill DUT's interface info into inf_yph
# key_ar [0] : interface name e.g. "eth0"
def interface_get_info(inf_yph, key_ar):
    vlan_output = interface_get_vlan_output()

    # 1. fill port channel info
    #    also fill member port's aggregate-id
    ret_val = interface_get_pc_info(inf_yph, True, vlan_output)

    if key_ar and "PortChannel" in key_ar[0]:
        # only need port channel info
        return ret_val

    # 2. fill port info
    ret_val = interface_get_port_info(inf_yph, key_ar, vlan_output) or ret_val

    return ret_val

def interface_create_all_infs(inf_yph):
    ret_val = False
    inf_status_cmd = 'intfutil status'
    p = subprocess.Popen(inf_status_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode == 0:
        output = output.splitlines()
        oc_infs = inf_yph.get("/interfaces")[0]
        for idx in range(len(output)):
            # skip element 0/1, refer to output of intfutil status
            if idx <= 1: continue

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if ldata[0] not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(ldata[0])
        ret_val = True

    ret_val = interface_get_pc_info(inf_yph, False, None) or ret_val

    return ret_val
