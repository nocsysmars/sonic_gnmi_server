import unittest, pdb, argparse, test_inc, types, json

PATH_SET_ACL_TMPL    = '/acl/acl-sets/acl-set[name={0}][type={1}]/config'
PATH_GET_ACL_TMPL    = '/acl/acl-sets/acl-set'

PATH_SET_RUL_TMPL    = '/acl/acl-sets/acl-set[name={0}][type={1}]/acl-entries/acl-entry'
PATH_GET_RUL_TMPL    = '/acl/acl-sets/acl-set[name={0}][type={1}]/acl-entries/acl-entry'

PATH_SET_ACL_BIND_TMPL = '/acl/interfaces/interface[id={0}]/ingress-acl-sets/ingress-acl-set[set-name={1}][type={2}]/config'
PATH_GET_ACL_BIND_TMPL = '/acl/interfaces'

ACL_CFG_TMPL      = '{{"name":"{0}","type":"{1}"}}'
ACL_BIND_CFG_TMPL = '{{"set-name":"{0}","type":"{1}"}}'

TEST_ACL_NAME = 'AclTest1'
TEST_ACL_TYPE = 'ACL_IPV4'
TEST_PORT     = 'Ethernet4'

TEST_RUL_FLD_TBL = {
    'IP_PROTOCOL' : {'str':'["ipv4"]["config"]["protocol"]',             'val': 17                     },
    'SRC_IP'      : {'str':'["ipv4"]["config"]["source-address"]',       'val': '"100.100.100.100/24"' },
    'DST_IP'      : {'str':'["ipv4"]["config"]["destination-address"]',  'val': '"100.100.100.200/24"' },
    'DSCP'        : {'str':'["ipv4"]["config"]["dscp"]',                 'val': 32                     },
    'ETHER_TYPE'  : {'str':'["l2"]["config"]["ethertype"]',              'val': 2048                   },
    'L4_SRC_PORT' : {'str':'["transport"]["config"]["source-port"]',     'val': 63                     },
    'L4_DST_PORT' : {'str':'["transport"]["config"]["destination-port"]','val': 64                     },
    'TCP_FLAGS'   : {'str':'["transport"]["config"]["tcp-flags"]',       'val': ['TCP_FIN','TCP_SYN']  }, # TODO: must in alphabet order
    'PACKET_ACTION':{'str':'["actions"]["config"]["forwarding-action"]', 'val': '"ACCEPT"'             },
    }

class TestAcl(test_inc.MyTestCase):
    def test_1_create_acl(self):
        acl_cfg = ACL_CFG_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE)
        output = self.run_script(['update', PATH_SET_ACL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(acl_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_TMPL, ''])
        self.assertIn(TEST_ACL_NAME, output)

    def test_2_destroy_acl(self):
        acl_cfg = ACL_CFG_TMPL.format("", TEST_ACL_TYPE)
        output = self.run_script(['update', PATH_SET_ACL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(acl_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_TMPL, ''])
        self.assertNotIn(TEST_ACL_NAME, output)

    def create_rule_cfg(self, seq_id, rule_name, rule_flds, is_del = False):
        rule_cfg = {
            seq_id : {
                "sequence-id": seq_id,
                "config": {
                    "sequence-id": seq_id,
                    "description": rule_name,
                    },
                }
            }

        if not is_del:
            rule_cfg [seq_id]['ipv4'     ] = {"config" : {} }
            rule_cfg [seq_id]['l2'       ] = {"config" : {} }
            rule_cfg [seq_id]['transport'] = {"config" : {} }
            rule_cfg [seq_id]['actions'  ] = {"config" : {} }

            exec_str_tmpl = "rule_cfg['{0}']{1} = {2}"
            for fld in rule_flds:
                exec_str = exec_str_tmpl.format(seq_id, TEST_RUL_FLD_TBL[fld]['str'], TEST_RUL_FLD_TBL[fld]['val'])
                exec(exec_str)

        ret_val = json.dumps(rule_cfg)

        return ret_val

    def chk_rule_output(self, seq_id, input_dict, output, chk_tbl, is_assert_in):
        for chk_key in chk_tbl:
            tmp_cfg = input_dict[seq_id][chk_key]

            for fld in tmp_cfg['config'].keys():
                tmp_val = input_dict[seq_id][chk_key]['config'][fld]
                tmp_str = json.dumps(tmp_val,  separators=(',', ':'))
                chk_str = '"%s":%s' % (fld, tmp_str)
                if is_assert_in:
                    self.assertIn(chk_str, output)
                else:
                    self.assertNotIn(chk_str, output)

    def test_3_mod_rule(self):
        TEST_SEQ_ID   = "2"
        TEST_RUL_NAME = "RULE_2"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, TEST_RUL_NAME, ['SRC_IP'])
        output = self.run_script(['update', PATH_SET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), ''])
        output = "".join(output.replace('\n', '').split())
        input_dict = eval(rule_cfg)

        self.chk_rule_output(TEST_SEQ_ID, input_dict, output, ["ipv4"], True)

        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, TEST_RUL_NAME, ['DST_IP'])
        output = self.run_script(['update', PATH_SET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), ''])
        output = "".join(output.replace('\n', '').split())

        self.chk_rule_output(TEST_SEQ_ID, input_dict, output, ["ipv4"], False)

        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, TEST_RUL_NAME, None, True)
        output = self.run_script(['update', PATH_SET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), ''])
        output = "".join(output.replace('\n', '').split())
        self.assertNotIn(TEST_SEQ_ID, output)

    def test_4_add_rule_to_acl(self):
        #pdb.set_trace()
        TEST_SEQ_ID   = "1"
        TEST_RUL_NAME = "RULE_1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, TEST_RUL_NAME, TEST_RUL_FLD_TBL.keys())

        output = self.run_script(['update', PATH_SET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), ''])
        output = "".join(output.replace('\n', '').split())
        input_dict = eval(rule_cfg)
        chk_tbl = [ "ipv4", "l2", "transport", "actions" ]
        self.chk_rule_output(TEST_SEQ_ID, input_dict, output, chk_tbl, True)

    def test_5_del_rule_from_acl(self):
        #pdb.set_trace()
        TEST_SEQ_ID   = "1"
        TEST_RUL_NAME = "RULE_1"
        rule_cfg = self.create_rule_cfg(TEST_SEQ_ID, TEST_RUL_NAME, None, True)

        output = self.run_script(['update', PATH_SET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(rule_cfg)])
        output = self.run_script(['get', PATH_GET_RUL_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE), ''])
        output = "".join(output.replace('\n', '').split())
        self.assertNotIn(TEST_SEQ_ID, output)

    def test_6_bind_acl_to_port(self):
        acl_bind_cfg = ACL_BIND_CFG_TMPL.format(TEST_ACL_NAME, TEST_ACL_TYPE)
        output = self.run_script(['update', PATH_SET_ACL_BIND_TMPL.format(TEST_PORT, TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(acl_bind_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_BIND_TMPL, ''])
        self.assertIn(TEST_PORT, output)

    def test_7_unbind_acl_from_port(self):
        acl_bind_cfg = ""
        output = self.run_script(['update', PATH_SET_ACL_BIND_TMPL.format(TEST_PORT, TEST_ACL_NAME, TEST_ACL_TYPE), "'{0}'".format(acl_bind_cfg)])
        output = self.run_script(['get', PATH_GET_ACL_BIND_TMPL, ''])
        self.assertNotIn(TEST_PORT, output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,3,4,6,7,5,2]

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

    TestCls = TestAcl
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

