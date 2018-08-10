import unittest
import subprocess
import time
import pdb
import threading
import argparse
import logging
import sys
from test_inc import GNMI_URL_CMD_TMPL
from test_inc import TEST_URL

sys.path.append("../")
from gnmi_server import gNMITarget

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_AGG_ID_TMPL   = '/interfaces/interface[name={0}]/ethernet/config/aggregate-id'
PATH_INF_CFG_EN_TMPL   = '/interfaces/interface[name={0}]/config/enabled'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
#TEAMDCTL_CFG_CMD_TMPL  = 'teamdctl {0} config dump actual'

GNMI_CMD_TMPL          = GNMI_URL_CMD_TMPL.format(TEST_URL)

# 1. need to install gnmi command manually to the same path as GNMI_CMD_TMPL.

class TestPortChannel(unittest.TestCase):
    # if set to False, need to start the server manually first
    # ex: ./gnmi_server.py localhost:5001 --log-level 5
    use_internal_svr = True

    # if set to True, print debug messages for each test case
    dbg_print        = False

    def setUp(self):
        self.time_beg = time.time()

    def tearDown(self):
        print "Time spent : %s" % (time.time() - self.time_beg)

    @classmethod
    def setUpClass(cls):
        if cls.use_internal_svr:
            log_path = '/var/log/gnmi_server.log'
            # clear log file
            with open(log_path, 'w'):
                pass

            log_fmt  = '%(asctime)-1s %(levelname)-5s [%(filename)s %(funcName)s %(lineno)d] %(message)s'
            logging.basicConfig(level = logging.CRITICAL, format = log_fmt, filename = log_path)

            cls.test_svr = gNMITarget(TEST_URL, False, None, None, True)
            cls.test_thd = threading.Thread(target=cls.test_svr.run)
            cls.test_thd.start()
            while not cls.test_svr.is_ready:
                time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.use_internal_svr:
            cls.test_svr.is_stopped = True
            cls.test_thd.join()

    def run_script(self, argument, check_stderr=False):
        exec_cmd = GNMI_CMD_TMPL.format(*argument)

        if self.dbg_print:
            print '\n    Running %s' % exec_cmd

        if check_stderr:
            output = subprocess.check_output(exec_cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(exec_cmd, shell=True)

        if self.dbg_print:
            linecount = output.strip().count('\n')
            if linecount <= 0:
                print '    Output: ' + output.strip()
            else:
                print '    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output))
        return output

    def test_create_pc(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '"{0}"'.format(pc_name)])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn(pc_name, output)

    def test_destroy_pc(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '""'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(pc_name, output)

    def test_add_port_to_pc(self):
        inf_name = 'Ethernet2'
        pc_name  = 'PortChannel2'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '"{0}"'.format(pc_name)])
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        chk_str = '"aggregate-id":"{0}"'.format(pc_name)
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_set_pc_admin_status(self):
        pc_name  = 'PortChannel2'

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
        chk_str = '"admin-status":"UP"'

        is_admin_up = True if chk_str in "".join(output.replace('\n', '').split()) else False

        output = self.run_script(['update',
                                  PATH_INF_CFG_EN_TMPL.format(pc_name),
                                  '"{0}"'.format(["true", "false"][is_admin_up])])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
        chk_str = '"admin-status":"{0}"'.format(["UP", "DOWN"][is_admin_up])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_remove_port_from_pc(self):
        inf_name = 'Ethernet2'
        pc_name  = 'PortChannel2'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '""'])
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        chk_str = '"aggregate-id":"{0}"'.format(pc_name)
        self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestPortChannel('test_create_pc'))
    suite.addTest(TestPortChannel('test_add_port_to_pc'))
    suite.addTest(TestPortChannel('test_set_pc_admin_status'))
    suite.addTest(TestPortChannel('test_remove_port_from_pc'))
    suite.addTest(TestPortChannel('test_destroy_pc'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestPortChannel.use_internal_svr = False
        TEST_URL = args.target
        GNMI_CMD_TMPL = GNMI_URL_CMD_TMPL.format(TEST_URL)

    TestPortChannel.dbg_print        = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

