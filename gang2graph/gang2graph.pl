#!/usr/bin/env perl
# Drew Stephens <drew@dinomite.net>
# Copyright 2011, Clearspring, Inc.
# 
# This is free software; you can redistribute it and/or modify it under
# the same terms as the Perl 5 programming language system itself.
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

# Socket for sending to Graphite
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
$graphiteSocket->close();

sub getXMLFromSocket {
    my $socket = IO::Socket::INET->new(
        PeerHost    => $gangliaHost,
        PeerPort    => $gangliaPort,
    ) or die "Couldn't connect to " . $gangliaHost . ':' . $gangliaPort . " - $!\n";

    my $xml = '';
    my $part = '';
    my $recvSize = 1024;
    $socket->recv($part, $recvSize);

    # Accumulate the XML file from the socket
    my $chunk = 0;
    while ($part ne '' && $chunk < 1_000_000) {
        $xml .= $part;
        $socket->recv($part, $recvSize);
        $chunk++
    }

    return $xml;
}

1;
