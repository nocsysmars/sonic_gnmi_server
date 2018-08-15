#
# util_interface.py
#
# APIs for processing interface info.
#

import subprocess
import json
import pdb
import time
import sys
import logging
from util import util_utl

# inf list needed to clear the old agg id setting
OLD_AGG_MBR_LST = []

VLAN_AUTO_CREATE     = True
VLAN_ID_MAX          = 4094
VLAN_ID_MIN          = 1

GET_VAR_LST_CMD_TMPL = 'sonic-cfggen -d -v "{0}"'
GET_LST_CMD_TMPL     = 'sonic-cfggen -d -v "{0}.keys() if {0}"'
GET_VLAN_MBR_LST_CMD = GET_LST_CMD_TMPL.format("VLAN_MEMBER")
GET_VLAN_LST_CMD     = GET_LST_CMD_TMPL.format("VLAN")
GET_PC_LST_CMD       = GET_LST_CMD_TMPL.format("PORTCHANNEL")

CFG_VLAN_MBR_CMD_TMPL= 'config vlan member {0} {1} {2} {3}'
CFG_VLAN_CMD_TMPL    = 'config vlan {0} {1}'

MY_MAC_ADDR          = ""
TEAMD_CFG_PORT_CMD_TMPL='teamdctl {0} port {1} {2}'
TEAMD_CONF_PATH      = "/etc/teamd"
TEAMD_CONF_TMPL      = """
    {
        "device": "%s",
        "hwaddr": "%s",
        "runner": {
            "name": "roundrobin",
            "active": true,
            "min_ports": 0,
            "tx_hash": ["eth", "ipv4", "ipv6"]
        },
        "link_watch": {
            "name": "ethtool"
        },
        "ports": {
        }
    }"""

def interface_get_vlan_output():
    """
    use 'show vlan config' command to gather interface counters information
    """
    ret_output = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('show vlan config')
    if is_ok:
        output = output.splitlines()
        for idx in range(len(output)):
            ret_output.append(output[idx].split())

    return ret_output

# fill vlan info into inf
def interface_get_info_vlan(oc_inf, inf_name, vlan_output):
    #pdb.set_trace()
    t_vlan = []
    u_vlan = []
    # skip element 0/1, refer to output of show vlan config
    for idx in range(2, len(vlan_output)):

        ldata = vlan_output[idx]
        #                Name       VID    Member       Mode
        # ex of ldata : ['Vlan400', '400', 'Ethernet6', 'untagged']
        if ldata [2] == inf_name:
            if ldata [3] == 'tagged':
                t_vlan.append(int(ldata[1]))
            else:
                u_vlan.append(int(ldata[1]))

    # fill info if oc_inf exists
    if oc_inf:
        oc_inf.ethernet.switched_vlan._unset_config()

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
    else:
        return (t_vlan, u_vlan)

# fill inf's admin/oper status by "ifconfig xxx" output
def interface_fill_admin_oper(oc_inf, inf_name):
    exec_cmd = 'ifconfig %s' % inf_name
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        if 'UP' in output:
            oc_inf.state._set_admin_status('UP')
        else:
            oc_inf.state._set_admin_status('DOWN')

        if 'RUNNING' in output:
            oc_inf.state._set_oper_status('UP')
        else:
            oc_inf.state._set_oper_status('DOWN')

# get all pc info with "teamdctl" command
def interface_get_pc_info(inf_yph, is_fill_info, key_ar, vlan_output):
    global OLD_AGG_MBR_LST

    # 1. clear all port's aggregate-id info
    oc_infs = inf_yph.get("/interfaces")[0]
    if is_fill_info:
        for inf in OLD_AGG_MBR_LST:
            inf.ethernet.config._unset_aggregate_id()
        OLD_AGG_MBR_LST = []

    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_PC_LST_CMD)
    if is_ok:
        pc_lst = [] if output.strip('\n') =='' else eval(output)

        is_key_pc = True if key_ar and key_ar[0].find('PortChannel') == 0 else False
        is_key_et = True if key_ar and key_ar[0].find('Ethernet')    == 0 else False

        for pc in pc_lst:
            # case 1, key: PortChannelX
            if is_key_pc and key_ar[0] != pc: continue

            if pc not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(pc)
            else:
                oc_inf = oc_infs.interface[pc]
                oc_inf._unset_aggregation()

            if is_fill_info:
                if not is_key_et:
                    interface_get_info_vlan(oc_inf, pc, vlan_output)
                    oc_inf.state._set_type('ianaift:ieee8023adLag')

                    interface_fill_admin_oper(oc_inf, pc)

                exec_cmd = 'teamdctl %s state dump' % pc
                (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
                if is_ok:
                    pc_state = json.loads(output)

                    if not is_key_et:
                        if pc_state["setup"]["runner_name"] != "roundrobin":
                            oc_inf.aggregation.state._set_lag_type('LACP')
                        else:
                            oc_inf.aggregation.state._set_lag_type('STATIC')

                    if "ports" in pc_state:
                        for port in pc_state["ports"]:
                            if port in oc_infs.interface:
                                if not is_key_et:
                                    OLD_AGG_MBR_LST.append(oc_infs.interface[port])
                                    oc_inf.aggregation.state.member.append(port)
                                oc_infs.interface[port].ethernet.config._set_aggregate_id(pc)
                            else:
                                util_utl.utl_log("pc [%s]'s mbr port [%s] does not exist !!!" % (pc, port))

                            # case 2, key: EthernetX
                            if is_key_et and key_ar[0] == port:
                                return True

        ret_val = True

    return ret_val

# get all pc info with "teamshow" command
def interface_get_pc_info_teamshow(inf_yph, is_fill_info, vlan_output):
    #root@switch1:/home/admin# teamshow
    #Flags: A - active, I - inactive, Up - up, Dw - Down, N/A - not available, S - selected, D - deselected
    #  No.  Team Dev          Protocol        Ports
    #-----  ----------------  --------------  -------------------------
    #    2  PortChannel2      ROUNDROBIN(Up)  Ethernet2(S) Ethernet4(S)
    #    3  PortChannel3      ROUNDROBIN(Dw)  N/A
    # PortChannel...
    global OLD_AGG_MBR_LST

    # 1. clear all port's aggregate-id info
    oc_infs = inf_yph.get("/interfaces")[0]
    if is_fill_info:
        for inf in OLD_AGG_MBR_LST:
            inf.ethernet.config._unset_aggregate_id()
        OLD_AGG_MBR_LST = []

    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('teamshow')
    if is_ok:
        output = output.splitlines()
        # skip element 0/1/2, refer to output of teamshow
        for idx in range(3, len(output)):

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
                oc_inf.state._set_type('ianaift:ieee8023adLag')

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
                            OLD_AGG_MBR_LST.append(oc_infs.interface[ptmp])
                        idx = idx +1

        ret_val = True

    return ret_val

def interface_get_port_info(inf_yph, key_ar, vlan_output):
    # 1. fill interface statistics
    # use 'portstat -j' command to gather interface counters information
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('portstat -j')
    if is_ok:
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
            oc_inf.state._set_type('ift:ethernetCsmacd')

            for d, dv in dir_dict.items():
                for c, cv in cnt_dict.items():
                    set_fun = getattr(oc_inf.state.counters, "_set_%s_%s" % (d, c))
                    if set_fun: set_fun(val["%s_%s" % (dv, cv)])

        ret_val = True

    # 2. fill admin/oper status/mtu
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('intfutil status')
    if is_ok:
        output = output.splitlines()
        # skip element 0/1, refer to output of intfutil status
        for idx in range(2, len(output)):

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if key_ar and key_ar[0] != ldata[0]: continue

            oc_inf = inf_yph.get_unique("/interfaces/interface[name=%s]" % ldata[0])
            if oc_inf:
                key_map = {"admin_status": 6, "oper_status" :5, "mtu": 3,}
                for k, v in key_map.items():
                    set_fun = getattr(oc_inf.state, "_set_%s" % (k))
                    if set_fun:
                        val = ldata [v]
                        val = int(val) if k == "mtu" else val.upper()
                        set_fun(val)

                #pdb.set_trace()
                if ldata[2] !=  'N/A':
                    oc_inf.ethernet.state._set_port_speed("SPEED_%sB" % ldata[2])

        ret_val = True

    return ret_val

# get all vlan info
def interface_get_vlan_info(inf_yph, is_fill_info, key_ar):
    exec_cmd = GET_VAR_LST_CMD_TMPL.format("VLAN")
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        vlan_cfg = {} if output.strip('\n') == '' else eval(output)

        oc_infs = inf_yph.get("/interfaces")[0]

        # vlan_cfg ex : "{'Vlan1113': {'vlanid': '1113'},
        #                 'Vlan1111': {'members': ['Ethernet2', 'Ethernet5'], 'vlanid': '1111'}}"
        for vname, vdata in  vlan_cfg.items():
            if vname not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(vname)
            else:
                oc_inf = oc_infs.interface[vname]
                oc_inf._unset_state()

            if is_fill_info:
                interface_fill_admin_oper(oc_inf, vname)

        return True

# fill DUT's interface info into inf_yph
# key_ar [0] : interface name e.g. "eth0"
def interface_get_info(inf_yph, key_ar):

    is_done = False
    # 0. fill vlan info
    if not key_ar or "Vlan" in key_ar[0]:
        ret_val = interface_get_vlan_info(inf_yph, True, key_ar)
        if key_ar and "Vlan" in key_ar[0]:
            # only need vlan info
            is_done = True

    if not is_done:
        vlan_output = interface_get_vlan_output()
        # 1. fill port channel info
        #    also fill member port's aggregate-id
        ret_val = interface_get_pc_info(inf_yph, True, key_ar, vlan_output) or ret_val

        if key_ar and "PortChannel" in key_ar[0]:
            # only need port channel info
            is_done = True

    if not is_done:
        # 2. fill port info
        ret_val = interface_get_port_info(inf_yph, key_ar, vlan_output) or ret_val

    return ret_val

def interface_get_my_mac():
    global MY_MAC_ADDR
    exec_cmd = "ip link show eth0 | grep ether | awk '{print $2}'"
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok: MY_MAC_ADDR = output.strip('\n')

def interface_create_all_infs(inf_yph, is_dbg_test):
    time_beg = time.clock()

    # fill my mac addr for port channel usage
    interface_get_my_mac()

    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('intfutil status')
    if is_ok:
        output = output.splitlines()
        oc_infs = inf_yph.get("/interfaces")[0]
        # skip element 0/1, refer to output of intfutil status
        for idx in range(2, len(output)):

            # to save time, create some infs for test only
            if is_dbg_test and idx > 10:  continue

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if ldata[0] not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(ldata[0])
        ret_val = True

    ret_val = interface_get_pc_info(inf_yph, False, None, None) or ret_val

    ret_val = interface_get_vlan_info(inf_yph, False, None) or ret_val

    time_end = time.clock()

    util_utl.utl_log("Time spent in creating all infs : %s" %  (time_end - time_beg))

    return ret_val

# get old pc name by port with "teamdctl" command
def interface_get_old_pc_name_by_port(port_name):
    old_pc_name = ""

    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_PC_LST_CMD)
    if is_ok:
        pc_lst = [] if output.strip('\n') == '' else eval(output)

        for pc in pc_lst:
            exec_cmd = 'teamdctl %s config dump actual' % pc
            (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
            if is_ok:
                pc_cfg = json.loads(output)
                if port_name in pc_cfg["ports"]:
                    old_pc_name = pc
                    break

    return old_pc_name

# get old pc name by port with "teamshow" command
def interface_get_old_pc_name_by_port_teamshow(port_name):
    old_pc_name = ""

    (is_ok, output) = util_utl.utl_get_execute_cmd_output('teamshow')
    if is_ok:
        output = output.splitlines()
        # skip element 0/1/2, refer to output of teamshow
        for idx in range(3, len(output)):

            ldata = output[idx].split()
            #                No.  Team Dev        Protocol          Ports
            # ex of ldata : ['2', 'PortChannel2', 'ROUNDROBIN(Up)', 'Ethernet2(S)', 'Ethernet4(S)']

            ldata_len = len(ldata)
            idx = 3
            while idx < ldata_len:
                if port_name in ldata[idx]:
                    old_pc_name = ldata[1]
                    break
                idx = idx+1

    return old_pc_name

# To make interface join/leave port channel
def interface_set_aggregate_id(oc_yph, pkey_ar, val, is_create):
    # not support to create port interface
    if is_create: return False

    is_remove = True if val == "" else False

    if is_remove:
        # get old pc name
        pc_name = interface_get_old_pc_name_by_port(pkey_ar[0])
        if not pc_name: return True
    else:
        pc_name = val
        # set port down before adding port to port channel
        exec_cmd = 'ifconfig %s down' % pkey_ar[0]
        util_utl.utl_execute_cmd(exec_cmd)

    # use teamdctl to add/remove port
    exec_cmd = TEAMD_CFG_PORT_CMD_TMPL.format(pc_name, ["add", "remove"][is_remove], pkey_ar[0])

    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val

def interface_remove_all_mbr_for_pc(pc_name):
    exec_cmd = 'teamdctl %s config dump actual' % pc_name
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        pc_cfg = json.loads(output)

        for port in pc_cfg["ports"]:
            exec_cmd = TEAMD_CFG_PORT_CMD_TMPL.format(pc_name, 'remove', port)
            util_utl.utl_execute_cmd(exec_cmd)

# To create/remove port channel by set name
def interface_set_cfg_name_pc(oc_yph, pkey_ar, is_create):
    set_cmd = 'sonic-cfggen -a \'{"PORTCHANNEL": {"%s":%s}}\' --write-to-db' \
                % (pkey_ar[0], ["null", "{}"][is_create])
    oc_infs = oc_yph.get("/interfaces")[0]

    #pdb.set_trace()
    if is_create:
        # need to write to db first to let other app start working
        if not util_utl.utl_execute_cmd(set_cmd): return False

        # populate create info to teamd
        conf =  TEAMD_CONF_TMPL % (pkey_ar[0], MY_MAC_ADDR)

        exec_cmd = "echo '%s' | (docker exec -i teamd bash -c 'cat > %s/%s.conf')" \
                    % (conf, TEAMD_CONF_PATH, pkey_ar[0])
        if not util_utl.utl_execute_cmd(exec_cmd): return False

        exec_cmd = 'docker exec teamd teamd -d -f %s/%s.conf' % (TEAMD_CONF_PATH, pkey_ar[0])
        if not util_utl.utl_execute_cmd(exec_cmd): return False

        oc_infs.interface.add(pkey_ar[0])
    else:
        oc_infs.interface.delete(pkey_ar[0])

        interface_remove_all_mbr_for_pc(pkey_ar[0])

        # populate delete info to teamd
        exec_cmd = 'docker exec teamd teamd -k -t %s' % pkey_ar[0]
        util_utl.utl_execute_cmd(exec_cmd)

        # remove port channel in db last to let other app finish jobs
        util_utl.utl_execute_cmd(set_cmd)

    return True

# vlan_name should be in "VlanXXX" format
def interface_extract_vid(vlan_name):
    vid_str = vlan_name.lstrip('Vlan')

    ret_vid = vid_str.isdigit() and \
                int(vid_str) if int(vid_str) in range (VLAN_ID_MIN, VLAN_ID_MAX) else 0 \
                or 0

    return ret_vid

# To create/remove vlan by set name
def interface_set_cfg_name_vlan(oc_yph, pkey_ar, is_create):
    #pdb.set_trace()
    ret_val = False
    vid = interface_extract_vid(pkey_ar[0])
    if vid > 0:
        if not is_create:
            # remove all vlan member before removing vlan
            exec_cmd = GET_VAR_LST_CMD_TMPL.format("VLAN")
            (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
            if is_ok:
                vlan_cfg = {} if output.strip('\n') == '' else eval(output)

                # vlan_cfg ex : "{'Vlan1113': {'vlanid': '1113'},
                #                 'Vlan1111': {'members': ['Ethernet2', 'Ethernet5'], 'vlanid': '1111'}}"
                for vname, vdata in  vlan_cfg.items():
                    if vid == int(vdata['vlanid']):
                        mbrs = vdata['members'] if 'members' in vdata else []
                        for mbr in mbrs:
                            exec_cmd = CFG_VLAN_MBR_CMD_TMPL.format('del', '', vid, mbr)
                            util_utl.utl_execute_cmd(exec_cmd)

                #time.sleep(2)

        exec_cmd = CFG_VLAN_CMD_TMPL.format(["del", "add"][is_create], vid)
        util_utl.utl_execute_cmd(exec_cmd)

        oc_infs = oc_yph.get("/interfaces")[0]
        if is_create:
            oc_infs.interface.add(pkey_ar[0])
        else:
            oc_infs.interface.delete(pkey_ar[0])

        ret_val = True

    return ret_val

# To set name of inf
def interface_set_cfg_name(oc_yph, pkey_ar, val, is_create):
    # support to create/remove port channel/vlan only
    #  if_type 1 : PC
    #  if_type 2 : VLAN
    if_type = 1 if pkey_ar[0].find("PortChannel") == 0 else \
              2 if pkey_ar[0].find("Vlan") == 0 else 0

    if if_type == 0: return False

    if is_create:
        if val == "": return True
        # key and val should use the same name
        if pkey_ar[0] != val: return False
    else:
        if pkey_ar[0] == val: return True
        # not support to change name
        if val != "": return False

    return [interface_set_cfg_name_pc, interface_set_cfg_name_vlan] \
                [if_type -1](oc_yph, pkey_ar, is_create)


# To set admin status of inf
def interface_set_cfg_enabled(oc_yph, pkey_ar, val, is_create):

    # not support create
    if is_create: return False

    exec_cmd = 'ifconfig %s %s' % (pkey_ar[0], ["down", "up"][val.upper() == "TRUE"])

    #pdb.set_trace()
    util_utl.utl_execute_cmd(exec_cmd)

    return True

# Return false if any vlan in the list not exist
# auto create vlan if VLAN_AUTO_CREATE == True
def interface_is_vlan_lst_valid(oc_yph, vid_lst):
    ret_val = True

    exec_cmd = GET_VAR_LST_CMD_TMPL.format("VLAN")
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        vlan_cfg = {} if output.strip('\n') == '' else eval(output)

        #is_add_vlan = False
        for vid in vid_lst:
            if "Vlan%s" % str(vid) not in vlan_cfg:
                if not VLAN_AUTO_CREATE:
                    ret_val = False
                    break
                else:
                    # auto create vlan
                    interface_set_cfg_name_vlan(oc_yph, ["Vlan%s" % str(vid)], True)
                    util_utl.utl_log("auto create vlan %d" % vid)
                    #is_add_vlan = True

        #if is_add_vlan:
        #    time.sleep(2)
    return ret_val

# To set inf's tagged vlan membership
def interface_set_trunk_vlans(oc_yph, pkey_ar, val, is_create):
    # pdb.set_trace()

    # not support create
    if is_create: return False

    vlan_output = interface_get_vlan_output()
    (old_tvlan, old_uvlan) = interface_get_info_vlan(None, pkey_ar[0], vlan_output)

    # handle syntax error exception
    try:
        new_tvlan = [] if val == "" else eval(val)
    except:
        return False

    del_tvlan =[]
    for vid in old_tvlan:
        int_vid = int(vid)
        if int_vid not in new_tvlan:
            del_tvlan.append(int_vid)
        else:
            new_tvlan.remove(int_vid)


    # check if all new tvlan exists
    if new_tvlan and not interface_is_vlan_lst_valid(oc_yph, new_tvlan):
        util_utl.utl_log("new vlan list not valid !")
        return False

    # remove inf from vlan
    for vid in del_tvlan:
        exec_cmd = CFG_VLAN_MBR_CMD_TMPL.format('del', '', vid, pkey_ar[0])
        util_utl.utl_execute_cmd(exec_cmd)

    # add inf into vlan
    for vid in new_tvlan:
        exec_cmd = CFG_VLAN_MBR_CMD_TMPL.format('add', '', vid, pkey_ar[0])
        util_utl.utl_execute_cmd(exec_cmd)

    return True

# To set inf's native vlan
def interface_set_native_vlan(oc_yph, pkey_ar, val, is_create):
    # not support create

    if is_create: return False

    vlan_output = interface_get_vlan_output()
    (old_tvlan, old_uvlan) = interface_get_info_vlan(None, pkey_ar[0], vlan_output)

    if val == "":
        new_uvlan = 0
    else:
        new_uvlan = interface_extract_vid(val)

        if new_uvlan == 0: return False

        # check if new uvlan exists
        if not interface_is_vlan_lst_valid(oc_yph, [new_uvlan] ):
            util_utl.utl_log("native vlan not valid !")
            return False

    # remove inf from old uvlan
    for vid in old_uvlan:
        exec_cmd = CFG_VLAN_MBR_CMD_TMPL.format('del', '', vid, pkey_ar[0])
        util_utl.utl_execute_cmd(exec_cmd)

    # add inf into new uvlan
    if new_uvlan != 0:
        exec_cmd = CFG_VLAN_MBR_CMD_TMPL.format('add', '-u', new_uvlan, pkey_ar[0])
        util_utl.utl_execute_cmd(exec_cmd)

    return True



