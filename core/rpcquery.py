from logger import *
from impacket.dcerpc.v5 import transport, srvs, wkst
from impacket.dcerpc.v5.dtypes import NULL
import settings

class RPCQUERY():
    def __init__(self, username, password, domain='', hashes=None):
        self.__username = username
        self.__password = password
        self.__domain = domain
        self.__lmhash = ''
        self.__nthash = ''
        self.__ts = ('8a885d04-1ceb-11c9-9fe8-08002b104860', '2.0')
        if hashes:
            self.__lmhash, self.__nthash = hashes.split(':')

    def connect(self, host, service):

        if service == 'wkssvc':
            stringBinding = r'ncacn_np:{}[\PIPE\wkssvc]'.format(host)
        elif service == 'srvsvc':
            stringBinding = r'ncacn_np:{}[\PIPE\srvsvc]'.format(host)

        rpctransport = transport.DCERPCTransportFactory(stringBinding)
        rpctransport.set_credentials(self.__username, self.__password, self.__domain, self.__lmhash, self.__nthash)

        dce = rpctransport.get_dce_rpc()
        dce.connect()

        if service == 'wkssvc':
            dce.bind(wkst.MSRPC_UUID_WKST, transfer_syntax = self.__ts)
        elif service == 'srvsvc':
            dce.bind(srvs.MSRPC_UUID_SRVS, transfer_syntax = self.__ts)

        return dce, rpctransport

    def enum_lusers(self, host):
        dce, rpctransport = self.connect(host, 'wkssvc')
        users_info = {}
        try:
            resp = wkst.hNetrWkstaUserEnum(dce, 1)
            lusers =  resp['UserInfo']['WkstaUserInfo']['Level1']['Buffer']
        except Exception:
            resp = wkst.hNetrWkstaUserEnum(dce, 0)
            lusers = resp['UserInfo']['WkstaUserInfo']['Level0']['Buffer']

        print_succ("{}:{} Logged on users:".format(host, settings.args.port))
        for luser in lusers:
            for fname in luser.fields.keys():
                print_message("{} {}".format(fname, yellow(luser[fname])))

    def enum_sessions(self, host):
        dce, rpctransport = self.connect(host, 'srvsvc')
        session_info = {}
        try:
            resp = srvs.hNetrSessionEnum(dce, NULL, NULL, 502)
            sessions  = resp['InfoStruct']['SessionInfo']['Level502']['Buffer']
        except Exception:
            resp = srvs.hNetrSessionEnum(dce, NULL, NULL, 0)
            sessions  = resp['InfoStruct']['SessionInfo']['Level0']['Buffer']

        print_succ("{}:{} Current active sessions:".format(host, settings.args.port))
        for session in sessions:
            for fname in session.fields.keys():
                print_message("{} {}".format(fname, yellow(session[fname])))

    def enum_disks(self, host):
        dce, rpctransport = self.connect(host, 'srvsvc')
        try:
            resp = srvs.hNetrServerDiskEnum(dce, 1)
        except Exception:
            resp = srvs.hNetrServerDiskEnum(dce, 0)

        print_succ("{}:{} Available disks:".format(host, settings.args.port))
        for disk in resp['DiskInfoStruct']['Buffer']:
            for dname in disk.fields.keys():
                print_att(disk[dname])
