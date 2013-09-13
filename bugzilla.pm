# Written 2013 by Bernhard M. Wiedemann
# Licensed under GNU GPL v2

package bugzilla;
use DBI;

our %sevmap = (Cri=>1, Maj=>2, Nor=>3, Min=>4, Enh=>5);
our %statemap = (NEW=>1, ASSIGNED=>2, NEEDINFO=>3, RESOLVED=>4, VERIFIED=>5, CLOSED=>6, REOPENED=>7);

my $dbhost="192.168.235.1";
my $connectionInfo="dbi:mysql:bernhard_bugzilla;$dbhost";
my $dbuser="bernhard";
my $dbpasswd="xxx";
eval `cat ~/.dbpasswd`;
our $dbh = DBI->connect($connectionInfo,$dbuser,$dbpasswd);

sub mapdata($)
{
    my $bugdata = shift;
    my %d = (id=>$bugdata->{id}, descr=>$bugdata->{descr}, updated_at=>$bugdata->{date});
    
    my $assign = $bugdata->{AssignedTo};
    if($assign) {$d{assign}=$assign}

    my $pri = $bugdata->{Priority};
    if($pri) { $pri=~s/^P(\d).*/$1/ or die "bad prio $pri"; $d{pri}=$pri+0}

    my $sev = $bugdata->{Severity};
    if($sev) { $d{sev}=$sevmap{substr($sev,0,3)} or die "bad sev $sev";}

    my $state = $bugdata->{Status};
    if($state) { $d{state}=$statemap{$state} or die "bad state $state"}

    if($bugdata->{new}) { $d{created_at}=$d{updated_at} }

    return \%d;
}

sub updatebug($)
{
    my $bugdata = shift;
    my $newdata = mapdata($bugdata);
#    use Data::Dumper;
#    print Dumper($bugdata, $newdata);
#die "debug";

    if($bugdata->{new}) {
	# using a hash slice to fill in newdata values in the right order
	$dbh->do("INSERT INTO bugs VALUES (?,?,?,?,?,?,?,?)", {}, @{$newdata}{qw(id state sev pri descr assign created_at updated_at)});
    } else {
	my(@set,@sqlparams);
	foreach my $k (keys(%$newdata)) {
	    next if $k eq "id";
	    my $v=$newdata->{$k};
	    push(@set, "$k=?");
	    push(@sqlparams, $v);
	}
	my $sql = join(",", @set);
	#print "UPDATE bugs SET $sql WHERE id=? @sqlparams";
	$dbh->do("UPDATE bugs SET $sql WHERE id=?", {}, @sqlparams, $newdata->{id});
    }

}

1;
