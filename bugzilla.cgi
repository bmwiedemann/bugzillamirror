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
our %cache=();
our $n=1;
sub add_cache($)
{ my $url=shift;
	my $list=LWP::Simple::get($url);
	$list=~s{.*</th>}{}s;
	my @a=split("</tr>", $list);
	foreach(@a) {
		my($bugid,$descr,$sev,$pri,$assign);
		m/show_bug.cgi\?id=(\d+)/ && ($bugid=$1);
		m{(.+)\s+</td>\s*$} && ($descr=$1);
		m{<span title="([^"]+)">\1\n} && ($assign=$1);
		m{<span title="P(\d) - [^"]+">P\1 \n} && ($pri=$1);
		m{class="bz_([CEMN][ainor][hijnr])"} && ($sev=$sevmap{$1});
#		s/[<>]/&lt;/g;
		$_="";
		next unless $bugid && $descr;
		$assign||="?";
		$sev||=0;
		$pri||=0;
		$_="$bugid $descr";
		$cache{$bugid}=$descr;
		if(param("insert")) {
			$dbh->do("INSERT INTO bugs VALUES (?,?,?,0,?,?,?,0)", {}, $bugid, ++$n, $descr, $sev, $pri, $assign);
		}
	}
#	print join("<hr/>", @a);
}

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

if(my $bncid=param("skip")) {
	sanitizenum($bncid);
	print note("skipped bug $bncid.");
	#addprio($bncid, $skipprio);
}
if(my $bncid=param("take")) {
	sanitizenum($bncid);
	my $b=getbug($bncid);
	if($b) {
		my $dbprio=$b->[1];
		#print param("prio")." vs $dbprio\n<br>";
		if(param("prio")+200 >= $dbprio) {
			print note("reserved ".bnclink($bncid)." for you.");
			#addprio($bncid, $takeprio);
			#marktaken($bncid,1);
		} else {
			print note(bnclink($bncid)." already taken. Please choose another one.");
		}
	}
}


if(param("stats")) {
		my $r=$dbh->selectall_arrayref("SELECT id FROM bugs");
		if($r) {
			foreach my $b (@$r) {
				print "$b->[0] ";
			}
		}
}
# http://aw.lsmod.de/cgi-bin/public/openbugs?update=1&insert=1
if(param("update")) {
	if(1) {
		#add_cache("https://bugzilla.novell.com/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=NEEDINFO&bug_status=REOPENED&chfield=[Bug%20creation]&chfield=assigned_to&chfield=bug_severity&chfield=bug_status&chfield=component&chfield=infoprovider&chfield=keywords&chfield=op_sys&chfield=priority&chfield=product&chfield=resolution&chfield=short_desc&chfield=version&chfield=votes&chfieldto=2010-12-31&classification=openSUSE&product=openSUSE%2010.2&product=openSUSE%2010.3&product=openSUSE%2011.0&product=openSUSE%2011.1&product=SUSE%20LINUX%2010.0&product=SUSE%20Linux%2010.1&query_format=advanced&order=assigned_to%2Cbug_severity%2Cpriority%2Cbug_status%2Cbug_id&query_based_on=");
#	add_cache("https://bugzilla.novell.com/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=NEEDINFO&bug_status=REOPENED&classification=openSUSE&product=openSUSE%2011.4&query_format=advanced&version=Milestone%201%20of%206&version=Milestone%202%20of%206&version=Milestone%203%20of%206&version=Milestone%204%20of%206&version=Milestone%205%20of%206&order=bug_id&query_based_on=");
#	add_cache("https://bugzilla.novell.com/buglist.cgi?classification=openSUSE&chfieldto=2010-12-31&query_format=advanced&chfieldfrom=2010-07-01&bug_status=NEW&bug_status=ASSIGNED&bug_status=NEEDINFO&bug_status=REOPENED&version=Factory&product=openSUSE%2011.4");
	}
}

my $numbugs=9;
my $groupsize=100;
my @cond;
my @condvars=();

if(my $t=param("topic")) {
	$keepoptions.="&amp;topic=$t";
	$t=~s/^[^%]/%$&/; $t=~s/[^%]$/$&%/;
	push(@cond, " ( descr LIKE ? OR assign LIKE ? ) ");
	push(@condvars, $t, $t);

#	$cond.=" AND MATCH ( descr, assign ) AGAINST ( ? )";
#	push(@condvars, $t);
}
my %since=(0=>"ever", 1=>"a day", 7=>"a week", 31=>"a month", 122=>"4 months", 365=>"a year" );
my $since=param("since");
if(!defined($since)) {$since=122; param("since",$since)}
if($since) {
	push(@cond, " ( updated_at > ? ) ");
	push(@condvars, time-($since*24*60*60));
}
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
	my $ip=$ENV{REMOTE_ADDR}; $ip=~s/[.:]//g; srand($ip);
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

print end_html();

