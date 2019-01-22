#
# util_lr.py
#
# APIs for processing local routing info.
#

import subprocess
import json
import pdb
import util_utl

# sr list needed to check existence
OLD_SR_LST = []

def lr_get_pfx_str(pfx_str):
    return '0.0.0.0/0' if pfx_str == 'default' else pfx_str

def lr_del_all_nhop(sr_obj):
    old_nhop_lst = [ x for x in sr_obj.next_hops.next_hop ]
    for old_nhop in old_nhop_lst:
        sr_obj.next_hops.next_hop.delete(old_nhop)

def lr_add_nexthop(lr_yph, sr_obj, idx, nh_str, inf):
    infs = lr_yph.get("/interfaces")[0]
    if inf not in infs.interface:
        # currently 'eth0' is not usable via gnmi service
        # so just return if inf does not exist
        # infs.interface.add(inf)
        return False

    nh = sr_obj.next_hops.next_hop.add(idx)
    nh.config.next_hop = nh_str
    nh.interface_ref.config._set_interface(inf)
    return True

def lr_get_oc_sr(oc_lr, pfx_str, new_sr_lst, old_sr_lst):
    oc_sr = None
    if pfx_str in oc_lr.static_routes.static:
        oc_sr = oc_lr.static_routes.static[pfx_str]
        if pfx_str in old_sr_lst:
            old_sr_lst.remove(pfx_str)
        lr_del_all_nhop(oc_sr)
    else:
        oc_sr = oc_lr.static_routes.static.add(pfx_str)
    new_sr_lst.append(pfx_str)

    return oc_sr

# fill DUT's route info into lr_yph
# ex: key_ar = [u'0.0.0.0/0', u'prefix']
def lr_get_info(lr_yph, path_ar, key_ar, disp_args):
    """
    use 'ip route show' command to gather information
    """
    ret_val = False
    oc_lr = lr_yph.get("/local-routes")[0]

    global OLD_SR_LST
    new_sr_lst = []
    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 route show')
    if is_ok:
        output = output.splitlines()
        # ex:
        #   default via 192.168.200.254 dev eth0
        #   172.17.2.0/24
        #       nexthop via 10.0.0.108  dev Ethernet54 weight 1
        #       nexthop via 10.0.0.142  dev Ethernet71 weight 1
        #
        #   default via 192.168.200.254 dev eth0 proto zebra
        #   100.100.100.0/24 dev Ethernet4 proto kernel scope link src 100.100.100.104 linkdown
        #   172.17.2.0/24 linkdown
        #           nexthop via 100.100.100.104  dev Ethernet4 weight 1 linkdown
        #           nexthop via 100.100.100.108  dev Ethernet8 weight 1 linkdown

        idx = 0
        while idx < len(output):
            ldata = output[idx].split()
            nh_id = 0
            oc_sr = None
            pfx_str = lr_get_pfx_str(ldata[0])

            if 'dev' not in ldata:
                # ecmp
                oc_sr = lr_get_oc_sr(oc_lr, pfx_str, new_sr_lst, OLD_SR_LST)
                idx += 1
                while 'nexthop' in output[idx]:
                    nh_data = output[idx].split()
                    if lr_add_nexthop(lr_yph, oc_sr, nh_id, nh_data[2], nh_data[4]):
                        nh_id += 1
                    idx += 1
            else:
                oc_sr = lr_get_oc_sr(oc_lr, pfx_str, new_sr_lst, OLD_SR_LST)
                if lr_add_nexthop(lr_yph, oc_sr, 0, ldata[2], ldata[4]):
                    nh_id += 1
                idx += 1

            if oc_sr and nh_id == 0:
                oc_lr.static_routes.static.delete(pfx_str)

            if key_ar and key_ar[0] == pfx_str:
                break

        ret_val = True

    # remote old sr
    for old_sr in OLD_SR_LST:
        oc_sr = oc_lr.static_routes.static[old_sr]
        lr_del_all_nhop(oc_sr)
        oc_lr.static_routes.static.delete(old_sr)

    OLD_SR_LST = new_sr_lst

    return ret_val

# ex:    pkey_ar = [u'172.17.2.0/24']
#   val for del all = ''
#   val for add     = '{'1': {'interface-ref': {'config': {'interface': 'Ethernet71'}},
#                             'config': {'next-hop': '10.0.0.142'}}}'
# To set static route (v4)
def lr_set_route_v4(oc_yph, pkey_ar, val, is_create, disp_args):
    try:
        rt_cfg  = {} if val == "" else eval(val)

        nh_str = ""
        for k, v in rt_cfg.items():
            rt_inf  = v['interface-ref']['config']['interface']
            rt_nh   = v['config']['next-hop']
            nh_tmp  = "nexthop via {0} dev {1}".format(rt_nh, rt_inf)
            nh_str  = " ".join([nh_str, nh_tmp])
    except:
        return False

    # {0} : add/del
    # {1} : 172.17.2.0/24
    # {2} : nexthop via 10.0.0.108 dev Ethernet54
    IP_ROUTE_CMD_TMPL = "ip route {0} {1} {2}"

    # delete all old routes
    exec_cmd = IP_ROUTE_CMD_TMPL.format("del", pkey_ar[0], "")
    ret_val = util_utl.utl_execute_cmd(exec_cmd)

    # add new routes
    if nh_str != "":
        exec_cmd = IP_ROUTE_CMD_TMPL.format("add", pkey_ar[0], nh_str)
        ret_val = util_utl.utl_execute_cmd(exec_cmd)

    return ret_val

