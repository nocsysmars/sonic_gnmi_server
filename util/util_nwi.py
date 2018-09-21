#
# util_nwi.py
#
# APIs for processing network instance info.
#

import subprocess
import json
import pdb
import util_utl

from util_utl import GET_ACL_TBL_LST_CMD
from util_utl import GET_ACL_RUL_LST_CMD
from util_utl import CFG_ACL_CMD_TMPL
from util_utl import CFG_RUL_CMD_TMPL
from util_utl import RULE_MAX_PRI
from util_utl import RULE_MIN_PRI

DEFAULT_NWI_NAME = 'DEFAULT'

GET_MSESS_LST_CMD    = util_utl.GET_VAR_LST_CMD_TMPL.format("MIRROR_SESSION")

FILL_INFO_NONE  = 0     # fill no info
FILL_INFO_FDB   = 0x01  # fill fdb info
FILL_INFO_PF    = 0x02  # fill policy-forwarding info
FILL_INFO_INTFS = 0x04  # fill interface info
FILL_INFO_ALL   = 0xff  # fill all info

# convert sonic to openconfig yang model
INT_TYPE = 1
STR_TYPE = 2
HEX_TYPE = 3
NON_TYPE = 4
OCYANG_FLDMAP_TBL_PF = {
    'IP_PROTOCOL' : {'str':'ipv4.config.protocol',             'type': INT_TYPE }, # 5
    'SRC_IP'      : {'str':'ipv4.config.source_address',       'type': STR_TYPE }, # '1.1.1.1/24'
    'DST_IP'      : {'str':'ipv4.config.destination_address',  'type': STR_TYPE },
    'DSCP'        : {'str':'ipv4.config.dscp',                 'type': INT_TYPE }, # 5
    'ETHER_TYPE'  : {'str':'l2.config.ethertype',              'type': INT_TYPE }, # 5
    'L4_SRC_PORT' : {'str':'transport.config.source_port',     'type': INT_TYPE },
    'L4_DST_PORT' : {'str':'transport.config.destination_port','type': INT_TYPE },
    'TCP_FLAGS'   : {'str':'transport.config.tcp_flags',       'type': INT_TYPE },
    'MIRROR_ACTION':{'str':'not_used',                         'type': STR_TYPE },
    'PRIORITY'    : {'str':'not_used',                         'type': NON_TYPE },
    }

@util_utl.utl_timeit
def nwi_create_dflt_nwi(nwi_yph, is_dbg_test):
    oc_nwis = nwi_yph.get("/network-instances")[0]
    oc_nwi_dflt = oc_nwis.network_instance.add(DEFAULT_NWI_NAME)
    oc_nwi_dflt.config.enabled = True
    oc_nwi_dflt.config.type = 'DEFAULT_INSTANCE'

# key_ar[0] : 'DEFAULT' (instance name)
# key_ar[1] : mac
# key_ar[2] : vlan
def nwi_get_fdb_info(oc_nwis, path_ar, key_ar):
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
        key_mac  = None
        key_vlan = None
        if key_ar:
            if key_ar[0] in oc_nwis.network_instance:
                oc_nwi = oc_nwis.network_instance[key_ar[0]]
            else:
                return False

            if len(key_ar) > 3: return False

            for key in key_ar[1:]:
                if ':' in key:
                    if key_mac != None: return False
                    key_mac = key
                else:
                    if key_vlan != None: return False
                    key_vlan = key
        else:
            # only support default network instance
            oc_nwi = oc_nwis.network_instance[DEFAULT_NWI_NAME]

        oc_nwi.fdb.mac_table._unset_entries()
        output = output.splitlines()
        # skip element 0/1, refer to output of fdbshow
        for idx in range(2, len(output)-1):
            ldata = output[idx].split()
            if key_mac  and key_mac  != ldata[2]: continue
            if key_vlan and key_vlan != ldata[1]: continue

            mac_entry = oc_nwi.fdb.mac_table.entries.entry.add(mac_address=ldata[2], vlan=int(ldata[1]))
            mac_entry.interface.interface_ref.config.interface = ldata[3]
            mac_entry.state._set_entry_type('DYNAMIC')

        return True

# ex: act_data = 'session1'
#     mess_lst = '{}'
# add a action to oc_rule with act_data and msess_lst
def nwi_pf_add_one_mirror_action(oc_rule, act_data, msess_lst):
    if act_data in oc_rule.action.encapsulate_gre.targets.target:
        oc_target = oc_rule.action.encapsulate_gre.targets.target['act_data']
    else:
        oc_target = oc_rule.action.encapsulate_gre.targets.target.add(act_data)

    if act_data in msess_lst:
        oc_target.config.source      = msess_lst[act_data]['src_ip']
        oc_target.config.destination = msess_lst[act_data]['dst_ip'] + '/32'
        oc_target.config.ip_ttl      = msess_lst[act_data]['ttl']

# add a rule to oc_pol with rule_name and rule_data
def nwi_pf_add_one_rule(oc_pol, rule_name, rule_data, msess_lst):
    # {0} : entry name
    # {1} : field
    # {2} : value
    pdb.set_trace()
    EXEC_STR_TMPL = '{0}.{1} = {2}'
    seq_id = RULE_MAX_PRI - int(rule_data['PRIORITY'])
    oc_rule = oc_pol.rules.rule.add(seq_id)

    for d_key in rule_data.keys():
        if d_key in OCYANG_FLDMAP_TBL_PF:
            if OCYANG_FLDMAP_TBL_PF[d_key]['type'] == NON_TYPE: continue

            value_str = rule_data[d_key]

            if value_str == 'None': continue

            if d_key == 'MIRROR_ACTION':
                nwi_pf_add_one_mirror_action(oc_rule, value_str, msess_lst)
                value_str = None

            elif d_key == 'TCP_FLAGS':
                pass
                #TODO: value_str = acl_cnv_to_oc_tcp_flags(value_str)

            if value_str:
                if OCYANG_FLDMAP_TBL_PF[d_key]['type'] == STR_TYPE:
                    value_str = '"{0}"'.format(value_str)

                exec_str = EXEC_STR_TMPL.format("oc_rule", OCYANG_FLDMAP_TBL_PF[d_key]['str'], value_str)
                exec(exec_str)
        else:
            util_utl.utl_err("field(%s) is not supported !" % d_key)

# fill binding info for policy-forwarding
def nwi_pf_fill_binding_info(oc_pf, acl_name, acl_info):
    for port in acl_info['ports']:
        if port == '': continue

        if port not in oc_pf.interfaces.interface:
            oc_pf_inf = oc_pf.interfaces.interface.add(port)
        else:
            oc_pf_inf = oc_pf.interfaces.interface[port]

        oc_pf_inf.config.apply_forwarding_policy = acl_name

# key_ar[0] : 'DEFAULT' (instance name)
def nwi_get_pf_info(oc_nwis, path_ar, key_ar):
    oc_pf = oc_nwis.network_instance[DEFAULT_NWI_NAME].policy_forwarding

    old_pol_lst = [ x for x in oc_pf.policies.policy ]
    for old_pol in old_pol_lst:
        oc_pf.policies.policy.delete(old_pol)

    # clear binding info
    old_inf_lst = [ x for x in oc_pf.interfaces.interface ]
    for old_inf in old_inf_lst:
        oc_pf.interfaces.interface.delete(old_inf)

    ret_val = False
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_MSESS_LST_CMD)
    if is_ok:
        msess_lst = {} if output.strip('\n') =='' else eval(output)

    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_ACL_TBL_LST_CMD)
    if is_ok:
        acl_tlst = {} if output.strip('\n') =='' else eval(output)
        ret_val = True

    if acl_tlst:
        (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_ACL_RUL_LST_CMD)
        if is_ok:
            acl_rlst = {} if output.strip('\n') =='' else eval(output)

        for acl_name in acl_tlst.keys():
            if acl_tlst[acl_name]['type'] == 'MIRROR':
                oc_pol = oc_pf.policies.policy.add(acl_name)

                for acl_rule_key in acl_rlst.keys():
                    if acl_name in acl_rule_key:
                        oc_acl_rule = nwi_pf_add_one_rule(oc_pol, acl_rule_key[1], acl_rlst[acl_rule_key], msess_lst)

        # all policies should be created first before being used by interfaces
        # otherwise the reference relationship will be corrupted.
        for acl_name in acl_tlst.keys():
            if acl_tlst[acl_name]['type'] == 'MIRROR':
                nwi_pf_fill_binding_info(oc_pf, acl_name, acl_tlst[acl_name])

    return ret_val

# key_ar[0] : 'DEFAULT' (instance name)
def nwi_get_info(root_yph, path_ar, key_ar):
    fill_type_tbl = { "fdb"                 : FILL_INFO_FDB,
                      "policy-forwarding"   : FILL_INFO_PF,
                    #  "interfaces"          : FILL_INFO_INTFS,
    }
    try:
        fill_info_type = fill_type_tbl[path_ar[-1]]
    except:
        fill_info_type = FILL_INFO_ALL

    func_tbl = [ {'func': nwi_get_fdb_info,  'type' : FILL_INFO_FDB   },
                 {'func': nwi_get_pf_info,   'type' : FILL_INFO_PF    },
#                 {'func': nwi_get_intfs_info,'type' : FILL_INFO_INTFS },
    ]

    oc_nwis = root_yph.get("/network-instances")[0]
    for func_fld in func_tbl:
        if func_fld['type'] & fill_info_type:
            func_fld['func'](oc_nwis, path_ar, key_ar)

    return True

# ex:    pkey_ar = [u'DEFAULT', u'Ethernet10']
#   val for del  = '' or '{}'
#   val for add  = '{"apply-forwarding-policy": "lll"}'
#
# To bind/unbind a policy to an interface
def nwi_pf_set_interface(root_yph, pkey_ar, val, is_create):
    pdb.set_trace()

    ret_val = False

    # 1. get old port list
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_ACL_TBL_LST_CMD)
    if is_ok:
        # ex: {'type': 'MIRROR', 'policy_desc': 'lll', 'ports': ['']}
        acl_lst = {} if output.strip('\n') =='' else eval(output)

    # acl must be created b4 binding to interface
    if acl_lst:
        acl_name = None
        if val == "" or val == "{}":
            is_add = False
            for acl in acl_lst:
                if pkey_ar[1] in acl_lst[acl]['ports']:
                    acl_name = acl
                    acl_cfg  = acl_lst[acl]
                    break

            if not acl_name: return False
        else:
            try:
                tmp_cfg = eval(val)
                acl_name = tmp_cfg['apply-forwarding-policy']
                acl_cfg  = acl_lst[acl_name]
            except:
                return False

            is_add = True

        if acl_cfg['type'] != 'MIRROR': return False

        if '' in acl_cfg['ports']:
            acl_cfg['ports'].remove('')

        is_changed = False
        # 2. add/remove new port to/from old port list
        if is_add:
            if pkey_ar[1] not in acl_cfg['ports']:
                acl_cfg['ports'].append(pkey_ar[1])
                is_changed = True
        else:
            if pkey_ar[1] in acl_cfg['ports']:
                acl_cfg['ports'].remove(pkey_ar[1])
                is_changed = True

        if is_changed:
            exec_cmd = CFG_ACL_CMD_TMPL % (acl_name, json.dumps(acl_cfg))
            ret_val = util_utl.utl_execute_cmd(exec_cmd)
        else:
            ret_val = True

    return ret_val