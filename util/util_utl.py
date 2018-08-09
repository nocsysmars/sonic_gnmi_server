#
# util_utl.py
#
# Utility APIs.
#

import subprocess
import json
import logging
import inspect

DBG_MODE = 1

def utl_log(str, lvl = logging.DEBUG):
    if DBG_MODE == 1:
        print str

    logging.log (lvl, str)

def utl_execute_cmd(exe_cmd):
    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        utl_log("Failed to [%s] by %s !!!" % (exe_cmd, inspect.stack()[1][3]), logging.ERROR)
        return False

    return True

def utl_get_execute_cmd_output(exe_cmd):
    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if returncode != 0:
        utl_log("Failed to [%s] by %s !!!" % (exe_cmd, inspect.stack()[1][3]), logging.ERROR)
        return (False, None)

    return (True, output)
