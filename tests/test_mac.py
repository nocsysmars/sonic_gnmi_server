import unittest, pdb, argparse, test_inc, types, json

PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_TAG_VLAN_TMPL = '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/trunk-vlans'

PATH_SET_MAC_TMPL = '/vesta/mac'
PATH_GET_MAC_TMPL = '/vesta/mac'

class TestMac(test_inc.MyTestCase):
    def chk_output(self, tbl, output, is_assert_in = True):
        if isinstance(tbl, dict):
            for key in tbl:
                self.chk_output(tbl[key], output, is_assert_in)
        else:
            chk_str = str(tbl)
            if is_assert_in:
                self.assertIn(chk_str, output)
            else:
                self.assertNotIn(chk_str, output)

    def test_1_create_vlan100(self):
        vlan_name = 'Vlan100'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '"{0}"'.format(vlan_name)])

    def test_2_add_port5_to_tag_vlan100(self):
        inf_name = 'Ethernet5'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[100]"'])

    def test_3_add_mac_to_port5(self):
        TEST_CFG_JSON="""{
          "1": {
            "port": "Ethernet5",
            "mac" : "00:00:00:10:20:30",
            "vlan": 100
          }
        }"""

        output = self.run_script(['update', PATH_SET_MAC_TMPL, "'{0}'".format(TEST_CFG_JSON)])

    def test_4_del_mac_from_port5(self):
        TEST_CFG_JSON="""{
          "1": {
            "mac" : "00:00:00:10:20:30",
            "vlan": 100,
          }
        }"""

        output = self.run_script(['update', PATH_SET_MAC_TMPL, "'{0}'".format(TEST_CFG_JSON)])

    def test_5_del_mac_from_port5_2(self):
        TEST_CFG_JSON="""{
          "1": {
            "port": "",
            "mac" : "00:00:00:10:20:30",
            "vlan": 100,
          }
        }"""

        output = self.run_script(['update', PATH_SET_MAC_TMPL, "'{0}'".format(TEST_CFG_JSON)])

    def test_6_del_mac_from_port5_swss(self):
        TEST_CFG_JSON="""{
          "1": {
            "port": "Ethernet5",
            "mac" : "00:00:00:10:20:30",
            "vlan": 100,
            "mode": "del"
          }
        }"""

        output = self.run_script(['update', PATH_SET_MAC_TMPL, "'{0}'".format(TEST_CFG_JSON)])

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1, 2]

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

    TestCls = TestMac
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

