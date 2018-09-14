import unittest
import pdb
import argparse
import test_inc
import json

PATH_SET_NTP_TMPL   = '/system/ntp/servers/server[address={0}]/config'
PATH_GET_NTP_TMPL   = '/system'

CFG_NTP_TMPL        = '{{"address":"{0}"}}'

TEST_NTP_SVR_IP     = '103.18.128.60'
TEST_CUR_DATE_TAG   = 'current-datetime'

class TestNtp(test_inc.MyTestCase):
    def test_add_ntp_server(self):
        ntp_cfg = CFG_NTP_TMPL.format(TEST_NTP_SVR_IP)
        output = self.run_script(['update', PATH_SET_NTP_TMPL.format(TEST_NTP_SVR_IP), "'{0}'".format(ntp_cfg)])
        output = self.run_script(['get', PATH_GET_NTP_TMPL, ''])
        self.assertIn(TEST_NTP_SVR_IP, output)

    def test_del_ntp_server(self):
        ntp_cfg = CFG_NTP_TMPL.format("")
        output = self.run_script(['update', PATH_SET_NTP_TMPL.format(TEST_NTP_SVR_IP), "'{0}'".format(ntp_cfg)])
        output = self.run_script(['get', PATH_GET_NTP_TMPL, ''])
        self.assertIn(TEST_CUR_DATE_TAG, output)
        self.assertNotIn(TEST_NTP_SVR_IP, output)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestNtp('test_add_ntp_server'))
    suite.addTest(TestNtp('test_del_ntp_server'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestNtp.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestNtp.dbg_print = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

