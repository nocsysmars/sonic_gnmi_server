import unittest, pdb, argparse, test_inc, types, json

PATH_GET_ALL_INF_NAME  = '/interfaces/interface/config/name'
PATH_INF_CFG_NAME_TMPL = '/interfaces/interface[name={0}]/config/name'
PATH_INF_AGG_ID_TMPL   = '/interfaces/interface[name={0}]/ethernet/config/aggregate-id'
PATH_INF_CFG_EN_TMPL   = '/interfaces/interface[name={0}]/config/enabled'
PATH_GET_INF_TMPL      = '/interfaces/interface[name={0}]'
#TEAMDCTL_CFG_CMD_TMPL  = 'teamdctl {0} config dump actual'

PATH_INF_TAG_VLAN_TMPL = '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/trunk-vlans'
PATH_INF_UTAG_VLAN_TMPL= '/interfaces/interface[name={0}]/ethernet/switched-vlan/config/native-vlan'

PATH_SET_IP_TMPL       = '/interfaces/interface[name={0}]/routed-vlan/ipv4/addresses/address[ip={1}]/config'

class TestPortChannel(test_inc.MyTestCase):
    def test_1_create_pc2(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '"{0}"'.format(pc_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
            self.assertIn(pc_name, output)

    def test_2_destroy_pc2(self):
        pc_name = 'PortChannel2'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '""'])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
            self.assertNotIn(pc_name, output)

    def test_3_add_port4_to_pc2(self):
        inf_name = 'Ethernet4'
        pc_name  = 'PortChannel2'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '"{0}"'.format(pc_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            chk_str = '"aggregate-id":"{0}"'.format(pc_name)
            self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_4_set_pc2_admin_status_reverse(self):
        pc_name  = 'PortChannel2'

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
        chk_str = '"admin-status":"UP"'

        is_admin_up = True if chk_str in "".join(output.replace('\n', '').split()) else False

        output = self.run_script(['update',
                                  PATH_INF_CFG_EN_TMPL.format(pc_name),
                                  '"{0}"'.format(["true", "false"][is_admin_up])])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
            chk_str = '"admin-status":"{0}"'.format(["UP", "DOWN"][is_admin_up])
            self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_5_remove_port4_from_pc2(self):
        inf_name = 'Ethernet4'
        pc_name  = 'PortChannel2'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '""'])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            chk_str = '"aggregate-id":"{0}"'.format(pc_name)
            self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_6_create_pc1(self):
        pc_name = 'PortChannel1'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(pc_name), '"{0}"'.format(pc_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
            self.assertIn(pc_name, output)

    def test_7_add_port3_to_pc1(self):
        inf_name = 'Ethernet3'
        pc_name  = 'PortChannel1'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '"{0}"'.format(pc_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            chk_str = '"aggregate-id":"{0}"'.format(pc_name)
            self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_8_create_vlan100(self):
        vlan_name = 'Vlan100'
        output = self.run_script(['update', PATH_INF_CFG_NAME_TMPL.format(vlan_name), '"{0}"'.format(vlan_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
            self.assertIn(vlan_name, output)

    def test_9_add_ip4_to_vlan100(self):
        inf_name = 'Vlan100'
        ip       = "100.100.100.1"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip, pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_10_del_ip4_from_vlan100(self):
        inf_name = 'Vlan100'
        ip       = "100.100.100.1"
        pfx      = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)

        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_name, ip),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            self.assertNotIn(ip, "".join(output.replace('\n', '').split()))

    def test_11_add_pc1_to_tag_vlan100(self):
        inf_name = 'PortChannel1'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[100]"'])
#        output = self.run_script(['get', PATH_GET_ALL_INF_NAME, ''])
#        self.assertIn('Vlan100', output)
#        self.assertIn('Vlan2002', output)

#        chk_str = '"trunk-vlans":[100]'
#        output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
#        self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_12_remove_pc1_from_tag_vlan100(self):
        inf_name = 'PortChannel1'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[]"'])

        if self.chk_ret:
            chk_str = '"trunk-vlans"'
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_13_add_port5_to_tag_vlan100(self):
        inf_name = 'Ethernet5'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[100]"'])

    def test_14_remove_port5_from_tag_vlan100(self):
        inf_name = 'Ethernet5'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[]"'])

        if self.chk_ret:
            chk_str = '"trunk-vlans"'
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_15_add_port6_to_tag_vlan100(self):
        inf_name = 'Ethernet6'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[100]"'])

    def test_16_remove_port6_from_tag_vlan100(self):
        inf_name = 'Ethernet6'
        output = self.run_script(['update',
                                  PATH_INF_TAG_VLAN_TMPL.format(inf_name),
                                  '"[]"'])

        if self.chk_ret:
            chk_str = '"trunk-vlans"'
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            self.assertNotIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_17_set_port4_admin_status_reverse(self):
        pc_name  = 'Ethernet4'

        output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
        chk_str = '"admin-status":"UP"'

        is_admin_up = True if chk_str in "".join(output.replace('\n', '').split()) else False

        output = self.run_script(['update',
                                  PATH_INF_CFG_EN_TMPL.format(pc_name),
                                  '"{0}"'.format(["true", "false"][is_admin_up])])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(pc_name), ''])
            chk_str = '"admin-status":"{0}"'.format(["UP", "DOWN"][is_admin_up])
            self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

    def test_18_add_ip4_to_pc2(self):
        inf_1 = 'PortChannel2'
        ip1   = "100.100.100.137"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip1, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
            self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_19_add_ip4_to_port4(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.137"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format(ip1, pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
            self.assertIn(cfg_str, "".join(output.replace('\n', '').split()))

    def test_20_del_ip4_from_pc2(self):
        inf_1 = 'PortChannel2'
        ip1   = "100.100.100.137"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
            self.assertNotIn(ip1, "".join(output.replace('\n', '').split()))

    def test_21_del_ip4_from_port4(self):
        inf_1 = 'Ethernet4'
        ip1   = "100.100.100.137"
        pfx   = "24"
        cfg_str  = '{{"ip":"{0}","prefix-length":{1}}}'.format("", pfx)
        output = self.run_script(['update',
                                  PATH_SET_IP_TMPL.format(inf_1, ip1),
                                  "'{0}'".format(cfg_str)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_1), ''])
            self.assertNotIn(ip1, "".join(output.replace('\n', '').split()))

    def test_22_add_port8_to_pc2(self):
        inf_name = 'Ethernet8'
        pc_name  = 'PortChannel2'
        output = self.run_script(['update',
                                  PATH_INF_AGG_ID_TMPL.format(inf_name),
                                  '"{0}"'.format(pc_name)])

        if self.chk_ret:
            output = self.run_script(['get', PATH_GET_INF_TMPL.format(inf_name), ''])
            chk_str = '"aggregate-id":"{0}"'.format(pc_name)
            self.assertIn(chk_str, "".join(output.replace('\n', '').split()))

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic test
    test_case[0] = [1,3,4,5,2]

    test_case[1] = [8,9,15,16,14,15,16]

    # syncd exit unexpectedly case when adding/removing vlan member
    test_case[2] = [8,15,9,16,14]

    test_case[3] = [8,15,9,14,16]

    # set pc admin status than set pc mbr port admin status test
    test_case[4] = [1,3,4,17]

    if t_case:
        t_sel = eval (t_case)
    else:
        t_sel = 0

    if type(t_sel) == types.ListType:
        print 'Running Custom Test Case, %s' % (t_sel)
        test_flst = map(lambda x: test_inc.TEST_OP_LST[x], t_sel)
    elif t_sel in test_case:
        test_flst = map(lambda x: test_inc.TEST_OP_LST[x], test_case[t_sel])
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

    TestCls = TestPortChannel
    if args.target:
        TestCls.use_internal_svr = False
        test_inc.TEST_URL = args.target

    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

