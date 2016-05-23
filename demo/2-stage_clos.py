#!/usr/bin/python

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
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from itertools import combinations

from p4_mininet import P4Switch, P4Host

import argparse
from time import sleep


class ClosTopo(Topo):
    "2 stage Clos topology"

    def __init__(self, sw_path, json_path, base_thrift_port, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        bmv2SwitchParams = dict(sw_path=sw_path,
                                json_path=json_path,
                                debugger=False,
                                loglevel="warn",
                                persistent=True)

        bmv2SwitchIds = ["s11", "s12", "s13", "s21", "s22", "s23"]

        bmv2Switches = {}

        count = 0
        for switchId in bmv2SwitchIds:
            bmv2Switches[switchId] = self.addSwitch(switchId,
                                                    thrift_port=base_thrift_port + count,
                                                    device_id=int(switchId[1:]),
                                                    **bmv2SwitchParams)
            count += 1

        for i in (1, 2, 3):
            for j in (1, 2, 3):
                if i == j:
                    # 2 links
                    self.addLink(bmv2Switches["s1%d" % i], bmv2Switches["s2%d" % j])
                    self.addLink(bmv2Switches["s1%d" % i], bmv2Switches["s2%d" % j])
                else:
                    self.addLink(bmv2Switches["s1%d" % i], bmv2Switches["s2%d" % j])

        for hostId in (1, 2, 3):
            host = self.addHost("h%d" % hostId,
                                ip="10.0.0.%d/24" % hostId,
                                mac='00:00:00:00:00:%02x' % hostId)
            self.addLink(host, bmv2Switches["s1%d" % hostId])


def main(args):
    topo = ClosTopo(sw_path=args.behavioral_exe,
                    json_path=args.json,
                    base_thrift_port=args.thrift_port)

    net = Mininet(topo=topo,
                  host=P4Host,
                  switch=P4Switch,
                  controller=None,
                  build=False,
                  autoSetMacs=True)

    # net.addController( 'c0', controller=RemoteController, ip="192.168.57.1", port=6633)

    net.build()
    net.start()

    print "Network started..."

    sleep(4)

    for (h1, h2) in combinations(net.hosts, 2):
        h1.startPingBg(h2)
        h2.startPingBg(h1)

    for h in net.hosts:
        h.startIperfServer()

    print "Background ping started..."

    sleep(4)

    print "Starting traffic from h1 to h3..."

    # net.hosts[0].startIperfClient(net.hosts[-1], flowBw="200k", numFlows=100, duration=10)

    CLI(net)

    net.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='2-stage Clos Bmv2 Mininet Demo')
    parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                        type=str, action="store", required=True)
    parser.add_argument('--thrift-port', help='Thrift server port for table updates (base)',
                        type=int, action="store", default=9090)
    parser.add_argument('--json', help='Path to JSON config file',
                        type=str, action="store", required=True)
    args = parser.parse_args()
    setLogLevel('info')
    main(args)
