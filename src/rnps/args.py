# ----------------------------------------------------------------------------------------
# RNPS aka Rapid Network Port Scan
# Copyright (C) 2022 Ivan Maruca <ivan>DOT<maruca>AT<gmail>DOT<com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/agpl-3.0.en.html
# ----------------------------------------------------------------------------------------

import argparse
import itertools
import sys
import textwrap
from rnps.version import Version
from rnps.port import Port

class Args:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            prog='rnps',
            formatter_class=argparse.RawTextHelpFormatter,
            description=textwrap.dedent(f'''\
                RNPS aka Rapid Network Port Scan
                Ver {Version.MAJOR}.{Version.MINOR}.{Version.PATCH}
            ''')
        )
        self.parser.add_argument('host',type=str,metavar='<HOST>',help=textwrap.dedent('''\
            The hostname or IP address.
            You can enter a CIDR notation to specify an address range.
            Examples :
                www.example.com
                192.168.1.100
                192.168.1.0/24
            '''))
        self.parser.add_argument('-p','--port',type=int,nargs='+',help=textwrap.dedent('''\
            The port to be scanned.
            Can be a list of ports, for example:
                -p 80 443 22
            '''))
        self.parser.add_argument('-r','--port-range',type=self.port_range,help=textwrap.dedent('''\
            A range of ports to be scanned.
            Examples : 
                -r 50-80
            '''))
        self.parser.add_argument('-e','--exclude',type=self.exlude_port,help=textwrap.dedent('''\
            A list of ports to be exluded from scan.
            Examples : 
                -e 110 111 (exclude ports 110 and 111)
                -e 100-110 (exclude from port 100 to 110)
            '''))
        self.parser.add_argument('--all',action='store_true',help=textwrap.dedent('''\
            Scan all ports range
            from 0 to 65535
            '''))
        self.parser.add_argument('--reserved',action='store_true',help=textwrap.dedent('''\
            Scan all reserved ports range
            from 0 to 1023
            '''))
        self.parser.add_argument('--registered',action='store_true',help=textwrap.dedent('''\
            Scan all registered ports range
            from 1024 to 49151
            '''))
        self.parser.add_argument('--free',action='store_true',help=textwrap.dedent('''\
            Scan all free/unregistered ports range
            from 49152 to 65535
            '''))
        self.parser.add_argument('--udp',action='store_true',help=textwrap.dedent('''\
            Specifies that the ports to be scanned are UDP
            '''))
        self.parser.add_argument('--json',action='store_true',help=textwrap.dedent('''\
            Output format to JSON
            '''))
        self.parser.add_argument('-f','--file',type=str,help=textwrap.dedent('''\
            Save the scan result to a file
            Examples :
                -f my_scan.txt
            '''))
        self.parser.add_argument('-v','--verbose',action='store_true',help=textwrap.dedent('''\
            View all results
            '''))
        self.parser.add_argument('-t','--max-threads',type=int,help=textwrap.dedent('''\
            Limit the use of threads to a specific value.
            On some OS the use of processes per user is limited, 
            if you find incomplete scans try to reduce the number of threads generated.
            A common value of this limit is 1024, 
            try to set it lower (consider the processes already active on the system)
            Too low value will increase the execution time
            '''))
        self.args = self.parser.parse_args()
        self.cmdline = " ".join(arg for index,arg in enumerate(sys.argv) if index != 0)

    def exlude_port(self,args):
        try:
            if '-' in args:
                a = args.split('-')
                return range(int(a[0]),int(a[1])+1)
            else:
                a = args.split(' ')
                aa = []
                for b in a:
                    aa.append(int(b))
                return aa
        except Exception:
            raise argparse.ArgumentTypeError('Invalid port range {}'.format(args))

    def port_range(self,args):
        try:
            a = args.split('-')
            return range(int(a[0]),int(a[1])+1)
        except Exception:
            raise argparse.ArgumentTypeError('Invalid port range {}'.format(args))
        
    def getHost(self):
        return self.args.host
    
    def getPorts(self):
        ports = self.args.port if self.args.port is not None else []
        port_range = self.args.port_range if self.args.port_range is not None else []
        exclude = self.args.exclude if self.args.exclude is not None else []
        all =  Port.ALL_RANGE if self.args.all else []
        registered =  Port.REGISTERED_RANGE if self.args.registered else []
        reserved =  Port.RESERVED_RANGE if self.args.reserved else []
        free =  Port.FREE_RANGE if self.args.free else []
        port_list = list()
        for p in itertools.chain(ports,port_range,all,registered,reserved,free):
            port_list.append(p)

        port_list = sorted(set(port_list) - set(exclude))
        if len(port_list) == 0:
            port_list = [80]
        return port_list
    
    def getPortType(self):
        return Port.UDP if self.args.udp else Port.TCP

    def isVerbose(self):
        return self.args.verbose

    def isJSON(self):
        return self.args.json

    def filename(self):
        return self.args.file

    def getCmdLine(self):
        return self.cmdline

    def getMaxThreads(self):
        return self.args.max_threads