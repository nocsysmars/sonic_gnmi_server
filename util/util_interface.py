#
# util_interface.py
#
# APIs for processing interface info.
#

import subprocess
import json
import pdb
import time
import re
import util_utl

# inf list needed to clear the old agg id setting
OLD_AGG_MBR_LST = []

# inf list needed to check existence
OLD_VLAN_INF_LST = []
OLD_PC_INF_LST = []

VLAN_AUTO_CREATE     = True
VLAN_ID_MAX          = 4094
VLAN_ID_MIN          = 1

MGMT_PORT_NAME       = 'eth0'

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

FILL_INFO_NONE  = 0     # fill no info
FILL_INFO_NAME  = 0x01  # fill name info
FILL_INFO_VLAN  = 0x02  # fill vlan mbr info
FILL_INFO_STATE = 0x04  # fill counter/admin/oper info
FILL_INFO_PC    = 0x08  # fill port channel info
FILL_INFO_IP    = 0x10  # fill arp/route info
FILL_INFO_ALL   = 0xff  # fill all info

def interface_get_vlan_output():
    """
    use 'show vlan config' command to gather vlan information
    """
    ret_output = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('show vlan config')
    if is_ok:
        output = output.splitlines()
        for idx in range(len(output)):
            ret_output.append(output[idx].split())

    return ret_output

def interface_get_ip4_addr_output():
    """
    use 'ip -4 addr show' command to gather information
    """
    ret_output = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 addr show')
    if is_ok:
        ret_output = output.splitlines()

    return ret_output

def interface_get_ip4_nbr_output():
    """
    use 'ip -4 neigh show' command to gather information
    """
    ret_output = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 neigh show')
    if is_ok:
        output = output.splitlines()
        for idx in range(len(output)):
            ret_output.append(output[idx].split())

    return ret_output

def interface_get_ifcfg_output():
    """
    use 'ifconfig -a' command to gather information
    """
    ret_output = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ifconfig -a')
    if is_ok:
        ret_output = output.splitlines()

    return ret_output

# fill a inf's vlan info
def interface_fill_inf_vlanmbr_info(oc_inf, inf_name, vlan_output):
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

# fill inf's ip v4 neighbours (arp) info here
def interface_fill_inf_nbr_info(oc_inf, inf_name, out_tbl):
    # ex:
    #  192.168.200.10 dev eth0 lladdr a0:36:9f:8d:52:fa STALE
    #  192.168.200.66 dev eth0 lladdr 34:64:a9:2b:2e:ad REACHABLE
    #  192.168.200.1 dev eth0  FAILED
    output = out_tbl["ip4_nbr_output"]
    for idx in range(0, len(output)-1):
        nbr_info =  output[idx]
        if nbr_info[2] != inf_name: continue
        if nbr_info[3] == 'FAILED': continue

        oc_nbr = oc_inf.routed_vlan.ipv4.neighbors.neighbor.add(nbr_info[0])
        oc_nbr.config.link_layer_address = nbr_info[4]
        oc_nbr.state._set_origin('DYNAMIC')


def interface_get_inf_ip_output(ip4_addr_output, inf_name):
    ret_output = []
    is_found = False
    if "Vlan" in inf_name:
        match_name = inf_name + "@Bridge:"
    else:
        match_name = inf_name + ":"

    for idx in range(0, len(ip4_addr_output)):
        if is_found:
            if ':' in ip4_addr_output[idx]:
                break
            else:
                ret_output.append(ip4_addr_output[idx])

        if match_name in ip4_addr_output[idx]:
            is_found = True
            ret_output.append(ip4_addr_output[idx])

    return ret_output

def interface_get_inf_ifcfg_output(ifcfg_output, inf_name):
    ret_output = []
    is_found = False
    for idx in range(0, len(ifcfg_output)):
        if is_found:
            if '' == ifcfg_output[idx]:
                break
            else:
                ret_output.append(ifcfg_output[idx])

        if inf_name in ifcfg_output[idx]:
            is_found = True
            ret_output.append(ifcfg_output[idx])

    return ret_output

# fill inf's ip v4 info here
def interface_fill_inf_ip_info(oc_inf, inf_name, out_tbl):
    oc_inf.routed_vlan._unset_ipv4()

    # ex:
    #  89: Vlan3000@Bridge: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default
    #  inet 100.100.100.200/24 scope global Vlan3000
    #  valid_lft forever preferred_lft forever
    output = interface_get_inf_ip_output(out_tbl["ip4_addr_output"], inf_name)
    for idx in range(1, len(output)):
        m = re.match(r'.*inet ([\d.\/]+) (.*)', output[idx])
        if m:
            ip_info = m.group(1).split('/')

            oc_addr = oc_inf.routed_vlan.ipv4.addresses.address.add(ip_info[0])
            oc_addr.config.prefix_length = int(ip_info[1])

    interface_fill_inf_nbr_info(oc_inf, inf_name, out_tbl)

# fill inf's admin/oper status by "ifconfig xxx" output
def interface_fill_inf_admin_oper(oc_inf, inf_name, out_tbl):
    output = interface_get_inf_ifcfg_output(out_tbl["ifcfg_output"], inf_name)
    if output:
        if 'UP' in output[1]:
            oc_inf.state._set_admin_status('UP')
        else:
            oc_inf.state._set_admin_status('DOWN')

        if 'RUNNING' in output[1]:
            oc_inf.state._set_oper_status('UP')
        else:
            oc_inf.state._set_oper_status('DOWN')

# get all pc info with "teamdctl" command
def interface_get_pc_inf_info(inf_yph, fill_info_bmp, key_ar, out_tbl):
    global OLD_AGG_MBR_LST, OLD_PC_INF_LST

    # 1. clear all port's aggregate-id info
    oc_infs = inf_yph.get("/interfaces")[0]
    if fill_info_bmp & FILL_INFO_PC:
        for inf in OLD_AGG_MBR_LST:
            inf.ethernet.config._unset_aggregate_id()
        OLD_AGG_MBR_LST = []

    ret_val = False
    new_pc_inf_lst = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_PC_LST_CMD)
    if is_ok:
        pc_lst = [] if output.strip('\n') =='' else eval(output)

        is_key_pc = True if key_ar and key_ar[0].find('PortChannel') == 0 else False
        is_key_et = True if key_ar and key_ar[0].find('Ethernet')    == 0 else False

        ret_val = True
        for pc in pc_lst:
            # case 1, key: PortChannelX
            if is_key_pc and key_ar[0] != pc: continue

            if pc not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(pc)
            else:
                oc_inf = oc_infs.interface[pc]
                oc_inf._unset_aggregation()

            new_pc_inf_lst.append(pc)

            if not is_key_et:
                if fill_info_bmp & FILL_INFO_STATE:
                    oc_inf.state._set_type('ianaift:ieee8023adLag')
                    interface_fill_inf_admin_oper(oc_inf, pc, out_tbl)
                if fill_info_bmp & FILL_INFO_VLAN:
                    interface_fill_inf_vlanmbr_info(oc_inf, pc, out_tbl["vlan_output"])
                if fill_info_bmp & FILL_INFO_IP:
                    interface_fill_inf_ip_info(oc_inf, pc, out_tbl)

            if fill_info_bmp & FILL_INFO_PC:
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
                                util_utl.utl_err("pc [%s]'s mbr port [%s] does not exist !!!" % (pc, port))

                            # case 2, key: EthernetX
                            if is_key_et and key_ar[0] == port:
                                return True

        # remove no existing pc
        for pc in OLD_PC_INF_LST:
            if pc not in new_pc_inf_lst and pc in oc_infs.interface:
                oc_infs.interface.delete(pc)

        OLD_PC_INF_LST = new_pc_inf_lst

    return ret_val

def interface_get_port_inf_info(inf_yph, fill_info_bmp, key_ar, out_tbl, is_dbg_test = False):
    ret_val = False
    oc_infs = inf_yph.get("/interfaces")[0]

    # 1. fill admin/oper status/mtu
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('intfutil status')
    if is_ok:
        output = output.splitlines()
        # skip element 0/1, refer to output of intfutil status
        for idx in range(2, len(output)):
            # to save time, create some infs for test only
            if is_dbg_test and idx > 10:  return True

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if key_ar and key_ar[0] != ldata[0]: continue

            if ldata[0] not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(ldata[0])
            else:
                oc_inf = oc_infs.interface[ldata[0]]
                oc_inf._unset_state()

            if fill_info_bmp & FILL_INFO_VLAN:
                interface_fill_inf_vlanmbr_info(oc_inf, ldata[0], out_tbl["vlan_output"])
            if fill_info_bmp & FILL_INFO_IP:
                interface_fill_inf_ip_info(oc_inf, ldata[0], out_tbl)
            if fill_info_bmp & FILL_INFO_STATE:
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

    if fill_info_bmp & FILL_INFO_STATE:
        # 2. fill interface statistics
        # use 'portstat -j' command to gather interface counters information
        (is_ok, output) = util_utl.utl_get_execute_cmd_output('portstat -j')
        if is_ok:
            dir_dict = {"in" : "RX", "out" : "TX"}
            cnt_dict = {"octets": "OK", "discards" : "DRP", "errors" : "ERR"}

            pstat_info = json.loads(output)
            for inf, val in pstat_info.items():
                if key_ar and inf != key_ar[0]: continue

                oc_inf = inf_yph.get_unique("/interfaces/interface[name=%s]" % inf)

                if oc_inf:
                    oc_inf.state._set_type('ift:ethernetCsmacd')

                    for d, dv in dir_dict.items():
                        for c, cv in cnt_dict.items():
                            set_fun = getattr(oc_inf.state.counters, "_set_%s_%s" % (d, c))
                            if set_fun: set_fun(val["%s_%s" % (dv, cv)])

            ret_val = True

    return ret_val

# get all vlan info
def interface_get_vlan_inf_info(inf_yph, fill_info_bmp, key_ar, out_tbl):
    if fill_info_bmp & (FILL_INFO_NAME | FILL_INFO_STATE | FILL_INFO_IP) == 0:
        return True

    global OLD_VLAN_INF_LST

    new_vlan_inf_lst = []
    ret_val = False
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

            new_vlan_inf_lst.append(vname)

            if fill_info_bmp & FILL_INFO_STATE:
                interface_fill_inf_admin_oper(oc_inf, vname, out_tbl)
            if fill_info_bmp & FILL_INFO_IP:
                interface_fill_inf_ip_info(oc_inf, vname, out_tbl)

            ret_val = True

    # remove no existing vlan
    for vlan  in OLD_VLAN_INF_LST:
        if vlan not in new_vlan_inf_lst and vlan in oc_infs.interface:
            oc_infs.interface.delete(vlan)

    OLD_VLAN_INF_LST = new_vlan_inf_lst

    return ret_val

def interface_get_mgmtport_info(inf_yph, fill_info_bmp, key_ar, out_tbl):
    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ifconfig %s' % MGMT_PORT_NAME)
    if is_ok:
        oc_infs = inf_yph.get("/interfaces")[0]
        if MGMT_PORT_NAME not in oc_infs.interface:
            oc_inf = oc_infs.interface.add(MGMT_PORT_NAME)
        else:
            oc_inf = oc_infs.interface[MGMT_PORT_NAME]

        if fill_info_bmp & FILL_INFO_STATE:
            interface_fill_inf_admin_oper(oc_inf, MGMT_PORT_NAME, out_tbl)
        if fill_info_bmp & FILL_INFO_IP:
            interface_fill_inf_ip_info(oc_inf, MGMT_PORT_NAME, out_tbl)

        ret_val = True

    return ret_val

# ex:
#  key_ar [0] : interface name e.g. "eth0"
#  path_ar    : [u'interfaces', u'interface', u'state']
#
# fill DUT's interface info into inf_yph
def interface_get_info(inf_yph, path_ar, key_ar):
    if path_ar == ['interfaces', 'interface', 'config', 'name']: return True

    # update needed info according to the specified path.
    #   /interfaces/interface/state                  : counters, admin, oper
    #   /interfaces/interface/ethernet/config        : pc
    #   /interfaces/interface/ethernet/switched-vlan : vlan
    #   /interfaces/interface/routed-vlan            : ip-info
    #
    #   state       -> get_port_info + get_pc_info + get_vlan_info
    #   routed-vlan -> get_port_info + get_pc_info + get_vlan_info
    #   pc          -> get_port_info + get_pc_info
    #   vlan        -> get_port_info + get_pc_info

    fill_type_tbl = { "state"         : FILL_INFO_STATE,
                      "config"        : FILL_INFO_PC,
                      "switched-vlan" : FILL_INFO_VLAN,
                      "routed-vlan"   : FILL_INFO_IP
    }

    try:
        fill_info_type = fill_type_tbl[path_ar[-1]]
    except:
        fill_info_type = FILL_INFO_ALL

    is_done = False
    # fill mgmt port info, not used now
    #if not key_ar or MGMT_PORT_NAME == key_ar[0]:
    #    ret_val = interface_get_mgmtport_info(inf_yph, True, key_ar)
    #    if key_ar and MGMT_PORT_NAME == key_ar[0]:
    #        # only need mgmt port info
    #        is_done = True

    out_tbl = { "vlan_output"       : None,
                "ip4_addr_output"   : None,
                "ip4_nbr_output"    : None,
                "ifcfg_output"      : None,
    }

    if fill_info_type & FILL_INFO_IP:
        out_tbl["ip4_addr_output"] = interface_get_ip4_addr_output()
        out_tbl["ip4_nbr_output"]  = interface_get_ip4_nbr_output()

    if fill_info_type & FILL_INFO_VLAN:
        out_tbl["vlan_output"] = interface_get_vlan_output()

    if fill_info_type & FILL_INFO_STATE:
        out_tbl["ifcfg_output"] = interface_get_ifcfg_output()

    if not is_done and (not key_ar or "Vlan" in key_ar[0]):
        # 0. fill vlan info
        ret_val = interface_get_vlan_inf_info(inf_yph, fill_info_type, key_ar, out_tbl)
        if key_ar and "Vlan" in key_ar[0]:
            # only need vlan info
            is_done = True

    if not is_done:
        vlan_output = interface_get_vlan_output()
        # 1. fill port channel info
        #    also fill member port's aggregate-id
        ret_val = interface_get_pc_inf_info(inf_yph, fill_info_type, key_ar, out_tbl) or ret_val

        if key_ar and "PortChannel" in key_ar[0]:
            # only need port channel info
            is_done = True

    if not is_done:
        # 2. fill port info
        ret_val = interface_get_port_inf_info(inf_yph, fill_info_type, key_ar, out_tbl) or ret_val

    return ret_val

def interface_get_my_mac():
    global MY_MAC_ADDR
    exec_cmd = "ip link show eth0 | grep ether | awk '{print $2}'"
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok: MY_MAC_ADDR = output.strip('\n')

@util_utl.utl_timeit
def interface_create_all_infs(inf_yph, is_dbg_test):
    # fill my mac addr for port channel usage
    interface_get_my_mac()

    #ret_val = interface_get_mgmtport_info(inf_yph, False, None) or ret_val
    ret_val = interface_get_port_inf_info(inf_yph, FILL_INFO_NAME, None, None, is_dbg_test)

    ret_val = interface_get_pc_inf_info(inf_yph, FILL_INFO_NAME, None, None) or ret_val

    ret_val = interface_get_vlan_inf_info(inf_yph, FILL_INFO_NAME, None, None) or ret_val

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
    (old_tvlan, old_uvlan) = interface_fill_inf_vlanmbr_info(None, pkey_ar[0], vlan_output)

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
        util_utl.utl_err("new vlan list is not valid !")
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
    (old_tvlan, old_uvlan) = interface_fill_inf_vlanmbr_info(None, pkey_ar[0], vlan_output)

    if val == "":
        new_uvlan = 0
    else:
        new_uvlan = interface_extract_vid(val)

        if new_uvlan == 0: return False

        # check if new uvlan exists
        if not interface_is_vlan_lst_valid(oc_yph, [new_uvlan] ):
            util_utl.utl_err("native vlan is not valid !")
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

# ex:    pkey_ar = [u'Vlan3000', u'100.100.100.100']
#   val for del = '{"ip" : "0",   "prefix-length" : 24 }'
#   val for add = '{"ip" : "xxx", "prefix-length" : 24 }'
# To set inf's ip address (v4)
def interface_set_ip_v4(oc_yph, pkey_ar, val, is_create):

    try:
        ip_cfg  = [] if val == "" else eval(val)
        ip_new  = ip_cfg["ip"]
        ip_pfx  = ip_cfg["prefix-length"]
    except:
        return False

    op_str = 'del' if ip_new == "0" or ip_new == "" else 'add'

    exec_cmd = "ip addr {0} {1}/{2} dev {3}".format(op_str, pkey_ar[1], ip_pfx, pkey_ar[0])

    return util_utl.utl_execute_cmd(exec_cmd)



