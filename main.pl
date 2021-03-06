#!/usr/bin/perl -w
# Written 2013 by Bernhard M. Wiedemann
# Licensed under GNU GPL v2

use strict;

use parse;
use bugzilla;

#my $infile=shift || "test.mail";
foreach my $infile (@ARGV)
{
    local $/;
    open(my $f, "<", $infile) or die $!;
    my $content=<$f>;
    close $f;
    my $bugdata=parse::parse_bugmail($content);
    #use Data::Dumper;
    #print Dumper($bugdata);
    print "importing $infile id=$bugdata->{id}\n";
    bugzilla::updatebug($bugdata);
    #unlink $infile; # FIXME danger! (here to avoid re-processing)
}

