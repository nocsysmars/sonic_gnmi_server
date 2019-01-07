#
# util_bcm.py
#
# Utility APIs for bcm diag shell.
#

import subprocess, json, logging, inspect
import sys, os, time, functools, util_utl, pdb

BCM_PORT_MAP      = {}
BCM_PORT_MAP_INIT = False

BCM_MIRROR_OFF  = 0
BCM_MIRROR_RX   = 1
BCM_MIRROR_TX   = 2
BCM_MIRROR_ALL  = 3

BCM_DIAG_CMD_TMPL   = 'bcmcmd "%s"'
BCM_MIRROR_MODE_TBL = {
    BCM_MIRROR_OFF : {'diag': 'off',     'gtag': 'OFF' },
    BCM_MIRROR_RX  : {'diag': 'ingress', 'gtag': 'RX'  },
    BCM_MIRROR_TX  : {'diag': 'egress',  'gtag': 'TX'  },
    BCM_MIRROR_ALL : {'diag': 'all',     'gtag': 'BOTH'}
}

@util_utl.utl_timeit
def bcm_execute_diag_cmd(exe_cmd):
    diag_cmd = BCM_DIAG_CMD_TMPL % exe_cmd
    p = subprocess.Popen(diag_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        # if no decorator, use inspect.stack()[1][3] to get caller
        util_utl.utl_log("Failed to [%s] by %s !!!" % (diag_cmd, inspect.stack()[2][3]), logging.ERROR)
        return False

    if any(x in output for x in ['Fail', 'Err']):
        util_utl.utl_log("Failed to [%s] by %s !!!" % (diag_cmd + '(' + output +')',
                inspect.stack()[2][3]), logging.ERROR)
        return False

    return True

# get a dictionary mapping port name ("Ethernet48") to a physical port number
def bcm_get_diag_port_map():
    global BCM_PORT_MAP, BCM_PORT_MAP_INIT

    if BCM_PORT_MAP_INIT: return

    exe_cmd = 'docker exec -i syncd cat /usr/share/sonic/hwsku/port_config.ini'
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exe_cmd)
    if is_ok:
        # Default column definition
        titles = ['name', 'lanes', 'alias', 'index']
        output = output.splitlines()
        BCM_PORT_MAP = {}
        for line in output:
            if line.startswith('#'):
                if "name" in line:
                    titles = line.strip('#').split()
                    continue
            tokens = line.split()
            if len(tokens) < 2:
                continue
            name_index = titles.index('name')
            name = tokens[name_index]
            data = {}
            for i, item in enumerate(tokens):
                if i == name_index:
                   continue
                data[titles[i]] = item
            data.setdefault('alias', name)
            BCM_PORT_MAP[name] = data

        BCM_PORT_MAP_INIT = True

# convert "Ethernet0" to "xe#"
def bcm_get_diag_port_name(log_port_name):
    global BCM_PORT_MAP

    bcm_get_diag_port_map()

    diag_port_name = None
    if log_port_name:
        if log_port_name in BCM_PORT_MAP:
            diag_port_name = 'xe%s' % BCM_PORT_MAP[log_port_name]['index']
        else:
            util_utl.utl_err("Failed to get diag port name (%s)" % log_port_name)

    return diag_port_name

# ex: in_mode = 'BOTH'
#     ret_val = 'all'
def bcm_get_diag_mirror_mode(in_mode):
    ret_val = None
    for key in BCM_MIRROR_MODE_TBL.keys():
        if BCM_MIRROR_MODE_TBL[key]['gtag'] == in_mode:
            ret_val = BCM_MIRROR_MODE_TBL[key]['diag']
            break

    if not ret_val:
        util_utl.utl_err("Failed to get diag mirror mode (%d)" % in_mode)

    return ret_val

# ex: src_port= 'Ethernet0'
#     dst_port= 'Ethernet3' (None to delete)
#         mode= 'Both'      (None or 'OFF' to delete)
#         vlan= 4000        (None to ignore)
#      pm_cfg = '{"src-port": "Ethernet0","dst-port": "Ethernet3",
#                 "mode": "Both","vlan": 4000}'
def bcm_set_one_port_mirror(pm_cfg):
    try:
        src_port = pm_cfg['src-port']
        dst_port = None if 'dst-port' not in pm_cfg else pm_cfg['dst-port']
        m_mode   = 'OFF' if 'mode' not in pm_cfg else pm_cfg['mode'].upper()
        vlan     = None if 'vlan' not in pm_cfg else int (pm_cfg['vlan'])
    except:
        return False

    bcm_src_port = bcm_get_diag_port_name(src_port)
    bcm_dst_port = bcm_get_diag_port_name(dst_port)
    m_mode       = bcm_get_diag_mirror_mode(m_mode)

    ret_val = False
    dp_cmd = "" if not bcm_dst_port else "dp=%s" % bcm_dst_port
    if m_mode == "off" or dp_cmd != "":
        mode_cmd= "mode=%s" % m_mode
        vlan_cmd= ("mtpid=0x8100 mvid=%d" % vlan) if vlan else ""
        tmp_cmd = "dmirror %s %s %s %s" % (bcm_src_port, mode_cmd, dp_cmd, vlan_cmd)
        ret_val = bcm_execute_diag_cmd(tmp_cmd)

    return ret_val

#
# To set vesta port mirror
def bcm_set_vesta_mirror(root_yph, pkey_ar, val, is_create, disp_args):
    """ example:
    {
      "1": {
        "src-port": "Ethernet0",
        "dst-port": "Ethernet3",
        "mode"    : "Both",
        "vlan"    : 4001
      }
    }
    """
    pm_cfg = {} if val == "" else eval(val)

    # only one entry
    if 'src-port' in pm_cfg.keys():
        ret_val = bcm_set_one_port_mirror(pm_cfg)
    else:
        ret_val = True
        for seq_id in pm_cfg.keys():
            ret_val = bcm_set_one_port_mirror(pm_cfg[seq_id])
            if not ret_val:
                break

    return ret_val

# ex:
#      port = None or "" to delete
#   mac_cfg = '{"port": "Ethernet0","mac": "00:00:00:00:00:02","vlan": 4000}'
def bcm_set_one_mac(mac_cfg):
    try:
        mac_port = None if 'port' not in mac_cfg else mac_cfg['port']
        mac_trgt = mac_cfg['mac']
        vlan     = int (mac_cfg['vlan'])
    except:
        return False

    mode_cmd = None
    if mac_port and mac_port != "":
        bcm_mac_port = bcm_get_diag_port_name(mac_port)
        if bcm_mac_port:
            port_cmd = "port=%s" % bcm_mac_port
            mode_cmd = "add"
    else:
        mode_cmd = "del"
        port_cmd = ""

    # ex: l2 add mac=00:00:00:00:00:02 v=10 port=xe5
    ret_val = False
    if mode_cmd:
        tmp_cmd = "l2 %s %s v=%s mac=%s" % (mode_cmd, port_cmd, vlan, mac_trgt)
        ret_val = bcm_execute_diag_cmd(tmp_cmd)

    return ret_val

#
# To set vesta static mac
def bcm_set_vesta_mac(root_yph, pkey_ar, val, is_create, disp_args):
    """ example:
    {
      "1": {
        "port" : "Ethernet0",
        "mac"  : "00:00:00:00:00:02",
        "vlan" : 4001
      }
    }
    """
    mac_cfg = {} if val == "" else eval(val)

    # only one entry
    if 'port' in mac_cfg.keys():
        ret_val = bcm_set_one_mac(mac_cfg)
    else:
        ret_val = True
        for seq_id in mac_cfg.keys():
            ret_val = bcm_set_one_mac(mac_cfg[seq_id])
            if not ret_val:
                break

    return ret_val
