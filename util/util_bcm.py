#
# util_bcm.py
#
# Utility APIs for bcm diag shell.
#

import subprocess, json, logging, inspect
import sys, os, time, functools, util_utl, re, pdb

BCM_PHY_PORT_MAP = {}   # key : Ethernet#
BCM_USR_PORT_MAP = {}   # key : xe#
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

VESTA_ROOT_PATH     = 'vesta'
VESTA_TABLE_NAME_PM = 'mirror'

class oc_subobj_pm(object):
    def __init__(self, path):
        self.path = path
        self._data = {}

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def get(self, filter = True):
        return self.data

    def _yang_path(self):
        return self.path

class openconfig_vesta(object):
    def __init__(self, path_helper):
        path_helper.register([VESTA_ROOT_PATH], self)
        self.dispatch_tbl = {}
        reg_path = {
                VESTA_TABLE_NAME_PM : oc_subobj_pm
            }

        for path in reg_path.keys():
            self.dispatch_tbl[path] = reg_path[path]('/'.join(['', VESTA_ROOT_PATH, path]))
            path_helper.register([VESTA_ROOT_PATH, path], self.dispatch_tbl[path])

    def get(self, filter = True):
        data = {}
        for key in self.dispatch_tbl:
            data[key] = self.dispatch_tbl[key].get()
        return data

    def _yang_path(self):
        return '/' + VESTA_ROOT_PATH

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

@util_utl.utl_timeit
def bcm_get_execute_diag_cmd_output(exe_cmd):
    diag_cmd = BCM_DIAG_CMD_TMPL % exe_cmd
    p = subprocess.Popen(diag_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        # if no decorator, use inspect.stack()[1][3] to get caller
        util_utl.utl_log("Failed to [%s] by %s !!!" % (diag_cmd, inspect.stack()[2][3]), logging.ERROR)
        return (False, None)

    if any(x in output for x in ['Fail', 'Err']):
        util_utl.utl_log("Failed to [%s] by %s !!!" % (diag_cmd + '(' + output +')',
                inspect.stack()[2][3]), logging.ERROR)
        return (False, None)

    return (True, output)

# get a dictionary mapping port name ("Ethernet48") to a physical port number
def bcm_get_diag_port_map():
    global BCM_PHY_PORT_MAP, BCM_USR_PORT_MAP, BCM_PORT_MAP_INIT

    if BCM_PORT_MAP_INIT: return

    exe_cmd = 'docker exec -i syncd cat /usr/share/sonic/hwsku/port_config.ini'
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exe_cmd)
    if is_ok:
        # Default column definition
        titles = ['name', 'lanes', 'alias', 'index']
        output = output.splitlines()
        BCM_PHY_PORT_MAP = {}
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
            BCM_PHY_PORT_MAP[name] = data

        for key in BCM_PHY_PORT_MAP.keys():
            BCM_USR_PORT_MAP['xe'+BCM_PHY_PORT_MAP[key]['index']] = key

        BCM_PORT_MAP_INIT = True

# convert "Ethernet#" to "xe#"
def bcm_get_phy_port_name(usr_port_name):
    global BCM_PHY_PORT_MAP

    bcm_get_diag_port_map()

    phy_port_name = None
    if usr_port_name:
        if usr_port_name in BCM_PHY_PORT_MAP:
            phy_port_name = 'xe%s' % BCM_PHY_PORT_MAP[usr_port_name]['index']
        else:
            util_utl.utl_err("Failed to get diag port name (%s)" % usr_port_name)

    return phy_port_name

# convert "xe#" to "Ethernet#"
def bcm_get_usr_port_name(phy_port_name):
    global BCM_USR_PORT_MAP

    bcm_get_diag_port_map()

    usr_port_name = None
    if phy_port_name:
        if phy_port_name in BCM_USR_PORT_MAP:
            usr_port_name = BCM_USR_PORT_MAP[phy_port_name]
        else:
            util_utl.utl_err("Failed to get port name (%s)" % phy_port_name)

    return usr_port_name

# ex: in_mode = 'BOTH', in_type = 'gtag'
#     in_mode = 'all',  in_type = 'diag'
def bcm_get_mirror_mode_by_type(in_mode, in_type):

    out_type = 'diag' if in_type == 'gtag' else 'gtag'

    ret_val = None
    for key in BCM_MIRROR_MODE_TBL.keys():
        if BCM_MIRROR_MODE_TBL[key][in_type] == in_mode:
            ret_val = BCM_MIRROR_MODE_TBL[key][out_type]
            break

    if not ret_val:
        util_utl.utl_err("Failed to get mirror mode (%s/%s)" % (in_mode, in_type))

    return ret_val

# ex: in_mode = 'BOTH'
#     ret_val = 'all'
def bcm_get_diag_mirror_mode(in_mode):
    return bcm_get_mirror_mode_by_type(in_mode, 'gtag')

# ex: in_mode = 'all'
#     ret_val = 'BOTH'
def bcm_get_user_mirror_mode(in_mode):
    return bcm_get_mirror_mode_by_type(in_mode, 'diag')

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

    bcm_src_port = bcm_get_phy_port_name(src_port)
    bcm_dst_port = bcm_get_phy_port_name(dst_port)
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
# To set port mirror
def bcm_set_port_mirror(root_yph, pkey_ar, val, is_create, disp_args):
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

def bcm_extract_one_mirror_info(mir_diag_str, pat_obj):
    # ex:
    #  xe3: Mirror egress to local port xe5 (TPID=0x8100(33024), VLAN=0x0064(100))
    #  g1 -> xe3,    "src-port"
    #  g2 -> egress, "mode"
    #  g3 -> xe5,    "dst-port"
    #  g4 -> 100     "vlan"     (optional)
    #
    ret_val = None
    match = pat_obj.match(mir_diag_str)
    if match:
        ret_val = { "src-port" : bcm_get_usr_port_name(match.group(1)),
                    "dst-port" : bcm_get_usr_port_name(match.group(3)),
                    "mode"     : bcm_get_user_mirror_mode(match.group(2)) }

        if match.group(4):
            ret_val["vlan"] = int(match.group(4))

    return ret_val

def bcm_get_mirror_info():
    (is_ok, output) = bcm_get_execute_diag_cmd_output('dmirror show')
    output = output.replace('\r','').split('\n')

    # ex:
    # dmirror show
    #  xe1: Mirror all to local port xe3
    #  xe3: Mirror egress to local port xe5 (TPID=0x8100(33024), VLAN=0x0064(100))
    #
    # dmirror show
    # DMIRror: No mirror ports configured
    #
    pat_obj = re.compile(r'\s*(xe\d+): Mirror (\w*) to local port (xe\d+)(?:\s\(TPID=.*?, VLAN=.*?\((\d+)\))?')
    idx = 1
    ret_val = {}
    for line in output:
        tmp_ret = 'to' in line and bcm_extract_one_mirror_info(line, pat_obj)
        if tmp_ret:
            ret_val[str(idx)] = tmp_ret
            idx = idx +1

    return ret_val

# fill port mirror info into root_yph
def bcm_get_info(root_yph, path_ar, key_ar, disp_args):
    oc_vesta = root_yph.get('/'+VESTA_ROOT_PATH)[0]
    if len (path_ar) == 1 or path_ar[1] == VESTA_TABLE_NAME_PM:
        oc_vesta.dispatch_tbl[VESTA_TABLE_NAME_PM].data = bcm_get_mirror_info()

    return True

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
        bcm_mac_port = bcm_get_phy_port_name(mac_port)
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
# To add/del mac address
def bcm_set_mac(root_yph, pkey_ar, val, is_create, disp_args):
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
