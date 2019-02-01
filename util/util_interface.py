#
# util_interface.py
#
# APIs for processing interface info.
#

import subprocess, json, pdb, time, re, swsssdk, util_utl

from util_utl import CFG_PC_CMD_TMPL

# inf list needed to clear the old agg id setting
OLD_AGG_MBR_LST = []

# inf list needed to check existence
OLD_VLAN_INF_LST = []
OLD_PC_INF_LST = []

VLAN_AUTO_CREATE     = True
VLAN_ID_MAX          = 4094
VLAN_ID_MIN          = 1

MGMT_PORT_NAME       = 'eth0'

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
FILL_INFO_STATE = 0x04  # fill admin/oper info
FILL_INFO_PC    = 0x08  # fill port channel info
FILL_INFO_IP    = 0x10  # fill arp/route info
FILL_INFO_CNTR  = 0x20  # fill counter info
FILL_INFO_PORT  = 0x40  # fill port info
FILL_INFO_ALL   = 0xff  # fill all info

# refer to /usr/bin/intfutil
PORT_STATUS_TABLE_PREFIX = "PORT_TABLE:"
PORT_OPER_STATUS         = "oper_status"
PORT_ADMIN_STATUS        = "admin_status"
PORT_MTU_SIZE            = "mtu"
PORT_SPEED               = "speed"

PORT_LANES_STATUS        = "lanes"
PORT_ALIAS               = "alias"
PORT_DESCRIPTION         = "description"

# refer to /usr/bin/teamshow
PC_STATUS_TABLE_PREFIX   = "LAG_TABLE:"


VLAN_STATUS_TABLE_PREFIX = "VLAN_TABLE:"

# refer to /usr/bin/portstat
COUNTER_TABLE_PREFIX     = "COUNTERS:"
COUNTERS_PORT_NAME_MAP   = "COUNTERS_PORT_NAME_MAP"

# set to True if teammgrd is used to manage all port channel related configuration
IS_NEW_TEAMMGRD = False

# t_vlan, u_vlan for inf
def interface_get_vlan_output(disp_args):
    # ex: {'Vlan10': {'vlanid': '10', 'members': ['Ethernet9']}}
    vlan_lst     = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_VLAN)
    # ex: {('Vlan10', 'Ethernet9'): {'tagging_mode': 'tagged'}}
    vlan_mbr_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_VLAN_MBR)

    ret_output = {}
    for vlan in vlan_lst:
        vid = int (vlan_lst[vlan]['vlanid'])

        if 'members' in vlan_lst[vlan]:
            for mbr in vlan_lst[vlan]['members']:
                if mbr not in ret_output:
                    ret_output[mbr] = {'t_vlan' : [], 'u_vlan' : []}

                if vlan_mbr_lst[vlan, mbr]['tagging_mode'] == 'tagged':
                    ret_output[mbr]['t_vlan'].append (vid)
                else:
                    ret_output[mbr]['u_vlan'].append (vid)

    return ret_output

def interface_get_ip4_addr_output():
    """
    use 'ip -4 addr show' command to gather information
    """
    ret_output = {}
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 addr show')
    if is_ok:
        tmp_output = output.splitlines()

    blk_head = 0
    for idx in range(0, len(tmp_output)):
        if ':' in tmp_output[idx] or idx == len(tmp_output) -1:
            # ex: 163: Ethernet0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 9100 qdisc pfifo_fast state DOWN group default qlen 1000
            head_line = tmp_output[blk_head].split(':')
            inf_name = head_line[1].strip()
            ret_output[inf_name] = []
            for blk_idx in range(blk_head, idx):
                ret_output[inf_name].append(tmp_output[blk_idx])

            blk_head = idx

    return ret_output

def interface_get_ip4_nbr_output():
    """
    use 'ip -4 neigh show' command to gather information
    """
    ret_output = {}
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 neigh show')
    if is_ok:
        tmp_output = output.splitlines()
        for idx in range(len(tmp_output)):
            tmp_line = tmp_output[idx].split()
            # ex:
            #  192.168.200.10 dev eth0 lladdr a0:36:9f:8d:52:fa STALE
            #  192.168.200.66 dev eth0 lladdr 34:64:a9:2b:2e:ad REACHABLE
            #  192.168.200.1 dev eth0  FAILED
            if tmp_line[3] == 'FAILED': continue
            inf_name = tmp_line[2]
            if inf_name not in ret_output:
                ret_output[inf_name] = []

            ret_output[inf_name].append(tmp_line)

    return ret_output

def interface_get_ip_link_output():
    """
    use 'ip link show' command to gather information
    """
    ret_output = {}
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -o link show')
    if is_ok:
        tmp_output = output.splitlines()

        for idx in range(0, len(tmp_output)):
            # ex:
            #  27: Ethernet84: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 9100 qdisc pfifo_fast state DOWN mode DEFAULT group default qlen 1000\    link/ether 50:6b:4b:95:e1:00 brd ff:ff:ff:ff:ff:ff
            onel = tmp_output[idx].split()
            inf_name = onel[1].rstrip(':')
            ret_output[inf_name] = tmp_output[idx]

    return ret_output

# fill a inf's vlan info
def interface_fill_inf_vlanmbr_info(oc_inf, inf_name, vlan_output):
    if inf_name in vlan_output:
        t_vlan = vlan_output[inf_name]['t_vlan']
        u_vlan = vlan_output[inf_name]['u_vlan']
    else:
        t_vlan = []
        u_vlan = []

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
    #  100.102.100.12 dev Ethernet2 lladdr 00:00:00:00:00:30 PERMANENT
    old_nbr_lst  = [x for x in oc_inf.routed_vlan.ipv4.neighbors.neighbor]

    if inf_name in out_tbl["ip4_nbr_output"]:
        nbr_output = out_tbl["ip4_nbr_output"][inf_name]

        for idx in range(0, len(nbr_output)):
            nbr_info = nbr_output[idx]

            if nbr_info[0] not in oc_inf.routed_vlan.ipv4.neighbors.neighbor:
                oc_nbr = oc_inf.routed_vlan.ipv4.neighbors.neighbor.add(nbr_info[0])
            else:
                oc_nbr = oc_inf.routed_vlan.ipv4.neighbors.neighbor[nbr_info[0]]
                old_nbr_lst.remove(nbr_info[0])

            oc_nbr.config.link_layer_address = nbr_info[4]

            if nbr_info[5] == "PERANENT":
                oc_nbr.state._set_origin('DYNAMIC')
            else:
                oc_nbr.state._set_origin('STATIC')

    # remove unused nbr entry
    for x in old_nbr_lst:
        oc_inf.routed_vlan.ipv4.neighbors.neighbor.delete(x)

def interface_get_inf_ip_output(ip4_addr_output, inf_name):
    if "Vlan" in inf_name:
        match_name = inf_name + "@Bridge"
    else:
        match_name = inf_name

    return ip4_addr_output[match_name] if match_name in ip4_addr_output else []

# fill inf's ip v4 info here
def interface_fill_inf_ip_info(oc_inf, inf_name, out_tbl):
    old_addr_lst = [x for x in oc_inf.routed_vlan.ipv4.addresses.address]

    # ex:
    #  89: Vlan3000@Bridge: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default
    #  inet 100.100.100.200/24 scope global Vlan3000
    #  valid_lft forever preferred_lft forever
    output = interface_get_inf_ip_output(out_tbl["ip4_addr_output"], inf_name)
    for idx in range(1, len(output)):
        m = re.match(r'.*inet ([\d.\/]+) (.*)', output[idx])
        if m:
            ip_info = m.group(1).split('/')

            if ip_info[0] not in oc_inf.routed_vlan.ipv4.addresses.address:
                oc_addr = oc_inf.routed_vlan.ipv4.addresses.address.add(ip_info[0])
            else:
                old_addr_lst.remove (ip_info[0])
                oc_addr = oc_inf.routed_vlan.ipv4.addresses.address[ip_info[0]]

            oc_addr.config.prefix_length = int(ip_info[1])

    interface_fill_inf_nbr_info(oc_inf, inf_name, out_tbl)

    # remove unused addr entry
    for x in old_addr_lst:
        oc_inf.routed_vlan.ipv4.addresses.address.delete(x)

# fill inf's admin/oper status by "ifconfig xxx" output
def interface_fill_inf_admin_oper(oc_inf, inf_name, out_tbl):
    oc_inf._unset_state()

    if inf_name.startswith('Vlan'):
        match_name = inf_name + "@Bridge"
    else:
        match_name = inf_name

    output = out_tbl["ip_link_output"][match_name] if match_name in out_tbl["ip_link_output"] else []
    if output:
        if re.search(r'\bUP\b', output):
            oc_inf.state._set_admin_status('UP')
        else:
            oc_inf.state._set_admin_status('DOWN')

        if re.search(r'\bLOWER_UP\b', output):
            oc_inf.state._set_oper_status('UP')
        else:
            oc_inf.state._set_oper_status('DOWN')

# get all pc info with "teamdctl" command
def interface_get_pc_inf_info(oc_infs, fill_info_bmp, key_ar, out_tbl, disp_args):
    global OLD_AGG_MBR_LST, OLD_PC_INF_LST

    # 1. clear all port's aggregate-id info
    if fill_info_bmp & FILL_INFO_PC:
        for inf in OLD_AGG_MBR_LST:
            inf.ethernet.config._unset_aggregate_id()
        OLD_AGG_MBR_LST = []

    ret_val = False
    new_pc_inf_lst = []
    pc_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_PC)
    if pc_lst:
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

            new_pc_inf_lst.append(pc)

            if not is_key_et:
                if fill_info_bmp & FILL_INFO_STATE:
                    interface_fill_inf_state(oc_inf, pc, disp_args.appdb, FILL_INFO_PC)
                if fill_info_bmp & FILL_INFO_VLAN:
                    interface_fill_inf_vlanmbr_info(oc_inf, pc, out_tbl["vlan_output"])
                if fill_info_bmp & FILL_INFO_IP:
                    interface_fill_inf_ip_info(oc_inf, pc, out_tbl)

            if fill_info_bmp & FILL_INFO_PC:
                oc_inf._unset_aggregation()
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
                                break

        # remove no existing pc
        for pc in OLD_PC_INF_LST:
            if pc not in new_pc_inf_lst and pc in oc_infs.interface:
                oc_infs.interface.delete(pc)

        OLD_PC_INF_LST = new_pc_inf_lst

    return ret_val

# get inf status form appl db
def interface_db_inf_status_get(db, inf_name, status_fld, fill_info):
    pfx_tbl = { FILL_INFO_PC   : PC_STATUS_TABLE_PREFIX,
                FILL_INFO_PORT : PORT_STATUS_TABLE_PREFIX,
                FILL_INFO_VLAN : VLAN_STATUS_TABLE_PREFIX }

    if fill_info in pfx_tbl:
        pfx = pfx_tbl[fill_info]
    else:
        return None

    full_table_id = pfx + inf_name
    status = db.get(db.APPL_DB, full_table_id, status_fld)
    return status

def interface_convert_speed(speed_in_mb):
    speed_tbl = {    10:'10MB',    100:'100MB',  1000:'1GB',   2500:'2500MB',
                   5000:'5GB',   10000:'10GB',  25000:'25GB', 40000:'40GB',
                  50000:'50GB', 100000:'100GB' }

    str_speed = speed_tbl[speed_in_mb] if speed_in_mb in speed_tbl else 'UNKNOWN'
    return 'SPEED_{0}'.format(str_speed)

def interface_fill_inf_state(oc_inf, inf_name, db, fill_info):
    # Ethernet?     => PORT_TABLE
    # PortChannel?  => LAG_TABLE
    # Vlan?         => VLAN_TABLE (TODO ?)

    # fill alias into description to make topology discovery using lldp work
    fld_tbl = {
        "admin_status": { "tag": PORT_ADMIN_STATUS, "info" : FILL_INFO_PORT|FILL_INFO_PC },
        "oper_status" : { "tag": PORT_OPER_STATUS,  "info" : FILL_INFO_PORT|FILL_INFO_PC },
        "mtu"         : { "tag": PORT_MTU_SIZE,     "info" : FILL_INFO_PORT|FILL_INFO_PC|FILL_INFO_VLAN },
        "description" : { "tag": PORT_ALIAS,        "info" : FILL_INFO_PORT              },
        "port_speed"  : { "tag": PORT_SPEED,        "info" : FILL_INFO_PORT              },  # in Mbps
        }

    type_tbl = {
        FILL_INFO_PC  : "ianaift:ieee8023adLag",
        FILL_INFO_PORT: "ift:ethernetCsmacd"
        }

    oc_inf._unset_state()
    if fill_info in type_tbl:
        oc_inf.state._set_type(type_tbl[fill_info])

    for fld in fld_tbl:
        if not fld_tbl[fld]["info"] & fill_info: continue

        val = interface_db_inf_status_get(db, inf_name, fld_tbl[fld]["tag"], fill_info)
        if val and val != "N/A":
            if fld in ["mtu", "port_speed"]:
                val = int(val)
            elif fld not in ["description"]:
                val = val.upper()
        else:
            # default value for description
            if fld in ["description"]:
                val = inf_name
        if val:
            if fld == "port_speed":
                set_fun = getattr(oc_inf.ethernet.config, "_set_%s" % (fld))
                val = interface_convert_speed(val)
            else:
                set_fun = getattr(oc_inf.state, "_set_%s" % (fld))

            if set_fun:
                set_fun(val)

def interface_fill_inf_counters(oc_inf, inf_name, counter_port_name_map, db):
    cntr_map_tbl = {
        'SAI_PORT_STAT_IF_IN_UCAST_PKTS'        :  'in_unicast_pkts',
        'SAI_PORT_STAT_IF_IN_NON_UCAST_PKTS'    :  'in_multicast_pkts',
        'SAI_PORT_STAT_IF_IN_ERRORS'            :  'in_errors',
        'SAI_PORT_STAT_IF_IN_DISCARDS'          :  'in_discards',
#        'SAI_PORT_STAT_ETHER_RX_OVERSIZE_PKTS'  :
        'SAI_PORT_STAT_IF_OUT_UCAST_PKTS'       :  'out_unicast_pkts',
        'SAI_PORT_STAT_IF_OUT_NON_UCAST_PKTS'   :  'out_multicast_pkts',
        'SAI_PORT_STAT_IF_OUT_ERRORS'           :  'out_errors',
        'SAI_PORT_STAT_IF_OUT_DISCARDS'         :  'out_discards',
#        'SAI_PORT_STAT_ETHER_TX_OVERSIZE_PKTS'  :
        'SAI_PORT_STAT_IF_IN_OCTETS'            :  'in_octets',
        'SAI_PORT_STAT_IF_OUT_OCTETS'           :  'out_octets',
        }

    for cntr in cntr_map_tbl:
        set_fun = getattr(oc_inf.state.counters, "_set_%s" % cntr_map_tbl[cntr])

        if set_fun:
            table_id = counter_port_name_map[inf_name]
            full_table_id = COUNTER_TABLE_PREFIX + table_id
            cntr_data =  db.get(db.COUNTERS_DB, full_table_id, cntr)
            if cntr_data:
                set_fun(cntr_data)

def interface_get_port_inf_info(oc_infs, fill_info_bmp, key_ar, out_tbl, disp_args, is_dbg_test = False):
    # ex: ['PORT_TABLE:Ethernet65',...]
    if is_dbg_test:
        pattern = 'PORT_TABLE:Ethernet?'
    else:
        pattern = 'PORT_TABLE:*'

    db_keys = disp_args.appdb.keys(disp_args.appdb.APPL_DB, pattern)
    for i in db_keys:
        inf_name = re.split(':', i, maxsplit=1)[-1].strip()
        if inf_name and inf_name.startswith('Ethernet'):
            if key_ar and key_ar[0] != inf_name: continue

            if inf_name not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(inf_name)
            else:
                oc_inf = oc_infs.interface[inf_name]

            if fill_info_bmp & FILL_INFO_VLAN:
                interface_fill_inf_vlanmbr_info(oc_inf, inf_name, out_tbl["vlan_output"])
            if fill_info_bmp & FILL_INFO_IP:
                interface_fill_inf_ip_info(oc_inf, inf_name, out_tbl)
            if fill_info_bmp & FILL_INFO_STATE:
                interface_fill_inf_state(oc_inf, inf_name, disp_args.appdb, FILL_INFO_PORT)

            if fill_info_bmp & FILL_INFO_CNTR:
                if inf_name in out_tbl["cntr_pname_map"]:
                    interface_fill_inf_counters(oc_inf, inf_name, out_tbl["cntr_pname_map"], disp_args.appdb)

            ret_val = True

    return ret_val

# get all vlan info
def interface_get_vlan_inf_info(oc_infs, fill_info_bmp, key_ar, out_tbl, disp_args):
    if fill_info_bmp & (FILL_INFO_NAME | FILL_INFO_STATE | FILL_INFO_IP) == 0:
        return True

    global OLD_VLAN_INF_LST

    new_vlan_inf_lst = []
    ret_val = False

    vlan_cfg = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_VLAN)
    if vlan_cfg:
        # vlan_cfg ex : "{'Vlan1113': {'vlanid': '1113'},
        #                 'Vlan1111': {'members': ['Ethernet2', 'Ethernet5'], 'vlanid': '1111'}}"
        for vname, vdata in vlan_cfg.items():
            if vname not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(vname)
            else:
                oc_inf = oc_infs.interface[vname]

            new_vlan_inf_lst.append(vname)

            if fill_info_bmp & FILL_INFO_STATE:
                interface_fill_inf_admin_oper(oc_inf, vname, out_tbl)
                # status in VLAN_TABLE is not ready yet
                # interface_fill_inf_state(oc_inf, vname, disp_args.appdb, FILL_INFO_VLAN)
            if fill_info_bmp & FILL_INFO_IP:
                interface_fill_inf_ip_info(oc_inf, vname, out_tbl)

            ret_val = True

    # remove no existing vlan
    for vlan  in OLD_VLAN_INF_LST:
        if vlan not in new_vlan_inf_lst and vlan in oc_infs.interface:
            oc_infs.interface.delete(vlan)

    OLD_VLAN_INF_LST = new_vlan_inf_lst

    return ret_val

def interface_get_mgmtport_info(oc_infs, fill_info_bmp, key_ar, out_tbl):
    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ifconfig %s' % MGMT_PORT_NAME)
    if is_ok:
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
def interface_get_info(inf_yph, path_ar, key_ar, disp_args):
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

    fill_type_tbl = { "state"         : FILL_INFO_STATE | FILL_INFO_CNTR,
                      "counters"      : FILL_INFO_CNTR,
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

    out_tbl = {}

    if fill_info_type & FILL_INFO_IP:
        out_tbl["ip4_addr_output"] = interface_get_ip4_addr_output()
        out_tbl["ip4_nbr_output"]  = interface_get_ip4_nbr_output()

    if fill_info_type & FILL_INFO_VLAN:
        out_tbl["vlan_output"] = interface_get_vlan_output(disp_args)

    if fill_info_type & FILL_INFO_STATE:
        out_tbl["ip_link_output"] = interface_get_ip_link_output()

    if fill_info_type & FILL_INFO_CNTR:
        out_tbl["cntr_pname_map"] = disp_args.appdb.get_all(disp_args.appdb.COUNTERS_DB, COUNTERS_PORT_NAME_MAP)

    oc_infs = inf_yph.get("/interfaces")[0]

    ret_val = True
    if not is_done and (not key_ar or "Vlan" in key_ar[0]):
        # 0. fill vlan info
        ret_val = interface_get_vlan_inf_info(oc_infs, fill_info_type, key_ar, out_tbl, disp_args)
        if key_ar and "Vlan" in key_ar[0]:
            # only need vlan info
            is_done = True

    if not is_done:
        # 1. fill port channel info
        #    also fill member port's aggregate-id
        ret_val = interface_get_pc_inf_info(oc_infs, fill_info_type, key_ar, out_tbl, disp_args) or ret_val
        if key_ar and "PortChannel" in key_ar[0]:
            # only need port channel info
            is_done = True

    if not is_done:
        # 2. fill port info
        ret_val = interface_get_port_inf_info(oc_infs, fill_info_type, key_ar, out_tbl, disp_args) or ret_val

    return ret_val

def interface_get_my_mac():
    global MY_MAC_ADDR
    #exec_cmd = "ip link show eth0 | grep ether | awk '{print $2}'"
    # bcz some vendors use different mac for eth0
    exec_cmd = "sonic-cfggen -d -v DEVICE_METADATA.localhost.mac"
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok: MY_MAC_ADDR = output.strip('\n')


@util_utl.utl_timeit
def interface_create_all_infs(inf_yph, is_dbg_test, disp_args):
    # fill my mac addr for port channel usage
    interface_get_my_mac()

    oc_infs = inf_yph.get("/interfaces")[0]

    #ret_val = interface_get_mgmtport_info(inf_yph, False, None) or ret_val
    ret_val = interface_get_port_inf_info(oc_infs, FILL_INFO_NAME, None, None, disp_args, is_dbg_test)

    ret_val = interface_get_pc_inf_info(oc_infs, FILL_INFO_NAME, None, None, disp_args) or ret_val

    ret_val = interface_get_vlan_inf_info(oc_infs, FILL_INFO_NAME, None, None, disp_args) or ret_val

    return ret_val

# get old pc name by port with "teamdctl" command
def interface_get_old_pc_name_by_port(port_name, disp_args):
    old_pc_name = ""

    pc_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_PC)
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
def interface_set_aggregate_id(oc_yph, pkey_ar, val, is_create, disp_args):
    # not support to create port interface
    if is_create: return False

    is_remove = True if val == "" else False

    if is_remove:
        # get old pc name
        pc_name = interface_get_old_pc_name_by_port(pkey_ar[0], disp_args)
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

        if "ports" in pc_cfg:
            for port in pc_cfg["ports"]:
                exec_cmd = TEAMD_CFG_PORT_CMD_TMPL.format(pc_name, 'remove', port)
                util_utl.utl_execute_cmd(exec_cmd)

# destroy pc by teamd operation
def interface_destroy_pc(pc_name, is_force = False):
    # teammgrd will destroy pc when pc is removed from db
    if not IS_NEW_TEAMMGRD or is_force:
        exec_cmd = 'docker exec teamd teamd -k -t %s' % pc_name
        return util_utl.utl_execute_cmd(exec_cmd)

    return True

# destroy pc created by teammgrd
def interface_destroy_pc_by_teammgrd(pc_name):
    LOOP_CNT = 10
    exec_cmd = "teamdctl %s state" % pc_name

    # wait for the pc created by teammgrd to show up
    for idx in range(LOOP_CNT):
        time.sleep(1)

        if util_utl.utl_execute_cmd(exec_cmd):
            break

    return interface_destroy_pc(pc_name, True)

# create pc by teamd operation
def interface_create_pc(pc_name):
    global MY_MAC_ADDR
    if IS_NEW_TEAMMGRD:
        interface_destroy_pc_by_teammgrd(pc_name)

        # re-create the pc (static trunk)
        pc_cfg   = '{"device":"%s","hwaddr":"%s","runner":{"active":"true","name":"roundrobin"}}' % (pc_name, MY_MAC_ADDR)
        exec_cmd = "docker exec teamd bash -c '/usr/bin/teamd -r -t %s -c '\\''%s'\\'' -L /var/warmboot/teamd/ -d'" % (pc_name, pc_cfg)

        return util_utl.utl_execute_cmd(exec_cmd)
    else:
        # populate create info to teamd
        conf =  TEAMD_CONF_TMPL % (pc_name, MY_MAC_ADDR)

        exec_cmd = "echo '%s' | (docker exec -i teamd bash -c 'cat > %s/%s.conf')" \
                    % (conf, TEAMD_CONF_PATH, pc_name)
        if not util_utl.utl_execute_cmd(exec_cmd): return False

        exec_cmd = 'docker exec teamd teamd -d -f %s/%s.conf' % (TEAMD_CONF_PATH, pc_name)
        if not util_utl.utl_execute_cmd(exec_cmd): return False

# To create/remove port channel by set name
def interface_set_cfg_name_pc(oc_yph, pkey_ar, is_create, disp_args):
    set_cmd = CFG_PC_CMD_TMPL % (pkey_ar[0], ["null", "{}"][is_create])
    oc_infs = oc_yph.get("/interfaces")[0]

    #pdb.set_trace()
    ret_val = False
    if is_create:
        # need to write to db first to let other app start working
        if util_utl.utl_execute_cmd(set_cmd):
            interface_create_pc(pkey_ar[0])
            oc_infs.interface.add(pkey_ar[0])
            ret_val = True
    else:
        oc_infs.interface.delete(pkey_ar[0])
        interface_remove_all_mbr_for_pc(pkey_ar[0])
        interface_destroy_pc(pkey_ar[0])

        # remove port channel in db last to let other app finish jobs
        ret_val = util_utl.utl_execute_cmd(set_cmd)

    return ret_val

# vlan_name should be in "VlanXXX" format
def interface_extract_vid(vlan_name):
    vid_str = vlan_name.lstrip('Vlan')

    ret_vid = vid_str.isdigit() and \
                int(vid_str) if int(vid_str) in range (VLAN_ID_MIN, VLAN_ID_MAX) else 0 \
                or 0

    return ret_vid

# create/remove vlan entry in config db
def interface_db_set_vlan(db, vid, is_add):
    vlan = 'Vlan{}'.format(vid)
    if is_add:
        if len(db.get_entry('VLAN', vlan)) != 0:
            util_utl.utl_err("{} already exists".format(vlan))
        else:
            db.set_entry('VLAN', vlan, {'vlanid': vid})
    else:
        # remove all vlan member of vid
        keys = [ (k, v) for k, v in db.get_table('VLAN_MEMBER') if k == 'Vlan{}'.format(vid) ]
        for k in keys:
            db.set_entry('VLAN_MEMBER', k, None)
        db.set_entry('VLAN', 'Vlan{}'.format(vid), None)

# To create/remove vlan by set name
def interface_set_cfg_name_vlan(oc_yph, pkey_ar, is_create, disp_args):
    #pdb.set_trace()
    ret_val = False
    vid = interface_extract_vid(pkey_ar[0])
    if vid > 0:
        interface_db_set_vlan(disp_args.cfgdb, vid, is_create)

        oc_infs = oc_yph.get("/interfaces")[0]
        if is_create:
            oc_infs.interface.add(pkey_ar[0])
        else:
            oc_infs.interface.delete(pkey_ar[0])

        ret_val = True

    return ret_val

# To set name of inf
def interface_set_cfg_name(oc_yph, pkey_ar, val, is_create, disp_args):
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
                [if_type -1](oc_yph, pkey_ar, is_create, disp_args)

# To set admin status of inf
def interface_set_cfg_enabled(oc_yph, pkey_ar, val, is_create, disp_args):
    # not support create
    if is_create: return False

    tbl = None
    if pkey_ar[0].startswith("Ethernet"):
        tbl = "PORT"
    elif pkey_ar[0].startswith("PortChannel"):
        tbl = "PORTCHANNEL"

    if IS_NEW_TEAMMGRD and tbl:
        val = ["down", "up"][val.upper() == "TRUE"]
        disp_args.cfgdb.mod_entry(tbl, pkey_ar[0], {"admin_status": val})
    else:
        exec_cmd = 'ifconfig %s %s' % (pkey_ar[0], ["down", "up"][val.upper() == "TRUE"])
        util_utl.utl_execute_cmd(exec_cmd)

    return True

# Return false if any vlan in the list not exist
# auto create vlan if VLAN_AUTO_CREATE == True
def interface_is_vlan_lst_valid(oc_yph, vid_lst, disp_args):
    ret_val = True

    vlan_cfg = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_VLAN)
    #is_add_vlan = False
    for vid in vid_lst:
        if "Vlan%s" % str(vid) not in vlan_cfg:
            if not VLAN_AUTO_CREATE:
                ret_val = False
                break
            else:
                # auto create vlan
                interface_set_cfg_name_vlan(oc_yph, ["Vlan%s" % str(vid)], True, disp_args)
                util_utl.utl_log("auto create vlan %d" % vid)
                #is_add_vlan = True

    #if is_add_vlan:
    #    time.sleep(2)
    return ret_val

# add/remove vlan member port in config db
def interface_db_set_vlan_member(db, is_add, vid, interface_name, untagged = True):
    vlan_name = 'Vlan{}'.format(vid)
    vlan = db.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        util_utl.utl_err("{} doesn't exist".format(vlan_name))
        return

    if is_add:
        members = vlan.get('members', [])
        if interface_name in members:
            util_utl.utl_log("{} is already a member of {}".format(interface_name, vlan_name))
            return
        members.append(interface_name)
        vlan['members'] = members
        db.set_entry('VLAN', vlan_name, vlan)
        db.set_entry('VLAN_MEMBER', (vlan_name, interface_name), {'tagging_mode': "untagged" if untagged else "tagged" })
    else:
        members = vlan.get('members', [])
        if interface_name not in members:
            util_utl.utl_log("{} is not a member of {}".format(interface_name, vlan_name))
            return
        members.remove(interface_name)
        if len(members) == 0:
            del vlan['members']
        else:
            vlan['members'] = members
        db.set_entry('VLAN', vlan_name, vlan)
        db.set_entry('VLAN_MEMBER', (vlan_name, interface_name), None)

# To set inf's tagged vlan membership
def interface_set_trunk_vlans(oc_yph, pkey_ar, val, is_create, disp_args):
    # not support create
    if is_create: return False

    vlan_output = interface_get_vlan_output(disp_args)
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
    if new_tvlan and not interface_is_vlan_lst_valid(oc_yph, new_tvlan, disp_args):
        util_utl.utl_err("new vlan list is not valid !")
        return False

    # remove inf from vlan
    for vid in del_tvlan:
        interface_db_set_vlan_member(disp_args.cfgdb, False, vid, pkey_ar[0])

    # add inf into vlan
    for vid in new_tvlan:
        interface_db_set_vlan_member(disp_args.cfgdb, True, vid, pkey_ar[0], False)

    return True

# To set inf's native vlan
def interface_set_native_vlan(oc_yph, pkey_ar, val, is_create, disp_args):
    # not support create
    if is_create: return False

    vlan_output = interface_get_vlan_output(disp_args)
    (old_tvlan, old_uvlan) = interface_fill_inf_vlanmbr_info(None, pkey_ar[0], vlan_output)

    if val == "":
        new_uvlan = 0
    else:
        new_uvlan = interface_extract_vid(val)

        if new_uvlan == 0: return False

        # check if new uvlan exists
        if not interface_is_vlan_lst_valid(oc_yph, [new_uvlan], disp_args):
            util_utl.utl_err("native vlan is not valid !")
            return False

    # remove inf from old uvlan
    for vid in old_uvlan:
        interface_db_set_vlan_member(disp_args.cfgdb, False, vid, pkey_ar[0])

    # add inf into new uvlan
    if new_uvlan != 0:
        interface_db_set_vlan_member(disp_args.cfgdb, True, new_uvlan, pkey_ar[0])

    return True

# get intf table name in db from intf name
def interface_db_get_intf_table_name(intf_name):
    db_tbl_map = {
        'Vlan'        : util_utl.CFGDB_TABLE_NAME_VLAN_INTF,
        'Ethernet'    : util_utl.CFGDB_TABLE_NAME_INTF,
        'PortChannel' : util_utl.CFGDB_TABLE_NAME_PC_INTF,
        'Loopback'    : util_utl.CFGDB_TABLE_NAME_LBK_INTF
    }

    ret_tbl_name = None
    for key in db_tbl_map.keys():
        if intf_name.startswith(key):
            ret_tbl_name = db_tbl_map[key]
            break

    return ret_tbl_name

# add/remove ip of interface in config db
def interface_db_set_ip(db, is_add, intf_name, ip):
    ret_val = False

    intf_tbl_name = interface_db_get_intf_table_name(intf_name)

    if intf_tbl_name:
        val = {} if is_add else None
        db.set_entry(intf_tbl_name, (intf_name, ip), val)
        ret_val = True

    return ret_val

# ex:   pkey_ar = [u'Vlan3000', u'100.100.100.100']
#   val for del = '{"ip" : "0",   "prefix-length" : 24 }'
#   val for add = '{"ip" : "xxx", "prefix-length" : 24 }'
# To set inf's ip address (v4)
def interface_set_ip_v4(oc_yph, pkey_ar, val, is_create, disp_args):
    try:
        ip_cfg  = {} if val == "" else eval(val)
        ip_new  = ip_cfg["ip"]
        ip_pfx  = ip_cfg["prefix-length"]
    except:
        return False

    is_del = True if ip_new == "0" or ip_new == "" else False

    ret_val = interface_db_set_ip(disp_args.cfgdb, not is_del, pkey_ar[0], pkey_ar[1]+'/'+ str(ip_pfx))

    # only ip on vlan interface can take effect immediately
    if pkey_ar[0].startswith('Vlan'):
        return ret_val

    if ret_val:
        exec_cmd = "ip addr {0} {1}/{2} dev {3}".format(
            ['add', 'del'][is_del], pkey_ar[1], ip_pfx, pkey_ar[0])

        util_utl.utl_execute_cmd(exec_cmd)

    return ret_val

# ex:   pkey_ar = [u'Vlan3000', u'100.100.100.100']
#   val for del = '{"link-layer-address" : ""} or {} or ""'
#   val for add = '{"link-layer-address" : "00:00:00:00:00:20"}'
# To set inf's arp (v4)
def interface_set_nbr_v4(oc_yph, pkey_ar, val, is_create, disp_args):
    #pdb.set_trace()

    try:
        nbr_cfg     = {} if val == "" else eval(val)
        lladdr_cmd  = "" if "link-layer-address" not in nbr_cfg else \
                      "lladdr %s" % nbr_cfg["link-layer-address"]
    except:
        return False

    exec_cmd = "ip neigh {0} {1} {2} dev {3}".format(
        ['replace', 'del'][lladdr_cmd == ""], pkey_ar[1], lladdr_cmd, pkey_ar[0])

    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val