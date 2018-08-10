
# url of gnmi server to test
TEST_URL               = 'localhost:5001'

# {0}   : URL to test
# {{0}} : get/update
# {{1}} : path (ex: "/interfaces/interface/config/name")
# {{2}} : new value for update
GNMI_URL_CMD_TMPL      = '/home/admin/gocode/bin/gnmi -addr {0} {{0}} {{1}} {{2}}'

