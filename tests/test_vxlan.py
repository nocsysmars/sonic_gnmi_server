import unittest, pdb, argparse, test_inc, types, json

PATH_SET_SONIC_TMPL = '/sonic'
PATH_GET_SONIC_TMPL = '/sonic'
TEST_CFG_VXLAN_JSON   = """
{
    "VXLAN_TUNNEL": {
        "vtnl01": {
            "src_ip": "169.254.200.31",
            "dst_ip": "169.254.200.35"
            }
        },

    "VXLAN_TUNNEL_MAP": {
        "vtnl01|map1": {
            "vni": "8000",
            "vlan": "Vlan10"
            }
        }
}"""

TEST_CLR_VXLAN_JSON   = """
{
    "VXLAN_TUNNEL": {
        "vtnl01": null
        },

    "VXLAN_TUNNEL_MAP": {
        "vtnl01|map1": null
        }
}"""

class TestVxlan(test_inc.MyTestCase):
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

    def test_1_set_sonic_vxlan_cfg(self):
        org_cfg = eval(TEST_CFG_VXLAN_JSON)
        output = self.run_script(['update', PATH_SET_SONIC_TMPL, "'{0}'".format(TEST_CFG_VXLAN_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_SONIC_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_2_clear_sonic_vxlan_cfg(self):
        org_cfg = eval(TEST_CFG_VXLAN_JSON)
        output = self.run_script(['update', PATH_SET_SONIC_TMPL, "'{0}'".format(TEST_CLR_VXLAN_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_SONIC_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output, False)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,2]
    test_case[1] = [1]
    test_case[2] = [2]

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

    TestCls = TestVxlan
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

