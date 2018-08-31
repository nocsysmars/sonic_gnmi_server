#
# util_acl.py
#
# APIs for processing acl info.
#

import subprocess
import json
import pdb
import util_utl

GET_VAR_LST_CMD_TMPL = 'sonic-cfggen -d -v "{0}"'
GET_ACL_TBL_LST_CMD  = GET_VAR_LST_CMD_TMPL.format("ACL_TABLE")
GET_ACL_RUL_LST_CMD  = GET_VAR_LST_CMD_TMPL.format("ACL_RULE")

# convert sonic's acl type to openconfig's acl type
def acl_cnv_to_oc_acl_type(in_acl_type):
    # todo ...
    map_tbl = { 'L3'        : 'ACL_IPV4',
                'MIRROR'    : 'ACL_IPV4',
                'CTRLPLANE' : 'ACL_IPV4',
              }

    try:
        ret_val = map_tbl[in_acl_type]
    except:
        ret_val = None

    return ret_val

def acl_add_one_rule_action(oc_rule, rule_data):
    map_tbl = {'FORWARD' : 'ACCEPT',
               'DROP'    : 'DROP',
              }
    #pdb.set_trace()

    oc_rule.actions.config.forwarding_action = map_tbl[rule_data['PACKET_ACTION']]

def acl_add_one_rule(oc_acl, rule_data):
    # {0} : entry name
    # {1} : field
    # {2} : value
    EXEC_STR_TMPL = '{0}.{1} = {2}'
    INT_TYPE = 1
    STR_TYPE = 2
    HEX_TYPE = 3
    fld_tbl = {'IP_PROTOCOL' : {'str':'ipv4.config.protocol',            'type': INT_TYPE }, # 5
               'SRC_IP'      : {'str':'ipv4.config.source_address',      'type': STR_TYPE }, # '1.1.1.1/24'
               'DST_IP'      : {'str':'ipv4.config.destination-address', 'type': STR_TYPE },
               'DSCP'        : {'str':'ipv4.config.dscp',                'type': INT_TYPE }, # 5
               'ETHER_TYPE'  : {'str':'l2.config.ethertype',             'type': HEX_TYPE }, # 5
               #'PRIORITY'    : 'sequence_id'
              }

    oc_rule = oc_acl.acl_entries.acl_entry.add(int(rule_data['PRIORITY']))

    for d_key in rule_data.keys():
        if d_key in fld_tbl:
            if fld_tbl[d_key]['type'] == INT_TYPE:
                value_str = rule_data[d_key]
            elif fld_tbl[d_key]['type'] == HEX_TYPE:
                value_str = int(rule_data[d_key], 16)
            else:
                value_str = "'{0}'".format(rule_data[d_key])
            exec_str = EXEC_STR_TMPL.format("oc_rule", fld_tbl[d_key]['str'], value_str)
            exec(exec_str)

    acl_add_one_rule_action(oc_rule, rule_data)

# fill DUT's current acl info into root_yph
# key_ar [0] : interface name e.g. "eth0"
# ret        : True/False
def acl_get_info(root_yph, key_ar):
    """
    use '' command to gather information
    """
    ret_val = False
    #pdb.set_trace()

    (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_ACL_TBL_LST_CMD)
    if is_ok:
        acl_tlst = {} if output.strip('\n') =='' else eval(output)

    if acl_tlst:
        oc_acl = root_yph.get("/acl")[0]

        # bcz _unset_acl_set will not remove old entries correctly.
        for old_acl in oc_acl.acl_sets.acl_set:
            oc_acl.acl_sets.acl_set.delete(old_acl)

        (is_ok, output) = util_utl.utl_get_execute_cmd_output(GET_ACL_RUL_LST_CMD)
        if is_ok:
            acl_rlst = {} if output.strip('\n') =='' else eval(output)

        for acl_name in acl_tlst.keys():
            acl_type = acl_cnv_to_oc_acl_type(acl_tlst[acl_name]['type'])
            if acl_type:
                oc_acl_set = oc_acl.acl_sets.acl_set.add(name = acl_name, type = acl_type)

                for acl_rule_key in acl_rlst.keys():
                    if acl_name in acl_rule_key:
                        oc_acl_rule = acl_add_one_rule(oc_acl_set, acl_rlst[acl_rule_key])

        ret_val = True

    return ret_val

# ex:    pkey_ar = [u'DATAACL', u'ACL_IPV4']
#   val for del  = '{"type":"ACL_IPV4", "name":""}'
#   val for add  = '{"type":"ACL_IPV4", "name":"DATAACL"}'
#
# To create/remove an acl
def acl_set_acl_set(root_yph, pkey_ar, val, is_create):
    #pdb.set_trace()

    try:
        acl_cfg = {} if val == "" else eval(val)

        if acl_cfg["name"] == "":
            cfg_str = "null"
        else:
            cfg_str = '{"type": "L3", "policy_desc": "%s", "ports":[]}' % (acl_cfg["name"])

    except:
        return False

    ACL_CMD_TMPL = 'sonic-cfggen -a \'{"ACL_TABLE": {"%s" : %s}}\' --write-to-db'

    exec_cmd = ACL_CMD_TMPL % (pkey_ar[0], cfg_str)

    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val