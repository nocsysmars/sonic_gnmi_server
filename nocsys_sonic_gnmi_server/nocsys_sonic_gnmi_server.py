#!/usr/bin/env python

#
# nocsys_sonic_gnmi_server.py
#
# GNMI Server
#

import argparse, time, json, Queue, threading
import logging, logging.handlers, re, pdb

from concurrent import futures
import grpc
from gnmi import gnmi_pb2
from gnmi import gnmi_pb2_grpc
import pyangbind.lib.pybindJSON as pybindJSON

from util import util_utl
from oc_dispatcher import ocDispatcher


#          input : PathElem
# example of ret : [ 'interfaces', 'interface' ]
#
# TODO: check if input path is invalid, e.g. [ip=]
def EncodePath(path):
    pathStrs = []
    for pe in path:
        pstr = pe.name
        if pe.key:
             for k, v in sorted(pe.key.iteritems()):
                pstr += "[" + str(k) + "=" + str(v) + "]"
        pathStrs += [pstr]
    return pathStrs

#          input : PathElem
# example of ret : [ 'eth0', 'kkk' ]
def EncodePathKey(path):
    key_strs = []
    key_tags = []
    for pe in path:
        if pe.key:
             for k, v in sorted(pe.key.iteritems()):
                  key_strs += [v]
                  key_tags += [k]
    return key_strs + key_tags

# example of input : [ 'interfaces', 'interface' ]
# example of ret   : "/interfaces/interface"
def EncodeYangPath(path_ar):
    ypath = ""
    for p in path_ar:
        ypath += "/" + p

    return ypath

def ExtractJson(oc_obj, leaf_str):
    # sometimes leaf can not be dumped,
    # so dump the parent for safe
    # set filter True to filter attributes which are not configured
    if hasattr(oc_obj, 'get'):
        tmp_json = json.loads(pybindJSON.dumps(oc_obj, filter = True))
    else:
        tmp_json = json.loads(pybindJSON.dumps(oc_obj._parent, filter = True))

        leaf_name = oc_obj.yang_name()

        if leaf_name in tmp_json:
            tmp_json = tmp_json[leaf_name]
        else:
            tmp_json = None

    if leaf_str and leaf_str in tmp_json:
        tmp_json = tmp_json[leaf_str]

    return tmp_json

#
# class gNMITargetServicer
#
class gNMITargetServicer(gnmi_pb2_grpc.gNMIServicer):
    def __init__(self, isDbgTest):
        self.myDispatcher = ocDispatcher(isDbgTest)
        self.Timer_Q = []
        self.is_stopped = False
        self.lock = threading.Lock()

    def __getCapabilitiesResponseObj(self):
        capResp = gnmi_pb2.CapabilityResponse()
        supModel = gnmi_pb2.ModelData(name="accton_model", organization="Accton", version="1.0")
        capResp.supported_models.extend([supModel])
        capResp.supported_encodings.extend(gnmi_pb2.JSON)
        capResp.gNMI_version = "GNMI Version 0.6"
        return capResp

    # refer to gnmi.proto
    #  get: prefix, path, type, encoding, use_models, extension
    #  set: prefix, delete, replace, update, extension
    #  cap: extension
    #  sub: subscribe, ...
    def __processGetRequestObj(self, reqGetObj):
        pfx_ar = EncodePath(reqGetObj.prefix.elem)
        t = reqGetObj.type

        #FIXME: Build the get response for all the paths
        getResp = gnmi_pb2.GetResponse()
        for path in reqGetObj.path:
            er_code = grpc.StatusCode.INVALID_ARGUMENT
            path_ar = pfx_ar + EncodePath(path.elem)
            pkey_ar = EncodePathKey(path.elem)
            yp_str  = EncodeYangPath(path_ar)

            util_utl.utl_log("get req path :" + yp_str)

            tmp_json = None
            self.lock.acquire()
            try:
                oc_yph = self.myDispatcher.GetRequestYph(path_ar, pkey_ar)
                if isinstance(oc_yph, grpc.StatusCode):
                    er_code = oc_yph
                else:
                    if path_ar[0] == "components":
                        tmp_obj = oc_yph.get("/components") if oc_yph else []
                    else:
                        tmp_obj = oc_yph.get(yp_str) if oc_yph else []

                    # TODO: if got more than one obj ?
                    if len(tmp_obj) >= 1:
                        tmp_json = {}
                        for idx in range(len(tmp_obj)):
                            obj_json = ExtractJson(tmp_obj[idx], None)
                            if obj_json:
                                # remove "'" for the key in the _yang_path
                                obj_path = re.sub(r'\[([\w-]*)=\'([^]]*)\'\]', r'[\1=\2]', tmp_obj[idx]._yang_path())
                                if len(tmp_obj) == 1 and obj_path == yp_str:
                                    tmp_json = obj_json
                                else:
                                    tmp_json[obj_path]= obj_json
            except:
                er_code = grpc.StatusCode.INTERNAL
                tmp_json= None
            finally:
                self.lock.release()

            if tmp_json != None:
                notif = getResp.notification.add()
                notif.timestamp = int(time.time())
                notif.prefix.CopyFrom(reqGetObj.prefix)
                update = notif.update.add()
                update.path.CopyFrom(reqGetObj.path[0])

                util_utl.utl_log("get req json :" + json.dumps(tmp_json))

                update.val.json_val = json.dumps(tmp_json)
                er_code = grpc.StatusCode.OK

            util_utl.utl_log("get req code :" + str(er_code))

            if er_code != grpc.StatusCode.OK:
                getResp.error.code    = er_code.value[0]
                getResp.error.message = er_code.value[1]
                break

        return getResp

    # ErCode : grpc.StatusCode.XXX
    def __AddOneSetResp(self, SetRespObj, Path, Op, ErCode, ErMsg):
        OneUpdRes = SetRespObj.response.add()
        OneUpdRes.path.CopyFrom(Path)
        OneUpdRes.op   = Op
        OneUpdRes.message.code = ErCode.value[0]
        OneUpdRes.message.message = ErMsg if ErMsg != None else ErCode.value[1]

    def __processSetRequestObj(self, reqSetObj):
        IsAnyErr = False
        pathPrefix = EncodePath(reqSetObj.prefix.elem)

        util_utl.utl_log(reqSetObj)

        # Now Build the set response
        #
        #   one error => error code
        #   all other => aborted (10)
        #   over all  => aborted (10)
        setResp = gnmi_pb2.SetResponse()
        setResp.timestamp = int(time.time())

        #pdb.set_trace()

        # process order is delete, replace, update
        # refer to gnmi-specification.md

        # input: path (delete)
        for delete in reqSetObj.delete:
            delPath = pathPrefix + EncodePath(delete.elem)

            pkey_ar = EncodePathKey(delete.elem)
            yp_str = EncodeYangPath(delPath)

            util_utl.utl_log("delete req path: " + yp_str)

            self.lock.acquire()
            ret_status = self.myDispatcher.DeleteRequestByPath(yp_str, pkey_ar)
            self.lock.release()

            if ret_status:
                ret_status = grpc.StatusCode.OK
            else:
                IsAnyErr = True
                ret_status = grpc.StatusCode.INVALID_ARGUMENT

            self.__AddOneSetResp(setResp, delete, 1, ret_status, None)

            util_utl.utl_log("delete request finished code: " + str(ret_status))

        # input: path, val
        #  When the `replace` operation omits values that have been previously set,
        #  they MUST be treated as deleted from the data tree.
        #  Otherwise, omitted data elements MUST be created with their
        #  default values on the target.
        for replace in reqSetObj.replace:
            repPath = pathPrefix + EncodePath(replace.path.elem)

            # k = replace.val.WhichOneof("value")
            # util_utl.utl_log(k)
            # val = getattr(replace.val, k)
            # util_utl.utl_log(val)
            # util_utl.utl_log(repPath)

            pkey_ar = EncodePathKey(replace.path.elem)
            set_val = getattr(replace.val, replace.val.WhichOneof("value"))
            yp_str = EncodeYangPath(repPath)

            self.lock.acquire()
            status = self.myDispatcher.ReplaceRequestByPath(yp_str, pkey_ar, set_val)
            self.lock.release()

            if status:
                status = grpc.StatusCode.OK
            else:
                IsAnyErr = True
                status = grpc.StatusCode.INVALID_ARGUMENT

            self.__AddOneSetResp(setResp, replace.path, 2, status, None)

            util_utl.utl_log("request-" + "/".join(repPath) + "set code: " + str(status))

        # input: same as replace
        for update in reqSetObj.update:
            updPath = pathPrefix + EncodePath(update.path.elem)

            # 1. check if path is valid
            # 2. issue command to do configuration
            #
            # only support '/interfaces/interface[name=Ethernet7]/ethernet/config/aggregate-id'
            #
            pkey_ar = EncodePathKey(update.path.elem)
            set_val = getattr(update.val, update.val.WhichOneof("value"))
            yp_str  = EncodeYangPath(updPath)

            util_utl.utl_log("set req path :" + yp_str)
            util_utl.utl_log("set req val  :" + set_val)

            self.lock.acquire()
            ret_set = self.myDispatcher.SetValByPath(yp_str, pkey_ar, set_val)
            self.lock.release()

            if ret_set:
                ret_set = grpc.StatusCode.OK
            else:
                IsAnyErr = True
                ret_set = grpc.StatusCode.INVALID_ARGUMENT

            self.__AddOneSetResp(setResp, update.path, 3, ret_set, None)

            util_utl.utl_log("set req code :" + str(ret_set))

        # Fill error message
        # refer to google.golang.org/grpc/codes
        #
        # overall result
        if IsAnyErr == True:
            ret_code = grpc.StatusCode.ABORTED
        else:
            ret_code = grpc.StatusCode.OK

        setResp.message.code = ret_code.value[0];
        setResp.message.message = ret_code.value[1];

        return setResp

    def __processSubscribeRequestObj(self, reqSubObj, context):

        # TODO: process more than one req ?
        for req in reqSubObj:
            util_utl.utl_log(req)
            #pdb.set_trace()

            k = req.WhichOneof("request")
            util_utl.utl_log(k)
            #val = getattr(req, k)
            #print val

            if k == 'subscribe':
                my_work_q = Queue.Queue()

                for subs in req.subscribe.subscription:
                    work_rec = { 'req' : req,
                                 'subs': subs }
                    my_work_q.put(work_rec)

                while not self.is_stopped:
                    # wait here until work_rec occurs (from Timer_Q or enter here first time)
                    try:
                        cur_work_rec = my_work_q.get(True, 1)
                    except Queue.Empty:
                        continue

                    cur_req = cur_work_rec['req']
                    cur_subs= cur_work_rec['subs']

                    print ["stream", "once", "poll"][cur_req.subscribe.mode]
                    subResp = gnmi_pb2.SubscribeResponse()
                    subResp.update.timestamp = int(time.time())

                    if cur_req.subscribe.mode == 0:
                        # stream
                        # send first response then wait for next round
                        # 1) put each subs into Timer_Q ???
                        # 2) wait for timer event occurs
                        print ["target defined", "on change", "sample"][cur_subs.mode]
                        print cur_subs.path
                        # on_change     : check heartbeat_interval
                        # sample        : check sample_interval, suppress_redundant (heartbeat_interval)
                        # target defined: per leaf
                        path_ar = []
                        path_ar += EncodePath(cur_req.subscribe.prefix.elem)
                        path_ar += EncodePath(cur_subs.path.elem)

                        subResp.update.prefix.CopyFrom(cur_req.subscribe.prefix)
                        update = subResp.update.update.add()
                        update.path.CopyFrom(cur_subs.path)
                        update.val.string_val = "Test"
                        yield subResp

                        trec = {'req'     : cur_req,
                                'subs'    : cur_subs,
                                'cur-tick': 10,
                                'context' : context,
                                'workq'   : my_work_q
                        }
                        self.Timer_Q.append(trec)
                        pass
                    elif cur_req.subscribe.mode == 1:
                        # once
                        # send a final response with sync_response set to True
                        # not need to check the subscription's mode
                        if my_work_q.empty():
                            subResp.sync_response = True
                            yield subResp
                            return
                        else:
                            update = subResp.update.update.add()
                            update.val.string_val = "Test"
                            yield subResp
                            path_lst = []
                        pass
                    elif cur_req.subscribe.mode == 2:
                        # poll
                        # send first response then wait for next round
                        pass


            elif k == 'poll':
                # on demand request
                pass
            elif k == 'aliases':
                pass

    # gNMI Services Capabilities Routine
    def Capabilities(self, request, context):
        util_utl.utl_log("Recv'ed Capabiality Request")
        return self.__getCapabilitiesResponseObj()

    # gNMI Services Get Routine
    def Get(self, request, context):
        util_utl.utl_log("Recv'ed Get Request")
        return self.__processGetRequestObj(request)

    # gNMI Services Set Routine
    def Set(self, request, context):
        util_utl.utl_log("Recv'ed Set Request")
        return self.__processSetRequestObj(request)

    # gNMI Services Subscribe Routine
    def Subscribe(self, request, context):
        util_utl.utl_log("Recv'ed Subscribe Request")
        return self.__processSubscribeRequestObj(request, context)

#
# class gNMITarget
#
class gNMITarget:
    """gNMI Wrapper for the Server/Target"""
    def __init__(self, targetUrl, tlsEnabled, caCertPath, privKeyPath, isDbgTest):
        self.is_stopped = False
        self.is_ready = False
        self.grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.grpcServicer = gNMITargetServicer(isDbgTest)

        gnmi_pb2_grpc.add_gNMIServicer_to_server(self.grpcServicer, self.grpcServer)

        if tlsEnabled == True:
            # secure connection
            print privKeyPath, caCertPath
            with open(privKeyPath) as f:
                privateKey = f.read()
            with open(caCertPath) as f:
                certChain = f.read()
            credentials = grpc.ssl_server_credentials(((privateKey, certChain, ), ))
            self.grpcServer.add_secure_port(targetUrl, credentials)
        else:
            # insecure connection
            self.grpcServer.add_insecure_port(targetUrl)

    # timer_rec: { 'req':, 'subs':, 'cur-tick':, 'context': , 'workq': }
    # workq_rec: { 'req':, 'subs': }
    def TimerEventHandler(self, timer_q):
        l_timer_q = []
        while not self.is_stopped:
            #pdb.set_trace()
            while len(timer_q) > 0:
                l_timer_q.append(timer_q.pop())

            new_q = []
            for trec in l_timer_q:
                if trec['context'].is_active():
                    trec['cur-tick'] -= 1
                    if trec['cur-tick'] == 0:
                        trec['workq'].put( { 'req' : trec['req'],
                                             'subs': trec['subs'] }
                                         )
                    else:
                        new_q.append(trec)
                else:
                    util_utl.utl_log("subscribe client exit %s" % trec['subs'].path )

            l_timer_q[0:] = new_q
            time.sleep(1)

    def run(self):
        threads = []
        t = threading.Thread(target=self.TimerEventHandler, args = (self.grpcServicer.Timer_Q,))
        threads.append(t)
        #t.daemon = True
        t.start()

        self.grpcServer.start()
        self.is_ready = True
        try:
            while not self.is_stopped:
                time.sleep(1)
        except KeyboardInterrupt:
            self.is_stopped = True
        finally:
            self.grpcServicer.is_stopped = True
            self.grpcServer.stop(0)

        t.join()


#
# main
#
def main():
    parser = argparse.ArgumentParser()
    parserGrp = parser.add_argument_group("secure grpc")
    parser.add_argument('targetURL', help="target url, typically localhost:<port>")
    parserGrp.add_argument('--tls', action="store_true", help="enable tls connection")
    parserGrp.add_argument('--cert', help="path to the certificate")
    parserGrp.add_argument('--pvtkey', help="path to the private key file")
    parser.add_argument('--log-level', help="set log level", default =3, type=int)
    args = parser.parse_args()

    #print args
    log_path = '/var/log/nocsys_sonic_gnmi_server.log'

    if args.log_level < 0:
        # clear log file
        with open(log_path, 'w'):
            pass

#   let systemd redirect the stdout to syslog
#
#    else:
#        util_utl.DBG_MODE = 0

    log_level_map = [logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
                     logging.ERROR, logging.CRITICAL]
    log_fmt  = '%(asctime)s.%(msecs)03d %(levelname)-5s [%(filename)s %(lineno)d %(funcName)s] %(message)s'
    log_lvl  = log_level_map [args.log_level] if args.log_level < len(log_level_map) else logging.CRITICAL

    # remove any log handlers created automatically
    logging.getLogger().handlers = []

    handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=1024000, backupCount=2)
    handler.setFormatter(logging.Formatter(fmt = log_fmt, datefmt='%y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(log_lvl)

    util_utl.utl_log(args)

    gTarget = gNMITarget(args.targetURL, args.tls, args.cert, args.pvtkey, args.log_level < 0)
    gTarget.run()

# Starts here
if __name__ == '__main__':
    main()
