import unittest
import pdb
import argparse
import test_inc

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_AGG_ID_TMPL   = '/interfaces/interface[name={0}]/ethernet/config/aggregate-id'
PATH_INF_CFG_EN_TMPL   = '/interfaces/interface[name={0}]/config/enabled'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
#TEAMDCTL_CFG_CMD_TMPL  = 'teamdctl {0} config dump actual'

class TestPortChannel(test_inc.MyTestCase):
    def test_create_pc(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '"{0}"'.format(pc_name)])
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
        self.assertIn(pc_name, output)

    def test_destroy_pc(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '""'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(pc_name, output)

    def test_add_port_to_pc(self):
        inf_name = 'Ethernet4'
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
        inf_name = 'Ethernet4'
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
        test_inc.TEST_URL = args.target

    TestPortChannel.dbg_print        = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

