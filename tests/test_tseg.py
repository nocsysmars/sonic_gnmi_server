import unittest, pdb, argparse, test_inc, types, json

PATH_SET_TSEG_TMPL = '/vesta/traffic-seg'
PATH_GET_TSEG_TMPL = '/vesta/traffic-seg'

class TestTSeg(test_inc.MyTestCase):
    def chk_output(self, tbl, output, is_assert_in = True):
        if isinstance(tbl, dict):
            for key in tbl:
                self.chk_output(json.dumps(tbl[key]).replace(' ',''), output, is_assert_in)
        else:
            chk_str = str(tbl)
            if is_assert_in:
                self.assertIn(chk_str, output)
            else:
                self.assertNotIn(chk_str, output)

    def test_1_add_port1_to_downlink(self):
        TEST_CFG_TSEG_JSON="""{
          "downlink": ["Ethernet1"],
        }"""

        org_cfg = eval(TEST_CFG_TSEG_JSON)
        output = self.run_script(['update', PATH_SET_TSEG_TMPL, "'{0}'".format(TEST_CFG_TSEG_JSON)])

        if self.chk_ret:
           output = self.run_script(['get', PATH_GET_TSEG_TMPL, ''])
           output = "".join(output.replace('\n', '').split())
           self.chk_output(org_cfg, output)

    def test_2_add_p1p2_to_downlink(self):
        TEST_CFG_TSEG_JSON="""{
          "downlink": ["Ethernet1", "Ethernet2"],
        }"""

        org_cfg = eval(TEST_CFG_TSEG_JSON)
        output = self.run_script(['update', PATH_SET_TSEG_TMPL, "'{0}'".format(TEST_CFG_TSEG_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_TSEG_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_3_add_port1_to_downlink2(self):
        TEST_CFG_TSEG_JSON="""{
          "downlink": "Ethernet1",
        }"""

        org_cfg = eval(TEST_CFG_TSEG_JSON)
        output = self.run_script(['update', PATH_SET_TSEG_TMPL, "'{0}'".format(TEST_CFG_TSEG_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_TSEG_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

    def test_4_clear_downlink(self):
        TEST_CFG_TSEG_JSON="""{
          "downlink": []
        }"""

        org_cfg = eval(TEST_CFG_TSEG_JSON)
        output = self.run_script(['update', PATH_SET_TSEG_TMPL, "'{0}'".format(TEST_CFG_TSEG_JSON)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_TSEG_TMPL, ''])
            output = "".join(output.replace('\n', '').split())
            self.chk_output(org_cfg, output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1, 2, 3, 4]

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

    TestCls = TestTSeg
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

