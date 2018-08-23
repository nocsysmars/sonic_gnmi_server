import unittest
import pdb
import argparse
import test_inc

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
PATH_SET_IP_TMPL       = '/interfaces/interface[name={0}]/routed-vlan/ipv4/addresses/address[ip={1}]/config'

class TestIp(test_inc.MyTestCase):
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

    def test_add_ip4_to_vlan(self):
        inf_name = 'Vlan3001'
        ip       = "100.100.100.200"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip, pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_del_ip4_from_vlan(self):
        inf_name = 'Vlan3001'
        ip       = "100.100.100.200"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
        self.assertNotIn(ip, "".join(output.replace('\n', '').split()))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIp('test_create_vlan'))
    suite.addTest(TestIp('test_add_ip4_to_vlan'))
    suite.addTest(TestIp('test_del_ip4_from_vlan'))
    suite.addTest(TestIp('test_destroy_vlan'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestIp.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestIp.dbg_print        = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

