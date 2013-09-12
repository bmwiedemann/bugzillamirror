package parse;
use Email::Simple;
use Date::Parse;

sub parse_bugmail($)
{
    my $email = Email::Simple->new($_[0]);

    # process headers
    my $subject = $email->header("Subject");
    return {} if(not $subject or $subject!~m/\[Bug (\d+)\] (.*)/);
    my %data = (id=>$1, descr=>$2);
    my $new=0;
    $data{descr}=~s/^New: // and $new=1;
    $data{new} = $new;
    $data{date} = str2time($email->header("Date"));


    # process body info
    my $body = $email->body;
    # OS+Version Component
    $body=~s#OS/Version#OSVersion#;
    my @lines=split("\n", $body);
    foreach(@lines){s/\015$//} # drop CR from DOS EOLs
    if($new) {
        my $heading;
        for my $i (6..40) {
	    my $l=$lines[$i];
	    last if(!$l); # empty or undef
	    if($l=~m/^\s*([a-zA-Z\/ ]+): (.*)/) {
	    	$heading=$1;
		$data{$heading}=$2;
	    } elsif ($l=~m/\s+(\S.*)/) {
	        die unless defined $heading;
	    	$data{$heading}.=" ".$1; # gather continuation lines
	    } else {
	        $data{debug}=$l;
	    }
	}
    } else {
        if($lines[8] && $lines[8] eq "           What    |Removed                     |Added") {
	    my $heading;
            for my $i (10..40) {
	        my $l=$lines[$i];
		last if($l eq "");
		my @a=split(/\|/, $l);
	    	foreach(@a) {s/^\s+//; s/\s+$//;}
		my $v=$a[2]||"";
		if($a[0]) {
		    $heading=$a[0];
		    $data{$heading}=$v;
		} else {
		    $data{$heading}.=" $v" # continuation lines
		}
	    }
	}
    }

    return \%data;
}

1;
