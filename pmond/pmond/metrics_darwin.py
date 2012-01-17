# This is the MIT License
# http://www.opensource.org/licenses/mit-license.php
#
# Copyright (c) 2007,2008 Nick Galbreath
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""
Core metrics for Darwin (uhhh Mac OS X).

Tested on Mac OSX 10.5
"""

from subprocess import Popen, PIPE
from time import time

from metric import metric

class metric_proc(metric):

    def interval(self):
        return 80

    def gather(self, tree):
        p = Popen(['ps', '-ax'],  stdout=PIPE)    
        lines = p.stdout.read().split('\n')
        self.addMetric({'NAME':'proc_total', 'VAL':len(lines) -1,
                        'TYPE':'uint32', 'UNITS':'', 'TMAX':950,
                        'DMAX':0, 'SLOPE':'zero'})    
        
class metric_sys_clock(metric):
    def interval(self):
        return 1200

    def gather(self, tree):
        self.addMetric({'NAME':'sys_clock', 'VAL':int(time()),
                        'TYPE':'timestamp', 'UNITS':'s', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})    

class metric_cpu(metric):
    def interval(self):
        return 20

    def gather(self, tree):
        sysctls = [ 'sysctl',
                    'hw.ncpu',
                    'hw.cpufrequency',
                    'hw.memsize',
                    'kern.boottime',
                    'kern.ostype',
                    'kern.osrelease',
                    'hw.machine'
                    ]
        p = Popen(sysctls, stdout=PIPE)
        lines = p.stdout.read().split('\n')

        val = lines[0].split(' ')[1]
        self.addMetric({'NAME':'cpu_num', 'VAL':val,
                        'TYPE':'uint16', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})

        val = lines[1].split(' ')[1]
        self.addMetric({'NAME':'cpu_speed', 'VAL': int(val) / 1000000,
                        'TYPE':'uint32', 'UNITS':'MHz', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})

        val = lines[2].split(' ')[1]
        self.addMetric({'NAME':'mem_total', 'VAL': int(val) / 1024,
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})
        
        val = lines[3].split(' ')[4].strip(',')
        self.addMetric({'NAME':'boottime', 'VAL': int(val),
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})

        val = lines[4].split(' ')[1]
        self.addMetric({'NAME':'os_name', 'VAL':val,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero'})

        val = lines[5].split(' ')[1]
        self.addMetric({'NAME':'os_release', 'VAL':val,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})

        val = lines[6].split(' ')[1]
        self.addMetric({'NAME':'machine_type', 'VAL':val,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})


class metric_net(metric):
    last_time = time()
    last_out = -1
    last_in = -1

    def interval(self):
        return 40

    def gather(self, tree):
        now = time()
        interval = self.last_time - now

        p = Popen(['sysctl',
                   'net.inet.tcp.out_sw_cksum_bytes',
                   'net.inet.udp.out_sw_cksum_bytes',
                   'net.inet.tcp.in_sw_cksum_bytes',
                   'net.inet.udp.in_sw_cksum_bytes'], stdout=PIPE)

        lines = p.stdout.read().split('\n')
        tcp_out = int(lines[0].split(' ')[1])
        udp_out = int(lines[1].split(' ')[1])
        tcp_in = int(lines[2].split(' ')[1])
        udp_in = int(lines[3].split(' ')[1])
        
        total_out = tcp_out + udp_out
        total_in  = tcp_in + udp_in


        # Ideally you'd just return total_out and total_in
        # and let RRD figure out bytes/sec using a COUNTER

        # BUT, oddly  "official" gmond returns bytes per second 
        # which seems odd.  So sadly, we have do all this nonsense
        if self.last_out == -1:
            self.last_out  = total_out
            self.last_in  = total_in
            return
        
        out_bps = float(total_out - self.last_out) / interval
        in_bps = float(total_in - self.last_in) / interval
        self.last_time = time()
        self.last_out = total_out
        self.last_in = total_in

        self.addMetric({'NAME':'bytes_in', 'VAL':in_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})

        self.addMetric({'NAME':'bytes_out', 'VAL':out_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})

class metric_mem(metric):
    """
    parser output of 'vm_stat' (not 'vmstat' ;-) which is like this:

$ vm_stat
Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                   138536.
Pages active:                  93700.
Pages inactive:                45617.
Pages wired down:             244883.
"Translation faults":      642439019.
Pages copy-on-write:        11321212.
Pages zero filled:         244573300.
Pages reactivated:            498124.
Pageins:                      484456.
Pageouts:                     278246.
"""
    def interval(self):
        return 60

    def gather(self, tree):
        p = Popen(['vm_stat'], stdout=PIPE)
        lines = p.stdout.read().split('\n')
        mem_free = int(lines[1].strip(',').split(':')[1].strip('.').strip()) * 4
        self.addMetric({'NAME':'mem_free', 
                        'VAL' : mem_free,
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        sysctls = ['sysctl', 'vm.swapusage']

        p = Popen(sysctls, stdout=PIPE)
        lines = p.stdout.read().split(' ')

        # lines is now the list:
        # ['vm.swapusage:', 'total', '=', '1024.00M', '',
        #     'used', '=', '590.66M', '', 'free', '=', '433.34M',
        #      '', '(encrypted)\n']

        swap_total = float(lines[3].strip('M')) * 1024
        swap_free  = float(lines[11].strip('M')) * 1024

        self.addMetric({'NAME':'swap_total', 'VAL':int(swap_total),
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})

        self.addMetric({'NAME':'swap_free', 'VAL':int(swap_free),
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})

        # Bonus - not part of gmond
        #self.addMetric({'NAME':'swap_used', 'VAL':val,
        #                'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
        #                'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})


class metric_disk(metric):
    def interval(self):
        return 40

    def gather(self, tree):
        p = Popen(['df', '-m', '/'], stdout=PIPE)
        lines = p.stdout.read().split('\n')
        values = filter(lambda x: len(x), lines[1].split(' '))
        # volume name, size in MB, used in MB, free in MB, %used, mount
        # ['/dev/disk0s2', '111', '89', '22', '81%', '/']
        self.addMetric({'NAME':'disk_total', 
                        'VAL' :float(values[1]) /  1048576.0,
                        'TYPE':'double', 'UNITS':'GB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        self.addMetric({'NAME':'disk_free', 
                        'VAL' :float(values[3]) /  1048576.0,
                        'TYPE':'double', 'UNITS':'GB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})


class metric_iostat(metric):
    def interval(self):
        return 20

    def gather(self, tree):
        p = Popen(['iostat', '-n', '1' '-C'], stdout=PIPE)
        lines = p.stdout.read().split('\n')
        values = filter(lambda x: len(x), lines[2].split(' '))

        self.addMetric({'NAME':'cpu_user', 'VAL':values[3],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'cpu_system', 'VAL':values[4],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'cpu_idle', 'VAL':values[5],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'load_one', 'VAL':values[6],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'load_five', 'VAL':values[7],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'load_fifteen', 'VAL':values[8],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})


