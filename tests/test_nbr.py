import unittest, pdb, argparse, test_inc, types

PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
PATH_INF_CFG_EN_TMPL   = '/interfaces/interface[name={0}]/config/enabled'
PATH_GET_NBR_TMPL      = '/interfaces/interface/routed-vlan/ipv4/neighbors/neighbor'

class TestNbr(test_inc.MyTestCase):
    def test_1_set_admin_status_port2(self):
        intf_name  = 'Ethernet2'

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(intf_name), ''])
        chk_str = '"admin-status":"UP"'

        is_admin_up = True if chk_str in "".join(output.replace('\n', '').split()) else False

        if not is_admin_up:
            output = self.run_script(['update',
                                      PATH_INF_CFG_EN_TMPL.format(intf_name),
                                      '"{0}"'.format(["true", "false"][is_admin_up])])

            if self.chk_ret:
                output = self.run_script(['get', PATH_GET_INF_TMPL.format(intf_name), ''])
                chk_str = '"admin-status":"{0}"'.format(["UP", "DOWN"][is_admin_up])
                self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_2_add_nbr1_to_port2(self):
        intf_name = 'Ethernet2'
        ip        = "100.102.100.11"
        mac       = "00:00:00:00:00:20"
        output = self.run_shell_cmd(['ip neigh replace %s lladdr %s dev %s' % (ip, mac, intf_name)])

        #self.assertIn(vlan_name, output)
        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_NBR_TMPL.format(intf_name), ''])
            output = "".join(output.replace('\n', '').split())

            self.assertIn(ip, output)
            self.assertIn(mac, output)
            self.assertIn(intf_name, output)

    def test_3_add_nbr2_to_port2(self):
        intf_name = 'Ethernet2'
        ip        = "100.102.100.12"
        mac       = "00:00:00:00:00:30"
        output = self.run_shell_cmd(['ip neigh replace %s lladdr %s dev %s' % (ip, mac, intf_name)])

        #self.assertIn(vlan_name, output)
        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_NBR_TMPL.format(intf_name), ''])
            output = "".join(output.replace('\n', '').split())

            self.assertIn(ip, output)
            self.assertIn(mac, output)
            self.assertIn(intf_name, output)

    def test_4_del_nbr1_from_port2(self):
        intf_name = 'Ethernet2'
        ip        = "100.102.100.11"
        mac       = "00:00:00:00:00:20"
        output = self.run_shell_cmd(['ip neigh del %s lladdr %s dev %s' % (ip, mac, intf_name)])

        if self.chk_ret:
        #self.assertIn(vlan_name, output)
            output = self.run_script(['get', PATH_GET_NBR_TMPL.format(intf_name), ''])
            output = "".join(output.replace('\n', '').split())

            self.assertNotIn(ip, output)
            self.assertNotIn(mac, output)

    def test_5_del_nbr2_from_port2(self):
        intf_name = 'Ethernet2'
        ip        = "100.102.100.12"
        mac       = "00:00:00:00:00:30"
        output = self.run_shell_cmd(['ip neigh del %s lladdr %s dev %s' % (ip, mac, intf_name)])

        #self.assertIn(vlan_name, output)
        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_NBR_TMPL.format(intf_name), ''])
            output = "".join(output.replace('\n', '').split())

            self.assertNotIn(ip, output)
            self.assertNotIn(mac, output)


def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,2,3,4,5]
    #
    #

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

    TestCls = TestNbr
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

