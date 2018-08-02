#
# util_interface.py
#
# APIs for processing interface info.
#

import subprocess
import json
import pdb
from util import util_utl

# inf list needed to clear the old agg id setting
OLD_AGG_MBR_LST = []

MY_MAC_ADDR     = ""
TEAMD_CONF_PATH = "/etc/teamd"
TEAMD_CONF_TMPL = """
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

# fill vlan info into inf
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

# get all pc info with "teamdctl" command
def interface_get_pc_info(inf_yph, is_fill_info, vlan_output):
    global OLD_AGG_MBR_LST

    # 1. clear all port's aggregate-id info
    oc_infs = inf_yph.get("/interfaces")[0]
    if is_fill_info:
        for inf in OLD_AGG_MBR_LST:
            inf.ethernet.config._unset_aggregate_id()
        OLD_AGG_MBR_LST = []

    #pdb.set_trace()

    ret_val = False
    exec_cmd = 'sonic-cfggen -d -v "PORTCHANNEL.keys() if PORTCHANNEL"'
    p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()
    if returncode == 0:
        pc_lst = eval(output) if output.strip('\n') !="" else []

        for pc in pc_lst:
            if pc not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(pc)
            else:
                oc_inf = oc_infs.interface[pc]
                oc_inf._unset_aggregation()

            if is_fill_info:
                interface_get_info_vlan(oc_inf, pc, vlan_output)
                oc_inf.state._set_type('ianaift:ieee8023adLag')

                exec_cmd = 'ifconfig %s' % pc
                p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
                (output, err) = p.communicate()
                ## Wait for end of command. Get return code ##
                returncode = p.wait()
                if returncode == 0:
                    if 'UP' in output:
                        oc_inf.state._set_admin_status('UP')
                    else:
                        oc_inf.state._set_admin_status('DOWN')

                    if 'RUNNING' in output:
                        oc_inf.state._set_oper_status('UP')
                    else:
                        oc_inf.state._set_oper_status('DOWN')

                exec_cmd = 'teamdctl %s state dump' % pc
                p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
                (output, err) = p.communicate()
                ## Wait for end of command. Get return code ##
                returncode = p.wait()
                if returncode == 0:
                    pc_state = json.loads(output)

                    if pc_state["setup"]["runner_name"] != "roundrobin":
                        oc_inf.aggregation.state._set_lag_type('LACP')
                    else:
                        oc_inf.aggregation.state._set_lag_type('STATIC')

                        if "ports" in pc_state:
                            for port in pc_state["ports"]:
                                if port in oc_infs.interface:
                                    oc_inf.aggregation.state.member.append(port)
                                    oc_infs.interface[port].ethernet.config._set_aggregate_id(pc)
                                    OLD_AGG_MBR_LST.append(oc_infs.interface[port])
                                else:
                                    util_utl.utl_log("pc [%s]'s mbr port [%s] does not exist !!!" % (pc, port))

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
            oc_inf.state._set_type('ift:ethernetCsmacd')

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

def interface_get_my_mac():
    global MY_MAC_ADDR
    exec_cmd = "ip link show eth0 | grep ether | awk '{print $2}'"
    p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()
    if returncode == 0:
        MY_MAC_ADDR = output.strip("\n")

def interface_create_all_infs(inf_yph, is_dbg_test):
    # fill my mac addr for port channel usage
    interface_get_my_mac()

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

            # to save time, create some infs for test only
            if is_dbg_test and idx > 10:  continue

            ldata = output[idx].split()
            #                Interface    Lanes Speed  MTU     Alias       Oper    Admin
            # ex of ldata : ['Ethernet0', '13', 'N/A', '9100', 'tenGigE0', 'down', 'up']
            if ldata[0] not in oc_infs.interface:
                oc_inf = oc_infs.interface.add(ldata[0])
        ret_val = True

    ret_val = interface_get_pc_info(inf_yph, False, None) or ret_val

    return ret_val

# get old pc name by port with "teamdctl" command
def interface_get_old_pc_name_by_port(port_name):
    old_pc_name = ""

    exec_cmd = 'sonic-cfggen -d -v "PORTCHANNEL.keys()"'
    p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()
    if returncode == 0:
        pc_lst = eval(output)

        for pc in pc_lst:
            exec_cmd = 'teamdctl %s config dump actual' % pc

            p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            ## Wait for end of command. Get return code ##
            returncode = p.wait()

            if returncode == 0:
                pc_cfg = json.loads(output)
                if port_name in pc_cfg["ports"]:
                    old_pc_name = pc
                    break

    return old_pc_name

# get old pc name by port with "teamshow" command
def interface_get_old_pc_name_by_port_teamshow(port_name):
    old_pc_name = ""

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
        if not pc_name: return False
    else:
        pc_name = val
        # set port down before adding port to port channel
        exec_cmd = 'ifconfig %s down' % pkey_ar[0]
        util_utl.utl_execute_cmd(exec_cmd)

    # use teamdctl to add/remove port
    set_cmd = 'teamdctl %s port %s %s' %  (pc_name, ["add", "remove"][is_remove], pkey_ar[0])

    return util_utl.utl_execute_cmd(set_cmd)

def interface_remove_all_mbr_for_pc(pc_name):
    exec_cmd = 'teamdctl %s config dump actual' % pc_name

    p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode == 0:
        pc_cfg = json.loads(output)

        for port in pc_cfg["ports"]:
            exec_cmd = 'teamdctl %s port remove %s' % (pc_name, port)
            util_utl.utl_execute_cmd(exec_cmd)


# To create/remove port channel by set name
def interface_set_cfg_name(oc_yph, pkey_ar, val, is_create):
    # support to create/remove port channel only
    if pkey_ar[0].find("PortChannel") != 0:
        return False

    if is_create:
        # key and val should use the same name
        if pkey_ar[0] != val: return False
    else:
        # not support change port channel name
        if val != "": return False

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

        exec_cmd = 'docker exec -i teamd teamd -d -f %s/%s.conf' % (TEAMD_CONF_PATH, pkey_ar[0])
        if not util_utl.utl_execute_cmd(exec_cmd): return False

        oc_infs.interface.add(pkey_ar[0])
    else:
        oc_infs.interface.delete(pkey_ar[0])

        interface_remove_all_mbr_for_pc(pkey_ar[0])

        # populate delete info to teamd
        exec_cmd = 'docker exec -i teamd teamd -k -t %s' % pkey_ar[0]
        util_utl.utl_execute_cmd(exec_cmd)

        # remove port channel in db last to let other app finish jobs
        util_utl.utl_execute_cmd(set_cmd)

    return True

# To set admin status of inf
def interface_set_cfg_enabled(oc_yph, pkey_ar, val, is_create):
    # not support create
    if is_create: return False

    exec_cmd = 'ifconfig %s %s' % (pkey_ar[0], ["down", "up"][val.upper() == "TRUE"])

    #pdb.set_trace()
    util_utl.utl_execute_cmd(exec_cmd)

    return True