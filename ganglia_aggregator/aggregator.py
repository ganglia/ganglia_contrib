import os
import re
from sets import Set
import socket
import xml.parsers.expat

# the aggregator was written to be used from within chef, generating the
# list of clusters and metrics to be aggregated from attributes in other
# chef recipes. It can, however, be used standalone by manually configuring
# the clusters at the bottom of the file.
#
# In this file you'll find both examples of chef attributes to set as well
# as how to set the hashes directly.


# reads chef attributes indicating metrics to aggregate across a group
# reports the aggregated metrics spoofed to a host named all_$groupname
#
# Options to include in the chef attributes:
#    name: the name of the metric to aggregate
#    pattern: (optional) a regex to use to identify the source metrics
#              if absent, the 'name' field is used instead
#              it's a good idea to include ^ and $ to bound your pattern
#    aggregator: the operation to use to aggregate metrics
#                can be AVG, MAX, MIN, or SUM
#    units: the label to put on the Y axis of the generated graph
#
# Example attributes
#   {
#           "name" => "nginx_total_90th",
#           "aggregator" => "AVG",
#           "units" => "eps"
#   },
#   {
#           "name" => 'haproxy_\\1_hits',
#           "pattern" => '^haproxy_(.+)_hits$',
#           "aggregator" => "SUM",
#           "units" => "hits/sec"
#   },


class GangliaAggregator:
    AVG = 'AVG'
    SUM = 'SUM'
    MAX = 'MAX'
    MIN = 'MIN'
    def __init__(self, metrics, cluster_map):
        """Creates a ganglia aggregator that uses cluster_map to find the ports
          of the collector for a cluster and aggregates the metrics provided
          in metrics.  metrics is a dictionay of cluster name to an array of
          [<metric_name>, AVG | SUM | MAX | MIN, <units>, <metric pattern>]."""
        self._cluster_map = cluster_map
        self._tracked_metrics = metrics
        # Compile the regular expressions in each metric
        for cluster in self._tracked_metrics:
            for metric in self._tracked_metrics[cluster]:
                metric[3] = re.compile(metric[3])

        # a name like foo_\1 might turn into several foo_bar metrics. this
        # is a reverse index of foo_bar -> foo_\1
        self._expanded_names = {}

        # This is a tmp variable that is used to accumulate the data
        # while we are parsing the xml.  The key is the metric_pattern
        # and the value will be an array of the raw data points.
        self._accumulated_values = {}
        self._metric_units = {}

    def grab_xml(self, cluster):
        """Grabs the xml of the metrics for a given cluster."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', self._cluster_map[cluster]))
        full_data = ''
        data = s.recv(1024)
        while data:
            full_data += data
            data = s.recv(1024)
        s.close()
        return full_data


    # Any time the name includes "\x" where x is a digit, we will replace
    # replace that part of the name with the value from the regex caputure
    # (matches are 0-indexed; in this example \1 matches (\[a-zA-Z]+)), not \d+
    # i.e. name: push_expansion_trace_\1_duration_avg
    #      pattern: push_expansion_\d+_trace_(\[a-zA-Z]+)_duration_avg
    #      wil match push_expansion_1_trace_YieldDevice_duration_avg and
    #      aggregate it in push_expansion_trace_YieldDevice_duration_avg
    def metric_name(self, name, re_match):
        captures = re_match.groups(())
        for n in xrange(len(captures)):
            name = name.replace('\\%i' % (n + 1), captures[n])
        return name

    def handle_start(self, cluster, name, attrs):
        """Handles a start tag for a given cluster.  name is the name of the
           tag (the only one that we care about is METRIC).  attrs is the
           attributes for the tag."""
        if not name == 'METRIC':
            return
        metric_name = attrs['NAME']
        tracked_metrics = self._tracked_metrics[cluster]
        keys_to_update = []
        for x in tracked_metrics:
            match = x[3].match(metric_name)
            if match:
                expanded_name = self.metric_name(x[0], match)
                if x[0] not in self._expanded_names:
                    self._expanded_names[x[0]] = []
                if expanded_name not in self._expanded_names[x[0]]:
                    self._expanded_names[x[0]].append(expanded_name)
                keys_to_update.append(expanded_name)

        if len(keys_to_update) == 0:
            return

        value = float(attrs['VAL'])
        for key in Set(keys_to_update):
            if key not in self._accumulated_values:
              self._accumulated_values[key] = []
            self._accumulated_values[key].append(value)
            self._metric_units[key] = attrs['UNITS']


    def parse_xml(self, cluster, xmlstring):
        """Parses the given xmlstring for a cluster and compute the aggregate
           the metrics."""
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = (
                lambda name, attrs: self.handle_start(cluster, name, attrs))
        parser.Parse(xmlstring)

    def proccess_cluster(self, cluster):
        """Process the metrics for a given cluster."""
        if not self._tracked_metrics.has_key(cluster):
            print 'Skipping %s because no metrics are needed' % cluster
            return
        if not self._cluster_map.has_key(cluster):
            print 'Unknown cluster %s' % cluster
            return
        self._accumulated_values = {}
        self._metric_units = {}

        xml_string = self.grab_xml(cluster)
        self.parse_xml(cluster, xml_string)

        config_file = '/etc/ganglia/gmond_collector_%s.conf' % cluster
        tracked_metrics = self._tracked_metrics[cluster]
        for base_name, aggregator, units, pattern in tracked_metrics:
            if base_name not in self._expanded_names:
                continue
            for expanded_name in self._expanded_names[base_name]:
                try:
                    values = self._accumulated_values[expanded_name]
                except KeyError:
                    values = [0] 
                total = sum(values)
                if aggregator == GangliaAggregator.AVG and len(values) > 0:
                    total = total / len(values)
                elif aggregator == GangliaAggregator.MAX and len(values) > 0:
                    total = max(values)
                elif aggregator == GangliaAggregator.MIN and len(values) > 0:
                    total = min(values)
                metric_name = '%s_%s' % (expanded_name, aggregator)
                try:
                    if self._metric_units[expanded_name] != "":
                        units = self._metric_units[expanded_name]
                except KeyError:
                    #use the existing value for units
                    pass

                values = {
                    'config' : config_file,
                    'value' : total,
                    'name' : metric_name,
                    'units' : units,
                    'type' : 'float',
                    'spoof' : 'all_%s:all_%s' %(cluster, cluster)
                }
                command = "gmetric -c %(config)s -n '%(name)s' -v %(value)f " % values
                command += "-u %(units)s -S %(spoof)s -t %(type)s" % values
                os.system(command)

    def process_all(self):
        for key in self._tracked_metrics.keys():
            self.proccess_cluster(key)

cluster_map = {
    # format is 'cluster_name' : port
    'default' : 8649
}
metrics = {
    'default' : [
        # format is ['new_metric_name', 'op', 'y axis label', 'metric regex to match']
        # new_metric_name will have op appended eg load_one_SUM
        ['load_one', 'SUM', 'load', '^load_one$'],
        ['cpu_user', 'AVG', '%', '^cpu_user$']
        ]
}

# Uncomment the following to use this from within chef.
# cluster_map = {
#     <% @clusters.each do |name, port| %>
#     '<%= name %>' : <%= port %>,
#     <% end %>
# }
# metrics = {
#     <% @metrics.each do |cluster, values| %>
#     '<%= cluster %>' : [ <% values.each do |metric| %>
#             [r'<%= metric[0] %>', '<%= metric[1] %>', '<%= metric[2] %>', '<%= metric[3] %>'],<% end %>
#             ],
#     <% end %>
# }

aggregator = GangliaAggregator(metrics, cluster_map)
aggregator.process_all()
