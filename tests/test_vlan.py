import unittest, pdb, argparse, test_inc, types, json

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_TAG_VLAN_TMPL = '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/trunk-vlans'
PATH_INF_UTAG_VLAN_TMPL= '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/native-vlan'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'

class TestVlan(test_inc.MyTestCase):
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

    def test_3_add_port_to_tag_vlan(self):
        inf_name = 'Ethernet4'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[2001, 2002]"'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn('Vlan2001', output)
        self.assertIn('Vlan2002', output)

        chk_str = '"trunk-vlans":[2001,2002]'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_4_remove_port_from_tag_vlan(self):
        inf_name = 'Ethernet4'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[]"'])

        chk_str = '"trunk-vlans"'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

        # bcz vlanmgrd will exit unexpectedly when destroying the vlan, so
        # remove this temporarily...
        #
        # remove vlan 2001, 2002
        #vlan_2001 = 'Vlan2001'
        #vlan_2002 = 'Vlan2002'
        #output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_2001), '""'])
        #output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_2002), '""'])

        #output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        #self.assertNotIn(vlan_2001, output)
        #self.assertNotIn(vlan_2002, output)
        #time.sleep(2)

    def test_5_add_port_to_untag_vlan(self):
        inf_name = 'Ethernet8'
        output = self.run_script(['update',
                                  PATH_INF_UTAG_VLAN_TMPL.format(inf_name),
                                  '"1111"'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn('Vlan1111', output)

        chk_str = '"access-vlan":1111'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_6_remove_port_from_untag_vlan(self):
        inf_name = 'Ethernet8'
        output = self.run_script(['update',
                                  PATH_INF_UTAG_VLAN_TMPL.format(inf_name),
                                  '""'])

        chk_str = '"access-vlan"'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

        # bcz vlanmgrd will exit unexpectedly when destroying the vlan, so
        # remove this temporarily...
        #
        # remove vlan 1111
        #vlan_name = 'Vlan1111'
        #output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '""'])
        #output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        #self.assertNotIn(vlan_name, output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,2,3,4,5,6]
    test_case[1] = [1,3]
    test_case[2] = [4,2]

    if t_case:
        t_sel = eval (t_case)
    else:
        t_sel = 0

    if type(t_sel) == types.ListType:
        print 'Running Custom Test Case, %s' % (t_sel)
        test_flst = map  (lambda x: test_inc.TEST_OP_LST[x], t_sel)
    elif t_sel in test_case:
        test_flst = map (lambda x: test_inc.TEST_OP_LST[x], test_case[t_sel])
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

    TestCls = TestVlan
    if args.target:
        TestVlan.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

