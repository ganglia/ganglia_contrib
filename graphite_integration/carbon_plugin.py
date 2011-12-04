#/*******************************************************************************
#* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
#* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#* IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#* ARE DISCLAIMED. IN NO EVENT SHALL Novell, Inc. OR THE CONTRIBUTORS
#* BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#* CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#* SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#* INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#* CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#* ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#* POSSIBILITY OF SUCH DAMAGE.
#*
#* Authors: Avishai Ish-Shalom (avishai AT fewbytes.com)
#*
#* This is a gmetad-python plugin for sending metrics to carbon-cache.
#******************************************************************************/

import logging
import socket
import pickle
import struct
import string

from Gmetad.gmetad_plugin import GmetadPlugin
from Gmetad.gmetad_config import getConfig, GmetadConfig

def get_plugin():
    ''' All plugins are required to implement this method.  It is used as the factory
        function that instanciates a new plugin instance. '''
    # The plugin configuration ID that is passed in must match the section name 
    #  in the configuration file.
    return CarbonPlugin('carbon-writer')

class CarbonPlugin(GmetadPlugin):
    ''' This class implements a carbon plugin which sends metrics to carbon-cache via line reciever'''
    
    _strucFormat = '!I'
    MAX_METRICS_PER_OP = 20
    _tr_table = string.maketrans(" .", "__")

    def __init__(self, cfgid):
        logging.debug("Initializing carbon-writer plugin")
        self.cfg = None
        self.carbon_socket = None
        self._resetConfig()
        
        logging.debug("Initialized carbon writer plugin")
        # The call to the parent class __init__ must be last
        GmetadPlugin.__init__(self, cfgid)

    def _resetConfig(self):
        self.sendMetrics = self._sendTextMetrics
        self.carbon_host = None
        self.carbon_port = None

    def _parseConfig(self, cfgdata):
        logging.debug("Parsing configdata %s" % cfgdata)
        for kw, args in cfgdata:
            if hasattr(self, '_cfg_' + kw):
                getattr(self, '_cfg_' + kw)(args)
            else:
                raise Exception('Wrong configuration directive %s' % kw)

    def _cfg_host(self, host):
        if ":" in host:
            host, port = host.split(":", 1)
            self._cfg_port(port)
        self.carbon_host = host

    def _cfg_port(self, port):
        self.carbon_port = int(port)

    def _cfg_protocol(self, protocol):
        protocol = protocol.lower().strip()
        if protocol == "pickle":
            self.sendMetrics = self._sendPickledMetrics
        elif protocol == "text" or protocol == "line" or protocol == "plain":
            self.sendMetrics = self._sendTextMetrics
        else:
            raise Exception("Unknown protocol type %s" % protocol)

    @classmethod
    def _carbonEscape(cls, s):
        if type(s) is not str: str(s)
        return s.translate(cls._tr_table)

    def _connectCarbon(self):
        self._closeConnection()
        logging.debug("Connecting to carbon at %s:%d" % (self.carbon_host, self.carbon_port))
        if self.carbon_host is None or self.carbon_port is None:
            logging.warn("can't connect. carbon host: %s, port %d" % (self.carbon_host, self.carbon_port))
            return
        try:
            self.carbon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            self.carbon_socket.connect((self.carbon_host, self.carbon_port))
        except socket.error as e:
            if not e.errno == 106:
                raise e
        logging.debug("Connected to carbon at %s:%d" % (self.carbon_host, self.carbon_port))

    def _closeConnection(self):
        if self.carbon_socket:
            logging.debug("Closing connection to carbon")
            self.carbon_socket.shutdown(socket.SHUT_RDWR)
            self.carbon_socket.close()
            self.carbon_socket = None

    def _sendPickledMetrics(self, metrics):
        # the pickle protocol used by carbon works by packing metrics into a list/tuple, each item packed as:
        # (metric_name, (timstamp, value))
        try:
            # we use sendall because we trust items won't be unpickled if something bad happens. worse case we lose entire metrics batch.
            logging.info("Sending pickled data to carbon")
            logging.debug("Metrics (dump):\n%s" % metrics)
            data = pickle.dumps(
                    # convert metrics to (metric_name, (timestamp, value)) format
                    [(metric_name, (timestamp, value)) for (metric_name, timestamp, value) in metrics],
                    protocol=-1
                    )
            data = struct.pack(self._strucFormat, len(data)) + data
            total_sent_bytes = 0
            while total_sent_bytes < len(data):
                sent_bytes = self.carbon_socket.send(data[total_sent_bytes:])
                if sent_bytes == 0: raise Exception("Zero bytes sent, connection error?")
                logging.debug("Sent %d bytes to carbon" % sent_bytes)
                total_sent_bytes += sent_bytes
            logging.debug("Done sending pickled data to carbon")

        except Exception as e:
           logging.error("Failed to send metrics to carbon:\n%s" % e)
           self._connectCarbon()
    
    def _sendTextMetrics(self, metrics):
        for metric in metrics:
            try:
                logging.debug("Sending text data to carbon")
                self.carbon_socket.sendall(" ".join(metric))
            except Exception as e:
                logging.error("Failed to send metrics to carbon:\n%s" % e)
                self._connectCarbon()

    def start(self):
        '''Called by the engine during initialization to get the plugin going.'''
        logging.debug("Starting plugin carbon-writer")
        self._connectCarbon()
    
    def stop(self):
        '''Called by the engine during shutdown to allow the plugin to shutdown.'''
        logging.debug("Stopping plugin carbon-writer")
        self._closeConnection()

    def notify(self, clusterNode):
        '''Called by the engine when the internal data source has changed.'''
        # Get the current configuration
        if 'GRID' == clusterNode.id:
            # we don't need aggregation by GRID, this can be easily done in grpahite
            return
        gmetadConfig = getConfig()
        # Find the data source configuration entry that matches the cluster name
        for ds in gmetadConfig[GmetadConfig.DATA_SOURCE]:
            if ds.name == clusterNode.getAttr('name'):
                break
        if ds is None:
            logging.info('No matching data source for %s'%clusterNode.getAttr('name'))
            return
        try:
            if clusterNode.getAttr('status') == 'down':
                return
        except AttributeError:
            pass

        # Update metrics for each host in the cluster
        self.sendMetrics([
                (".".join(
                    ("ganglia", self._carbonEscape(clusterNode.getAttr('name')),
                        self._carbonEscape(hostNode.getAttr('name')),
                        metricNode.getAttr('name'))
                        ), # metric name
                    int(hostNode.getAttr('REPORTED')) + int(metricNode.getAttr('TN')), float(metricNode.getAttr('VAL')))
                    for hostNode in clusterNode
                    for metricNode in hostNode
                if metricNode.getAttr('type') not in ('string', 'timestamp' )
                ]
        )

