#
# oc_dispatcher.py
#
# OpenConfig Dispatcher
#

from oc_binding.oc_if_binding import openconfig_interfaces
from oc_binding.oc_lldp_binding import openconfig_lldp
from oc_binding.oc_platform_binding import openconfig_platform
from oc_binding.oc_nwi_binding import openconfig_network_instance
from pyangbind.lib.xpathhelper import YANGPathHelper
from grpc import StatusCode

from util import util_lldp
from util import util_interface
from util import util_platform
from util import util_utl
from util import util_nwi

import re
#import pdb

# Dispatch table for openconfig class and info function
ocTable = {
    "interfaces" : { "cls"   : openconfig_interfaces,
                     "info_f": "util_interface.interface_get_info"  },
    "lldp"       : { "cls"   : openconfig_lldp,
                     "info_f": "util_lldp.lldp_get_info"            },
    "components" : { "cls"   : openconfig_platform,
                     "info_f": "util_platform.platform_get_info"    },
    "network-instances" : {
                     "cls"   : openconfig_network_instance,
                     "info_f": "util_nwi.nwi_get_info"              },
}

# Dispatch table for registered path and set function
setPathTable = {
    # path : set function
    # [xxx] means key
    '/interfaces/interface[name]/ethernet/config/aggregate-id' :
            "util_interface.interface_set_aggregate_id",
    '/interfaces/interface[name]/config/name' :
            "util_interface.interface_set_cfg_name",
    '/interfaces/interface[name]/config/enabled' :
            "util_interface.interface_set_cfg_enabled",
    '/interfaces/interface[name]/ethernet/switched-vlan/config/trunk-vlans' :
            "util_interface.interface_set_trunk_vlans",
    '/interfaces/interface[name]/ethernet/switched-vlan/config/native-vlan' :
            "util_interface.interface_set_native_vlan",
}

class ocDispatcher:
    """ Open Config Dispatcher that dispatch requests to
        other openconfig binding modules """
    def __init__(self, is_dbg_test):
        # create the full yang tree
        # for performance, only update the tree node requested
        self.oc_yph = YANGPathHelper()
        for k in ocTable.keys():
            ocTable[k]["cls"](path_helper= self.oc_yph)

        # create all interfaces to speed up processing request for interfaces later
        util_interface.interface_create_all_infs(self.oc_yph, is_dbg_test)

        # create default network instance
        util_nwi.nwi_create_dflt_nwi(self.oc_yph, is_dbg_test)


    #def CreateAllInterfaces(self, is_dbg_test):
    #    return util_interface.interface_create_all_infs(self.oc_yph, is_dbg_test)

    @util_utl.utl_timeit
    @util_utl.utl_log_outer
    def GetRequestYph(self, path_ar, key_ar):
        # TODO: not support "/"
        if len(path_ar) < 1:
            #print "Invalid request"
            return StatusCode.INVALID_ARGUMENT

        if path_ar[0] not in ocTable:
            oc_yph = StatusCode.INVALID_ARGUMENT
        else:
            oc_yph = self.oc_yph
            if path_ar != ['interfaces', 'interface', 'config', 'name']:
                # suppose key_ar [0] is interface name e.g. "eth0"
                ret_val = eval(ocTable[path_ar[0]]["info_f"])(oc_yph, key_ar)
                if not ret_val: oc_yph = StatusCode.INTERNAL

        return oc_yph

    @util_utl.utl_timeit
    @util_utl.utl_log_outer
    def SetValByPath(self, yp_str, pkey_ar, val):
        tmp_obj = self.oc_yph.get(yp_str)

        # replace key [xxx=yyy] with [xxx]
        reg_path = re.sub(r'\[(\w*)=.*\]', r"[\1]", yp_str)

        #pdb.set_trace()
        ret_val = eval(setPathTable[reg_path])(self.oc_yph, pkey_ar, val.strip('"'), len(tmp_obj) == 0) \
                    if reg_path in setPathTable else False

        return ret_val

