#
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
Core metrics for Linux

Tested on  Linux Kernel 2.6.27.7.11, Ubuntu 8.10
"""

from subprocess import Popen, PIPE
from time import time

from metric import metric

class metric_proc(metric):
    def interval(self):
        return 80

    def gather(self, tree):
        # slow'n'dumb way of doing this
        # an alternate would be to list /proc
        # and count number of "files' that are "numbers"
        p = Popen(['ps', 'ax'],  stdout=PIPE)    
        lines = p.stdout.read().split('\n')
        self.addMetric({'NAME':'proc_total', 'VAL':len(lines) -1,
                        'TYPE':'uint32', 'UNITS':'', 'TMAX':950,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})    
        
        # now get running processes
        f = open('/proc/stat', 'rb')
        line = f.read().split('\n')
        f.close()

        proc_run = -1
        for line in lines:
            if line.startswith('procs_running'):
                proc_run = int(line.split()[1])
                break
        if proc_run != -1:
            self.addMetric({'NAME':'proc_run', 'VAL':proc_run,
                            'TYPE':'uint32', 'UNITS':'', 'TMAX':950,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

class metric_sys_clock(metric):
    def interval(self):
        return 1200

    def gather(self, tree):
        self.addMetric({'NAME':'sys_clock', 'VAL':int(time()),
                        'TYPE':'timestamp', 'UNITS':'s', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})    

class metric_cpu(metric):
    def interval(self):
        return 20

    def gather(self, tree):
        sysctls = [ 'sysctl',
                    'kernel.ostype',
                    'kernel.osrelease',
                    ]
        p = Popen(sysctls, stdout=PIPE)
        lines = p.stdout.read().split('\n')
        os_name = lines[0].split(' ')[1]
        os_release = lines[1].split(' ')[2]
        self.addMetric({'NAME':'os_name', 'VAL':os_name,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})

        self.addMetric({'NAME':'os_release', 'VAL':os_release,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})


        f = open('/proc/uptime', 'rb')
        lines = f.read()
        f.close()
        boottime = int(time() - float(lines.split(' ')[0]))
        self.addMetric({'NAME':'boottime', 'VAL': boottime,
                        'TYPE':'uint32', 'UNITS':'KB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})

        f = open('/proc/cpuinfo', 'rb')
        lines = f.read().split('\n')
        f.close()

        cpu_num = 0
        cpu_speed = 0
        for line in lines:
            pos = line.find(':')
            if pos != -1:
                k = line[0:pos].strip()
                v = line[pos+1:]
                if k.startswith('processor'):
                    cpu_num += 1
                elif k.startswith('cpu MHz'):
                    # for whatever reason CPUs frequently aren't
                    # nice whole numbers.
                    # use round so you don't have a CPU of 2599
                    cpu_speed = int(round(float(v.strip())))

        if cpu_num > 0:
            self.addMetric({'NAME':'cpu_num', 'VAL': cpu_num,
                            'TYPE':'uint32', 'UNITS':'', 'TMAX':1200,
                            'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})        
        if cpu_speed > 0:
            self.addMetric({'NAME':'cpu_speed', 'VAL': cpu_speed,
                            'TYPE':'uint32', 'UNITS':'MHz', 'TMAX':1200,
                            'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})
            
        # machine type.  gmond hardwires stuff at compile time with
        # a few types.  This is more dynamic
        p = Popen(['uname', '-m'], stdout=PIPE)
        line = p.stdout.read()
        machine_type = line.strip()
        self.addMetric({'NAME':'machine_type', 'VAL':machine_type,
                        'TYPE':'string', 'UNITS':'', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'zero', 'SOURCE':'gmond'})
         
class metric_net(metric):
    last_time = -1

    def interval(self):
        return 40

    def gather(self, tree):
        now = time()
        interval = now - self.last_time

        f = open('/proc/net/dev', 'rb')
        lines = f.read().split('\n')
        f.close()

        bytes_out = 0
        packets_out = 0
        bytes_in = 0
        packets_in = 0

        for line in lines[2:]:
            if not len(line):
                continue
            interface = line[0:7]
            if interface == 'lo':
                # skip loopback interface?
                continue

            fields = line[7:].split()
            bytes_in     += int(fields[0])
            packets_in   += int(fields[1])
            bytes_out    += int(fields[8])
            packets_out  += int(fields[9])
        
        # Ideally you'd just return total_out and total_in
        # and let RRD figure out bytes/sec using a COUNTER
        # and call it a day

        # BUT, oddly  "official" gmond returns bytes per second 
        # which seems odd.  So sadly, we have do all this nonsense
        if self.last_time == -1:
            self.last_time        = now
            self.last_bytes_out   = bytes_out
            self.last_bytes_in    = bytes_in
            self.last_packets_out = packets_out
            self.last_packets_in  = packets_in
            return
        
        bytes_out_bps   = float(bytes_out   - self.last_bytes_out)   / interval
        bytes_in_bps    = float(bytes_in    - self.last_bytes_in)    / interval
        packets_out_bps = float(packets_out - self.last_packets_out) / interval
        packets_in_bps  = float(packets_in  - self.last_packets_in)  / interval

        self.last_time = now
        self.last_bytes_out   = bytes_out
        self.last_bytes_in    = bytes_in
        self.last_packets_out = packets_out
        self.last_packets_in  = packets_in

        self.addMetric({'NAME':'bytes_in', 'VAL':bytes_in_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})
        self.addMetric({'NAME':'bytes_out', 'VAL':bytes_out_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})
        self.addMetric({'NAME':'pkts_in', 'VAL':packets_in_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})
        self.addMetric({'NAME':'pkts_out', 'VAL':packets_out_bps,
                        'TYPE':'float', 'UNITS':'bytes/sec',
                        'TMAX':300, 'DMAX': 0, 'SLOPE':'both',
                        'SOURCE':'gmond'})

class metric_mem(metric):
    """
    boh
    """

    def interval(self):
        return 60

    def gather(self, tree):

        f = open('/proc/meminfo', 'rb')
        lines = f.read().split('\n')
        f.close()
        swap_total  = -1
        swap_free   = -1
        mem_total   = -1
        mem_cached  = -1
        mem_buffers = -1
        mem_free    = -1

        # tbd
        mem_shared  = -1

        for line in lines:
            if line.startswith('SwapTotal'):
                swap_total = int(line.split()[1])
            elif line.startswith('SwapFree'):
                swap_free = int(line.split()[1])
            elif line.startswith('MemTotal'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree'):
                mem_free  = int(line.split()[1])
            elif line.startswith('Cached'):
                mem_cached = int(line.split()[1])
            elif line.startswith("Buffers"):
                mem_buffers = int(line.split()[1])

        if swap_total != -1:
            self.addMetric({'NAME':'swap_total','VAL' : swap_total,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if swap_free != -1:
            self.addMetric({'NAME':'swap_free', 'VAL' : swap_free,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if mem_cached != -1:
            self.addMetric({'NAME':'mem_cached', 'VAL' : mem_cached,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if mem_total != -1:
            self.addMetric({'NAME':'mem_total', 'VAL' : mem_total,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if mem_free != -1:
            self.addMetric({'NAME':'mem_free', 'VAL' : mem_free,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if mem_buffers != -1:
            self.addMetric({'NAME':'mem_buffers', 'VAL' : mem_buffers,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        if mem_shared != -1:
            self.addMetric({'NAME':'mem_shared', 'VAL' : mem_shared,
                            'TYPE':'uint32', 'UNITS':'KB', 'TMAX':180,
                            'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

class metric_disk(metric):
    def interval(self):
        return 40

    def gather(self, tree):
        """
        Only reads FIRST disk right now...
        """

        p = Popen(['df', '-m', '/'], stdout=PIPE)
        lines = p.stdout.read().split('\n')

        fields = lines[1].split()
        disk_total = float(fields[1]) /  1024.0
        disk_free  = float(fields[3]) /  1024.0

        self.addMetric({'NAME':'disk_total', 'VAL' : disk_total,
                        'TYPE':'double', 'UNITS':'GB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        self.addMetric({'NAME':'disk_free', 'VAL' : disk_free,
                        'TYPE':'double', 'UNITS':'GB', 'TMAX':1200,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

class metric_iostat(metric):
    last_time = -1
    cpus = []

    def interval(self):
        return 20

    def gather(self, tree):
        f = open('/proc/stat', 'rb')
        line = f.readline()
        f.close()

        fields = line.split()
        cpus = [int(fields[1]), int(fields[2]), int(fields[3]),int(fields[4])]

        if self.last_time == -1:
            self.last_time = time()
            self.cpus = cpus
            return

        # convert to zip
        cpu_diff = [float(cpus[i] - self.cpus[i]) for i in range(4)]
        cpu_sum = float(sum(cpu_diff))
        cpu_percent = [ 100.0* cpu_diff[i]/ cpu_sum for i in range(4) ]
        self.addMetric({'NAME':'cpu_user', 'VAL': cpu_percent[0],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'cpu_nice', 'VAL': cpu_percent[1],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'cpu_system', 'VAL':cpu_percent[2],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'cpu_idle', 'VAL':cpu_percent[3],
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})

        f = open('/proc/loadavg', 'rb')
        line = f.read().split(' ')
        f.close()

        load_one = float(line[0])
        load_five = float(line[1])
        load_fifteen = float(line[2])

        self.addMetric({'NAME':'load_one', 'VAL':load_one,
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'load_five', 'VAL':load_five,
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})
        self.addMetric({'NAME':'load_fifteen', 'VAL':load_fifteen,
                        'TYPE':'float', 'UNITS':'%', 'TMAX':90,
                        'DMAX':0, 'SLOPE':'both', 'SOURCE':'gmond'})


