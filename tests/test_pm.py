import unittest, pdb, argparse, test_inc, types, json

PATH_SET_MIRROR_TMPL = '/vesta/mirror'
PATH_GET_MIRROR_TMPL = '/vesta/mirror'

class TestPM(test_inc.MyTestCase):
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

    def test_1_add_mirror_port1_to_port3(self):
        TEST_CFG_MIRROR_JSON="""{
          "1": {
            "src-port": "Ethernet1",
            "dst-port": "Ethernet3",
            "mode"    : "Both"
          }
        }"""

        org_cfg = eval(TEST_CFG_MIRROR_JSON)
        output = self.run_script(['update', PATH_SET_MIRROR_TMPL, "'{0}'".format(TEST_CFG_MIRROR_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_MIRROR_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_2_del_mirror_port1_to_port3(self):
        TEST_CFG_MIRROR_JSON="""{
          "1": {
            "src-port": "Ethernet1",
            "dst-port": "Ethernet3",
            "mode"    : "Off"
          }
        }"""

        org_cfg = eval(TEST_CFG_MIRROR_JSON)
        output = self.run_script(['update', PATH_SET_MIRROR_TMPL, "'{0}'".format(TEST_CFG_MIRROR_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_MIRROR_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_3_del_mirror_port1_to_port3_2(self):
        TEST_CFG_MIRROR_JSON="""{
          "1": {
            "src-port": "Ethernet1"
          }
        }"""

        org_cfg = eval(TEST_CFG_MIRROR_JSON)
        output = self.run_script(['update', PATH_SET_MIRROR_TMPL, "'{0}'".format(TEST_CFG_MIRROR_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_MIRROR_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_4_add_mirror_port1_to_port3_vlan_100(self):
        TEST_CFG_MIRROR_JSON="""{
          "1": {
            "src-port": "Ethernet1",
            "dst-port": "Ethernet3",
            "mode"    : "Both",
            "vlan"    : 100
          }
        }"""

        org_cfg = eval(TEST_CFG_MIRROR_JSON)
        output = self.run_script(['update', PATH_SET_MIRROR_TMPL, "'{0}'".format(TEST_CFG_MIRROR_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_MIRROR_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1, 2, 3]

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

    TestCls = TestPM
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

