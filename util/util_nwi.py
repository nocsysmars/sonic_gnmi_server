#
# util_nwi.py
#
# APIs for processing network instance info.
#

import subprocess, json, pdb, util_utl
import os
from swsssdk import port_util
from util_utl import RULE_MAX_PRI, RULE_MIN_PRI, \
                     interface_ipaddr_dependent_on_interface, \
                     get_interface_table_name

from util_acl import acl_rule_yang2sonic, acl_set_one_acl_entry, \
                     acl_cnv_to_oc_tcp_flags, acl_is_acl_for_pf, \
                     OCYANG_FLDMAP_TBL, INT_TYPE, STR_TYPE, HEX_TYPE, NON_TYPE, \
                     MIRROR_POLICY_PFX, PROUTE_POLICY_PFX

DEFAULT_NWI_NAME = 'DEFAULT'

FILL_INFO_NONE  = 0     # fill no info
FILL_INFO_FDB   = 0x01  # fill fdb info
FILL_INFO_PF    = 0x02  # fill policy-forwarding info
FILL_INFO_INTFS = 0x04  # fill interface info
FILL_INFO_POL   = 0x08  # fill policy info
FILL_INFO_ALL   = 0xff  # fill all info

# mac list needed to check existence
OLD_MAC_LST = []

@util_utl.utl_timeit
def nwi_create_dflt_nwi(nwi_yph, is_dbg_test):
    oc_nwis = nwi_yph.get("/network-instances")[0]
    oc_nwi_dflt = oc_nwis.network_instance.add(DEFAULT_NWI_NAME)
    oc_nwi_dflt.config.enabled = True
    oc_nwi_dflt.config.type = 'DEFAULT_INSTANCE'

# ex: key_ar = [u'DEFAULT', u'00:00:00:00:00:01', u'10', u'name', u'mac-address', u'vlan']
def nwi_get_fdb_info(oc_nwis, fill_info_bmp, key_ar, disp_args):
    # refer to /usr/bin/fdbshow
    key_mac  = None
    key_vlan = None
    oc_nwi   = None

    len_key_ar = len(key_ar) // 2
    if len_key_ar > 3: return False

    for i in range(len_key_ar):
        if key_ar[i+len_key_ar] == 'name':
            if key_ar[i] in oc_nwis.network_instance:
                oc_nwi = oc_nwis.network_instance[key_ar[i]]
            else:
                return False
        elif key_ar[i+len_key_ar] == 'mac-address':
            key_mac  = key_ar[i]
        elif key_ar[i+len_key_ar] == 'vlan':
            key_vlan = key_ar[i]
        else:
            return False

    # instance name is omitted
    if not oc_nwi:
        oc_nwi = oc_nwis.network_instance[DEFAULT_NWI_NAME]

    if_name_map, \
    if_oid_map = port_util.get_interface_oid_map(disp_args.appdb)
    if_br_oid_map = port_util.get_bridge_port_map(disp_args.appdb)

    NEW_MAC_LST = []
    global OLD_MAC_LST

    fdb_str = disp_args.appdb.keys(disp_args.appdb.ASIC_DB, "ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY:*")
    if fdb_str and if_br_oid_map:
        oid_pfx = len("oid:0x")
        for s in fdb_str:
            fdb_entry = s.decode()
            fdb = json.loads(fdb_entry.split(":", 2)[-1])
            if not fdb: continue

            ent = disp_args.appdb.get_all('ASIC_DB', s, blocking=True)
            br_port_id = ent[b"SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID"][oid_pfx:]
            if br_port_id not in if_br_oid_map: continue

            port_id = if_br_oid_map[br_port_id]
            if_name = if_oid_map[port_id]

            if "vlan" not in fdb:
                if "bvid" in fdb:
                    fdb["vlan"] = port_util.get_vlan_id_from_bvid(disp_args.appdb, fdb["bvid"])
                else:
                    continue

            #pdb.set_trace()

            # ex:
            #   fdb["vlan"] : u'10'
            #   fdb["mac"]  : u'00:00:00:00:00:01'
            #   if_name     : 'Ethernet4'
            #   oc_nwi.fdb.mac_table.entries.entry['00:00:00:00:00:01 10']
            if key_mac  and key_mac  != fdb["mac"]: continue
            if key_vlan and key_vlan != fdb["vlan"]: continue

            mac_key = "%s %s" % (fdb["mac"], fdb["vlan"])
            if mac_key in OLD_MAC_LST:
                OLD_MAC_LST.remove(mac_key)
                mac_entry = oc_nwi.fdb.mac_table.entries.entry[mac_key]
            else:
                mac_entry = oc_nwi.fdb.mac_table.entries.entry.add(mac_key)

            mac_entry.interface.interface_ref.config.interface = if_name
            mac_entry.state._set_entry_type('DYNAMIC')

            NEW_MAC_LST.append(mac_key)

    # remove old mac entries not used
    for mac_key in OLD_MAC_LST:
        oc_nwi.fdb.mac_table.entries.entry.delete(mac_key)

    OLD_MAC_LST = NEW_MAC_LST

    return True

# ex: act_data = 'session1'
#     msess_lst = '{}'
# add a action to oc_rule with act_data and msess_lst
def nwi_pf_add_one_mirror_action(oc_rule, act_data, msess_lst):
    if act_data in oc_rule.action.encapsulate_gre.targets.target:
        oc_target = oc_rule.action.encapsulate_gre.targets.target[act_data]
    else:
        oc_target = oc_rule.action.encapsulate_gre.targets.target.add(act_data)

    if act_data in msess_lst:
        dst_ip_str = msess_lst[act_data]['dst_ip']
        if '/' not in dst_ip_str: dst_ip_str = dst_ip_str + '/32'

        oc_target.config.source      = msess_lst[act_data]['src_ip']
        oc_target.config.destination = dst_ip_str
        oc_target.config.ip_ttl      = msess_lst[act_data]['ttl']

# ex: act_data = 'REDIRECT:1.1.1.1'
def nwi_pf_add_one_pol_rt_action(oc_rule, act_data):
    if act_data.startswith('REDIRECT:'):
        value = act_data.lstrip('REDIRECT:')
        oc_rule.action.config._set_next_hop(value)

# add a rule to oc_pol with rule_name and rule_data
def nwi_pf_add_one_rule(oc_pol, rule_name, rule_data, msess_lst):
    # {0} : entry name
    # {1} : field
    # {2} : value
    #pdb.set_trace()
    EXEC_STR_TMPL = '{0}.{1} = {2}'
    seq_id = RULE_MAX_PRI - int(rule_data['PRIORITY'])
    oc_rule = oc_pol.rules.rule.add(seq_id)

    for d_key in rule_data.keys():
        if d_key in OCYANG_FLDMAP_TBL:
            if OCYANG_FLDMAP_TBL[d_key]['type'] == NON_TYPE: continue

            value_str = rule_data[d_key]

            if value_str == 'None': continue

            if d_key == 'MIRROR_ACTION':
                nwi_pf_add_one_mirror_action(oc_rule, value_str, msess_lst)
                value_str = None
            elif d_key == 'PACKET_ACTION':
                nwi_pf_add_one_pol_rt_action(oc_rule, value_str)
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

# fill binding info for policy-forwarding
def nwi_pf_fill_binding_info(oc_pf, acl_name, acl_info):
    for port in acl_info['ports']:
        if port == '': continue

        if port not in oc_pf.interfaces.interface:
            oc_pf_inf = oc_pf.interfaces.interface.add(port)
        else:
            oc_pf_inf = oc_pf.interfaces.interface[port]

        oc_pf_inf.config.apply_forwarding_policy = acl_name

# ex: pkey_ar = [u'DEFAULT', u'EVERFLOW_2', u'1', u'name', u'policy-id', u'sequence-id']
# ex: pkey_ar = [u'DEFAULT', u'Ethernet2',  u'name', u'interface-id']
def nwi_get_pf_info(oc_nwis, fill_info_bmp, key_ar, disp_args):
    #pdb.set_trace()
    key_pol = None
    key_seq = None
    key_inf = None
    oc_nwi  = None

    len_key_ar = len(key_ar) // 2
    if len_key_ar > 3: return False

    for i in range(len_key_ar):
        if key_ar[i+len_key_ar] == 'name':
            if key_ar[i] in oc_nwis.network_instance:
                oc_nwi = oc_nwis.network_instance[key_ar[i]]
            else:
                return False
        elif key_ar[i+len_key_ar] == 'policy-id':
            key_pol = key_ar[i]
        elif key_ar[i+len_key_ar] == 'sequence-id':
            key_seq = key_ar[i]
        elif key_ar[i+len_key_ar] == 'interface-id':
            key_inf = key_ar[i]
        else:
            return False

    # instance name is omitted
    if not oc_nwi:
        oc_nwi = oc_nwis.network_instance[DEFAULT_NWI_NAME]

    oc_pf = oc_nwi.policy_forwarding

    # clear binding info
    old_inf_lst = [ x for x in oc_pf.interfaces.interface ]
    for old_inf in old_inf_lst:
        oc_pf.interfaces.interface.delete(old_inf)

    # remove old policies
    old_pol_lst = [ x for x in oc_pf.policies.policy ]
    for old_pol in old_pol_lst:
        oc_pf.policies.policy.delete(old_pol)

    msess_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_MIRROR_SESSION)
    acl_tlst  = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_ACL)
    ret_val = True

    if acl_tlst:
        if FILL_INFO_POL & fill_info_bmp:
            acl_rlst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_RULE)

        for acl_name in acl_tlst.keys():
            if acl_is_acl_for_pf(acl_name):
                oc_pol = oc_pf.policies.policy.add(acl_name)

                if key_pol and key_pol != acl_name: continue

                if FILL_INFO_POL & fill_info_bmp:
                    for acl_rule_key in acl_rlst.keys():
                        if acl_name in acl_rule_key:
                            oc_acl_rule = nwi_pf_add_one_rule(oc_pol, acl_rule_key[1], acl_rlst[acl_rule_key], msess_lst)

        # all policies should be created first before being used by interfaces
        # otherwise the reference relationship will be corrupted.
        if FILL_INFO_INTFS & fill_info_bmp:
            for acl_name in acl_tlst.keys():
                if acl_is_acl_for_pf(acl_name):
                    nwi_pf_fill_binding_info(oc_pf, acl_name, acl_tlst[acl_name])

    return ret_val

# key_ar[0] : 'DEFAULT' (instance name)
def nwi_get_info(root_yph, path_ar, key_ar, disp_args):
    fill_type_tbl = { "fdb"                 : FILL_INFO_FDB,
                      "policy-forwarding"   : FILL_INFO_POL | FILL_INFO_INTFS,
                      "policies"            : FILL_INFO_POL,
                      "interfaces"          : FILL_INFO_INTFS,
        }

    fill_path_key = path_ar[2] if len(path_ar) > 2 else "not_exist"

    try:
        fill_info_type = fill_type_tbl[fill_path_key]
    except:
        fill_info_type = FILL_INFO_ALL

    func_tbl = [ {'func': nwi_get_fdb_info,  'type' : FILL_INFO_FDB   },
                 {'func': nwi_get_pf_info,   'type' : FILL_INFO_POL | \
                                                      FILL_INFO_INTFS }
        ]

    oc_nwis = root_yph.get("/network-instances")[0]
    ret_val = False
    for func_fld in func_tbl:
        if func_fld['type'] & fill_info_type:
            ret_val = func_fld['func'](oc_nwis, fill_info_type, key_ar, disp_args) or ret_val

    return ret_val

# ex:    pkey_ar = [u'DEFAULT', u'Ethernet10']
#   val for del  = '' or '{}'
#   val for add  = '{"apply-forwarding-policy": "lll"}'
#
# To bind/unbind a policy to an interface
# TODO: 1.filter out name not valid for PF ???
#       2.only one policy per port ???
def nwi_pf_set_interface(root_yph, pkey_ar, val, is_create, disp_args):
    #pdb.set_trace()

    tmp_cfg = {} if val == "" or val == "{}" else eval(val)
    acl_name = tmp_cfg.get('apply-forwarding-policy')
    is_add = True if acl_name else False
    ret_val = False if is_add else True

    # 1. get old port list
    # ex: {'type': 'MIRROR', 'policy_desc': 'lll', 'ports': ['']}
    acl_lst  = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_ACL)

    # acl must be created b4 binding to interface
    if acl_lst:
        # remove port from all policies
        for acl in acl_lst:
            if not is_add:
                # find old acl_name for binding port
                if pkey_ar[1] in acl_lst[acl]['ports'] and acl_is_acl_for_pf(acl):
                    acl_name = acl
                else:
                    continue

            acl_cfg  = acl_lst.get(acl_name)
            # ex: {'type': 'MIRROR', 'policy_desc': 'lll', 'ports': ['']}
            if not acl_cfg: return False

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

            ret_val = True
            if is_changed:
                disp_args.cfgdb.mod_entry(util_utl.CFGDB_TABLE_NAME_ACL, acl_name, acl_cfg)

            if is_add: break

    return ret_val

# ex:    pkey_ar = [u'DEFAULT', u'EVERFLOW']
#   val for del  = '' or '{}'
#   val for add  = '{"policy-id": "EVERFLOW"}'
#
# To add/remove a policy (no checking for existence)
# TODO: filter out name not valid for PF ???
def nwi_pf_set_policy(root_yph, pkey_ar, val, is_create, disp_args):
    try:
        pf_cfg = {"policy-id":""} if val == "" else eval(val)

        if pf_cfg["policy-id"] == "":
            acl_cfg = None
        else:
            if pf_cfg["policy-id"] != pkey_ar[1]: return False

            pf_type = 'MIRROR' if pkey_ar[1].find(MIRROR_POLICY_PFX) == 0 else 'L3'
            acl_cfg = {
                "type"       : pf_type,
                "policy_desc": pkey_ar[1],
                "ports"      :[]
                }

    except:
        return False

    disp_args.cfgdb.mod_entry(util_utl.CFGDB_TABLE_NAME_ACL, pkey_ar[1], acl_cfg)
    return True

# try to remove mirror sessions not used by any rule
def nwi_pf_clear_mirror_sessions(disp_args):
    msess_lst = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_MIRROR_SESSION)

    acl_rlst  = disp_args.cfgdb.get_table(util_utl.CFGDB_TABLE_NAME_RULE)
    if acl_rlst:
        for acl_rule_key in acl_rlst.keys():
            if 'MIRROR_ACTION' in acl_rlst[acl_rule_key]:
                sess_name = acl_rlst[acl_rule_key]['MIRROR_ACTION']

            if sess_name in msess_lst:
                del msess_lst[sess_name]

    for msess in msess_lst:
        disp_args.cfgdb.mod_entry(util_utl.CFGDB_TABLE_NAME_MIRROR_SESSION, msess, None)

# add one mirror session used by rule of pf (EVERFLOW)
def nwi_pf_add_one_mirror_session(disp_args, sess_name, target_yang):
    target_sonic = {
        "gre_type"  : str(int(0x6558)),
        "dscp"      : "0",      # TODO: default
        "queue"     : "0",      # TODO: default
        }
    target_sonic["src_ip"] = target_yang["config"]["source"]
    target_sonic["dst_ip"] = target_yang["config"]["destination"]
    target_sonic["ttl"]    = str(target_yang["config"]["ip-ttl"])

    disp_args.cfgdb.mod_entry(util_utl.CFGDB_TABLE_NAME_MIRROR_SESSION, sess_name, target_sonic)

# add one mirror session used by rule of pf (EVERFLOW)
def nwi_pf_add_mirror_sessions(disp_args, msess_tbl):
    for key, val in msess_tbl.items():
        nwi_pf_add_one_mirror_session(disp_args, key, val)

# ex:    pkey_ar = [u'DEFAULT', u'EVERFLOW']
#   val for del  = '' or '{}'
#   val for add  = '{"policy-id": "EVERFLOW"}'
#
# To add/remove a rule of pf
def nwi_pf_set_rule(root_yph, pkey_ar, val, is_create, disp_args):
    #pdb.set_trace()
    #
    # priority    => RULE_MAX_PRI - sequence-id
    #
    """ example:
    {
      "9999": {
        "sequence-id": 9999,
        "config": {
          "sequence-id": 9999,
        },
        "ipv4": {
          "config": {
            "protocol": 17,
            "source-address": "10.0.0.0/8"
          }
        },
        "action": {
          "config": {
            "next-hop": "10.0.0.0"
          }
        }
      }
    }
    """
    # TODO: check policy type and action ???
    rule_cfg  = {} if val == "" else eval(val)
    msess_tbl = {}
    rule_tbl  = {}
    is_del = False
    # only one entry
    if 'sequence-id' in rule_cfg.keys():
        rule_name, rule_cfg = acl_rule_yang2sonic(rule_cfg, msess_tbl)
        if rule_name == None: return False
        rule_tbl[rule_name] = rule_cfg
    else:
        for seq_id in rule_cfg.keys():
            rule_name, rule_cfg = acl_rule_yang2sonic(rule_cfg[seq_id], msess_tbl)
            if rule_name == None: return False
            rule_tbl[rule_name] = rule_cfg

    nwi_pf_add_mirror_sessions(disp_args, msess_tbl)

    for rule in rule_tbl.keys():
        if rule_tbl [rule] == None: is_del = True
        ret_val = acl_set_one_acl_entry(disp_args, pkey_ar[1], rule, rule_tbl[rule])
        if not ret_val: break

    if is_del:
        nwi_pf_clear_mirror_sessions(disp_args)

    return ret_val


def is_vrf_name_valid(vrf_name):
    if not vrf_name.startswith("Vrf") and vrf_name != 'mgmt' and vrf_name != 'management':
        util_utl.utl_err("{} is not start with Vrf, mgmt or management!".format(vrf_name))
        return False
    if len(vrf_name) > 15:
        util_utl.utl_err("{} is too long!".format(vrf_name))
        return False
    return True


def mvrf_restart_services():
    """Restart interfaces-config service and NTP service when mvrf is changed"""
    """
    When mvrf is enabled, eth0 should be moved to mvrf; when it is disabled,
    move it back to default vrf. Restarting the "interfaces-config" service
    will recreate the /etc/network/interfaces file and restart the
    "networking" service that takes care of the eth0 movement.
    NTP service should also be restarted to rerun the NTP service with or
    without "cgexec" accordingly.
    """
    cmd="service ntp stop"
    os.system (cmd)
    cmd="systemctl restart interfaces-config"
    os.system (cmd)
    cmd="service ntp start"
    os.system (cmd)


def vrf_add_management_vrf(config_db):
    """Enable management vrf in config DB"""

    entry = config_db.get_entry('MGMT_VRF_CONFIG', "vrf_global")
    if entry and entry['mgmtVrfEnabled'] == 'true':
        util_utl.utl_log("ManagementVRF is already Enabled.")
        return None
    config_db.mod_entry('MGMT_VRF_CONFIG', "vrf_global", {"mgmtVrfEnabled": "true"})
    mvrf_restart_services()


def vrf_delete_management_vrf(config_db):
    """Disable management vrf in config DB"""

    entry = config_db.get_entry('MGMT_VRF_CONFIG', "vrf_global")
    if not entry or entry['mgmtVrfEnabled'] == 'false':
        util_utl.utl_log("ManagementVRF is already Disabled.")
        return None
    config_db.mod_entry('MGMT_VRF_CONFIG', "vrf_global", {"mgmtVrfEnabled": "false"})
    mvrf_restart_services()


def del_interface_bind_to_vrf(config_db, vrf_name):
    """delete interface bind to vrf"""
    tables = ['INTERFACE', 'PORTCHANNEL_INTERFACE', 'VLAN_INTERFACE', 'LOOPBACK_INTERFACE']
    for table_name in tables:
        interface_dict = config_db.get_table(table_name)
        if interface_dict:
            for interface_name in interface_dict.keys():
                if interface_dict[interface_name].has_key('vrf_name') and vrf_name == interface_dict[interface_name]['vrf_name']:
                    interface_dependent = interface_ipaddr_dependent_on_interface(config_db, interface_name)
                    for interface_del in interface_dependent:
                        config_db.set_entry(table_name, interface_del, None)
                    config_db.set_entry(table_name, interface_name, None)


def is_interface_bind_to_vrf(config_db, interface_name):
    """whether interface bind to vrf or not"""
    table_name = get_interface_table_name(interface_name)
    if table_name == "":
        return False
    entry = config_db.get_entry(table_name, interface_name)
    if entry and entry.get("vrf_name"):
        return True
    return False


def bind_interface_to_vrf(config_db, interface_name, vrf_name):
    """bind interface to vrf"""
    table_name = get_interface_table_name(interface_name)
    if table_name == "":
        util_utl.utl_err("interface name is not valid.")
        return False
    if is_interface_bind_to_vrf(config_db, interface_name) is True and \
            config_db.get_entry(table_name, interface_name).get('vrf_name') == vrf_name:
        return True

    # Clean ip addresses if interface configured
    interface_dependent = interface_ipaddr_dependent_on_interface(config_db,
                                                                  interface_name)
    for interface in interface_dependent:
        config_db.set_entry(table_name, interface, None)
    config_db.set_entry(table_name, interface_name, {"vrf_name": vrf_name})
    # if does not work, please reference config source code
    return True


def add_vrf(config_db, vrf_name, vlan_ids):
    """Add vrf"""
    if not is_vrf_name_valid(vrf_name):
        return False

    if vrf_name == 'mgmt' or vrf_name == 'management':
        vrf_add_management_vrf(config_db)
    else:
        config_db.set_entry('VRF', vrf_name, {"NULL": "NULL"})

    for vlan_id in vlan_ids:
        vlan_name = "Vlan{}".format(vlan_id)
        if bind_interface_to_vrf(config_db, vlan_name, vrf_name):
            util_utl.utl_err("bind {} to {} failed".format(vlan_name, vrf_name))

    return True


def del_vrf(config_db, vrf_name):
    """Delete vrf"""

    if not is_vrf_name_valid(vrf_name):
        return False

    if vrf_name == 'mgmt' or vrf_name == 'management':
        vrf_delete_management_vrf(config_db)
    else:
        del_interface_bind_to_vrf(config_db, vrf_name)
        config_db.set_entry('VRF', vrf_name, None)
    return True


# To create vrf and bind vlan
# vrf name should be start with "VRF"
def nwi_db_cfg_vrf(oc_yph, pkey_ar, val, is_create, disp_args):
    vrf_name = pkey_ar[0]

    try:
        cfg = {} if val == "" else eval(val)
        vlan_ids = cfg["vlanIds"]
    except:
        return False

    return add_vrf(disp_args.cfgdb, vrf_name, vlan_ids)


# delete vrf
def nwi_delete_vrf(oc_yph, pkey_ar, disp_args):
    return del_vrf(disp_args.cfgdb, pkey_ar[0])
