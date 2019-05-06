import unittest, pdb, argparse, test_inc, types

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
PATH_SET_IP_TMPL       = '/interfaces/interface[name={0}]/routed-vlan/ipv4/addresses/address[ip={1}]/config'

PATH_SET_ROUTE_TMPL    = '/local-routes/static-routes/static[prefix={0}]/next-hops/next-hop'
PATH_GET_ROUTE_TMPL    = '/local-routes/static-routes'

class TestIp(test_inc.MyTestCase):
    def test_1_create_vlan(self):
        vlan_name = 'Vlan3001'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '"{0}"'.format(vlan_name)])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn(vlan_name, output)

    def test_2_destroy_vlan(self):
        vlan_name = 'Vlan3001'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '""'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(vlan_name, output)

    def test_3_add_ip4_to_vlan(self):
        inf_name = 'Vlan3001'
        ip       = "100.100.100.200"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip, pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_4_del_ip4_from_vlan(self):
        inf_name = 'Vlan3001'
        ip       = "100.100.100.200"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(ip, "".join(output.replace('\n', '').split()))

    def test_5_add_ip4_to_port(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.104"
        inf_2 = 'Ethernet8'
        ip2   = "200.100.100.108"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip1, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip2, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_2, ip2),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_2), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_6_del_ip4_from_port(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.104"
        inf_2 = 'Ethernet8'
        ip2   = "200.100.100.108"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
        self.assertNotIn(ip1, "".join(output.replace('\n', '').split()))

        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_2, ip2),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_2), ''])
        self.assertNotIn(ip2, "".join(output.replace('\n', '').split()))

    def test_7_add_static_route(self):
        ip_pfx   = "172.17.2.0/24"
        nh1      = '"next-hop":"100.100.100.104"'
        nh2      = '"next-hop":"200.100.100.108"'
        dev1     = '"interface":"Ethernet4"'
        dev2     = '"interface":"Ethernet8"'
        cfg_str  = """
        { "1" : {"config": { %s },
                 "interface-ref": {"config": {%s} } },
          "2" : {"config": { %s },
                 "interface-ref": {"config": {%s} } } }
        """.replace('\n', '') % (nh1, dev1, nh2, dev2)

        output = self.run_script(['update',
                                  PATH_SET_ROUTE_TMPL.format(ip_pfx),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_ROUTE_TMPL, ''])
        output = "".join(output.replace('\n', '').split())
        self.assertIn(ip_pfx, output)
        self.assertIn(nh1, output)
        self.assertIn(nh2, output)
        self.assertIn(dev1, output)
        self.assertIn(dev2, output)

    def test_8_del_static_route(self):
        ip_pfx   = "172.17.2.0/24"
        cfg_str = ""
        output = self.run_script(['update',
                                  PATH_SET_ROUTE_TMPL.format(ip_pfx),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_ROUTE_TMPL, ''])
        self.assertNotIn(ip_pfx, "".join(output.replace('\n', '').split()))

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,3,4,2,5,7,8,6]
    #
    test_case[1] = [1,3]
    #
    test_case[2] = [4,2]

    if t_case:
        t_sel = eval (t_case)
    else:
        t_sel = 0

    if type(t_sel) == types.ListType:
        print 'Running Custom Test Case, %s' % (t_sel)
        test_flst = map(lambda x: test_inc.TEST_OP_LST[x], t_sel)
    elif t_sel in test_case:
        test_flst = map(lambda x: test_inc.TEST_OP_LST[x], test_case[t_sel])
        print 'Running Test Case %d, %s' % (t_sel, test_case[t_sel])
    else:
        test_flst = ['test_case_not_found']
        t_cls.t_case = test_case
        t_cls.t_sel  = t_sel

    return unittest.TestSuite(map(t_cls, test_flst))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    parser.add_argument('--case', action="store", type=str, default=None,
                           help="ex: 1 (pre-defined test case) / \
                                     [1,2,3] (custom test case)")
    parser.add_argument('--chk', action="store_true", help="check result")
    args = parser.parse_args()

    TestCls = TestIp
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

