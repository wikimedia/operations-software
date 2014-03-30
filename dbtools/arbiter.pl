#!/usr/bin/perl
#
# If you're trying to save the cluster during an outage, don't
# use this :-) Instead go to:
#
# https://wikitech.wikimedia.org/wiki/MySQL#Killing_queries
#
# For a while we used pt-kill jobs to catch problems on slaves.
# That's still a good tool for emergencies and maintenance, but
# something a little more subtle in approach and able to deal
# intelligently with the foibles of MediaWiki and terbium and 
# the snapshot* hosts, was needed.

$|++;

use strict;
use DBI;
use Socket;
use Digest::MD5 qw(md5 md5_hex md5_base64);

my $cnf  = "~/.my.cnf";

my $host = "";
my $port = "3306";

foreach my $arg (@ARGV)
{
	if ($arg =~ /^--config=(.+)$/)
	{
		$cnf = $1;
	}
	elsif ($arg =~ /^--host=(.+)$/)
	{
		$host = $1;
	}
}

unless ($host ne "") { die("require host"); }

if ($host =~ /^([^:]+):([0-9]+)$/)
{
	$host = $1;
	$port = $2;
}

my $db = DBI->connect("DBI:mysql:;host=${host};port=${port};mysql_read_default_file=${cnf}", undef, undef,
	{ RaiseError => 1 }) or die("${host} db?");

$db->do("SET NAMES 'utf8'");

my $only_selects = "and info is not null"
	." and lower(info) regexp '^[[:space:]]*select'"
	." and not lower(info) regexp 'wikiexporter'"
	." and not lower(info) regexp 'master_pos_wait'"; 

while (1)
{
	my $utc = gmtime();
	my $kill = $db->prepare("kill ?");

	# wikiuser slow queries get killed at 300s
	# time < 1000000 mariadb 5.5 bug allows new connections to be 2147483647 briefly
	my $kills = $db->prepare("select * from information_schema.processlist"
		." where command = 'Query' and time > 300 and time < 1000000 and user = 'wikiuser'"
		." $only_selects order by time desc");
	$kills->execute;

	while (my $row = $kills->fetchrow_hashref)
	{
		$utc = gmtime();
		my $tid = $row->{ID};
		my $sql = $row->{INFO};
		my $sec = $row->{TIME};
		$kill->execute($tid);
		print "$utc -- kill $tid ${sec}s $sql\n";
	}

	# Note: We could set wait_timeout much lower than 28800s, but blunt instruments like that
	# treat all users equally and often just obscure bugs in application code. Let's be more
	# subtle in our approach.

	# Note: XtraDB has innodb_kill_idle_transaction. That would be a neater way of solving
	# problems like excessive purge lag, or lock-wait timeouts on commonswiki master, but
	# that doesn't solve sleepers taking up connection slots. Eg, bugs 62303 and 63058.
	# We should probably use both.

	# wikiuser sleepers get killed at 300s
	my $kills = $db->prepare("select * from information_schema.processlist"
		." where command = 'Sleep' and time > 300 and time < 1000000 and user = 'wikiuser'"
		." and info is null order by time desc");
	$kills->execute;

	while (my $row = $kills->fetchrow_hashref)
	{
		$utc = gmtime();
		my $tid = $row->{ID};
		my $sec = $row->{TIME};
		$kill->execute($tid);
		print "$utc -- kill $tid ${sec}s (sleep)\n";
	}

	# wikiuser sleeper overload: Too many connections taken up by sleepersfor sme reason. Kill the oldest.
	my $count = $db->prepare("select count(*) as n from information_schema.processlist"
		." where command = 'Sleep' and time > 30 and time < 1000000 and user = 'wikiuser' and info is null");
	$count->execute;
	my $row = $count->fetchrow_hashref;

	if ($row->{n} > 30)
	{
		$utc = gmtime();

		my $n = $row->{n};
		print "$utc -- $n sleepers\n";

		# wikiuser sleepers
		my $kills = $db->prepare("select * from information_schema.processlist"
			." where command = 'Sleep' and time > 30 and time < 1000000 and user = 'wikiuser'"
			." and info is null order by time desc limit 30");
		$kills->execute;

		while (my $row = $kills->fetchrow_hashref)
		{
			$utc = gmtime();
			my $tid = $row->{ID};
			my $sec = $row->{TIME};
			$kill->execute($tid);
			print "$utc -- kill $tid ${sec}s (sleep)\n";
		}
	}	

	# general overload: Active query count is high. Find out why... 
	my $count = $db->prepare("select count(*) as n from information_schema.processlist"
		." where command = 'Query' and info is not null");
	$count->execute;
	my $row = $count->fetchrow_hashref;

	if ($row->{n} > 75)
	{
		$utc = gmtime();

		my $n = $row->{n};
		print "$utc -- $n active\n";

		# slow wikiuser: Kill of stuff running over 60s. We normally don't complain about
		# slow stuff until 300s mark, but thise server is running hot, so be nastier.
		my $kills = $db->prepare("select * from information_schema.processlist"
			." where command = 'Query' and time > 60 and time < 1000000 and user = 'wikiuser'"
			." $only_selects order by time desc limit 25");
		$kills->execute;

		my $kill = $db->prepare("kill ?");
		while (my $row = $kills->fetchrow_hashref)
		{
			$utc = gmtime();
			my $tid = $row->{ID};
			my $sql = $row->{INFO};
			my $sec = $row->{TIME};
			$kill->execute($tid);
			print "$utc -- kill $tid ${sec}s $sql\n";
		}

		# storm of identical queries: Something is causing a single query to spike, which isn't
		# a useful way of getting a faster response from an overloaded DB server. Log and kill.
		my $list = $db->prepare(
			"select group_concat(id) as ids, info, count(id) as n, md5(concat(db,' ',info)) as q"
			." from information_schema.processlist"
			." where command = 'Query' and time > 5 and time < 1000000"
			." $only_selects group by q having n > 5"
		);
		$list->execute;

		while (my $row = $list->fetchrow_hashref)
		{
			$utc = gmtime();
			my $sql = $row->{info};
			print "$utc -- kill duplicates $sql\n";
			
			my @ids = split /,/, $row->{ids};
			foreach (@ids) {
				my $tid = $_;
				print "$utc -- kill $tid\n";
				$kill->execute($tid);
			}
		}
	}

	sleep 1;
}
