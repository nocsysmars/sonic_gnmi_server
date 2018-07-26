#
# oc_dispatcher.py
#
# OpenConfig Dispatcher
#

from oc_binding.oc_if_binding import openconfig_interfaces
from oc_binding.oc_lldp_binding import openconfig_lldp
from oc_binding.oc_platform_binding import openconfig_platform
from pyangbind.lib.xpathhelper import YANGPathHelper
from grpc import StatusCode

from util import util_lldp
from util import util_interface
from util import util_platform

import subprocess
import json

# Dispatch table for openconfig class and info function
ocTable = {
    "interfaces" : { "cls"   : openconfig_interfaces,
                     "info_f": "util_interface.interface_get_info"  },
    "lldp"       : { "cls"   : openconfig_lldp,
                     "info_f": "util_lldp.lldp_get_info"            },
    "components" : { "cls"   : openconfig_platform,
                     "info_f": "util_platform.platform_get_info"    },
}

class ocDispatcher:
    """ Open Config Dispatcher that dispatch requests to
        other openconfig binding modules """
    def __init__(self):
        # create the full yang tree
        # for performance, only update the tree node requested
        self.oc_yph = YANGPathHelper()
        for k in ocTable.keys():
            ocTable[k]["cls"](path_helper= self.oc_yph)

    def CreateAllInterfaces(self):
        return util_interface.interface_create_all_infs(self.oc_yph)

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


