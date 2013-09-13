#!/usr/bin/perl -w
# Written 2011-2013 by Bernhard M. Wiedemann
# Licensed under GNU AGPL v3

# TODO: add extra bonus levels as reward for good bug-handling

use strict;
use CGI ":standard";
require LWP::Simple;
use DBI;
use List::Util "shuffle";

our $dbh;
my $dbhost="192.168.235.1";
my $connectionInfo="dbi:mysql:bernhard_bugzilla;$dbhost";
my $dbuser="bernhard";
my $dbpasswd="xxx";
eval `cat ~/.dbpasswd`;
$dbh = DBI->connect($connectionInfo,$dbuser,$dbpasswd);

our %sevmap=(Cri=>1, Maj=>2, Nor=>3, Min=>4, Enh=>5);

if(0) {
	$dbh->do(
"CREATE TABLE `bernhard_bugzilla`.`bugs` (
`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY ,
`state` TINYINT NOT NULL DEFAULT '0',
`sev` TINYINT NOT NULL ,
`pri` TINYINT NOT NULL ,
`descr` VARCHAR( 255 ) NOT NULL ,
`assign` VARCHAR( 255 ) NOT NULL ,
`created_at` INT NOT NULL,
`updated_at` INT NOT NULL,
 INDEX (
`assign`
),
 INDEX (
`updated_at`
),
 FULLTEXT (
 `descr`
 )
) ENGINE = MYISAM 
");
}

print header(),start_html(-title=>"Bugzilla Mirror", -head=>['<meta name="robots" content="index, nofollow"/>', Link({-rel=>"shortcut icon", -href=>"/favicon.ico"}), Link({-rel=>"icon", -type=>"image/png", -href=>"http://static.opensuse.org/themes/bento/images/favicon.png"})]);

our $keepoptions="";

sub bnclink($)
{my $id=shift;
	qq{<a href="https://bugzilla.novell.com/show_bug.cgi?id=$id">bug $id</a>};
}

sub showbug($)
{ my $bugref=shift;
	my ($id,$state,$sev,$pri,$descr,$assign, $created, $updated)=@$bugref;
	print bnclink($id)." state=$state sev=$sev pri=$pri assigned=$assign descr=$descr<br/>\n";
}

sub getbug($)
{ my $bncid=shift;
	$dbh->selectrow_arrayref("SELECT * FROM `bugs` WHERE id=?", {}, $bncid);
}

sub sanitizenum($)
{ $_[0]=~s/\D//g;}

sub note($)
{
	return qq{<span style="color:red">@_</span><br/>\n};
}

my $numbugs=15;
my $groupsize=100;
my @cond;
my @condvars=();

if(my $t=param("topic")) {
	$keepoptions.="&amp;topic=$t";
	$t=~s/^[^%]/%$&/; $t=~s/[^%]$/$&%/;
	push(@cond, " ( descr LIKE ? OR assign LIKE ? ) ");
	push(@condvars, $t, $t);
}
my %since=(0=>"ever", 1=>"a day", 7=>"a week", 31=>"a month", 122=>"4 months", 365=>"a year" );
my $since=param("since");
if(!defined($since)) {$since=122; param("since",$since)}
if($since) {
	push(@cond, " ( updated_at > ? ) ");
	push(@condvars, time-($since*24*60*60));
}
if(!defined($since{$since})) { $since{$since}="custom" }
my $cond="";
if(@cond) {
	$cond="WHERE ".join(" AND ", @cond);
}

print start_form(-method=>"GET"),
	"since ",popup_menu(-name=>"since", -values=>[sort {$a<=>$b} keys %since], -labels=>\%since),"  ; ",
	textfield(-name=>"topic")," limit topic -&gt; ",
	qq{<input type="submit" value="filter">},br,end_form;

my $r=$dbh->selectall_arrayref("SELECT * FROM bugs $cond ORDER BY `id` DESC LIMIT ?", {}, @condvars, $groupsize);
if($r) {
	my $n=@$r;
# this is supposed to improve shuffling with less bugs
	if($n<$groupsize && $n>=$numbugs*1.5) {$r=[@$r[0..int($n/2)]]};
# have the same list for same users
	#my $ip=$ENV{REMOTE_ADDR}; $ip=~s/[.:]//g; srand($ip);
	my @randbugs=shuffle(@$r);
	print h1("Listing $numbugs/$n random bugs");
	my $max=@randbugs;
	$max=$numbugs if($max>$numbugs);
	foreach my $b (@randbugs[0..$max-1]) {
		showbug($b);
	}
	print h2("How To Use This Tool")."
This Tool was created to mirror openSUSE bugzilla bugs for easy access
<ul>
<li>Optional: limit the area you are interested in by typing a term like gnome or firefox into the topic textfield on top and click filter</li>
</ul>";
} else {
	print "DB error";
}

if(param("source")) {
	print "<blockquote>This CGI's Source: <pre>".
		`cat $ENV{SCRIPT_FILENAME}`.
		"</pre></blockquote>";
}
print br.a({-href=>"?source=1"}, "view CGI source");
print br."source coude is tracked ".a({-href=>"https://github.com/bmwiedemann/bugzillamirror"}, "on github");

print end_html();

