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

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.cli import CLI
from itertools import combinations

from p4_mininet import P4Switch, P4Host

import argparse
from time import sleep


class SingleSwitchTopo(Topo):

    def __init__(self, sw_path, json_path, base_thrift_port, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        bmv2SwitchParams = dict(sw_path=sw_path,
                                json_path=json_path,
                                debugger=False,
                                loglevel="debug",
                                persistent=False,
                                gdb=False)

        sw = self.addSwitch("s0",
                       thrift_port=base_thrift_port,
                       device_id=0,
                       **bmv2SwitchParams)

        for hostId in (1, 2):
            host = self.addHost("h%d" % hostId,
                                ip="10.0.0.%d/24" % hostId,
                                mac='00:04:00:00:%02x:01' % hostId)
            self.addLink(host, sw)


def main(args):
    topo = SingleSwitchTopo(sw_path=args.behavioral_exe,
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

    sleep(1)

    print "Ready !"

    # for (h1, h2) in combinations(net.hosts, 2):
    #     h1.startPingBg(h2)
    #     h2.startPingBg(h1)
    #
    # for h in net.hosts:
    #     h.startIperfServer()

    # net.hosts[0].startIperfClient(net.hosts[-1], flowBw="512k", numFlows=40, duration=10)

    CLI(net)

    net.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='1 switch topology Bmv2 Mininet Demo')
    parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                        type=str, action="store", required=True)
    parser.add_argument('--thrift-port', help='Thrift server port for table updates (base)',
                        type=int, action="store", default=9090)
    parser.add_argument('--json', help='Path to JSON config file',
                        type=str, action="store", required=True)
    args = parser.parse_args()
    setLogLevel('info')
    main(args)
