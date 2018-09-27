#
# util_acl.py
#
# APIs for processing acl info.
#

import subprocess
import json
import pdb
import util_utl
import swsssdk

from util_utl import CFG_ACL_CMD_TMPL
from util_utl import CFG_RUL_CMD_TMPL
from util_utl import CFG_MSESS_CMD_TMPL
from util_utl import RULE_MAX_PRI
from util_utl import RULE_MIN_PRI

# convert openconfig yang model to sonic
SONIC_FLDMAP_TBL = {
    "ipv4": {"protocol"           : "IP_PROTOCOL",
             "source-address"     : "SRC_IP",
             "destination-address": "DST_IP",
             "dscp"               : "DSCP"           },
    "l2"  : {"ethertype"          : "ETHER_TYPE"     },
    "transport" :
            {"source-port"        : "L4_SRC_PORT",
             "destination-port"   : "L4_DST_PORT",
             "tcp-flags"          : "TCP_FLAGS"
            },
    }

# convert sonic to openconfig yang model
INT_TYPE = 1
STR_TYPE = 2
HEX_TYPE = 3
NON_TYPE = 4
OCYANG_FLDMAP_TBL = {
    'IP_PROTOCOL' : {'str':'ipv4.config.protocol',             'type': INT_TYPE }, # 5
    'SRC_IP'      : {'str':'ipv4.config.source_address',       'type': STR_TYPE }, # '1.1.1.1/24'
    'DST_IP'      : {'str':'ipv4.config.destination_address',  'type': STR_TYPE },
    'DSCP'        : {'str':'ipv4.config.dscp',                 'type': INT_TYPE }, # 5
    'ETHER_TYPE'  : {'str':'l2.config.ethertype',              'type': INT_TYPE }, # 5
    'L4_SRC_PORT' : {'str':'transport.config.source_port',     'type': INT_TYPE },
    'L4_DST_PORT' : {'str':'transport.config.destination_port','type': INT_TYPE },
    'TCP_FLAGS'   : {'str':'transport.config.tcp_flags',       'type': INT_TYPE },
    'PACKET_ACTION':{'str':'actions.config.forwarding_action', 'type': STR_TYPE }, # for acl
    'MIRROR_ACTION':{'str':'not_used',                         'type': STR_TYPE }, # for pf
    'PRIORITY'    : {'str':'not_used',                         'type': NON_TYPE },
    }

OCYANG_ACTMAP_TBL = {
    'FORWARD' : 'ACCEPT',
    'DROP'    : 'DROP',
    }

OCYANG_ACLTYPEMAP_TBL = {
    'L3'        : 'ACL_IPV4',
#    'MIRROR'    : 'ACL_IPV4',
#    'CTRLPLANE' : 'ACL_IPV4',
    }

TCPFLAG_MAP_TBL = {
    "TCP_FIN" : 0x01,
    "TCP_SYN" : 0x02,
    "TCP_RST" : 0x04,
    "TCP_PSH" : 0x08,
    "TCP_ACK" : 0x10,
    "TCP_URG" : 0x20,
    "TCP_ECE" : 0x40,
    "TCP_CWR" : 0x80
    }

# convert sonic's acl type to openconfig's acl type
def acl_cnv_to_oc_acl_type(in_acl_type):
    # todo ...
    try:
        ret_val = OCYANG_ACLTYPEMAP_TBL[in_acl_type]
    except:
        ret_val = None

    return ret_val

# convert sonic's tcp flags to openconfig's tcp flag list
# ex: in_flag = "0x8/0x8"
def acl_cnv_to_oc_tcp_flags(in_flags):
    tcp_flags = []
    in_val = int (in_flags.split('/')[0], 16)
    for flag in TCPFLAG_MAP_TBL.keys():
        if TCPFLAG_MAP_TBL[flag] & in_val:
            tcp_flags.append(flag)

    return tcp_flags

# convert openconfig's tcp flag list to sonic's tcp flags
# ex: in_flag = ['TCP_SYN']
def acl_cnv_to_sonic_tcp_flags(in_flag_lst):
    tcp_flags = 0
    for flag in TCPFLAG_MAP_TBL.keys():
        if flag in in_flag_lst:
            tcp_flags = tcp_flags | TCPFLAG_MAP_TBL[flag]

    return '0x{:02x}/0x{:02x}'.format(tcp_flags, tcp_flags)

# add a rule to oc_acl with rule_name and rule_data
def acl_add_one_rule(oc_acl_set, rule_name, rule_data):
    # {0} : entry name
    # {1} : field
    # {2} : value
    #pdb.set_trace()
    EXEC_STR_TMPL = '{0}.{1} = {2}'
    seq_id = RULE_MAX_PRI - int(rule_data['PRIORITY'])
    oc_rule = oc_acl_set.acl_entries.acl_entry.add(seq_id)
    oc_rule.config.description = rule_name

    for d_key in rule_data.keys():
        if d_key in OCYANG_FLDMAP_TBL:
            if OCYANG_FLDMAP_TBL[d_key]['type'] == NON_TYPE: continue

            value_str = rule_data[d_key]

            if value_str == 'None': continue

            if d_key == 'PACKET_ACTION':
                if value_str in OCYANG_ACTMAP_TBL:
                    value_str = OCYANG_ACTMAP_TBL[value_str]
                else:
                    util_utl.utl_err("action(%s) is not valid !" % value_str)
                    value_str = None

            elif d_key == 'TCP_FLAGS':
                value_str = acl_cnv_to_oc_tcp_flags(value_str)

            if value_str:
                if OCYANG_FLDMAP_TBL[d_key]['type'] == STR_TYPE:
                    value_str = '"{0}"'.format(value_str)

                exec_str = EXEC_STR_TMPL.format("oc_rule", OCYANG_FLDMAP_TBL[d_key]['str'], value_str)
                exec(exec_str)
        else:
            util_utl.utl_err("field(%s) is not supported !" % d_key)

def acl_fill_binding_info(oc_acl, acl_name, acl_type, acl_info):
    #pdb.set_trace()
    for port in acl_info['ports']:
        if port == '': continue

        if port not in oc_acl.interfaces.interface:
            oc_acl_inf = oc_acl.interfaces.interface.add(port)
        else:
            oc_acl_inf = oc_acl.interfaces.interface[port]

        oc_acl_inf.ingress_acl_sets.ingress_acl_set.add(set_name=acl_name, type=acl_type)

# fill DUT's current acl info into root_yph
# key_ar [0] : interface name e.g. "eth0"
# ret        : True/False
def acl_get_info(root_yph, path_ar, key_ar, disp_args):
    #pdb.set_trace()
    oc_acl = root_yph.get("/acl")[0]

    # bcz _unset_acl_set will not remove old entries correctly.
    old_acl_lst = [ x for x in oc_acl.acl_sets.acl_set ]
    for old_acl in old_acl_lst:
        oc_acl.acl_sets.acl_set.delete(old_acl)

    # clear binding info
    old_inf_lst = [ x for x in oc_acl.interfaces.interface ]
    for old_inf in old_inf_lst:
        oc_acl.interfaces.interface.delete(old_inf)

    ret_val = True
    acl_tlst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_ACL)
    if acl_tlst:
        acl_rlst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_RULE)

        # acl_set must be created b4 filling binding info
        for acl_name in acl_tlst.keys():
            acl_type = acl_cnv_to_oc_acl_type(acl_tlst[acl_name]['type'])
            if acl_type:
                oc_acl_set = oc_acl.acl_sets.acl_set.add(name = acl_name, type = acl_type)

                for acl_rule_key in acl_rlst.keys():
                    if acl_name in acl_rule_key:
                        oc_acl_rule = acl_add_one_rule(oc_acl_set, acl_rule_key[1], acl_rlst[acl_rule_key])

        for acl_name in acl_tlst.keys():
            acl_type = acl_cnv_to_oc_acl_type(acl_tlst[acl_name]['type'])
            if acl_type:
                acl_fill_binding_info(oc_acl, acl_name, acl_type, acl_tlst[acl_name])

    return ret_val

# ex:    pkey_ar = [u'DATAACL', u'ACL_IPV4']
#   val for del  = '{"type":"ACL_IPV4", "name":""}' or ""
#   val for add  = '{"type":"ACL_IPV4", "name":"DATAACL"}'
#
# To create/remove an acl (no checking for existence)
def acl_set_acl_set(root_yph, pkey_ar, val, is_create, disp_args):
    try:
        acl_cfg = {"name":""} if val == "" else eval(val)

        if acl_cfg["name"] == "":
            cfg_str = "null"
        else:
            if acl_cfg["name"] != pkey_ar[0]: return False

            cfg_str = '{"type": "L3", "policy_desc": "%s", "ports":[]}' % (pkey_ar[0])

    except:
        return False

    exec_cmd = CFG_ACL_CMD_TMPL % (pkey_ar[0], cfg_str)
    ret_val = util_utl.utl_execute_cmd(exec_cmd)
    return ret_val

# add one mirror session used by rule of pf (EVERFLOW)
def acl_add_one_mirror_session(sess_name, target_yang):
    target_sonic = {
        "gre_type"  : "25944",  # 0x6558
        "dscp"      : "0",      # TODO: default
        "queue"     : "0",      # TODO: default
    }
    target_sonic["src_ip"] = target_yang["config"]["source"]
    target_sonic["dst_ip"] = target_yang["config"]["destination"]
    target_sonic["ttl"]    = str(target_yang["config"]["ip-ttl"])

    exec_cmd = CFG_MSESS_CMD_TMPL % (sess_name, json.dumps(target_sonic))
    ret_val = util_utl.utl_execute_cmd(exec_cmd)
    return ret_val

# copy action info from rule_yang to rule_sonic
def acl_rule_copy_action(rule_yang, rule_sonic, msess_tbl):
    #pdb.set_trace()
    ret_val = False
    if msess_tbl == None:
        # for acl: actions.config.forwarding-action
        if "actions" in rule_yang:
            act_tbl = {'ACCEPT' : 'FORWARD',
                       'DROP'   : 'DROP'    }
            val = rule_yang["actions"]["config"]["forwarding-action"]
            if val in act_tbl:
                val = act_tbl[val]
                rule_sonic["PACKET_ACTION"] = val
                ret_val = True

    else:
        # for pf: action.config.next-hop
        #         action.encapsulate-gre.targets
        if "action" in rule_yang:
            if "config" in rule_yang["action"]:
                # "REDIRECT:ip"
                val = rule_yang["action"]["config"]["next-hop"]
                rule_sonic["PACKET_ACTION"] = "REDIRECT:%s" % val
                ret_val = True

            elif 'encapsulate-gre' in rule_yang['action']:
                trg_cfgs = rule_yang["action"]["encapsulate-gre"]["targets"]["target"]
                for trg in trg_cfgs:
                    rule_sonic["MIRROR_ACTION"] = trg
                    if trg in msess_tbl: break

                    ret_val = acl_add_one_mirror_session(trg, trg_cfgs[trg])
                    msess_tbl.append(trg)
                    break # support only one session ???

    if not ret_val:
        util_utl.utl_err("No action for %s rule !!!" % ["pf", "acl"][msess_tbl==None])

    return ret_val

# copy cfg info from rule_yang to rule_sonic by key
def acl_rule_copy_cfg(rule_yang, rule_sonic, key, msess_tbl):

    if key in ['actions', 'action']:
        return acl_rule_copy_action(rule_yang, rule_sonic, msess_tbl)

    is_copy = False
    if key in rule_yang and 'config' in rule_yang[key] and key in SONIC_FLDMAP_TBL:
        fld_tbl = SONIC_FLDMAP_TBL[key]

        for fld in rule_yang[key]['config'].keys():
            if fld in fld_tbl:
                val = rule_yang[key]['config'][fld]

                if fld == 'tcp-flags':
                    val = acl_cnv_to_sonic_tcp_flags(val)

                if val:
                    rule_sonic[fld_tbl[fld]] = val
                    is_copy = True
            else:
                util_utl.utl_err("field(%s) is not supported !" % fld)

    return is_copy

# get rule name and copy pri info from rule_yang to rule_sonic
def acl_rule_get_name_and_pri(rule_yang, rule_sonic):
    rule_name = None
    seq_id = None
    if 'sequence-id' in rule_yang:
        seq_id = int (rule_yang['sequence-id'])

    if 'config' in rule_yang:
        if not seq_id and 'sequence-id' in rule_yang:
            seq_id = int (rule_yang['sequence-id'])

        if 'description' in rule_yang['config']:
            rule_name = rule_yang['config']['description']

    if seq_id:
        rule_sonic['PRIORITY'] = str(RULE_MAX_PRI - seq_id)

    if not rule_name:
        if seq_id:
            rule_name = 'RULE_{0}'.format(seq_id)

    return rule_name

# ret: rule_name, cfg_str
#   add: cfg_str = '{"PRIORITY": "9999","PACKET_ACTION":"FORWARD","SRC_IP":"10.0.0.0/8"}'
#   del: cfg_str = 'null'
#   msess_tbl = None if used for acl
def acl_rule_yang2sonic(rule_yang, msess_tbl = None):
    rule_sonic  = {}
    rule_name   = acl_rule_get_name_and_pri (rule_yang, rule_sonic)
    rule_sonic_str = "null"

    if rule_name:
        is_copy = False
        for key in rule_yang.keys():
            if key in ["ipv4", "l2", "transport", "actions" if msess_tbl == None else "action"]:
                is_copy_tmp = acl_rule_copy_cfg(rule_yang, rule_sonic, key, msess_tbl)
                if not is_copy_tmp:
                    util_utl.utl_err("Failed to get rule field (%s:%s)!!!" % (key, rule_yang[key]))

                is_copy = is_copy or is_copy_tmp
            elif key not in ["sequence-id", "config"]:
                util_utl.utl_err("Unrecognized key (%s:%s)!!!" % (key, rule_yang[key]))

        if is_copy:
            rule_sonic_str = json.dumps(rule_sonic)
    else:
        util_utl.utl_err("Failed to get rule name (%s)!!!" % rule_yang)

    return rule_name, rule_sonic_str

# ex:
#   acl_name = "kkk"
#   rule_name= "RULE_1"
#   rule_cfg = '{"PRIORITY": "9999","PACKET_ACTION": "FORWARD","SRC_IP": "10.0.0.0/8"}'
#
#   To write the rule config into sonic db
def acl_set_one_acl_entry(acl_name, rule_name, rule_cfg):
    if not rule_name: return False
    rule_db_name = "{0}|{1}".format(acl_name, rule_name)

    # 1. delete old entry
    exec_cmd = CFG_RUL_CMD_TMPL % (rule_db_name, "null")
    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    if rule_cfg != "null":
        # 2. add new entry
        exec_cmd = CFG_RUL_CMD_TMPL % (rule_db_name, rule_cfg)
        ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val

# ex:    pkey_ar = [u'DATAACL', u'ACL_IPV4']
#   val for del  = '{"type":"ACL_IPV4", "name":""}'
#   val for add  = '{"type":"ACL_IPV4", "name":"DATAACL"}'
#
# To create/remove an acl entry
def acl_set_acl_entry(root_yph, pkey_ar, val, is_create, disp_args):
    #pdb.set_trace()
    #
    # priority    => RULE_MAX_PRI - sequence-id
    # description => rule name (default : RULE_ + seq-id)
    #
    """ example:
    {
      "9999": {
        "sequence-id": 9999,
        "config": {
          "sequence-id": 9999,
          "description": "RULE_1",
        },
        "ipv4": {
          "config": {
            "protocol": 17,
            "source-address": "10.0.0.0/8"
          }
        },
        "actions": {
          "config": {
            "forwarding-action": "ACCEPT"
          }
        }
      }
    }
    """
    rule_cfg = {} if val == "" else eval(val)

    # only one entry
    if 'sequence-id' in rule_cfg.keys():
        rule_name, rule_cfg = acl_rule_yang2sonic(rule_cfg)
        ret_val = acl_set_one_acl_entry(pkey_ar[0], rule_name, rule_cfg)
    else:
        ret_val = True
        for seq_id in rule_cfg.keys():
            rule_name, rule_cfg = acl_rule_yang2sonic(rule_cfg[seq_id])
            ret_val = acl_set_one_acl_entry(pkey_ar[0], rule_name, rule_cfg)
            if not ret_val:
                break

    return ret_val

# ex:    pkey_ar = [u'Ethernet4', u'lll', u'ACL_IPV4']
#   val for del  = '' or '{}'
#   val for add  = '{"set-name": "lll", "type": "ACL_IPV4"}'
#
# To bind/unbind an acl to an interface
def acl_set_interface(root_yph, pkey_ar, val, is_create, disp_args):
    ret_val = False

    # 1. get old port list
    exec_cmd = 'sonic-cfggen -d -v "ACL_TABLE[\'%s\']"' % pkey_ar[1]
    (is_ok, output) = util_utl.utl_get_execute_cmd_output(exec_cmd)
    if is_ok:
        # ex: {'type': 'L3', 'policy_desc': 'lll', 'ports': ['']}
        acl_cfg = {} if output.strip('\n') =='' else eval(output)

    # acl must be created b4 binding to interface
    if acl_cfg:
        if val == "" or val == "{}":
            is_add = False
        else:
            try:
                tmp_chk = eval(val)
                # check old acl_type ???
                if tmp_chk['set-name'] == pkey_ar[1] and tmp_chk['type'] == pkey_ar[2]:
                    is_add = True
            except:
                return False

        is_changed = False

        if '' in acl_cfg['ports']:
            acl_cfg['ports'].remove('')

        # 2. add/remove new port to/from old port list
        if is_add:
            if pkey_ar[0] not in acl_cfg['ports']:
                acl_cfg['ports'].append(pkey_ar[0])
                is_changed = True
        else:
            if pkey_ar[0] in acl_cfg['ports']:
                acl_cfg['ports'].remove(pkey_ar[0])
                is_changed = True

        if is_changed:
            exec_cmd = CFG_ACL_CMD_TMPL % (pkey_ar[1], json.dumps(acl_cfg))
            ret_val = util_utl.utl_execute_cmd(exec_cmd)
        else:
            ret_val = True

    return ret_val