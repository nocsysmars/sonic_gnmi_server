#
# util_nwi.py
#
# APIs for processing network instance info.
#

import subprocess
import json
import pdb
from util import util_utl

@util_utl.utl_timeit
def nwi_create_dflt_nwi(nwi_yph, is_dbg_test):
    oc_nwis = nwi_yph.get("/network-instances")[0]
    oc_nwi_dflt = oc_nwis.network_instance.add('default')

    # create all vlans
#    for v in range(1, 100):
#        oc_nwi_dflt.vlans.vlan.add(str(v))

#    pdb.set_trace()
#    pass

def nwi_get_info(nwi_yph, key_ar):
    """
    fdbshow example:
    No.    Vlan  MacAddress         Port
    -----  ------  -----------------  ---------
        1    1111  CC:37:AB:EC:D9:B2  Ethernet2
        2    2001  00:00:00:00:00:01  Ethernet5
        3    3001  00:00:00:00:00:01  Ethernet5
    Total number of entries 3
    """
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('fdbshow')
    if is_ok:
        oc_nwi_dflt = nwi_yph.get("/network-instances/network-instance[name=default]")[0]
        oc_nwi_dflt.fdb.mac_table._unset_entries()
        output = output.splitlines()
        # skip element 0/1, refer to output of fdbshow

        for idx in range(2, len(output)-1):
            ldata = output[idx].split()
            mac_entry = oc_nwi_dflt.fdb.mac_table.entries.entry.add(mac_address=ldata[2], vlan=int(ldata[1]))
            mac_entry.interface.interface_ref.config.interface = ldata[3]

        #pdb.set_trace()

        return True
