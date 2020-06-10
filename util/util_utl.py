#
# util_utl.py
#
# Utility APIs.
#

import subprocess
import json
import logging
import inspect
import sys
import os
import time
import functools

CFGDB_TABLE_NAME_ACL            = 'ACL_TABLE'
CFGDB_TABLE_NAME_RULE           = 'ACL_RULE'
CFGDB_TABLE_NAME_VLAN           = 'VLAN'
CFGDB_TABLE_NAME_VLAN_MBR       = 'VLAN_MEMBER'
CFGDB_TABLE_NAME_MIRROR_SESSION = 'MIRROR_SESSION'
CFGDB_TABLE_NAME_PC             = 'PORTCHANNEL'
CFGDB_TABLE_NAME_NTP            = 'NTP_SERVER'

CFGDB_TABLE_NAME_TC2Q_MAP       = 'TC_TO_QUEUE_MAP'
CFGDB_TABLE_NAME_DSCP2TC_MAP    = 'DSCP_TO_TC_MAP'
CFGDB_TABLE_NAME_QUEUE          = 'QUEUE'
CFGDB_TABLE_NAME_SCHDLR         = 'SCHEDULER'
CFGDB_TABLE_NAME_TC2PG_MAP      = 'TC_TO_PRIORITY_GROUP_MAP'
CFGDB_TABLE_NAME_MAP_PFC_P2Q    = 'MAP_PFC_PRIORITY_TO_QUEUE'
CFGDB_TABLE_NAME_PORT_QOS_MAP   = 'PORT_QOS_MAP'
CFGDB_TABLE_NAME_WRED_PROFILE   = 'WRED_PROFILE'

CFGDB_TABLE_NAME_VXLAN_TUNNEL    = 'VXLAN_TUNNEL'
CFGDB_TABLE_NAME_VXLAN_TUNNEL_MAP= 'VXLAN_TUNNEL_MAP'

CFGDB_TABLE_NAME_INTF           = 'INTERFACE'
CFGDB_TABLE_NAME_PC_INTF        = 'PORTCHANNEL_INTERFACE'
CFGDB_TABLE_NAME_VLAN_INTF      = 'VLAN_INTERFACE'
CFGDB_TABLE_NAME_LBK_INTF       = 'LOOPBACK_INTERFACE'

GET_VAR_LST_CMD_TMPL = 'sonic-cfggen -d -v "{0}"'
CFG_WRITE_DB_CMD_TMPL= 'sonic-cfggen -a \'{{"{0}": {{"%s" : %s}}}}\' --write-to-db'
CFG_ACL_CMD_TMPL     = CFG_WRITE_DB_CMD_TMPL.format(CFGDB_TABLE_NAME_ACL)
CFG_RUL_CMD_TMPL     = CFG_WRITE_DB_CMD_TMPL.format(CFGDB_TABLE_NAME_RULE)
CFG_MSESS_CMD_TMPL   = CFG_WRITE_DB_CMD_TMPL.format(CFGDB_TABLE_NAME_MIRROR_SESSION)
CFG_PC_CMD_TMPL      = CFG_WRITE_DB_CMD_TMPL.format(CFGDB_TABLE_NAME_PC)

RULE_MAX_PRI         = 10000 # refer to acl_loader
RULE_MIN_PRI         = 1

DBG_MODE  = 1
DBG_PERF  = 1

VLAN_SUB_INTERFACE_SEPARATOR = '.'

def utl_log(str, lvl = logging.DEBUG, c_lvl=1):
    if DBG_MODE == 1:
        print str

    f1 = sys._getframe(c_lvl)

    if f1:
        my_logger = logging.getLogger()
        if lvl < my_logger.getEffectiveLevel(): return
        rec = my_logger.makeRecord(
            'gnmi_svr',
            lvl,
            os.path.basename(f1.f_code.co_filename),
            f1.f_lineno,
            str,
            None,
            None,
            f1.f_code.co_name)

        my_logger.handle(rec)
    else:
        logging.log (lvl, str)

def utl_err(str):
    utl_log(str, logging.ERROR, 2)

# decorator to get function execution time
def utl_timeit(f):
    @functools.wraps(f)
    def timed(*args, **kw):
        if DBG_PERF:
            t_beg = time.time()
            result = f (*args, **kw)
            t_end = time.time()
            utl_log("Time spent %s : %s %s" %  ((t_end - t_beg), f.__name__, args), logging.CRITICAL, 2)
        else:
            result = f (*args, **kw)

        return result
    return timed

# decorator to add separation line in logs
def utl_log_outer(f):
    @functools.wraps(f)
    def wrapped(*args, **kw):
        if DBG_PERF:
            utl_log("beg ==================", logging.CRITICAL, 3)
            result = f (*args, **kw)
            utl_log("end ==================", logging.CRITICAL, 3)
        else:
            result = f (*args, **kw)

        return result
    return wrapped

@utl_timeit
def utl_execute_cmd(exe_cmd):
    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        # if no decorator, use inspect.stack()[1][3] to get caller
        utl_log("Failed to [%s] by %s !!! (%s)" % (exe_cmd, inspect.stack()[2][3], err), logging.ERROR)
        return False

    return True

@utl_timeit
def utl_get_execute_cmd_output(exe_cmd):
    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        # if no decorator, use inspect.stack()[1][3] to get caller
        utl_log("Failed to [%s] by %s !!!" % (exe_cmd, inspect.stack()[2][3]), logging.ERROR)
        return (False, None)

    return (True, output)


def get_interface_table_name(interface_name):
    """Get table name by interface_name prefix"""

    if interface_name.startswith("Ethernet"):
        if VLAN_SUB_INTERFACE_SEPARATOR in interface_name:
            return "VLAN_SUB_INTERFACE"
        return "INTERFACE"
    elif interface_name.startswith("PortChannel"):
        if VLAN_SUB_INTERFACE_SEPARATOR in interface_name:
            return "VLAN_SUB_INTERFACE"
        return "PORTCHANNEL_INTERFACE"
    elif interface_name.startswith("Vlan"):
        return "VLAN_INTERFACE"
    elif interface_name.startswith("Loopback"):
        return "LOOPBACK_INTERFACE"
    else:
        return ""


def interface_ipaddr_dependent_on_interface(config_db, interface_name):
    """Get table keys including ipaddress"""

    data = []
    table_name = get_interface_table_name(interface_name)
    if table_name == "":
        return data
    keys = config_db.get_keys(table_name)
    for key in keys:
        if interface_name in key and len(key) == 2:
            data.append(key)
    return data
