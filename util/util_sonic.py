#
# util_sonic.py
#
# APIs for processing sonic db table.
#

import subprocess, json, pdb, re, util_utl

SONIC_ROOT_PATH = 'sonic'

class oc_custom_subobj(object):
    def __init__(self, path):
        #self.path = path, not used now
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
            self.dispatch_tbl[path] = oc_custom_subobj(path)
            path_helper.register([SONIC_ROOT_PATH, path], self.dispatch_tbl[path])

    def get(self, filter = True):
        data = {}
        for key in self.dispatch_tbl:
            data[key] = self.dispatch_tbl[key].get()
        return data

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
