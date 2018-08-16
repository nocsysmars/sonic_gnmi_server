import unittest
import pdb
import argparse
import test_inc

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_TAG_VLAN_TMPL = '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/trunk-vlans'
PATH_INF_UTAG_VLAN_TMPL= '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/native-vlan'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'

class TestVlan(test_inc.MyTestCase):
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
        inf_name = 'Ethernet4'
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
        inf_name = 'Ethernet4'
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

        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertNotIn(vlan_2001, output)
        self.assertNotIn(vlan_2002, output)
        #time.sleep(2)

    def test_add_port_to_untag_vlan(self):
        inf_name = 'Ethernet8'
        output = self.run_script(['update',
                                  PATH_INF_UTAG_VLAN_TMPL.format(inf_name),
                                  '"1111"'])
        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
        self.assertIn('Vlan1111', output)

        chk_str = '"access-vlan":1111'
        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_remove_port_from_untag_vlan(self):
        inf_name = 'Ethernet8'
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestVlan.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestVlan.dbg_print        = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

