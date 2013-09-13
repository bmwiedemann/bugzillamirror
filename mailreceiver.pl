#!/usr/bin/perl -w
my $spool="/home/bugzilla/spool";
my $tmp="$spool/mail.$$";
open(my $t, ">", $tmp) or die $!;
while(<>) {
	print $t $_;
}
close $t;
chdir "/home/bernhard/bugzillamirror";
system("./main.pl", $tmp);
unlink $tmp;
