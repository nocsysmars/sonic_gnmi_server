from util.util_utl import utl_log, CFGDB_TABLE_NAME_VLAN, CFGDB_TABLE_NAME_VLAN_MBR
from util.util_interface import VLAN_ID_MIN, VLAN_ID_MAX
from util.sonic_helper import VLANTaggingMode
from util.util_interface import interface_db_clear_ip
from sonicpb.sonic_vlan_pb2 import SonicVlan

def vlan_set(oc_yph, pkey_ar, val, is_create, disp_args):
    try:
        vlans = SonicVlan.Vlan.FromString(val)
        for vlan in vlans.vlan_list:
            vlan_info = {}
            vlan_name = vlan.vlan_name
            data = vlan.vlan_list
            if data.vlanid.value in range (VLAN_ID_MIN, VLAN_ID_MAX):
                vlan_info["vlanid"] = data.vlanid.value
                members = [member.value for member in data.members]
                if members:
                    vlan_info["members"] = members
                disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN, vlan_name, vlan_info)
    except:
        return False

    return True

def vlan_set_member(oc_yph, pkey_ar, val, is_create, disp_args):
    try:
        members = SonicVlan.VlanMember.FromString(val)
        for member in members.vlan_member_list:
            member_info = {}
            vlan_name = member.vlan_name
            interface_name = member.port
            data = member.vlan_member_list
            member_info["tagging_mode"] = str(VLANTaggingMode(data.tagging_mode))
            vlan_info = disp_args.cfgdb.get_entry(CFGDB_TABLE_NAME_VLAN, vlan_name)
            if len(vlan_info) == 0:
                utl_log("cannot find vlan {}".format(vlan_name))
                continue
            interface_names = vlan_info.get('members', [])
            if interface_name not in interface_names:
                interface_names.append(interface_name)
                vlan_info["members"] = interface_names
                disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN, vlan_name, vlan_info)
            disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN_MBR, (vlan_name, interface_name), member_info)
    except:
        return False

    return True

def vlan_delete(root_yph, pkey_ar, disp_args):
    try:
        vlan_name = pkey_ar[0]
        vlan_info = disp_args.cfgdb.get_entry(CFGDB_TABLE_NAME_VLAN, vlan_name)
        if len(vlan_info) == 0:
            utl_log("cannot find vlan {}".format(vlan_name))
            return False
        interface_names = vlan_info.get('members', [])
        for interface_name in interface_names:
            disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN_MBR, (vlan_name, interface_name), None)
            interface_db_clear_ip(disp_args.cfgdb, interface_name)
        disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN, vlan_name, None)
    except:
        return False
    return True

def vlan_delete_member(root_yph, pkey_ar, disp_args):
    try:
        vlan_name = pkey_ar[0]
        interface_name = pkey_ar[1]
        vlan_info = disp_args.cfgdb.get_entry(CFGDB_TABLE_NAME_VLAN, vlan_name)
        if len(vlan_info) == 0:
            utl_log("cannot find vlan {}".format(vlan_name))
            return False
        interface_names = vlan_info.get('members', [])
        if interface_name in interface_names:
            interface_names.remove(interface_name)
            if not interface_names:
                del vlan_info['members']
            else:
                vlan_info['members'] = interface_names
            disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN, vlan_name, vlan_info)
        disp_args.cfgdb.set_entry(CFGDB_TABLE_NAME_VLAN_MBR, (vlan_name, interface_name), None)
    except:
        return False

    return True