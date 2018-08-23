import unittest
import pdb
import argparse
import test_inc

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
PATH_SET_IP_TMPL       = '/interfaces/interface[name={0}]/routed-vlan/ipv4/addresses/address[ip={1}]/config'

PATH_SET_ROUTE_TMPL    = '/local-routes/static-routes/static[prefix={0}]/next-hops/next-hop'
PATH_GET_ROUTE_TMPL    = '/local-routes/static-routes'

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

    def test_add_ip4_to_port(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.104"
        inf_2 = 'Ethernet8'
        ip2   = "100.100.100.108"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip1, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip2, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_2, ip2),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_2), ''])
        self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_del_ip4_from_port(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.104"
        inf_2 = 'Ethernet8'
        ip2   = "100.100.100.108"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
        self.assertNotIn(cfg_str, "".join(output.replace('\n', '').split()))

        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_2, ip2),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_2), ''])
        self.assertNotIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_add_static_route(self):
        ip_pfx   = "172.17.2.0/24"
        nh1      = '"next-hop":"100.100.100.104"'
        nh2      = '"next-hop":"100.100.100.108"'
        dev1     = '"interface":"Ethernet4"'
        dev2     = '"interface":"Ethernet8"'
        cfg_str  = """
        { "1" : {"config": { %s },
                 "interface-ref": {"config": {%s} } },
          "2" : {"config": { %s },
                 "interface-ref": {"config": {%s} } } }
        """.replace('\n', '') % (nh1, dev1, nh2, dev2)

        output = self.run_script(['update',
                                  PATH_SET_ROUTE_TMPL.format(ip_pfx),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_ROUTE_TMPL, ''])
        output = "".join(output.replace('\n', '').split())
        self.assertIn(ip_pfx, output)
        self.assertIn(nh1, output)
        self.assertIn(nh2, output)
        self.assertIn(dev1, output)
        self.assertIn(dev2, output)

    def test_del_static_route(self):
        ip_pfx   = "172.17.2.0/24"
        cfg_str = ""
        output = self.run_script(['update',
                                  PATH_SET_ROUTE_TMPL.format(ip_pfx),
                                  "'{0}'".format(cfg_str)])

        output = self.run_script(['get', PATH_GET_ROUTE_TMPL, ''])
        self.assertNotIn(ip_pfx, "".join(output.replace('\n', '').split()))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIp('test_create_vlan'))
    suite.addTest(TestIp('test_add_ip4_to_vlan'))
    suite.addTest(TestIp('test_del_ip4_from_vlan'))
    suite.addTest(TestIp('test_destroy_vlan'))
    suite.addTest(TestIp('test_add_ip4_to_port'))
    suite.addTest(TestIp('test_add_static_route'))
    suite.addTest(TestIp('test_del_static_route'))
    suite.addTest(TestIp('test_del_ip4_from_port'))
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

