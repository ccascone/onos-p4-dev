# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from mininet.net import Mininet
from mininet.node import Switch, Host
from mininet.log import setLogLevel, info



class P4Host(Host):

    def __init__(self, name, inNamespace=True, **params):
        Host.__init__(self, name, inNamespace=inNamespace, **params)
        self.exectoken = "/tmp/mn-exec-token-host-%s" % name
        self.cmd("touch %s" % self.exectoken)


    def config(self, **params):
        r = super(Host, self).config(**params)

        self.defaultIntf().rename("eth0")

        for off in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload eth0 %s off" % off
            self.cmd(cmd)

        # disable IPv6
        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

        return r

    def loopCmdBg(self, cmdString, logfile="/dev/null", sleepSeconds=1):
        self.cmd("(while [ -e {} ]; do {} ; sleep {}; done;) > {} 2>&1 &".format(self.exectoken, cmdString,
                                                                                 sleepSeconds, logfile))

    def startPingBg(self, h):
        self.loopCmdBg("ping %s" % h.IP())
        self.loopCmdBg("arping %s" % h.IP())

    def startIperfServer(self):
        self.loopCmdBg("iperf3 -s")

    def startIperfClient(self, h, flowBw="512k", numFlows=5, duration=5):
        self.loopCmdBg("iperf3 -c{} -b{} -P{} -t{}".format(h.IP(), flowBw, numFlows, duration), sleepSeconds=0)

    def stop(self):
        self.cmd("killall iperf3")
        self.cmd("killall ping")

    def describe(self):
        print "**********"
        print self.name
        print "default interface: %s\t%s\t%s" % (
            self.defaultIntf().name,
            self.defaultIntf().IP(),
            self.defaultIntf().MAC()
        )
        print "**********"


class P4Switch(Switch):

    device_id = 0

    """P4 virtual switch"""
    def __init__(self, name, sw_path=None, json_path=None,
                 thrift_port=None,
                 pcap_dump=False,
                 verbose=False,
                 device_id=None,
                 debugger=False,
                 loglevel="info",
                 nanolog=False,
                 persistent=False,
                 gdb=False,
                 **kwargs):
        Switch.__init__(self, name, **kwargs)
        assert (sw_path)
        assert (json_path)
        self.sw_path = sw_path
        self.json_path = json_path
        self.verbose = verbose
        logfile = '/tmp/p4s.%s.log' % self.name
        self.output = open(logfile, 'w')
        self.thrift_port = thrift_port
        self.pcap_dump = pcap_dump
        if device_id is not None:
            self.device_id = device_id
            P4Switch.device_id = max(P4Switch.device_id, device_id)
        else:
            self.device_id = P4Switch.device_id
            P4Switch.device_id += 1
        self.nanomsg = "ipc:///tmp/bm-%d-log.ipc" % self.device_id
        self.debugger = debugger
        self.loglevel = loglevel
        self.nanolog = nanolog
        self.exectoken = "/tmp/mn-exec-token-sw-%s" % self.name
        self.cmd("touch %s" % self.exectoken)
        self.persistent = persistent
        self.gdb = gdb

    @classmethod
    def setup(cls):
        pass

    def loopCmdBg(self, cmdString, logfile="/dev/null", sleepSeconds=1):
        if self.persistent:
            c = "(while [ -e {} ]; do {} ; sleep {}; done;) > {} 2>&1 &".format(self.exectoken, cmdString,
                                                                                 sleepSeconds, logfile)
        else:
            c= "{} > {} 2>&1 &".format(cmdString, logfile)
        # print c
        self.cmd(c)

    def start(self, controllers):
        "Start up a new P4 switch"
        args = [self.sw_path]
        # args.extend( ['--name', self.name] )
        # args.extend( ['--dpid', self.dpid] )
        for port, intf in self.intfs.items():
            if not intf.IP():
                args.extend(['-i', str(port) + "@" + intf.name])
        if self.pcap_dump:
            args.append("--pcap")
            # args.append("--useFiles")
        if self.thrift_port:
            args.extend(['--thrift-port', str(self.thrift_port)])
        if self.nanolog:
            args.extend(['--nanolog', self.nanomsg])
        if self.debugger:
            args.extend(['--debugger'])
        args.extend(['--log-console -L%s' % self.loglevel]);
        args.extend(['--device-id', str(self.device_id)])
        P4Switch.device_id += 1
        args.append(self.json_path)

        logfile = '/tmp/p4s.%s.log' % self.name

        bmv2cmd = " ".join(args);

        print "\nStarting P4 switch: " + bmv2cmd

        if not self.gdb:
            self.loopCmdBg(bmv2cmd, logfile=logfile)
        else:
            print "GDB!! gdb %s" % bmv2cmd

    def stop(self):
        "Terminate switch."
        self.output.flush()
        self.cmd("rm -f %s" % self.exectoken)
        self.cmd('kill %' + self.sw_path)
        self.deleteIntfs()

    def attach(self, intf):
        "Connect a data port"
        assert (0)

    def detach(self, intf):
        "Disconnect a data port"
        assert (0)
