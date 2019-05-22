import unittest, pdb, argparse, test_inc, types, json

TEST_CLI_OPT = '-d'
TEST_CLI_CMD = '../ec_cfg.py'

class TestEcCfg(test_inc.MyTestCase):
    def chk_output(self, tbl, output, is_assert_in = True):
        if isinstance(tbl, dict):
            for key in tbl:
                self.chk_output(tbl[key], output, is_assert_in)
        else:
            chk_str = str(tbl)
            if is_assert_in:
                self.assertIn(chk_str, output)
            else:
                self.assertNotIn(chk_str, output)

    def _run_cmd(self, cmd, args):
        cmd_ar = [TEST_CLI_CMD, TEST_CLI_OPT, cmd] + args
        return self.run_shell_cmd([' '.join(cmd_ar)])

    def test_11_add_tunnel1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_VNID      = "33"

        args = ['tunnel add', TEST_TUNNEL_ID, TEST_VNID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_12_del_tunnel_dut1(self):
        TEST_TUNNEL_ID = "1"
        args = ['tunnel del', TEST_TUNNEL_ID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_13_add_nexthop1_dut1(self):
        TEST_NHID = "1"
        TEST_SA   = "00:00:00:00:00:aa"
        TEST_DA   = "00:00:00:00:00:bb"
        TEST_PORT = "2"
        TEST_VID  = "200"

        args = ['nexthop add', TEST_NHID, TEST_SA, TEST_DA, TEST_PORT, TEST_VID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_14_del_nexthop_dut1(self):
        TEST_NHID = "1"

        args = ['nexthop del', TEST_NHID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_15_add_avtep1_dut1(self):
        TEST_APID    = "1"
        TEST_PORT    = "1"
        TEST_VID     = "100"
        TEST_TAG_ING = "1"
        TEST_TAG_EGR = "0"

        args = ['vtep add avtep', TEST_APID, TEST_PORT, TEST_VID, TEST_TAG_ING, TEST_TAG_EGR]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_16_del_avtep1_dut1(self):
        TEST_APID = "1"

        args = ['vtep del', TEST_APID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_17_add_nvtep1_dut1(self):
        TEST_NPID = "2"
        TEST_RIP  = "2.2.2.2"
        TEST_LIP  = "1.1.1.1"
        TEST_NHID = "1"
        TEST_DPORT= "4789"
        TEST_TAG_EGR="0"

        args = ['vtep add nvtep', TEST_NPID, TEST_RIP, TEST_LIP, TEST_NHID, TEST_DPORT, TEST_TAG_EGR]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_18_del_nvtep1_dut1(self):
        TEST_NPID      = "2"

        args = ['vtep del', TEST_NPID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_19_attach_avtep1_to_tunnel1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_APID      = "1"

        args = ['tunnel portmbr add', TEST_TUNNEL_ID, TEST_APID]
        output = self._run_cmd("", args)

        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_20_detach_avtep1_to_tunnel1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_APID      = "1"

        args = ['tunnel portmbr del', TEST_TUNNEL_ID, TEST_APID]
        output = self._run_cmd("", args)

        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_21_attach_nvtep1_to_tunnel1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_NPID      = "2"

        args = ['tunnel portmbr add', TEST_TUNNEL_ID, TEST_NPID]
        output = self._run_cmd("", args)

        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_22_detach_nvtep1_to_tunnel1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_NPID      = "2"

        args = ['tunnel portmbr del', TEST_TUNNEL_ID, TEST_NPID]
        output = self._run_cmd("", args)

        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_23_add_grp1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_GID       = "1"
        TEST_SUBT      = "fuc"
        args = ['of group l2_ovr add', TEST_TUNNEL_ID, TEST_GID, TEST_SUBT]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_24_del_grp1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_GID       = "1"
        TEST_SUBT      = "fuc"
        args = ['of group l2_ovr del', TEST_TUNNEL_ID, TEST_GID, TEST_SUBT]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_25_add_dlf_tun1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_GID       = "1"
        args = ['of flow type3 add %s setGroupIdx %s' % (TEST_TUNNEL_ID, TEST_GID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_26_del_dlf_tun1_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_GID       = "1"
        args = ['of flow type3 del %s setGroupIdx %s' % (TEST_TUNNEL_ID, TEST_GID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_27_add_bkt_dut1(self):
        TEST_GID       = "1"
        TEST_ABID      = "1"
        TEST_APID      = "1"
        TEST_NBID      = "2"
        TEST_NPID      = "2"
        args = ['of bucket l2_ovr add', TEST_GID, TEST_ABID, TEST_APID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['of bucket l2_ovr add', TEST_GID, TEST_NBID, TEST_NPID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_28_del_bkt_dut1(self):
        TEST_GID       = "1"
        TEST_ABID      = "1"
        TEST_NBID      = "2"
        args = ['of bucket l2_ovr del', TEST_GID, TEST_ABID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['of bucket l2_ovr del', TEST_GID, TEST_NBID]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_29_add_rule_untag_mac_to_avtep_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_PORT      = "1"
        TEST_MAC       = "00:00:00:00:00:09"
        TEST_APID      = "1"
        args = ['of flow type2 add %s %s %s setIngVpid %s' % (TEST_TUNNEL_ID, TEST_PORT, TEST_MAC, TEST_APID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_30_del_rule_untag_mac_to_avtep_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_PORT      = "1"
        TEST_MAC       = "00:00:00:00:00:09"
        TEST_APID      = "1"
        args = ['of flow type2 del %s %s %s setIngVpid %s' % (TEST_TUNNEL_ID, TEST_PORT, TEST_MAC, TEST_APID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_31_add_untag_vlan1_port1_dut1(self):
        TEST_VID  = "1"
        TEST_PORT = "1"
        args = ['vlan add %s %s %s ' % (TEST_VID, TEST_PORT, 1)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['vlan add %s %s %s ' % (TEST_VID, TEST_PORT, 0)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_32_del_untag_vlan1_port1_dut1(self):
        TEST_VID  = "1"
        TEST_PORT = "1"
        args = ['vlan del %s %s %s ' % (TEST_VID, TEST_PORT, 1)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['vlan del %s %s %s ' % (TEST_VID, TEST_PORT, 0)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_33_add_rule_ingress_tun1_dut1(self):
        TEST_TID  = "1"
        args = ['of flow type4 add %s ' % (TEST_TID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_34_del_rule_ingress_tun1_dut1(self):
        TEST_TID  = "1"
        args = ['of flow type4 del %s ' % (TEST_TID)]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_35_add_mac_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_APID      = "1"
        TEST_NPID      = "2"
        TEST_LMAC      = "00:00:00:00:00:11"
        TEST_RMAC      = "00:00:00:00:00:99"
        args = ['-f tunnel mac add', TEST_TUNNEL_ID, TEST_APID, TEST_LMAC]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['-f tunnel mac add', TEST_TUNNEL_ID, TEST_NPID, TEST_RMAC]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

    def test_36_del_mac_dut1(self):
        TEST_TUNNEL_ID = "1"
        TEST_APID      = "1"
        TEST_NPID      = "2"
        TEST_LMAC      = "00:00:00:00:00:11"
        TEST_RMAC      = "00:00:00:00:00:99"
        args = ['-f tunnel mac del', TEST_TUNNEL_ID, TEST_APID, TEST_LMAC]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

        args = ['-f tunnel mac del', TEST_TUNNEL_ID, TEST_NPID, TEST_RMAC]
        output = self._run_cmd("", args)
        if self.chk_ret:
            self.assertIn("(NONE)", output)

def suite(t_case, t_cls):
    test_inc.gen_test_op_lst(t_cls)

    test_case = {}

    # basic add test dut1
    test_case[0] = [11,33,13,15,17,19,21,35,23,25,27,29,31]

    # basic del test dut2
    test_case[1] = [30,28,26,24,36,22,20,18,16,14,34,12,32]

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
    parser.add_argument('--dbg', action="store_true", help="print debug messages")
    parser.add_argument('--case', action="store", type=str, default=None,
                           help="ex: 1 (pre-defined test case) / \
                                     [1,2,3] (custom test case)")
    parser.add_argument('--chk', action="store_true", help="check result")
    args = parser.parse_args()

    TestCls = TestEcCfg
    TestCls.use_internal_svr = False
    TestCls.dbg_print = args.dbg
    TestCls.chk_ret   = args.chk

    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite(args.case, TestCls))

