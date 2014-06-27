#!/usr/bin/perl
#
# Sean's verbose script to manipulate MariaDB slaves.
#
# --switch-sibling-to-child --parent=FQDN:PORT --child=FQDN:PORT
# --switch-child-to-sibling --parent=FQDN:PORT --child=FQDN:PORT
# --stop-siblings-in-sync --host1=FQDN:PORT --host2=FQDN:PORT
#
# !!! NOTE !!! This is not for manipulating masters. Don't try.

use strict;
use DBI;

my $mode = "";
my $cnf  = "~/.my.cnf";

my $parent_host = "";
my $parent_port = "3306";
my $child_host  = "";
my $child_port  = "3306";

my @pvars = ();
my @cvars = ();

foreach my $arg (@ARGV)
{
	if ($arg eq "--switch-sibling-to-child")
	{
		$mode = "--switch-sibling-to-child";
	}
	elsif ($arg eq "--switch-child-to-sibling")
	{
		$mode = "--switch-child-to-sibling";
	}
	elsif ($arg eq "--stop-siblings-in-sync")
	{
		$mode = "--stop-siblings-in-sync";
	}
	elsif ($arg =~ /^--config=(.+)$/)
	{
		$cnf = $1;
	}
	elsif ($arg =~ /^--parent=(.+)$/)
	{
		$parent_host = $1;
	}
	elsif ($arg =~ /^--child=(.+)$/)
	{
		$child_host = $1;
	}
	elsif ($arg =~ /^--host1=(.+)$/)
	{
		$parent_host = $1;
	}
	elsif ($arg =~ /^--host2=(.+)$/)
	{
		$child_host = $1;
	}
	elsif ($arg =~ /^--parent-set=(.+)$/)
	{
		push(@pvars, $1);
	}
	elsif ($arg =~ /^--child-set=(.+)$/)
	{
		push(@cvars, $1);
	}
}

unless ($mode ne "") { die("require mode"); }
unless ($parent_host and $child_host) { die("require two hosts"); }

if ($parent_host =~ /^([^:]+):([0-9]+)$/)
{
	$parent_host = $1;
	$parent_port = $2;
}

if ($child_host =~ /^([^:]+):([0-9]+)$/)
{
	$child_host = $1;
	$child_port = $2;
}

my $parent = DBI->connect("DBI:mysql:;host=${parent_host};port=${parent_port};mysql_read_default_file=${cnf}", undef, undef)
	or die("${parent_host} db?");
my $child  = DBI->connect("DBI:mysql:;host=${child_host};port=${child_port};mysql_read_default_file=${cnf}",  undef, undef)
	or die("${child_host} db?");

$parent->do("SET NAMES 'utf8';");
$child->do("SET NAMES 'utf8';");

foreach (@pvars) {
	$parent->do("set $_");
}

foreach (@cvars) {
	$child->do("set $_");
}

my $pstatus = $parent->prepare("show slave status");
my $cstatus = $child->prepare("show slave status");

$pstatus->execute;
my $parent_status = $pstatus->fetchrow_hashref;

$cstatus->execute;
my $child_status = $cstatus->fetchrow_hashref;

my $times = 0;

sub clean_up()
{
	$parent->do("start slave");
	$child->do("start slave");
}

sub get_status()
{
	$pstatus->execute;
	$parent_status = $pstatus->fetchrow_hashref;

	$cstatus->execute;
	$child_status = $cstatus->fetchrow_hashref;
}

sub check_both_running()
{
	&get_status;

	unless ($parent_status->{Slave_IO_Running} == "Yes"
		and $parent_status->{Slave_SQL_Running} == "Yes") {
		die("${parent_host}:${parent_port} state not running");
	}

	unless ($child_status->{Slave_IO_Running} == "Yes"
		and $child_status->{Slave_SQL_Running} == "Yes") {
		die("${child_host}:${child_port} state not running");
	}
}

sub check_both_stopped()
{
	&get_status;

	unless ($parent_status->{Slave_IO_Running} == "No"
		and $parent_status->{Slave_SQL_Running} == "No") {
		die("${parent_host}:${parent_port} state still running");
	}

	unless ($child_status->{Slave_IO_Running} == "No"
		and $child_status->{Slave_SQL_Running} == "No") {
		die("${child_host}:${child_port} state still running");
	}
}

sub stop_sibs_in_sync()
{
	print "Checking relationship...\n";

	&check_both_running;

	if ($parent_status->{Relay_Master_Log_File} eq $child_status->{Relay_Master_Log_File}
		and $parent_status->{Exec_Master_Log_Pos} eq $child_status->{Exec_Master_Log_Pos}
		and $parent_status->{Slave_SQL_Running} eq "No"
		and $child_status->{Slave_SQL_Running} eq "No") {
		print "Slaves already stopped in sync\n";
		return;
	}

	unless ($child_status->{Master_Host} eq $parent_status->{Master_Host}
		and $child_status->{Master_Port} eq $parent_status->{Master_Port}) {
		die("${child_host}:${child_port} is not a sibling of ${parent_host}:${parent_port}");
	}

	unless ($parent_status->{Slave_IO_Running} eq "Yes"
		and $parent_status->{Slave_SQL_Running} eq "Yes") {
		die("${parent_host}:${parent_port} slave not running");
	}

	unless ($child_status->{Slave_IO_Running} eq "Yes"
		and $child_status->{Slave_SQL_Running} eq "Yes") {
		die("${child_host}:${child_port} slave not running");
	}

	unless ($parent_status->{Seconds_Behind_Master} < 5) {
		die("${parent_host}:${parent_port} is lagging");
	}

	unless ($child_status->{Seconds_Behind_Master} < 5) {
		die("${child_host}:${child_port} is lagging");
	}

	print "Stopping slaves...\n";

	$child->do("stop slave");

	# parent get a little ahead
	sleep(3);

	$parent->do("stop slave");

	&get_status;

	unless ($child_status->{Slave_IO_Running}  eq "No"
		and $child_status->{Slave_SQL_Running} eq "No") {
		&clean_up;
		die("${child_host}:${child_port} slave did not stop");
	}

	unless ($parent_status->{Slave_IO_Running}  eq "No"
		and $parent_status->{Slave_SQL_Running} eq "No") {
		&clean_up;
		die("${parent_host}:${parent_port} slave did not stop");
	}

	my $log_file = $parent_status->{Relay_Master_Log_File};
	my $log_pos  = $parent_status->{Exec_Master_Log_Pos};

	print "Starting ${child_host}:${child_port} until ${log_file} ${log_pos}...\n";

	$child->do("start slave until master_log_file = ?, master_log_pos = ${log_pos}", undef, $log_file);

	&get_status;

	for ($times = 0; $times < 5 and $child_status->{Slave_SQL_Running} eq "Yes"; $times++)
	{
		sleep(1);
		&get_status;
	}

	unless ($parent_status->{Relay_Master_Log_File} eq $child_status->{Relay_Master_Log_File}
		and $parent_status->{Exec_Master_Log_Pos} == $child_status->{Exec_Master_Log_Pos}
		and $parent_status->{Slave_SQL_Running} eq "No"
		and $child_status->{Slave_SQL_Running} eq "No") {
		&clean_up;
		die("${child_host}:${child_port} START SLAVE UNTIL apparently failed");
	}

	$child->do("stop slave io_thread");

	&check_both_stopped;

	print "Slaves stoped in sync.\n";
}

if ($mode eq "--switch-sibling-to-child")
{
	print "Make ${child_host}:${child_port} a child of ${parent_host}:${parent_port}? y/n";
	unless (<STDIN> =~ /^y/) { die("abort"); }

	&stop_sibs_in_sync;

	my $mstatus = $parent->prepare("show master status");

	$mstatus->execute();
	my $master_status = $mstatus->fetchrow_hashref;

	my $parent_log_file = $master_status->{File};
	my $parent_log_pos  = $master_status->{Position};

	print "Changing ${child_host}:${child_port} master to ${parent_log_file}, ${parent_log_pos}...\n";

	$child->do(
		"change master to master_host = ?, master_port = ${parent_port}, master_log_file = ?, master_log_pos = ${parent_log_pos}",
		undef, $parent_host, $parent_log_file
	);

	&get_status;

	unless ($child_status->{Master_Host} eq $parent_host
		and $child_status->{Master_Port} eq $parent_port) {
		&clean_up;
		die("${child_host}:${child_port} change master failed");
	}

	print "Restarting slaves threads...\n";

	$parent->do("start slave");
	$child->do("start slave");

	# IO thread time to connect
	sleep(3);

	&get_status;

	unless ($child_status->{Master_Host} eq $parent_host
		and $child_status->{Master_Port} == $parent_port
		and $child_status->{Slave_IO_Running}  eq "Yes"
		and $child_status->{Slave_SQL_Running} eq "Yes") {
		&clean_up;
		die("${child_host}:${child_port} slave not running");
	}

	&check_both_running;

	print "Success!\n";
}
elsif ($mode eq "--switch-child-to-sibling")
{
	print "Make ${child_host}:${child_port} a sibling of ${parent_host}:${parent_port}? y/n";
	unless (<STDIN> =~ /^y/) { die("abort"); }

	print "Checking relationship...\n";

	&check_both_running;

	unless ($child_status->{Master_Host} eq $parent_host and $child_status->{Master_Port} eq $parent_port) {
		die("${child_host}:${child_port} is not a slave of ${parent_host}:${parent_port}");
	}

	unless ($child_status->{Seconds_Behind_Master} < 10) {
		die("${child_host}:${child_port} is lagging");
	}

	print "Stopping slaves...";

	$parent->do("stop slave");
	print "parent...";

	&get_status;

	for ($times = 0; $times < 5 and $child_status->{Seconds_Behind_Master} > 0; $times++)
	{
		sleep(1);
		&get_status;
	}

	unless ($child_status->{Seconds_Behind_Master} < 1) {
		&clean_up;
		die("${child_host}:${child_port} failed to catch up");
	}

	$child->do("stop slave");
	print "child\n";

	&check_both_stopped;

	my $master_host     = $parent_status->{Master_Host};
	my $master_port     = $parent_status->{Master_Port};
	my $master_log_file = $parent_status->{Relay_Master_Log_File};
	my $master_log_pos  = $parent_status->{Exec_Master_Log_Pos};

	print "Changing ${child_host}:${child_port} master to ${master_log_file}, ${master_log_pos}...\n";

	$child->do(
		"change master to master_host = ?, master_port = ${master_port}, master_log_file = ?, master_log_pos = ${master_log_pos}",
		undef, $master_host, $master_log_file,
	);

	print "Restarting slaves threads...\n";

	$parent->do("start slave");
	$child->do("start slave");

	# IO thread time to connect
	sleep(3);

	&get_status;

	unless ($child_status->{Master_Host} eq $parent_status->{Master_Host}
		and $child_status->{Master_Port} eq $parent_status->{Master_Port}
		and $child_status->{Slave_IO_Running}  eq "Yes"
		and $child_status->{Slave_SQL_Running} eq "Yes") {
		&clean_up;
		die("${child_host}:${child_port} slave not running");
	}

	&check_both_running;

	print "Success!\n";
}
elsif ($mode eq "--stop-siblings-in-sync")
{
	print "Stop ${child_host}:${child_port} and ${parent_host}:${parent_port} in sync? y/n";
	unless (<STDIN> =~ /^y/) { die("abort"); }

	&stop_sibs_in_sync;

	print "Success!\n";
}