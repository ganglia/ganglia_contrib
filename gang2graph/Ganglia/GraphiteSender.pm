# Drew Stephens <drew@dinomite.net>
# Copyright 2011, Clearspring, Inc.
#
# This is free software; you can redistribute it and/or modify it under
# the same terms as the Perl 5 programming language system itself.
use warnings;
use strict;
use v5.10;
package Ganglia::GraphiteSender;

use base qw(XML::SAX::ExpatXS);
our @ISA = ('XML::SAX::ExpatXS');

use Carp qw/croak/;
use IO::Socket::INET;

my $debug = 0;

sub new {
    my $class = shift;
    my %params = @_;

    my $self = {
        grid    => '',
        cluster => '',
        host    => '',
        metric  => {
            name    => '',
            val     => '',
        },

        skipHost    => 0,

        now     => time,
        socket  => $params{socket},
        include_hosts   => defined $params{include_hosts} ? $params{include_hosts} : '.',
        metrics => 0,
    };

    bless $self, $class;
    return $self;
}

sub start_element {
    my ($self, $data) = @_;

    # Move along if we're skipping this host
    return if ($self->{skipHost} == 1);

    if ($data->{LocalName} eq 'METRIC') {
        $self->_handleMetric($data);
    } elsif ($data->{LocalName} eq 'HOST') {
        # Skip hosts that aren't in the includeHosts list
        unless (grep {$data->{Attributes}->{'{}NAME'}->{Value} =~ /$_/} @{$self->{includeHosts}}) {
            $self->{skipHost} = 1;
            return;
        }
        # Skip hosts that are in the excludeHosts list
        if (grep {$data->{Attributes}->{'{}NAME'}->{Value} =~ /$_/} @{$self->{excludeHosts}}) {
            $self->{skipHost} = 1;
            return;
        }

        $self->_handleHost($data);
    } elsif ($data->{LocalName} eq 'GRID') {
        $self->_handleGrid($data);
    } elsif ($data->{LocalName} eq 'CLUSTER') {
        $self->_handleCluster($data);
    }
}

sub end_element {
    my ($self, $data) = @_;

    if ($data->{LocalName} eq 'METRIC') {
    } elsif ($data->{LocalName} eq 'HOST') {
        # Reset the skipHost flag
        $self->{skipHost} = 0 if ($data->{LocalName} eq 'HOST');
    } elsif ($data->{LocalName} eq 'GRID') {
        print "Ending grid " . $self->{grid} . "\n" if ($debug);
    } elsif ($data->{LocalName} eq 'CLUSTER') {
        print "  Ending cluster " . $self->{cluster} . "\n" if ($debug);
    }
}

sub end_document {
    my ($self, $data) = @_;
    $self->{socket}->close();
    print "Processed " . $self->{metrics} . " metrics\n" if ($debug);
}

sub _handleGrid {
    my ($self, $data) = @_;
    $self->{grid} = $data->{Attributes}->{'{}NAME'}->{Value};
    $self->{grid} =~ s/ /_/g;
    print "Starting grid " . $self->{grid} . "\n" if ($debug);
}

sub _handleCluster {
    my ($self, $data) = @_;
    $self->{cluster} = $data->{Attributes}->{'{}NAME'}->{Value};
    $self->{cluster} =~ s/ /_/g;
    print "  Starting cluster " . $self->{cluster} . "\n" if ($debug);
}

sub _handleHost {
    my ($self, $data) = @_;
    $self->{host} = $data->{Attributes}->{'{}NAME'}->{Value};
    $self->{host} =~ s/ /_/g;
    print "    Host " . $self->{host} . "\n" if ($debug);
}

sub _handleMetric {
    my ($self, $data) = @_;
    my $name = $data->{Attributes}->{'{}NAME'}->{Value};
    my $val = $data->{Attributes}->{'{}VAL'}->{Value};

    # Graphite doesn't do non-numeric things
    if ($val !~ /^[0-9.]*$/) {
        return;
    }

    my $graphiteString = $self->{grid} . '.' . $self->{cluster} . '.' .
            $self->{host} . '.' . "$name $val " . $self->{now} . "\n";
    my $socket = $self->{socket};
    print $socket $graphiteString;
    print "        $graphiteString" if ($debug > 1);

    $self->{metrics}++;
}

1;
