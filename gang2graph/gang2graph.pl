#!/usr/bin/env perl
use warnings;
use strict;
use v5.10;
package App::Gang2Graph;

use Getopt::Long;
use IO::Socket::INET;
use XML::SAX::ParserFactory;

use Ganglia::GraphiteSender;

my $gangliaHost = 'localhost';
my $gangliaPort = 8651;
my $graphiteHost = 'localhost';
my $graphitePort =  2023;
# Set of hostname regexes that will be sent from Ganglia to Graphite
my $hosts = ['.'];

my $xml = getXMLFromSocket();

my $graphiteSocket = IO::Socket::INET->new(
        PeerHost    => $graphiteHost,
        PeerPort    => $graphitePort,
    ) or die"Couldn't connect to " . $graphiteHost . ':' . $graphitePort . " - $!\n";

my $parser = XML::SAX::ParserFactory->parser(
                Handler => Ganglia::GraphiteSender->new(
                    socket  => $graphiteSocket,
                    hosts   => $hosts,
                ),
            );
$parser->parse_string($xml);

sub getXMLFromSocket {
    my $socket = IO::Socket::INET->new(
        PeerHost    => $gangliaHost,
        PeerPort    => $gangliaPort,
    ) or die "Couldn't connect to " . $gangliaHost . ':' . $gangliaPort . " - $!\n";

    my $xml;
    my $part;
    my $recvSize = 1048576;
    $socket->recv($part, $recvSize);

    my $limit = 100000;
    while ($part ne '' && $limit > 0) {
        $socket->recv($part, $recvSize);
        $xml .= $part;
        $limit--;
    }

    return $xml;
}

1;
