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
        hosts   => defined $params{hosts} ? $params{hosts} : '.',
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
        # Skip hosts that aren't in the list of hosts to proces
        unless (grep {$data->{Attributes}->{'{}NAME'}->{Value} =~ /$_/} @{$self->{hosts}}) {
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
        #print "Ending grid " . $self->{grid} . "\n";
    } elsif ($data->{LocalName} eq 'CLUSTER') {
        #print "Ending cluster " . $self->{cluster} . "\n";
    }
}

sub end_document {
    my ($self, $data) = @_;
    $self->{socket}->close();
    #print "Processed " . $self->{metrics} . " metrics\n";
}

sub _handleGrid {
    my ($self, $data) = @_;
    $self->{grid} = $data->{Attributes}->{'{}NAME'}->{Value};
    #print "Starting grid " . $self->{grid} . "\n";
}

sub _handleCluster {
    my ($self, $data) = @_;
    $self->{cluster} = $data->{Attributes}->{'{}NAME'}->{Value};
    #print "Starting cluster " . $self->{cluster} . "\n";
}

sub _handleHost {
    my ($self, $data) = @_;
    $self->{host} = $data->{Attributes}->{'{}NAME'}->{Value};
    #print "Host " . $self->{host} . "\n";
}

sub _handleMetric {
    my ($self, $data) = @_;
    my $name = $data->{Attributes}->{'{}NAME'}->{Value};
    my $val = $data->{Attributes}->{'{}VAL'}->{Value};

    my $graphiteString = $self->{grid} . '.' . $self->{cluster} . '.' .
            $self->{host} . '.' . "$name $val " . $self->{now} . "\n";
    my $socket = $self->{socket};
    print $socket $graphiteString;

    $self->{metrics}++;
}

1;
