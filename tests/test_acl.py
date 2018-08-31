import unittest
import pdb
import argparse
import test_inc

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'

PATH_SET_ACL_TMPL    = '/acl/acl-sets/acl-set[name={0}][type={1}]/config'
PATH_GET_ACL_TMPL    = '/acl/acl-sets/acl-set'

ACL_CFG_TMPL = '{{"name":"{0}","type":"{1}"}}'

class TestAcl(test_inc.MyTestCase):
    def test_create_acl(self):
        acl_name = 'AclTest1'
        acl_type = 'ACL_IPV4'
        acl_cfg = ACL_CFG_TMPL.format(acl_name, acl_type)
        output = self.run_script(['update', PATH_SET_ACL_TMPL.format(acl_name, acl_type), "'{0}'".format(acl_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_TMPL, ''])
        self.assertIn(acl_name, output)

    def test_destroy_acl(self):
        acl_name = 'AclTest1'
        acl_type = 'ACL_IPV4'
        acl_cfg = ACL_CFG_TMPL.format("", acl_type)
        output = self.run_script(['update', PATH_SET_ACL_TMPL.format(acl_name, acl_type), "'{0}'".format(acl_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_TMPL, ''])
        self.assertNotIn(acl_name, output)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestAcl('test_create_acl'))
    suite.addTest(TestAcl('test_destroy_acl'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestAcl.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestAcl.dbg_print        = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

