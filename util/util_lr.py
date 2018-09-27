#
# util_lr.py
#
# APIs for processing local routing info.
#

import subprocess
import json
import pdb
import util_utl

def lr_add_static_route(lr_obj, pfx_str):
    if pfx_str == 'default':
        pfx_str = '0.0.0.0/0'

    return lr_obj.static_routes.static.add(pfx_str)

def lr_add_nexthop(lr_yph, sr_obj, idx, nh_str, inf):
    infs = lr_yph.get("/interfaces")[0]
    if inf not in infs.interface:
        # currently 'eth0' is not usable via gnmi service
        # so just return if inf does not exist
        # infs.interface.add(inf)
        return

    nh = sr_obj.next_hops.next_hop.add(idx)
    nh.config.next_hop = nh_str
    nh.interface_ref.config._set_interface(inf)

# fill DUT's route info into lr_yph
# key_ar [0] : e.g. ""
def lr_get_info(lr_yph, path_ar, key_ar, disp_args):
    """
    use 'ip route show' command to gather information
    """
    ret_val = False
    oc_lr = lr_yph.get("/local-routes")[0]
    oc_lr.static_routes._unset_static()

    (is_ok, output) = util_utl.utl_get_execute_cmd_output('ip -4 route show')
    if is_ok:
        output = output.splitlines()
        # ex:
        #   default via 192.168.200.254 dev eth0
        #   172.17.2.0/24
        #       nexthop via 10.0.0.108  dev Ethernet54 weight 1
        #       nexthop via 10.0.0.142  dev Ethernet71 weight 1
        idx = 0
        while idx < len(output):
            ldata = output[idx].split()
            if len(ldata) == 1:
                # ecmp
                nh_id = 0
                sr = lr_add_static_route(oc_lr, ldata[0])
                idx += 1
                while 'nexthop' in output[idx]:
                    nh_data = output[idx].split()
                    lr_add_nexthop(lr_yph, sr, nh_id, nh_data[2], nh_data[4])
                    nh_id += 1
                    idx += 1
            else:
                if ldata [1] == 'via':
                    sr = lr_add_static_route(oc_lr, ldata[0])
                    lr_add_nexthop(lr_yph, sr, 0, ldata[2], ldata[4])
                idx += 1

        ret_val = True

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

