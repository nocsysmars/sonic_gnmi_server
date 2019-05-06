#
# util_sonic.py
#
# APIs for processing sonic db table.
#

import subprocess, json, pdb, re, util_utl

SONIC_ROOT_PATH = 'sonic'

SWSS_CFG_TMPL_FDB ="""
[
     {
        "FDB_TABLE:Vlan%d:%s": {
               "port": "%s",
               "type": "static"
           },
           "OP": "%s"
      }
]
"""


class oc_custom_subobj(object):
    def __init__(self, path):
        self.path = path
        self._data = {}

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if isinstance(value, dict):
            self._data = {}
            for key in value:
                if isinstance(key, tuple):
                    fld_str = ""
                    for i in range(0, len(key)):
                        if i == 0:
                            fld_str = key[i]
                        else:
                            fld_str = fld_str + '|' + key[i]

                    self._data[fld_str] = value[key]
                else:
                    self._data[key] = value[key]
        else:
            self._data = value

    def get(self, filter = True):
        return self.data

    def _yang_path(self):
        return self.path

class openconfig_custom(object):
    def __init__(self, path_helper):
        path_helper.register([SONIC_ROOT_PATH], self)
        self.dispatch_tbl = {}
        reg_path = {
            util_utl.CFGDB_TABLE_NAME_TC2Q_MAP,
            util_utl.CFGDB_TABLE_NAME_DSCP2TC_MAP,
            util_utl.CFGDB_TABLE_NAME_QUEUE,
            util_utl.CFGDB_TABLE_NAME_SCHDLR,
            util_utl.CFGDB_TABLE_NAME_TC2PG_MAP,
            util_utl.CFGDB_TABLE_NAME_MAP_PFC_P2Q,
            util_utl.CFGDB_TABLE_NAME_PORT_QOS_MAP,
            util_utl.CFGDB_TABLE_NAME_WRED_PROFILE,
            util_utl.CFGDB_TABLE_NAME_VXLAN_TUNNEL,
            util_utl.CFGDB_TABLE_NAME_VXLAN_TUNNEL_MAP,
            }

        for path in reg_path:
            self.dispatch_tbl[path] = oc_custom_subobj('/'.join(['', SONIC_ROOT_PATH, path]))
            path_helper.register([SONIC_ROOT_PATH, path], self.dispatch_tbl[path])

    def get(self, filter = True):
        data = {}
        for key in self.dispatch_tbl:
            data[key] = self.dispatch_tbl[key].get()
        return data

    def _yang_path(self):
        return '/' + SONIC_ROOT_PATH

# ex: path_ar = [u'sonic', u'SCHEDULER']
# To get sonic qos settings
def sonic_get_sonic(root_yph, path_ar, key_ar, disp_args):
    oc_sonic = root_yph.get('/sonic')[0]
    if len (path_ar) == 1:
        disp_tbl = oc_sonic.dispatch_tbl
    else:
        if path_ar[1] in oc_sonic.dispatch_tbl:
            disp_tbl = {path_ar[1]}
        else:
            disp_tbl = {}

    for key in disp_tbl:
        oc_sonic.dispatch_tbl[key].data = disp_args.cfgdb.get_table(key)

    return True

#
# To set sonic qos settings
def sonic_set_sonic(root_yph, pkey_ar, val, is_create, disp_args):

    exec_cmd = 'sonic-cfggen -a \'%s\' --write-to-db' % val
    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val

# Use swssconfig to set static mac
# ex:
#      mode = None to add / "del" to delete
#   mac_cfg = '{"port": "Ethernet0","mac": "00:00:00:00:00:02","vlan": 4000,"mode": "del"}'
def sonic_set_one_mac_swss(mac_cfg):
    try:
        mac_port = None if 'port' not in mac_cfg else mac_cfg['port']
        mac_trgt = mac_cfg['mac']
        vlan     = int (mac_cfg['vlan'])
        mac_mode = "SET" if 'mode' not in mac_cfg else mac_cfg['mode'].upper()
    except:
        return False

    conf =  SWSS_CFG_TMPL_FDB % (vlan, mac_trgt.replace(':', '-'), mac_port, mac_mode)

    exec_cmd = "echo '%s' | (docker exec -i swss bash -c 'cat > /tmp/fdb.json')" \
                % (conf)
    if not util_utl.utl_execute_cmd(exec_cmd): return False

    exec_cmd = 'docker exec -i swss swssconfig /tmp/fdb.json'
    if not util_utl.utl_execute_cmd(exec_cmd): return False

    return True

#
# To set vesta static mac
def sonic_set_vesta_mac(root_yph, pkey_ar, val, is_create, disp_args):
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
        ret_val = sonic_set_one_mac_swss(mac_cfg)
    else:
        ret_val = True
        for seq_id in mac_cfg.keys():
            ret_val = sonic_set_one_mac_swss(mac_cfg[seq_id])
            if not ret_val:
                break

    return ret_val
