#
# util_qos.py
#
# APIs for processing qos info.
#

import subprocess
import json
import pdb
import re
import util_utl


#TODO: convert "PORT_QOS_MAP" to interfaces object

# ex: AZURE_1 (NAME + _ + TC)
FWDGRP_NAME_FMT  = '{0}_{1}'

# ex: AZURE_DSCP_1 (NAME + _ + TYPE _ + VAL)
CLFR_NAME_FMT  = '{0}_{1}_{2}'

# ex: DSCP_1 (TYPE _ + VAL)
TERM_NAME_FMT  = '{0}_{1}'

FILL_INFO_NONE  = 0     # fill no info
FILL_INFO_SCHED = 0x01  # fill scheduler info
FILL_INFO_QUEUE = 0x02  # fill queue info
FILL_INFO_FWDGP = 0x04  # fill fwd group info
FILL_INFO_CLSFR = 0x08  # fill classifier info
FILL_INFO_INTFS = 0x10  # fill interface info
FILL_INFO_ALL   = 0xff  # fill all info

SONIC_ROOT_PATH = 'sonic'

@util_utl.utl_timeit
def qos_create_dflt_obj(root_yph, is_dbg_test):
    oc_qos = root_yph.get("/qos")[0]

    for qid in range(0, 8):
        oc_qos.queues.queue.add(str(qid))

    # default scheduler policy
    oc_qos.scheduler_policies.scheduler_policy.add('DEFAULT_EGRESS')

def qos_get_fwdgrp_info(oc_qos, disp_args):
    tc2q_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_TC2Q_MAP)
    for tc2q in tc2q_lst:
        for tc in tc2q_lst[tc2q]:
            fwdgrp_name = FWDGRP_NAME_FMT.format(tc2q, tc)
            if fwdgrp_name not in oc_qos.forwarding_groups.forwarding_group:
                oc_fwd = oc_qos.forwarding_groups.forwarding_group.add(fwdgrp_name)
            else:
                oc_fwd = oc_qos.forwarding_groups.forwarding_group[fwdgrp_name]

            oc_fwd.config.fabric_priority = int(tc)
            q_name = tc2q_lst[tc2q][tc]
            if q_name in oc_qos.queues.queue:
                oc_fwd.config.output_queue = q_name
            else:
                util_utl.utl_err("queue (%d) does not exist !" % q_name)

def qos_get_clfr_info(oc_qos, disp_args):
    dscp2tc_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_DSCP2TC_MAP)
    for dscp2tc in dscp2tc_lst:
        for dscp in dscp2tc_lst[dscp2tc]:
            clfr_name = CLFR_NAME_FMT.format(dscp2tc, 'DSCP', dscp)
            if clfr_name not in oc_qos.classifiers.classifier:
                oc_clfr = oc_qos.classifiers.classifier.add(clfr_name)
                oc_clfr.config.type='IPV4'
            else:
                oc_clfr = oc_qos.classifiers.classifier[clfr_name]

            term_name = TERM_NAME_FMT.format('DSCP', dscp)
            if term_name not in oc_clfr.terms.term:
                oc_term = oc_clfr.terms.term.add(term_name)
                oc_term.conditions.ipv4.config.dscp = int(dscp)
                oc_term.actions.config.target_group = FWDGRP_NAME_FMT.format(dscp2tc, dscp2tc_lst[dscp2tc][dscp])

def qos_get_schdlr_info(oc_qos, disp_args):
    schdlr_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_SCHDLR)
    if schdlr_lst:
        # default WRR, seq 1 (0 reserved for strict priority)
        oc_schd_policy = oc_qos.scheduler_policies.scheduler_policy['DEFAULT_EGRESS']
        if 1 not in oc_schd_policy.schedulers.scheduler:
            oc_schdlr = oc_schd_policy.schedulers.scheduler.add(1)
            oc_schdlr.output.config.output_type = 'INTERFACE'
            # oc_schdlr.config.type = 1r2c or 2r3c
            # oc_schdlr.config.priority = 'STRICT'
        else:
            oc_schdlr = oc_schd_policy.schedulers.scheduler[1]

        for schdlr in schdlr_lst:
            if schdlr not in oc_schdlr.inputs.input:
            # ex: scheduler.0
                oc_inp = oc_schdlr.inputs.input.add(schdlr)
            else:
                oc_inp = oc_schdlr.inputs.input[schdlr]
            # IN_PROFILE/OUT_PROFILE/QUEUE
            oc_inp.config.input_type = 'QUEUE'
            oc_inp.config.weight = int(schdlr_lst[schdlr]['weight'])

        queue_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_QUEUE)
        for inf_q in queue_lst:
            inf, qid = inf_q
            # TODO multi q mapped to one scheduler
            if '-' in qid:
                util_utl.utl_err("extract qid (%s) failed !" % qid)
                continue

            sched_key = queue_lst[inf_q]['scheduler']
            m = re.match(r'\[SCHEDULER\|(.*)\]', sched_key)
            if m:
                if m.group(1) in oc_schdlr.inputs.input:
                    oc_inp = oc_schdlr.inputs.input[m.group(1)]
                    oc_inp.config.queue = qid
                else:
                    util_utl.utl_err("scheduler (%s) does not exist !" % m.group(1))
            else:
                util_utl.utl_err("extract scheduler (%s) from QUEUE failed !" % sched_key)

# fill DUT's current qos info into root_yph
# key_ar [0] : interface name e.g. "eth0"
# ret        : True/False
def qos_get_info(root_yph, path_ar, key_ar, disp_args):
    #pdb.set_trace()
    fill_type_tbl = { "classifiers"         : FILL_INFO_CLSFR,
                      "forwarding-groups"   : FILL_INFO_FWDGP,
                      "queues"              : FILL_INFO_QUEUE,
                      "scheduler-policies"  : FILL_INFO_SCHED,
                      "interfaces"          : FILL_INFO_INTFS,
        }
    try:
        fill_info_type = fill_type_tbl[path_ar[-1]]
    except:
        fill_info_type = FILL_INFO_ALL

    # forwarding group is used by classifier
    func_tbl = [ {'func': qos_get_fwdgrp_info, 'type' : FILL_INFO_FWDGP | FILL_INFO_CLSFR },
                 {'func': qos_get_clfr_info,   'type' : FILL_INFO_CLSFR },
                 {'func': qos_get_schdlr_info, 'type' : FILL_INFO_SCHED },
        ]

    oc_qos = root_yph.get("/qos")[0]
    for func_fld in func_tbl:
        if func_fld['type'] & fill_info_type:
            func_fld['func'](oc_qos, disp_args)

    return True

class oc_custom_subobj(object):
    def __init__(self, path):
        self.path = path
        self.data = {}

    def get(self, filter = True):
        new_data = {}
        is_convert = False

        for key in self.data:
            if isinstance(key, tuple):
                is_convert = True
                fld_str = ""
                for i in range(0, len(key)):
                    if i == 0:
                        fld_str = key[i]
                    else:
                        fld_str = fld_str + '|' + key[i]

                new_data[fld_str] = self.data[key]
            else:
                new_data[key] = self.data[key]

        return self.data if not is_convert else new_data

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
def qos_get_sonic(root_yph, path_ar, key_ar , disp_args):
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
def qos_set_sonic(root_yph, pkey_ar, val, is_create, disp_args):

    exec_cmd = 'sonic-cfggen -a \'%s\' --write-to-db' % val
    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val