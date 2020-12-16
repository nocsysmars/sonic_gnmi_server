#!/bin/bash
SDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYBINDPLUGIN=`/usr/bin/env python -c 'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))'`
pyang --plugindir $PYBINDPLUGIN -f pybind -p $SDIR/ -o $SDIR/oc_sys_binding.py --use-xpathhelper $SDIR/openconfig-system.yang   

echo "Bindings successfully generated!"


