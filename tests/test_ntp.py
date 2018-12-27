import unittest, pdb, argparse, test_inc, types, json

PATH_SET_NTP_TMPL   = '/system/ntp/servers/server[address={0}]/config'
PATH_GET_NTP_TMPL   = '/system'

CFG_NTP_TMPL        = '{{"address":"{0}"}}'

TEST_NTP_SVR_IP     = '103.18.128.60'
TEST_CUR_DATE_TAG   = 'current-datetime'

class TestNtp(test_inc.MyTestCase):
    def test_1_add_ntp_server(self):
        ntp_cfg = CFG_NTP_TMPL.format(TEST_NTP_SVR_IP)
        output = self.run_script(['update', PATH_SET_NTP_TMPL.format(TEST_NTP_SVR_IP), "'{0}'".format(ntp_cfg)])
        output = self.run_script(['get', PATH_GET_NTP_TMPL, ''])
        self.assertIn(TEST_NTP_SVR_IP, output)

    def test_2_del_ntp_server(self):
        ntp_cfg = CFG_NTP_TMPL.format("")
        output = self.run_script(['update', PATH_SET_NTP_TMPL.format(TEST_NTP_SVR_IP), "'{0}'".format(ntp_cfg)])
        output = self.run_script(['get', PATH_GET_NTP_TMPL, ''])
        self.assertIn(TEST_CUR_DATE_TAG, output)
        self.assertNotIn(TEST_NTP_SVR_IP, output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,2]

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

    TestCls = TestNtp
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

