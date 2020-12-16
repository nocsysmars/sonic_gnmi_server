import unittest, pdb, argparse, test_inc, types, json, sys

sys.path.append("../nocsys_sonic_gnmi_server/util/")

from util_acl import MIRROR_POLICY_PFX as TEST_MIRROR_PFX
from util_acl import PROUTE_POLICY_PFX as TEST_POL_RT_PFX
from util_nwi import DEFAULT_NWI_NAME as TEST_DFT_NWI_NAME

PATH_SET_POL_TMPL    = '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/config'
PATH_GET_POL_TMPL    = '/network-instances/network-instance[name={0}]/policy-forwarding/policies'

PATH_SET_POL_RUL_TMPL= '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/rules/rule'
PATH_GET_POL_RUL_TMPL= '/network-instances/network-instance[name={0}]/policy-forwarding/policies/policy[policy-id={1}]/rules/rule'

PATH_SET_POL_BIND_TMPL = '/network-instances/network-instance[name={0}]/policy-forwarding/interfaces/interface[interface-id={1}]/config'
PATH_GET_POL_BIND_TMPL = '/network-instances/network-instance[name={0}]/policy-forwarding/interfaces'

CFG_POLICY_TMPL      = '{{"policy-id" : "{0}"}}'
CFG_POLICY_BIND_TMPL = '{{"apply-forwarding-policy":"{0}"}}'

TEST_POL_NAME_MIR= "{0}_3".format(TEST_MIRROR_PFX)
TEST_POL_NAME_PRT= "{0}_3".format(TEST_POL_RT_PFX)
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

TEST_ACT_CFG_POL_RT = {
    "config": {
      "next-hop": "1.1.1.1"
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

    def create_policy(self, pol_name, is_add):
        if is_add:
            pol_cfg = CFG_POLICY_TMPL.format(pol_name)
            output = self.run_script(['update', PATH_SET_POL_TMPL.format(TEST_DFT_NWI_NAME, pol_name), "'{0}'".format(pol_cfg)])
            output = self.run_script(['get', PATH_GET_POL_TMPL.format(TEST_DFT_NWI_NAME), ''])
            self.assertIn(pol_name, output)
        else:
            pol_cfg = CFG_POLICY_TMPL.format("")
            output = self.run_script(['update', PATH_SET_POL_TMPL.format(TEST_DFT_NWI_NAME, pol_name), "'{0}'".format(pol_cfg)])
            output = self.run_script(['get', PATH_GET_POL_TMPL.format(TEST_DFT_NWI_NAME), ''])
            self.assertNotIn(pol_name, output)

    def test_1_create_policy_mirror(self):
        TEST_POL_NAME = TEST_POL_NAME_MIR
        self.create_policy(TEST_POL_NAME, True)

    def test_2_destroy_policy_mirror(self):
        TEST_POL_NAME = TEST_POL_NAME_MIR
        self.create_policy(TEST_POL_NAME, False)

    def create_rule_cfg(self, seq_id, is_del = False, is_mirror = True):
        rule_cfg = {
            seq_id : {
                "sequence-id": seq_id,
                "config": {
                    "sequence-id": seq_id,
                    # add rule with desc field (name),
                    # need to carry the desc field when del rule
                    #"description":"POLRT_policy1_tcp"
                    },
                }
            }

        if not is_del:
            rule_cfg [seq_id]['ipv4'     ] = {'config':{}}
            rule_cfg [seq_id]['l2'       ] = {'config':{}}
            rule_cfg [seq_id]['transport'] = {'config':{}}

            if is_mirror:
                rule_cfg [seq_id]['action'   ] = TEST_ACT_CFG
            else:
                rule_cfg [seq_id]['action'   ] = TEST_ACT_CFG_POL_RT

            exec_str_tmpl = "rule_cfg['{0}']{1} = {2}"
            for fld in TEST_RUL_FLD_TBL.keys():
                exec_str = exec_str_tmpl.format(seq_id, TEST_RUL_FLD_TBL[fld]['str'], TEST_RUL_FLD_TBL[fld]['val'])
                exec(exec_str)

        ret_val = json.dumps(rule_cfg)

        return ret_val

    def test_3_add_rule_to_policy_mirror(self):
        TEST_POL_NAME = TEST_POL_NAME_MIR
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID)

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

    def test_4_del_rule_from_policy_mirror(self):
        TEST_POL_NAME = TEST_POL_NAME_MIR
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, True)

        output = self.run_script(['update', PATH_SET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), ''])
        output = "".join(output.replace('\n', '').split())
        self.assertNotIn(TEST_SEQ_ID, output)

    def set_policy_to_port(self, pol_name, inf_name, is_add):
        if is_add:
            pol_bind_cfg = CFG_POLICY_BIND_TMPL.format(pol_name)
            output = self.run_script(['update', PATH_SET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME, inf_name), "'{0}'".format(pol_bind_cfg)])
            output = self.run_script(['get', PATH_GET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME), ''])
            #self.assertIn(pol_name, output)
            #use inf_name to check for binding muliple policy to one inf
            self.assertIn(inf_name, output)
        else:
            pol_bind_cfg = ""
            output = self.run_script(['update', PATH_SET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME, inf_name), "'{0}'".format(pol_bind_cfg)])
            output = self.run_script(['get', PATH_GET_POL_BIND_TMPL.format(TEST_DFT_NWI_NAME), ''])
            self.assertNotIn(inf_name, output)

    def test_5_bind_policy_to_port_mirror(self):
        self.set_policy_to_port(TEST_POL_NAME_MIR, TEST_PORT, True)

    def test_6_unbind_policy_from_port_mirror(self):
        self.set_policy_to_port(TEST_POL_NAME_MIR, TEST_PORT, False)

    def test_7_create_policy_prt(self):
        TEST_POL_NAME = TEST_POL_NAME_PRT
        self.create_policy(TEST_POL_NAME, True)

    def test_8_destroy_policy_prt(self):
        TEST_POL_NAME = TEST_POL_NAME_PRT
        self.create_policy(TEST_POL_NAME, False)

    def test_9_add_rule_to_policy_prt(self):
        TEST_POL_NAME = TEST_POL_NAME_PRT
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, False, False)

        output = self.run_script(['update', PATH_SET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), ''])
        output = "".join(output.replace('\n', '').split())
        input_dict = eval(rule_cfg)
        chk_tbl = [ "ipv4", "l2", "transport", "action" ]

        for chk_key in chk_tbl:
            tmp_cfg = input_dict[TEST_SEQ_ID][chk_key]
            if chk_key == "action":
                self.assertIn("".join(json.dumps(TEST_ACT_CFG_POL_RT).replace('\n','').split()), output)
            else:
                for fld in tmp_cfg['config'].keys():
                    tmp_val = input_dict[TEST_SEQ_ID][chk_key]['config'][fld]
                    tmp_str = json.dumps(tmp_val,  separators=(',', ':'))
                    chk_str = '"%s":%s' % (fld, tmp_str)
                    self.assertIn(chk_str, output)

    def test_10_del_rule_from_policy_prt(self):
        TEST_POL_NAME = TEST_POL_NAME_PRT
        TEST_SEQ_ID   = "1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, True, False)

        output = self.run_script(['update', PATH_SET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_POL_RUL_TMPL.format(TEST_DFT_NWI_NAME, TEST_POL_NAME), ''])
        output = "".join(output.replace('\n', '').split())
        self.assertNotIn(TEST_SEQ_ID, output)

    def test_11_bind_policy_to_port_prt(self):
        self.set_policy_to_port(TEST_POL_NAME_PRT, TEST_PORT, True)

    def test_21_bind_policy_to_port2_prt(self):
        self.set_policy_to_port(TEST_POL_NAME_PRT, 'Ethernet2', True)

    def test_12_unbind_policy_from_port_prt(self):
        self.set_policy_to_port(TEST_POL_NAME_PRT, TEST_PORT, False)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test for mirror
    test_case[0] = [1,3,5,6,4,2]

    # basic test for policy route
    test_case[1] = [7,9,11,12,10,8]

    # test for binding two policies to one port
    test_case[2] = [1,7,5,11,21] #2,8]

    if t_case:
        t_sel = eval (t_case)
    else:
        t_sel = 0

    if type(t_sel) == types.ListType:
        print 'Running Custom Test Case, %s' % (t_sel)
        test_flst = map  (lambda x: test_inc.TEST_OP_LST[x], t_sel)
    elif t_sel in test_case:
        test_flst = map (lambda x: test_inc.TEST_OP_LST[x], test_case[t_sel])
        print 'Running Test Case %d, %s' % (t_sel, test_case[t_sel])
    else:
        test_flst = ['test_case_not_found']
        t_cls.t_case = test_case
        t_cls.t_sel  = t_sel

    return unittest.TestSuite(map(t_cls, test_flst))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', help="target url, typically localhost:<port>")
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    parser.add_argument('--case', action="store", type=str, default=None,
                           help="ex: 1 (pre-defined test case) / \
                                     [1,2,3] (custom test case)")
    parser.add_argument('--chk', action="store_true", help="check result")
    args = parser.parse_args()

    TestCls = TestPf
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

