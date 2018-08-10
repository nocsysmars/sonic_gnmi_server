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

DBG_MODE  = 1
DBG_PERF  = 1

def utl_log(str, lvl = logging.DEBUG):
    if DBG_MODE == 1:
        print str

    f1 = sys._getframe(1)
    if f1:
        my_logger = logging.getLogger()
        if lvl < my_logger.getEffectiveLevel(): return
        rec = my_logger.makeRecord(
            'gnmi_svr',
            lvl,
            f1.f_code.co_filename,
            f1.f_lineno,
            str,
            None,
            None,
            os.path.basename(f1.f_code.co_filename))

        my_logger.handle(rec)
    else:
        logging.log (lvl, str)

def utl_execute_cmd(exe_cmd):
    if DBG_PERF:
        time_beg = time.time()

    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if DBG_PERF:
        time_end = time.time()
        utl_log("Time spent %s : (%s)" %  ((time_end - time_beg), exe_cmd), logging.CRITICAL)

    if returncode != 0:
        utl_log("Failed to [%s] by %s !!!" % (exe_cmd, inspect.stack()[1][3]), logging.ERROR)
        return False

    return True

def utl_get_execute_cmd_output(exe_cmd):
    if DBG_PERF:
        time_beg = time.time()

    p = subprocess.Popen(exe_cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    ## Wait for end of command. Get return code ##
    returncode = p.wait()

    if DBG_PERF:
        time_end = time.time()
        utl_log("Time spent %s : (%s)" %  ((time_end - time_beg), exe_cmd), logging.CRITICAL)

    if returncode != 0:
        utl_log("Failed to [%s] by %s !!!" % (exe_cmd, inspect.stack()[1][3]), logging.ERROR)
        return (False, None)

    return (True, output)
