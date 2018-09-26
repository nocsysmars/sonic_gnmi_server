import unittest
import pdb
import argparse
import test_inc
import json


PATH_SET_POL_TMPL    = '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/config'
PATH_GET_POL_TMPL    = '/network-instances/network-instance[name={0}]/policy-forwarding/policies'

PATH_SET_POL_RUL_TMPL= '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/rules/rule'
PATH_GET_POL_RUL_TMPL= '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/rules/rule'

PATH_SET_POL_BIND_TMPL = '/network-instances/network-instance[name={0}]/policy-forwarding/interfaces/interface[interface-id={1}]/config'
PATH_GET_POL_BIND_TMPL = '/network-instances/network-instance[name={0}]/policy-forwarding/interfaces'

CFG_POLICY_TMPL      = '{{"policy-id" : "{0}"}}'
CFG_POLICY_BIND_TMPL = '{{"apply-forwarding-policy":"{0}"}}'

TEST_DFT_NWI_NAME= 'DEFAULT'
TEST_MIRROR_PFX  = 'EVERFLOW'

TEST_POL_NAME    = "{0}_3".format(TEST_MIRROR_PFX)
TEST_PORT        = 'Ethernet4'
TEST_SESSION_NAME= 'session3'
TEST_ACT_CFG = {
    "encapsulate-gre": {
      "targets": {
        "target": {
          TEST_SESSION_NAME: {
            "config": {
                "source": "1.1.1.1",
                "destination": "2.2.2.2",
                "id": TEST_SESSION_NAME,
                "ip-ttl": 20
              },
            "id": TEST_SESSION_NAME
            }
          }
        }
      }
    }

TEST_RUL_FLD_TBL = {
    'IP_PROTOCOL' : {'str':'["ipv4"]["config"]["protocol"]',             'val': 17                     },
    'SRC_IP'      : {'str':'["ipv4"]["config"]["source-address"]',       'val': '"100.100.100.100/24"' },
    'DST_IP'      : {'str':'["ipv4"]["config"]["destination-address"]',  'val': '"100.100.100.200/24"' },
    'DSCP'        : {'str':'["ipv4"]["config"]["dscp"]',                 'val': 32                     },
    'ETHER_TYPE'  : {'str':'["l2"]["config"]["ethertype"]',              'val': 2048                   },
    'L4_SRC_PORT' : {'str':'["transport"]["config"]["source-port"]',     'val': 63                     },
    'L4_DST_PORT' : {'str':'["transport"]["config"]["destination-port"]','val': 64                     },
    'TCP_FLAGS'   : {'str':'["transport"]["config"]["tcp-flags"]',       'val': ['TCP_FIN','TCP_SYN']  }, # TODO: must in alphabet order
    #'MIRROR_ACTION':{'str':'["action"]',                                 'val': 'not used'             },
    }

class TestPf(test_inc.MyTestCase):
    def test_create_policy_mirror(self):
        pol_cfg = CFG_POLICY_TMPL.format(TEST_POL_NAME)
        output = self.run_script(['update', PATH_SET_POL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(pol_cfg)])
        output = self.run_script(['get', PATH_GET_POL_TMPL.format(TEST_DFT_NWI_NAME), ''])
        self.assertIn(TEST_POL_NAME, output)

    def test_destroy_policy_mirror(self):
        pol_cfg = CFG_POLICY_TMPL.format("")
        output = self.run_script(['update', PATH_SET_POL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(pol_cfg)])
        output = self.run_script(['get', PATH_GET_POL_TMPL.format(TEST_DFT_NWI_NAME), ''])
        self.assertNotIn(TEST_POL_NAME, output)

    def create_rule_cfg_mirror(self, seq_id, is_del = False):
        rule_cfg = {
            seq_id : {
                "sequence-id": seq_id,
                "config": {
                    "sequence-id": seq_id,
                    },
                }
            }

        if not is_del:
            rule_cfg [seq_id]['ipv4'     ] = {'config':{}}
            rule_cfg [seq_id]['l2'       ] = {'config':{}}
            rule_cfg [seq_id]['transport'] = {'config':{}}
            rule_cfg [seq_id]['action'   ] = TEST_ACT_CFG

            exec_str_tmpl = "rule_cfg['{0}']{1} = {2}"
            for fld in TEST_RUL_FLD_TBL.keys():
                exec_str = exec_str_tmpl.format(seq_id, TEST_RUL_FLD_TBL[fld]['str'], TEST_RUL_FLD_TBL[fld]['val'])
                exec(exec_str)

        ret_val = json.dumps(rule_cfg)

        return ret_val

    def test_add_rule_to_policy_mirror(self):
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg_mirror(TEST_SEQ_ID)

        output = self.run_script(['update', PATH_SET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), ''])
        output = "".join(output.replace('\n', '').split())
        input_dict = eval(rule_cfg)
        chk_tbl = [ "ipv4", "l2", "transport", "action" ]

        for chk_key in chk_tbl:
            tmp_cfg = input_dict[TEST_SEQ_ID][chk_key]
            if chk_key == "action":
                self.assertIn(TEST_SESSION_NAME, output)
            else:
                for fld in tmp_cfg['config'].keys():
                    tmp_val = input_dict[TEST_SEQ_ID][chk_key]['config'][fld]
                    tmp_str = json.dumps(tmp_val,  separators=(',', ':'))
                    chk_str = '"%s":%s' % (fld, tmp_str)
                    self.assertIn(chk_str, output)

    def test_del_rule_from_policy_mirror(self):
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg_mirror(TEST_SEQ_ID, True)

        output = self.run_script(['update', PATH_SET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), ''])
        output = "".join(output.replace('\n', '').split())
        self.assertNotIn(TEST_SEQ_ID, output)

    def test_bind_policy_to_port_mirror(self):
        pol_bind_cfg = CFG_POLICY_BIND_TMPL.format(TEST_POL_NAME)
        output = self.run_script(['update', PATH_SET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME, TEST_PORT), "'{0}'".format(pol_bind_cfg)])
        output = self.run_script(['get', PATH_GET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME), ''])
        self.assertIn(TEST_PORT, output)

    def test_unbind_policy_from_port_mirror(self):
        pol_bind_cfg = ""
        output = self.run_script(['update', PATH_SET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME, TEST_PORT), "'{0}'".format(pol_bind_cfg)])
        output = self.run_script(['get', PATH_GET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME), ''])
        self.assertNotIn(TEST_PORT, output)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestPf('test_create_policy_mirror'))
    suite.addTest(TestPf('test_add_rule_to_policy_mirror'))
    suite.addTest(TestPf('test_bind_policy_to_port_mirror'))
    suite.addTest(TestPf('test_unbind_policy_from_port_mirror'))
    suite.addTest(TestPf('test_del_rule_from_policy_mirror'))
    suite.addTest(TestPf('test_destroy_policy_mirror'))
    return suite

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    args = parser.parse_args()

    if args.target:
        TestPf.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestPf.dbg_print = args.dbg

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite())

