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
from os import environ

from mininet.node import Switch


class ONOSBmv2Switch(Switch):
    """BMv2 software switch """

    thrift_port = 9090
    device_id = 0

    def __init__(self, name, thrift_port=None,
                 device_id=None, debugger=False,
                 loglevel="warn", elogger=False, persistent=True, **kwargs):
        Switch.__init__(self, name, **kwargs)
        self.sw_path = environ['BMV2_EXE']
        self.json_path = environ['BMV2_DEFAULT_JSON']
        if not thrift_port:
            self.thrift_port = ONOSBmv2Switch.thrift_port
            ONOSBmv2Switch.thrift_port += 1
        else:
            self.thrift_port = thrift_port
            ONOSBmv2Switch.thrift_port = max(thrift_port, ONOSBmv2Switch.thrift_port)
        if not device_id:
            if self.dpid:
                if 'x' in self.dpid:
                    self.device_id = int(self.dpid, 0)
                else:
                    self.device_id = int(self.dpid, 16)
            else:
                self.device_id = ONOSBmv2Switch.device_id
                ONOSBmv2Switch.device_id += 1
        else:
            self.device_id = device_id
            ONOSBmv2Switch.device_id = max(device_id, ONOSBmv2Switch.device_id)
        self.debugger = debugger
        self.loglevel = loglevel
        self.logfile = '/tmp/bmv2-%d.log' % self.device_id
        self.output = open(self.logfile, 'w')
        self.elogger = elogger
        self.persistent = persistent
        if persistent:
            self.exectoken = "/tmp/bmv2-%d-exec-token" % self.device_id
            self.cmd("touch %s" % self.exectoken)

    @classmethod
    def setup(cls):
        pass

    def start(self, controllers):
        args = [self.sw_path, '--device-id %s' % str(self.device_id)]
        for port, intf in self.intfs.items():
            if not intf.IP():
                args.append('-i %d@%s' % (port, intf.name))
        if self.thrift_port:
            args.append('--thrift-port %d' % self.thrift_port)
        if self.elogger:
            nanomsg = "ipc:///tmp/bmv2-%d-log.ipc" % self.device_id
            args.append('--nanolog %s' % nanomsg)
        if self.debugger:
            args.append('--debugger')
        args.append('--log-console -L%s' % self.loglevel)
        args.append(self.json_path)

        assert controllers[0]
        c = controllers[0]
        args.append('--')
        args.append('--controller-ip %s' % c.IP())
        args.append('--controller-port %d' % c.port)

        bmv2cmd = " ".join(args);

        print "\nStarting BMv2 switch: " + bmv2cmd

        if self.persistent:
            # Re-exec the switch if it crashes.
            cmdStr = "(while [ -e {} ]; " \
                     "do {} ; " \
                     "sleep 1; " \
                     "done;) > {} 2>&1 &".format(self.exectoken, bmv2cmd, self.logfile)
        else:
            cmdStr = "{} > {} 2>&1 &".format(bmv2cmd, self.logfile)

        self.cmd(cmdStr)

    def stop(self):
        "Terminate switch."
        self.output.flush()
        if self.persistent:
            self.cmd("rm -f %s" % self.exectoken)
        self.cmd('kill %' + self.sw_path)
        self.deleteIntfs()

    def attach(self, intf):
        "Connect a data port"
        assert (0)

    def detach(self, intf):
        "Disconnect a data port"
        assert (0)


assert 'BMV2_EXE' in environ, "Environment $BMV2_EXE not set"
assert 'BMV2_DEFAULT_JSON' in environ, "Environment $BMV2_DEFAULT_JSON not set"

switches = {'onosbmv2': ONOSBmv2Switch}
