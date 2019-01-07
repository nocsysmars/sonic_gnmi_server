import unittest, time, logging, subprocess, threading, sys, types

sys.path.append("../")
from gnmi_server import gNMITarget

# {0}   : URL to test
# {{0}} : get/update
# {{1}} : path (ex: "/interfaces/interface/config/name")
# {{2}} : new value for update
#
#  NOTE : need to install gnmi command manually to the same path as GNMI_URL_CMD_TMPL.
GNMI_URL_CMD_TMPL      = '/home/admin/gocode/bin/gnmi -addr {0} {{0}} {{1}} {{2}}'

# url of gnmi server to test
TEST_URL               = 'localhost:5001'

TEST_OP_LST = {}

def gen_test_op_lst(cls):
    global TEST_OP_LST

    # test function name format: test_NN_xxx
    # NN: index of function in TEST_OP_LST
    for x, y in cls.__dict__.items():
        if type(y) == types.FunctionType:
            tmp_name = x.split('_')
            if tmp_name[1].isdigit():
                op_num = int(tmp_name[1])
                TEST_OP_LST[op_num] = x

def print_test_op_lst():
    global TEST_OP_LST

    print "\n"
    for x, y in TEST_OP_LST.items():
        print "OP %d : %s" % (x, y)


class MyTestCase(unittest.TestCase):
    # if set to False, need to start the server manually first
    # ex: ./gnmi_server.py localhost:5001 --log-level 5
    use_internal_svr = True

    # if set to True, print debug messages for each test case
    dbg_print        = False

    def setUp(self):
        self.time_beg = time.time()

    def tearDown(self):
        print "Time spent : %s" % (time.time() - self.time_beg)

    def test_case_not_found(self):
        print_test_op_lst()

        print "=" * 40
        for x, y in self.t_case.items():
            print "CASE %d : %s" % (x, y)

        self.assertIn(self.t_sel, self.t_case.keys())

    @classmethod
    def setUpClass(cls):
        if cls.use_internal_svr:
            t_beg = time.time()

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

            print "\nSetup internal test server, time spent : %s\n" % (time.time() - t_beg)

    @classmethod
    def tearDownClass(cls):
        if cls.use_internal_svr:
            cls.test_svr.is_stopped = True
            cls.test_thd.join()

    def run_script(self, argument, check_stderr=False):
        exec_cmd = GNMI_URL_CMD_TMPL.format(TEST_URL).format(*argument)

        if self.dbg_print:
            print '\n    Running %s' % exec_cmd

        if check_stderr:
            output = subprocess.check_output(exec_cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(exec_cmd, shell=True)

        if self.dbg_print:
            print '    Output:\n' + output.strip()
#            linecount = output.strip().count('\n')
#            if linecount <= 0:
#                print '    Output: ' + output.strip()
#            else:
#                print '    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output))
        return output

    def run_shell_cmd(self, argument, check_stderr=False):
        exec_cmd = "{0}".format(*argument)

        if self.dbg_print:
            print '\n    Running %s' % exec_cmd

        if check_stderr:
            output = subprocess.check_output(exec_cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(exec_cmd, shell=True)

        if self.dbg_print:
            print '    Output:\n' + output.strip()
        return output
