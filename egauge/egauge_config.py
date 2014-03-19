#!/usr/bin/env python

import httplib2
import httplib
import logging
import time
import urlparse
import urllib2
import xml.etree.ElementTree as ET
from collections import namedtuple
import EG_CTCFG
import json
import StringIO
from datetime import datetime, timedelta
import os

THISDIR = os.path.dirname(os.path.abspath(__file__))

Total = namedtuple('map', 'id,val')
Reg = namedtuple('reg', 'id,name,val,type')
Channel = namedtuple('ch', 'id,val')
User = namedtuple('user', 'id,user,priv')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("eg_cfg")


class REG(object):
    def __repr__(self):
        return self.__dict__.__repr__()


def parse_livevals(cont):
    root = ET.XML(cont)
    channels = {}
    for child in root:
        if child.tag in ('voltage', 'current'):
            channels[EG_CTCFG.CT_MAP[int(child.attrib['ch'])]] = child.text

    regs = []
    ctnum = 1
    for child in root:
        if child.tag == 'cpower':
            rg = REG()
            rg.ct = EG_CTCFG.CT_MAP[int(child.attrib['i'])]
            rg.l = EG_CTCFG.CT_MAP[int(child.attrib['u'])]
            ctnum += 1
            regs.append(rg)
            rg.I = float(channels[rg.ct])
            rg.V = float(channels[rg.l])
            rg.P = float(child.text)
            rg.reg = child.attrib['src']
            rg.pf = 0
            if rg.I and rg.V:
                rg.pf = abs(rg.P / (rg.I * rg.V))
            

    return int(root.find('timestamp').text), regs


class egcfg:

    def __init__(s, devurl, username, password, lg):
        if not devurl.startswith('http'):
            devurl = "http://" + devurl
        uu = urlparse.urlparse(devurl)
        if "." not in uu.hostname:
            # we will assume that it is egauge1910, or just 1910
            if not uu.hostname.startswith("egauge"):
                hn = "egauge" + uu.hostname
            else:
                hn = uu.hostname
            # add egauge.es at the end
            hn += ".egaug.es"
            uu = urlparse.urlparse("http://" + hn)

        s.devurl = uu
        s.username = username
        s.password = password
        s.lg = lg or logger
        s.req = httplib2.Http(timeout=60)
        s.req.add_credentials(username, password)   # Digest Authentication

    def request(s, uri, method="GET", body=None, verbose=True, retry=True):
        if not uri.startswith("/"):
            uri = "/" + uri
        requrl = s.devurl.geturl() + uri
        success = False
        if verbose:
            print requrl

        if retry:
            tries = 3
        else:
            tries = 1
        for rtry in range(tries):
            response, content = s.req.request(requrl, method=method,
                                          headers={'Connection': 'Keep-Alive',
                                                   'accept-encoding': 'gzip',
                                                   'Content-Type': 'application/xml'},
                                          body=body)
        
            if response['status'] == '404':
                s.lg.warning("device not found. Probably it is not up")
            else:
                break
            time.sleep(2)
        if response['status'] == '401':
            s.lg.warning("Unauthorized request!")
            raise urllib2.HTTPError(
                requrl, 401, "Unauthorized Request", hdrs=None, fp=None)
        elif response['status'] == '400':
            s.lg.warning("Bad Request!")
            raise urllib2.HTTPError(
                requrl, 400, "Bad Request", hdrs=None, fp=None)
        elif response['status'] == '500':
            s.lg.warning("Internal Error!")
            raise urllib2.HTTPError(
                requrl, 500, "Internal Error", hdrs=None, fp=None)
        elif response['status'] == '408':
            s.lg.warning("Request timeout!")
            raise urllib2.HTTPError(
                requrl, 408, "Request Timeout", hdrs=None, fp=None)
        elif response['status'] == '404':
            s.lg.warning("device not found. Probably it is not up")
            raise urllib2.HTTPError(
                requrl, 404, "Device not found", hdrs=None, fp=None)
        elif 'not authorized' in content.lower():
            s.lg.warning("Unauthorized request! using username={} and password={}".format(
                s.username, s.password))
            response['status'] = 401
            raise urllib2.HTTPError(
                requrl, 401, "Unauthorized Request", hdrs=None, fp=None)
        else:
            success = True

        if not success:
            print response, content

        return response, content

    def setcfg(s, ifile):
        """
        use the xml file that is provided and set config
        """
        # first save existing config somewhere

        s.getcfg()

        content = open(ifile, 'rt').read()
        channels, team, totals, users = s.parse_installation(content)
        body = s.get_installation_POST(channels, team, totals)

        uri = "/cgi-bin/protected/egauge-cfg"
        resp, cont = s.request(uri, method="POST", body=body)

        print resp, cont
        return resp, cont

    def setntp(s, ntpServer):
        """
        set ntp server configuration and reboot
        """
        uri = "/cgi-bin/protected/egauge-cfg"
        body = 'ntpServer=%s\n' % ntpServer
        resp, cont = s.request(uri, method="POST", body=body)
        print resp, cont
        return resp, cont

    def rotate_voltage_cofig(s, keep_phase_designator=True, meter_base_names=None):
        """
        if keep_phase_designator then rename registers to correct voltage val
        """
        (channels, team, totals, users) = s.getregisters(get_vals=True)
        # rotate
        rotated_team = []
        rotate_phase = True
        for reg in team:
            if meter_base_names is not None:
                rotate_phase=False
                if reg.name[:-2] in meter_base_names:
                    rotate_phase = True
                else:
                    rotate_phase = False
            
            if rotate_phase:
                if reg.type == 'P':
                    phase = int(reg.val[-1]) - 1
                    newphase = (phase + 1) % 3
                    if reg.name[-1] == reg.val[-1] and keep_phase_designator:
                        newname = "{}.{}".format(reg.name.rpartition(".")[0], newphase + 1)
                    else:
                        newname = reg.name

                    newval = "{}*L{}".format(reg.val[:-3], newphase + 1)
                    rotated_team.append(Reg._make((reg.id, newname, newval, reg.type)))
                else:
                    rotated_team.append(reg)
            else:
                rotated_team.append(reg)

        # rotate done
        body = s.get_installation_POST(channels, rotated_team, totals)
        uri = "/cgi-bin/protected/egauge-cfg"
        resp, cont = s.request(uri, method="POST", body=body)
        print resp, cont
        return resp, cont

    def _getversion(s):
        version = "2.0"
        try:
            sts = s.status()
            version = sts['swRev']
        except Exception as ex:
            print ex
        print "version=", version
        return version

    def setregisters(s, ifile, skip_backup=False, version=None):
        """
        use json file to set register and CT configuration
        """
        if version is None:
            version = s._getversion()
        if not skip_backup:
            s.getregisters(version=version)
        content = open(ifile, 'rt').read()
        obj = json.loads(content)
        channels, team, totals = s._from_json(obj, version=version)
        body = s.get_installation_POST(channels, team, totals)

        uri = "/cgi-bin/protected/egauge-cfg"
        resp, cont = s.request(uri, method="POST", body=body)

        print resp, cont
        return resp, cont

    def getregisters(s, ofile=None, skip_write=False, get_vals=False, version=None):
        if version is None:
            version = s._getversion()
        response, content = s.getcfg(skip_write=True)
        channels, team, totals, users = s.parse_installation(content)
        if ofile is None:
            ofile = "%s.conf.%d.json" % (s.devurl.hostname, int(time.time()))
        # create ouput json
        obj = s._to_json(channels, team, totals, version=version)
        obj_str = s._format_json(obj)

        if not skip_write:
            if ofile != "--":
                of = open(ofile, "wt")
                print >> of, obj_str
                of.close()
                print "saved config to ", ofile
            else:
                print obj_str

        if get_vals:
            return ((channels, team, totals, users))
        else:
            return obj_str

    @staticmethod
    def _format_json(obj):
        op = StringIO.StringIO()
        print >>op, '{"CTs": {'
        CTs = obj['CTs']
        ctnames = sorted(CTs.keys(), key=lambda nm: int(nm[2:]))
        for idx, ctname in enumerate(ctnames):
            if idx != 0:
                print >>op, ",",
            print >>op, '"%s":' % (ctname), json.dumps(CTs[ctname])
        print >>op, '}, "Registers": {'
        REGS = obj['Registers']
        regnames = sorted(REGS.keys(), key=lambda rg: int(rg[1:]))
        for idx, regname in enumerate(regnames):
            if idx != 0:
                print >>op, ",",
            print >>op, '"%s":' % (regname), json.dumps(REGS[regname])
        print >>op, '}}'
        return op.getvalue()

    @staticmethod
    def _to_json(channels, team, totals, version="2.0"):
        chmap = dict((ch.id, ch) for ch in channels)
        teammap = dict((tm.id, tm) for tm in team)

        obj = {}
        obj['Registers'] = REGS = {}
        obj['CTs'] = CTs = {}

        # we are only interested in CT1.. CT12 here
        # The PTs are considered
        for ctnum in range(1, 13):
            visualCTNAME = 'CT%d' % (ctnum)
            if visualCTNAME in EG_CTCFG.CT_MAP_REV and EG_CTCFG.CT_MAP_REV[visualCTNAME] in chmap:
                ct = chmap[EG_CTCFG.CT_MAP_REV[visualCTNAME]]
                mul, _, _, calibration, _ = ct.val.split(',')
                mul_str = "{:.3f}".format(float(mul))

            cts = {}
            ct_type = EG_CTCFG.get_ct_type_by_mul(mul_str, version=version)
            if ct_type is None:
                ct_type = 'custom'
                cts['mul'] = mul_str

            cts['rating'] = ct_type
            if calibration:
                cts['cal'] = calibration
            CTs[visualCTNAME] = cts

        for regnum in range(17):
            if regnum in teammap:
                reg = teammap[regnum]
                REGS["R{}".format(regnum)] = {'name': reg.name,
                                              'val': reg.val, 'type': reg.type}

        return obj

    @staticmethod
    def _from_json(obj, version="2.0"):
        channels, teams, totals = [], [], []
        # <ch0> ... <ch15> .. not all will always be available
        CTs = obj['CTs']
        for ch_id in range(16):
            if ch_id not in EG_CTCFG.CT_MAP:
                continue

            ctname = EG_CTCFG.CT_MAP[ch_id]
            if ctname in ["L1", "L2", "L3"]:
                channels.append(
                    Channel._make((ch_id, EG_CTCFG.get_ch_row('PT', version=version))))
            else:
                ct = CTs[ctname]
                cal = None
                if 'cal' in ct:
                    cal = ct['cal']
                mul = None
                if 'mul' in ct:
                    mul = ct['mul']
                ch_row = EG_CTCFG.get_ch_row(ct['rating'], cal, mul, version=version)
                channels.append(Channel._make((ch_id, ch_row)))

        # process team --> registers
        REGS = obj['Registers']
        regnames = sorted(REGS.keys(), key=lambda rg: int(rg[1:]))
        for idx, regname in enumerate(regnames):
            ridx = regname[1:]
            reg = REGS[regname]
            rg = Reg._make((int(ridx),
                           reg['name'],
                           reg['val'],
                           reg['type']))
            teams.append(rg)

        return channels, teams, totals

    @staticmethod
    def get_installation_POST(channels, team, totals):
        # channels
        op = ""
        for ch in channels:
            op += "ch%d=%s\n" % (ch.id, ch.val)
        # team
        op += "team=\n"
        op += "member=\"local\"\n"
        op += "link=\"local\"\n"

        for reg in team:
            op += "name=\"%s\"\n" % reg.name
            op += "id=\"%d\"\n" % reg.id
            op += "val=\"%s\"\n" % reg.val
            op += "type=\"%s\"\n" % reg.type

        op += "team_end=\n"
        op += "totals=\n"
        for mp in totals:
            op += "map%d=%s\n" % (mp.id, mp.val)

        return op

    @staticmethod
    def parse_installation(content):
        teams = []
        totals = []
        channels = []
        users = []
        root = ET.XML(content)
        # <ch0> ... <ch15> .. not all will always be available
        for ch_id in range(16):
            chid = "ch%d" % ch_id
            ch = root.find(chid)
            if ch is not None:
                channels.append(Channel._make((ch_id, ch.text)))

        # <settings> <team> <tmember> if type=='local'
        team = root.findall('team')[0]
        tmembers = team.findall('tmember')
        # this will be set correctly to 'local' tmember
        tmember = None

        for tm in tmembers:
            ttype = tm.find('type').text
            if ttype == 'local':
                tmember = tm
                break
        # tmember is set now
        #from IPython.core.debugger import Pdb; Pdb().set_trace()
        if tmember is not None:
            for reg in tmember.findall('reg'):
                rg = Reg._make((int(reg.find('id').text),
                                reg.find('name').text,
                                reg.find('val').text,
                                reg.find('type').text))
                teams.append(rg)

        # <user1>owner</user1>
        # <priv1>unlimited_save, view_settings</priv1>
        # <user2>user</user2>
        # <priv2>view_settings</priv2>
        # <user3>QSR</user3>
        # <priv3>local_save, view_settings</priv3>
        for uid in range(1, 10):
            usr = root.find("user{}".format(uid))
            if usr is None:
                break
            prv = root.find("priv{}".format(uid))
            users.append(User._make((uid, usr.text, prv.text)))

        # virtual registers
        total = root.findall('totals')[0]
        for idx, mp in enumerate(total.findall('map')):
            totals.append(Total._make((idx, mp.text)))

        return channels, teams, totals, users

    def getcfg(s, ofile=None, skip_write=False):
        uri = "/cgi-bin/protected/egauge-cfg"
        if ofile is None:
            ofile = "%s.conf.backup.%d" % (s.devurl.hostname, int(time.time()))

        resp, cont = s.request(uri)
        if not skip_write:
            if ofile != "--":
                of = open(ofile, "wt")
                print >> of, cont
                of.close()
                print "saved config to ", ofile
            else:
                print resp, cont
        return resp, cont

    """
     <pushURI></pushURI>
      <pushInterval>600</pushInterval>
       <pushOptions></pushOptions>
    """
    def register(s, pushURI, pushInterval=60, sec=False):
        uri = "/cgi-bin/protected/egauge-cfg"
        body = 'pushURI="%s"\n' % pushURI
        if pushInterval:
            body += "pushInterval=%d\n" % pushInterval
        if sec:
            body += 'pushOptions="sec,gzip"\n'
        s.request(uri, method="POST", body=body)
        print body

    def upgrade(s, branch):
        uri = "/cgi-bin/protected/sw-upgrade?branch="
        if branch != "stable":
            uri += branch
        ret = s.request(uri)
        ret1 = s.reboot()
        return (ret, ret1)

    def current_readings(s):
        """
        <?xml version="1.0" encoding="UTF-8" ?>
        <!DOCTYPE group PUBLIC "-//ESL/DTD eGauge 1.0//EN" "http://www.egauge.net/DTD/egauge-hist.dtd">
        <group serial="0x7da9fd6d">
        <data columns="15" time_stamp="0x52853f51" time_delta="120" delta="true" epoch="0x50f07c24">
         <cname t="P">MAIN.1</cname>
         <cname t="P">MAIN.2</cname>
         <cname t="P">MAIN.3</cname>
         <cname t="P">MAIN-CT04.1</cname>
         <cname t="P">MAIN-CT05.2</cname>
         <cname t="P">MAIN-CT06.3</cname>
         <cname t="P">MAIN-CT07.1</cname>
         <cname t="P">MAIN-CT08.2</cname>
         <cname t="P">MAIN-CT09.3</cname>
         <cname t="P">MAIN-CT10.3</cname>
         <cname t="P">MAIN-CT11.2</cname>
         <cname t="P">MAIN-CT12.1</cname>
         <cname t="S">MAIN.1*</cname>
         <cname t="S">MAIN.2*</cname>
         <cname t="S">MAIN.3*</cname>
        </data>
        </group>
        """
        uri = "/cgi-bin/egauge-show?e&m&C&s=1&n=1"
        resp, content = s.request(uri)
        root = ET.XML(content)
        ts = int(root[0].get('time_stamp'), 16)
        dt = datetime.utcfromtimestamp(ts)

        uri = "/cgi-bin/egauge?v1&inst"
        resp, content = s.request(uri)
        root = ET.XML(content)
        now = None
        for child in root:
            if child.tag == "ts":
                now = datetime.utcfromtimestamp(int(child.text))
                break
        print "Egauge database time is {},  egauge current time {}".format(dt, now)
        if abs(now - dt) < timedelta(minutes=2):
            ok = True
        else:
            ok = False
        return (ok, dt, root[2:])

    def upgrade_kernel(s):
        uri = "/cgi-bin/protected/sw-upgrade?kernel"
        ret = s.request(uri)
        ret1 = s.reboot()
        return (ret, ret1)

    def reboot(s):
        uri = "/cgi-bin/protected/reboot"
        ret = None
        try:
            ret = s.request(uri)
        except httplib.IncompleteRead:
            # it is possible to get this because the server reboots
            pass

        if s.timeout != 0:
            s.wait()

        return ret

    def netconfig(s):
        uri = "/cgi-bin/netcfg?live"
        ret = s.request(uri)
        print ret
        return ret

    def get(s, uri):
        ret = s.request(uri)
        print ret[1]
        return ret

    def getpushstatus(s):
        uri = "/cgi-bin/get?pushStatus"
        ret = s.request(uri)
        print ret[1]
        return ret

    def getntp(s):
        uri = "/cgi-bin/get?ntp"
        ret = s.request(uri)
        print ret[1]
        return ret

    def wait(s, fn=None):
        """
        wait for at most timeout seconds to check if the server is up
        """
        if fn is None:
            fn = lambda:  s.request("/status.xml")
        
        found = False
        waited = 0
        step = 2
        while waited <= s.timeout:
            time.sleep(step)
            waited += step
            try:
                #resp, content = s.request("/status.xml")
                fn()
                found = True
                break
            except urllib2.HTTPError as herr:
                if hasattr(herr, 'code') and herr.code == 404:
                    pass
                else:
                    raise
            step += 1

        print "found={} after waiting for {} sec".format(found, waited)
        if found:
            s.status()
        return found

    def channelchecker(s, samples=10):
        """
        return live vals monitored for give number of samples
        """
        uri = "/cgi-bin/egauge?noteam"

        chan = []
        for idx in range(samples):
            resp, content = s.request(uri, verbose=False)
            ts, regs = parse_livevals(content)
            chan.append((ts, regs))
            if idx == 0:
                print "time",
                for rg in regs:
                    print rg.ct,
                print ""
                print "time",
                for rg in regs:
                    print rg.reg,
                print ""
            print ts,
            for rg in regs:
                print "{}/({:.3f})".format(rg.P, rg.pf),
            print ""

        return chan

    def status(s):
        uri = "/status.xml"
        """
        <?xml version="1.0" encoding="UTF-8" ?>
        <status>
           <timestamp>0x52273a9b</timestamp>
           <swRev>1.35</swRev>
           <uptime>73442.63</uptime>
           <lastWebReboot>1378229174</lastWebReboot>
           <rebootReason>Software Reset</rebootReason>
           <tempC>52.00</tempC>
           <speed>12357142</speed>
           <osvers>#319 Fri Mar 22 14:57:37 MDT 2013</osvers>
           <model>egauge2</model>
        </status>
        """
        resp, content = s.request(uri)

        root = ET.XML(content)

        st = {}
        for child in root._children:
            st[child.tag] = child.text

        print st
        return st


actions = [
    "register", "de-register", "reboot", "upgrade", "upgrade-kernel", "getconfig",
    "getregisters", "setconfig", "setregisters", "netconfig", "getntp", "setntp",
    "getpushstatus", "status", "get", "wait", "is-caught-up", "channelchecker",
    "rotate-voltage-config", "auto-phase-match"]

DEFAULT_SAMPLES = 10
DEFAULT_PASSWORD = "default"
if 'EG_PASSWORD' in os.environ:
    DEFAULT_PASSWORD = os.environ['EG_PASSWORD']
DEFAULT_USERNAME = "owner"
if 'EG_USERNAME' in os.environ:
    DEFAULT_USERNAME = os.environ['EG_USERNAME']


def cfg_opts():
    from optparse import OptionParser
    parser = OptionParser(usage="""usage: %prog action device_url [options]
                action = {}""".format("|".join(actions)))
    parser.add_option("--seconds", default=False, action="store_true",
                      help="will try to fetch seconds data if specified")
    parser.add_option("--skip-backup", default=False, action="store_true",
                      help="Do not take backup of the current config")
    parser.add_option("--username", default=DEFAULT_USERNAME)
    parser.add_option("--timeout", default=0, type="int")
    parser.add_option("--samples", default=DEFAULT_SAMPLES, type="int")
    parser.add_option("--password", default=DEFAULT_PASSWORD, help="export EG_PASSWORD instead of this")
    parser.add_option("--cfgfile", default=None,
                      help="-- will write to stdout")
    parser.add_option("--branch", help="branch to use for upgrades, default=stable", default="stable")
    parser.add_option("--pushInterval")
    parser.add_option("--pushURI")
    parser.add_option("--ntpServer")
    parser.add_option("--path")
    parser.add_option("--version")
    parser.add_option("--restore", default=False, action="store_true")

    return parser


def main():
    parser = cfg_opts()
    (options, args) = parser.parse_args()
    main_opts(parser, options, args)


def main_opts(parser, options, args):
    if len(args) < 2:
        parser.print_help()
        exit(2)

    action = args[0]
    device_url = args[1]

    if action not in actions:
        print "unknown", action
        parser.print_help()
        exit(2)
    eg = egcfg(device_url, options.username, options.password, logger)
    eg.timeout = int(options.timeout)

    pushInterval = None
    retval = 0
    if options.pushInterval:
        pushInterval = int(options.pushInterval)
    if action == "register":
        eg.register(options.pushURI, pushInterval, options.seconds)
    if action == "de-register":
        eg.register("", pushInterval, options.seconds)
    if action == "channelchecker":
        eg.channelchecker(int(options.samples))
    elif action == "reboot":
        eg.reboot()
    elif action == "upgrade":
        eg.upgrade(options.branch)
    elif action == "upgrade-kernel":
        eg.upgrade_kernel()
    elif action == "netconfig":
        eg.netconfig()
    elif action == "status":
        eg.status()
    elif action == "getntp":
        eg.getntp()
    elif action == "is-caught-up":
        ok, dt, data = eg.current_readings()
        if not ok:
            retval = -1
    elif action == "get":
        eg.get(options.path)
    elif action == "getpushstatus":
        eg.getpushstatus()
    elif action == "getconfig":
        eg.getcfg(options.cfgfile)
    elif action == "setconfig":
        eg.setcfg(options.cfgfile)
    elif action == "wait":
        eg.wait()
    elif action == "setntp":
        if options.ntpServer is None:
            print "ntpServer is required for setntp"
            exit(2)
        eg.setntp(options.ntpServer)
    elif action == "getregisters":
        eg.getregisters(options.cfgfile, version=options.version)
    elif action == "setregisters":
        eg.setregisters(options.cfgfile, options.skip_backup, version=options.version)
    elif action == "rotate-voltage-config":
        eg.rotate_voltage_cofig()
    elif action == "auto-phase-match":
        import egauge_auto_config
        data = egauge_auto_config.auto_phase_match(eg, options.samples, options.restore)

    if hasattr(options, "exit") is False or options.exit is True:
        exit(retval)

if __name__ == "__main__":
    main()
