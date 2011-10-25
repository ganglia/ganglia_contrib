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

    if ($data->{LocalName} eq 'GRID') {
        $self->_handleGrid($data);
    } elsif ($data->{LocalName} eq 'CLUSTER') {
        $self->_handleCluster($data);
    } elsif ($data->{LocalName} eq 'HOST') {
        # Skip hosts that aren't in the list of hosts to proces
        unless (grep {$data->{Attributes}->{'{}NAME'}->{Value} =~ /$_/} @{$self->{hosts}}) {
            $self->{skipHost} = 1;
            return;
        }

        $self->_handleHost($data);
    } elsif ($data->{LocalName} eq 'METRIC') {
        $self->_handleMetric($data);
    }
}

sub end_element {
    my ($self, $data) = @_;

    # Reset the skipHost flag
    $self->{skipHost} = 0 if ($data->{LocalName} eq 'HOST');
}

sub end_document {
    my ($self, $data) = @_;
    $self->{socket}->close();
    #print "Processed " . $self->{metrics} . " metrics\n";
}

sub _handleGrid {
    my ($self, $data) = @_;
    $self->{grid} = $data->{Attributes}->{'{}NAME'}->{Value};
}

sub _handleCluster {
    my ($self, $data) = @_;
    $self->{cluster} = $data->{Attributes}->{'{}NAME'}->{Value};
}

sub _handleHost {
    my ($self, $data) = @_;
    $self->{host} = $data->{Attributes}->{'{}NAME'}->{Value};
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
