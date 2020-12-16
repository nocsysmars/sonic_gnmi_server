#
# util_portchannel.py
#
# APIs for processing portchannel
#

import util_utl
from sonicpb.sonic_portchannel_pb2 import SonicPortchannel
from sonicpb.enums_pb2 import SonicPortchannelAdminStatus

PORTCHANNEL_TABLE = "PORTCHANNEL"
PORTCHANNEL_MEMBER_TABLE = "PORTCHANNEL_MEMBER"


def create_portchannel(oc_yph, pkey_ar, val, disp_args):
    """Create port channel"""
    try:
        portchannel = SonicPortchannel.Portchannel.FromString(val)

        for list_key in portchannel.portchannel_list:
            name = list_key.portchannel_name
            min_links = list_key.portchannel_list.min_links
            mtu = list_key.portchannel_list.mtu

            # Delete portchannel and its members when the porchannel exists
            portchannel_member_list = disp_args.cfgdb.get_table(PORTCHANNEL_MEMBER_TABLE)
            for k, v in portchannel_member_list:
                if k == name:
                    disp_args.cfgdb.set_entry(PORTCHANNEL_MEMBER_TABLE, (k, v), None)

            if disp_args.cfgdb.get_entry(PORTCHANNEL_TABLE, name) is not None:
                disp_args.cfgdb.set_entry(PORTCHANNEL_TABLE, name, None)

            # Create new portchannel and add members to it
            fvs = {'admin_status': 'up'}
            fvs['min_links'] = str(min_links.value)
            fvs['mtu'] = str(mtu.value)
            # fvs['fallback'] = 'true'
            disp_args.cfgdb.set_entry(PORTCHANNEL_TABLE, name, fvs)

            for member in list_key.portchannel_list.members:
                member_name = member.value
                disp_args.cfgdb.set_entry(PORTCHANNEL_MEMBER_TABLE, (name, member_name),
                                          {'NULL': 'NULL'})
    except Exception as e:
        util_utl.utl_err("create portchannel failed: " + e.message)
        return False

    return True


def portchannel_add_member(oc_yph, pkey_ar, val, is_create, disp_args):
    """Add given port to portchannel's member"""
    try:
        portchannel = SonicPortchannel.Portchannel.FromString(val)

        for list_key in portchannel.portchannel_list:
            name = list_key.portchannel_name
            for member in list_key.portchannel_list.members:
                disp_args.cfgdb.set_entry(PORTCHANNEL_MEMBER_TABLE, (name, member),
                                          {'NULL': 'NULL'})
    except Exception as e:
        util_utl.utl_err("add member to portchannel failed: " + e.message)
        return False

    return True


def delete_portchannel(oc_yph, pkey_ar, disp_args):
    """Delete portchannel"""
    portchannel_name = pkey_ar[0]

    portchannel_list = disp_args.cfgdb.get_table(PORTCHANNEL_MEMBER_TABLE)
    for k, v in portchannel_list:
        if k == portchannel_name:
            disp_args.cfgdb.set_entry(PORTCHANNEL_MEMBER_TABLE, (k, v), None)

    disp_args.cfgdb.set_entry(PORTCHANNEL_TABLE, portchannel_name, None)

    return True


def remove_portchannel_member(oc_yph, pkey_ar, disp_args):
    """Remove given port from portchannel"""
    port_name = pkey_ar[0]

    portchannel_list = disp_args.cfgdb.get_table(PORTCHANNEL_MEMBER_TABLE)
    for k, v in portchannel_list:
        if v == port_name:
            disp_args.cfgdb.set_entry(PORTCHANNEL_MEMBER_TABLE, (k, v), None)

    return True
