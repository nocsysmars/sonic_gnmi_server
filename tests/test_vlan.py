import unittest
import subprocess
import os
import time
import pdb

# {0} : get/update
# {1} : path (ex: "/interfaces/interface/config/name")
# {2} : new value
GNMI_CMD_TMPL          = '/home/admin/gocode/bin/gnmi -addr 127.0.0.1:5001 {0} {1} {2}'

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_TAG_VLAN_TMPL = '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/trunk-vlans'
PATH_INF_UTAG_VLAN_TMPL= '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/native-vlan'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'

DBG_PRINT = False

# 1. need to install gnmi command manually to the same path as GNMI_CMD_TMPL.
# 2. need to start the server manually first, ex: ./gnmi_server.py localhost:5001 --log-level 5
class TestVlan(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))

    def run_script(self, argument, check_stderr=False):
        exec_cmd = GNMI_CMD_TMPL.format(*argument)

        if DBG_PRINT:
            print '\n    Running %s' % exec_cmd

        if check_stderr:
            output = subprocess.check_output(exec_cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(exec_cmd, shell=True)

        if DBG_PRINT:
            linecount = output.strip().count('\n')
            if linecount <= 0:
                print '    Output: ' + output.strip()
            else:
                print '    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output))
        return output

    def test_create_vlan(self):
        vlan_name = 'Vlan3001'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '"{0}"'.format(vlan_name)])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn(vlan_name, output)

    def test_destroy_vlan(self):
        vlan_name = 'Vlan3001'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '""'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(vlan_name, output)

    def test_add_port_to_tag_vlan(self):
        inf_name = 'Ethernet2'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[2001, 2002]"'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn('Vlan2001', output)
        self.assertIn('Vlan2002', output)

        chk_str = '"trunk-vlans":[2001,2002]'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_remove_port_from_tag_vlan(self):
        inf_name = 'Ethernet2'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[]"'])

        chk_str = '"trunk-vlans"'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

        # remove vlan 2001, 2002
        vlan_2001 = 'Vlan2001'
        vlan_2002 = 'Vlan2002'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_2001), '""'])
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_2002), '""'])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(vlan_2001, output)
        self.assertNotIn(vlan_2002, output)
        #time.sleep(2)

    def test_add_port_to_untag_vlan(self):
        inf_name = 'Ethernet3'
        output = self.run_script(['update',
                                  PATH_INF_UTAG_VLAN_TMPL.format(inf_name),
                                  '"1111"'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn('Vlan1111', output)

        chk_str = '"access-vlan":1111'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_remove_port_from_untag_vlan(self):
        inf_name = 'Ethernet3'
        output = self.run_script(['update',
                                  PATH_INF_UTAG_VLAN_TMPL.format(inf_name),
                                  '""'])

        chk_str = '"access-vlan"'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

        # remove vlan 1111
        vlan_name = 'Vlan1111'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '""'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(vlan_name, output)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestVlan('test_create_vlan'))
    suite.addTest(TestVlan('test_destroy_vlan'))
    suite.addTest(TestVlan('test_add_port_to_tag_vlan'))
    suite.addTest(TestVlan('test_remove_port_from_tag_vlan'))
    suite.addTest(TestVlan('test_add_port_to_untag_vlan'))
    suite.addTest(TestVlan('test_remove_port_from_untag_vlan'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

