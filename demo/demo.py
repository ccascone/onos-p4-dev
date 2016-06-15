from mininet.node import Host


class DemoHost(Host):
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

    def startPingBg(self, h):
        self.cmd(self.getInfiniteCmdBg("ping -i0.5 %s" % h.IP()))
        self.cmd(self.getInfiniteCmdBg("arping -w5000000 %s" % h.IP()))

    def startIperfServer(self):
        self.cmd(self.getInfiniteCmdBg("iperf3 -s"))

    def startIperfClient(self, h, flowBw="512k", numFlows=5, duration=5):
        iperfCmd = "iperf3 -c{} -b{} -P{} -t{}".format(h.IP(), flowBw, numFlows, duration)
        self.cmd(self.getInfiniteCmdBg(iperfCmd, sleep=0))

    def stop(self):
        self.cmd("killall iperf3")
        self.cmd("killall ping")
        self.cmd("killall arping")

    def describe(self):
        print "**********"
        print self.name
        print "default interface: %s\t%s\t%s" % (
            self.defaultIntf().name,
            self.defaultIntf().IP(),
            self.defaultIntf().MAC()
        )
        print "**********"

    def getInfiniteCmdBg(self, cmd, logfile="/dev/null", sleep=1):
        return "(while [ -e {} ]; " \
               "do {}; " \
               "sleep {}; " \
               "done;) > {} 2>&1 &".format(self.exectoken, cmd, sleep, logfile)

    def getCmdBg(self, cmd, logfile="/dev/null"):
        return "{} > {} 2>&1 &".format(cmd, logfile)
