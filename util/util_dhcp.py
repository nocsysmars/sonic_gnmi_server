#
# util_dhcp.py
#
# APIs for processing dhcp replay

import netaddr
import util_utl


def is_ipaddress(ip_addr):
    if not ip_addr:
        return False
    try:
        netaddr.IPAddress(str(ip_addr))
    except ValueError:
        return False
    return True


def restart_dhcp_relay():
    return util_utl.utl_execute_cmd("systemctl restart dhcp_relay")


def add_vlan_dhcp_relay(config_db, vid, ip_addr):
    if not is_ipaddress(ip_addr):
        util_utl.utl_err("{} is an invalid IP address".format(ip_addr))
        return False

    vlan_name = "Vlan{}".format(vid)
    vlan = config_db.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        util_utl.utl_err("{} does not exist".format(vlan_name))
        return False

    dhcp_relays = vlan.get('dhcp_servers', [])
    if ip_addr in dhcp_relays:
        util_utl.utl_log("{} is alreay a DHCP relay for {}".format(ip_addr,
                                                                   vlan_name))
    else:
        dhcp_relays.append(ip_addr)
        vlan['dhcp_servers'] = dhcp_relays
        config_db.set_entry('VLAN', vlan_name, vlan)
        util_utl.utl_log("Added DHCP relay destionation address {} to {}"
                         .format(ip_addr, vlan_name))
        # try:
        #     util_utl.utl_execute_cmd("systemctl restart dhcp_relay")
        # except SystemExit as e:
        #     util_utl.utl_log("Restart service dhcp_relay failed with error {}"
        #                      .format(e))
        #    return False
    return True


def del_vlan_dhcp_relay(config_db, vid, ip_addr):
    if not is_ipaddress(ip_addr):
        util_utl.utl_err("{} is an invalid IP address".format(ip_addr))
        return False

    vlan_name = "Vlan{}".format(vid)
    vlan = config_db.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        util_utl.utl_err("{} does not exist".format(vlan_name))
        return False

    dhcp_relays = vlan.get('dhcp_servers', [])
    if ip_addr not in dhcp_relays:
        util_utl.utl_log("{} is not a DHCP relay destination for {}"
                         .format(ip_addr, vlan_name))
    else:
        dhcp_relays.remove(ip_addr)
        if len(dhcp_relays) == 0:
            del vlan['dhcp_servers']
        else:
            vlan['dhcp_servers'] = dhcp_relays
        config_db.set_entry('VLAN', vlan_name, vlan)
        util_utl.utl_log("Remove DHCP relay destination address {} from {}"
                         .format(ip_addr, vlan_name))
        # try:
        #     util_utl.utl_execute_cmd("systemctl restart dhcp_relay")
        # except SystemExit as e:
        #     util_utl.utl_err("Restart service dhcp_relay failed with error {}"
        #                      .format(e))
        #     return False
    return True


def set_vlan_dhcp_relay(config_db, vid, ip_addresses):
    for ip_addr in ip_addresses:
        if not is_ipaddress(ip_addr):
            util_utl.utl_err("{} is an invalid IP address".format(ip_addr))
            return False

    vlan_name = "Vlan{}".format(vid)
    vlan = config_db.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        util_utl.utl_err("{} does not exist".format(vlan_name))
        return False

    dhcp_relays = vlan.get('dhcp_servers', [])
    if len(ip_addresses) == 0:
        del vlan['dhcp_servers']
    else:
        del dhcp_relays[:]
        for ip_addr in ip_addresses:
            dhcp_relays.append(ip_addr)
        vlan['dhcp_servers'] = dhcp_relays
    config_db.set_entry('VLAN', vlan_name, vlan)
    util_utl.utl_log("Set DHCP relay destination addresses {} for {}"
                     .format(ip_addresses, vlan_name))
    # try:
    #    util_utl.utl_execute_cmd("systemctl restart dhcp_relay")
    # except SystemExit as e:
    #     util_utl.utl_err("Restart service dhcp_relay failed with error {}"
    #                      .format(e))
    #    return False
    return True


def dhcp_relay_restart(oc_yph, pkey_ar, val, is_create, disp_args):
    util_utl.utl_log("Restart dhcp relay.")
    return restart_dhcp_relay()


def vlan_config_dhcp_relay(oc_yph, pkey_ar, val, is_create, disp_args):
    if not pkey_ar[1].isdigit():
        return False

    try:
        cfg = {} if val == "" else eval(val)
        ip_addr_add = cfg.get('ip-addr-add')
        ip_addr_del = cfg.get('ip-addr-del')
        ip_addr_set = cfg.get('ip-addr-set')
    except:
        return False

    vid = int(pkey_ar[1])
    if ip_addr_add is not None and ip_addr_add != "":
        return add_vlan_dhcp_relay(disp_args.cfgdb, vid, ip_addr_add)
    elif ip_addr_del is not None and ip_addr_del != "":
        return del_vlan_dhcp_relay(disp_args.cfgdb, vid, ip_addr_del)
    elif ip_addr_set is not None and len(ip_addr_set) > 0:
        return set_vlan_dhcp_relay(disp_args.cfgdb, vid, ip_addr_set)

    return False
