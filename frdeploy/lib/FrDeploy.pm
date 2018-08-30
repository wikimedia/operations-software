package FrDeploy;
use strict;
use Cwd;
use Fcntl ':mode';
use File::Copy;
use File::Find::Rule;
use File::Path 'remove_tree';
use IO::Select;
use IPC::Open3;
use Sys::Syslog;
use Storable;


sub affirm {
	my ($question,$y,$default) = @_;
	my ($indent,$qq) = ($question =~ /^(\s*)(\S.*)$/);
	my $qd = $default ? " ($default)" : '';
	print "\n${indent}[1m${qq}${qd}:[0m ";
	while (1) {
		chomp(my $input = <STDIN>);
		$input = $default if $default and $input eq '';
		if ($input =~ /^$y/) {
			return 'yes';
		} elsif ($input eq 'n') {
			return 'no';
		} else {
			print $indent . "[1mHuh? [ $y / n ]$qd:[0m ";
		}
	}
}


# attributes are set based on preferences for the specified project
# $check_file is relative to $project->{'install'}
sub check_attribs {
	my ($project,$check_file) = @_;

	# get file attributes on disk
	my $check_target = $check_file ? "$project->{'install'}/$check_file" : $project->{'install'};
	my ($check_mode,$check_uid,$check_gid) = (stat($check_target))[2,4,5];
	my $check_perms = sprintf "%04o", Fcntl::S_IMODE($check_mode) if $check_mode;

	# get configured default file attributes
	my ($set_perms,$check_type);
	my $set_uid = getpwnam($project->{'attr'}->[1]);
	my $set_gid = getgrnam($project->{'attr'}->[2]);
	if (-l $check_target) { # hack, posix macro doesn't seem to work as expected
		return;
	} elsif (S_ISREG($check_mode)) { # regular files get 'file' mode
		$set_perms = sprintf "%04o", $project->{'attr'}->[0];
		$check_type = 'file';
	} elsif (S_ISDIR($check_mode)) { # directories get 'dir' mode
		$set_perms = sprintf "%04o", $project->{'attr'}->[3];
		$check_type = 'dir';
	} else { # don't touch symlinks, etc
		return;
	}

	# override default attributes if we have specific file attributes configured
	# look for nonrecursive globbed file/directory name matches
	for (keys %{$project->{'files'}}) {
		if ($check_type eq $project->{'files'}->{$_}->[0]) {
			my $rx = glob_to_rx_pattern($_);
			if ($check_file =~ /$rx/) {
				$set_perms = sprintf "%04o", $project->{'files'}->{$_}->[1];
				$set_uid = getpwnam($project->{'files'}->{$_}->[2]);
				$set_gid = getgrnam($project->{'files'}->{$_}->[3]);
			}
		}
	}

	# adjust attributes if necessary
	unless (($set_uid eq $check_uid) and ($set_gid eq $check_gid) and ($set_perms eq $check_perms)) {

		# informative output kthx
		my $print_file = $check_file ? $check_file : './';
		print "   $print_file $set_perms:" . getpwuid($set_uid) . ':' . getgrgid($set_gid) . "\n";

		# set permissions
		chmod(oct($set_perms), $check_target) or print "   couldn't chmod file $!\n";

		# set ownership
		chown($set_uid, $set_gid, $check_target) or print "   couldn't chown file $!\n";

	}
}


# check if running as the configured local_user, otherwise croak
sub check_user {
	my $program = shift;
	unless ($ENV{'USER'} eq $program->{'local_user'}) {
		fatal($program, "$program->{'ident'} must run as user $program->{'local_user'}, try:\n" .
			"sudo -u $program->{'local_user'} $0 " . join(' ', @ARGV));
	}
}


# print debug output
sub debug {
	my $cmd = shift;
	$cmd =~ s/([0-9a-f]{10})[0-9a-f]{1,30}/$1/g;
	print " [34m> $cmd[0m\n";
}


# perform a git action, print output (and possibly die) if there's anything on stderr
sub execute_git {
	my ($program,$args) = @_;
	my $o = execute_shell($program,['/usr/bin/git',@{$args}]);
	for my $line (@{$o}) {
		if ($line->{'stderr'}) {
			fatal($program,$line->{'stderr'}) if $line->{'stderr'} =~ /^fatal/;
			print " [31m$line->{'stderr'}[0m\n";
		}
	}
	return $o;
}


# use IO::Select to loop through the output of open3 continuously cycling
# open3 filehandles until there is no more output on any of them
# return an array of ordered output, split into stdout vs stderr
sub execute_shell {
	my ($program,$command) = @_;
	my $r;
	debug(getcwd . '$ ' . join(' ', @{$command})) if defined $program->{'debug'};
	$SIG{'INT'} = 'IGNORE';
	my $child_pid = IPC::Open3::open3(*W, *R, *E, @{$command});
	close W;
	my ($selector) = IO::Select->new();
	$selector->add(*R,*E);
	while (1) {
		last if scalar ($selector->handles) == 0;
		my @ready = $selector->can_read (1);
		for my $fh (@ready) {
			my $ffh = fileno $fh;
			if (eof $fh) {
				$selector->remove($fh);
				next;
			}
			chomp(my $line = scalar <$fh>);
			my $filehandle = ($ffh == fileno E) ? 'stderr' : 'stdout';
			push @{$r}, { $filehandle => $line };
		}
	}
	close R;
	close E;
	$SIG{'INT'} = 'DEFAULT';
	return $r;
}


# print alarming message and exit with error
sub fatal {
	my ($program,$message) = @_;
	print "\n[31m$message[0m\n";
	print "[31myou may get more info if you rerun with debug output enabled[0m\n\n";
	exit 1;
}


## fetch a file from a different commit
sub extract_temp_file {
	my ($program,$file,$commit) = @_;
	my $temp_file = "/tmp/$$." . substr($commit,0,10) . '.lint';
	debug(getcwd . "\$ git show $commit:'$file' > $temp_file") if defined $program->{'debug'};
	open my $gx, "-|", '/usr/bin/git', ('show',"$commit:$file") or print "failed: $!";
	if (tell $gx != -1) {
		open my $fx, "> $temp_file";
		print $fx $_ while <$gx>;
		close $fx;
	}
	close $gx;
	return $temp_file if -e $temp_file;
}


# unroll sync arguments into individual project->host specifications
sub get_jobs_from_sync_args {
	my ($sync,$chunk,$jobs) = @_;
	my ($targets,$projects,$match);
	return unless $chunk =~ /^([\w\-,]+):([\w\-,]+)$/;
	for (split /,/,$1) {
		$targets->{$_} = 1;
	}
	for (split /,/,$2) {
		$projects->{$_} = 1;
	}
	for my $role (keys %{$sync}) {
		for my $host (@{$sync->{$role}->{'hosts'}}) {
			if ((defined $targets->{'ALL'}) or (defined $targets->{$role}) or (defined $targets->{$host})) {
				for my $project (@{$sync->{$role}->{'projects'}}) {
					if ((defined $projects->{$project}) or (defined $projects->{'ALL'})) {
						$jobs->{$host}->{$project} = 1; # define a project->host sync job
						$match->{'target'}->{'ALL'} = 1;
						$match->{'target'}->{$role} = 1;
						$match->{'target'}->{$host} = 1;
						$match->{'project'}->{'ALL'} = 1;
						$match->{'project'}->{$project} = 1;
					}
				}
			}
		}
	}

	my @errors;
	for (sort keys %{$targets}) {
		push @errors, "target $_ doesn't match any projects" unless $match->{'target'}->{$_};
	}
	for (sort keys %{$projects}) {
		push @errors, " project $_ doesn't match any targets" unless $match->{'project'}->{$_};
	}
	if (@errors) {
		print "\n [31m'$chunk': " . join(', ', @errors) . "[0m\n";
	}
	return $jobs;
}

# check out file from target commit to a temporary file in the current directory
# lint check it and returns hash of
# 'report' array of lint output
# use git ls-files to find files in a module or submodule directory
sub get_module_file_list {
	my ($program,$project,$module_dir,$r) = @_;
	my $rel_dir = (defined $module_dir) ? "$project->{'install'}/$module_dir" : $project->{'install'};
	chdir $rel_dir or fatal($program,"can't chdir to $rel_dir: $!");
	my $o = execute_git($program,['ls-files']);
	for my $line (@{$o}) {
		next unless $line->{'stdout'};
		chomp(my $rf = (defined $module_dir) ? "$module_dir/$line->{'stdout'}" : $line->{'stdout'});
		my @subdirs = split '/', $rf;
		for (reverse 0..$#subdirs) {
			my $sd .= join '/', (@subdirs[0..$_]);
			$r->{$sd} = 1;
		}
	}
	return $r;
}


# get the complete list of files that should be on disk, from main project,
# submodules, config tree, postinstall
sub get_project_file_list {

	my ($program,$project) = @_;
	my $r;

	# get project git files, if project itself is in git
	if ($project->{'repo'}) {

		# get file list for main git project
		$r->{'git_files'} = get_module_file_list($program,$project);

		# get file list for git project submodules
		chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");
		my $o = execute_git($program,['submodule','status','--recursive']);
		for my $line (@{$o}) {
			if ($line->{'stdout'} and $line->{'stdout'} =~ /^\s*[0-9a-f]{40}\s([^\(]+)\s+\(/) {
				$r->{'git_files'} = get_module_file_list($program,$project,$1,$r->{'git_files'});
			}
		}
	}

	# check for links or dirs created by postinstall
	my $postinstall;
	if (defined $project->{'postinstall'}) {
		for (@{$project->{'postinstall'}}) {
			my (@arg) = split(/\s+/);
			if ($arg[0] eq 'symlink') {
				$postinstall->{'link'}->{$arg[2]} = 1;
			} elsif ($arg[0] eq 'mkdir') {
				$postinstall->{'dir'}->{$arg[1]} = 1;
			}
		}
	}

	# build a delete queue
	for (File::Find::Rule->relative->in($project->{'install'})) {
		next if /(^|\/)\.git(\/|$)/;
		next if $project->{'versionfile'} and $_ eq $project->{'versionfile'};
		next if $postinstall->{'link'}->{$_} and -l "$project->{'install'}/$_";
		next if $postinstall->{'dir'}->{$_} and -d "$project->{'install'}/$_";
		next if $r->{'git_files'}->{$_};
		if ($project->{'config_dir'} and -e "$project->{'config_dir'}/$_") {
			$r->{'git_files'}->{$_} = 1;
		} elsif ($project->{'tidy'} and $project->{'tidy'} =~ /^(y|auto)$/) {
			my $type = (-d "$project->{'install'}/$_") ? 'dir' : 'file';
			$r->{'extraneous_files'}->{$type}->{$_} = 1;
		}
	}

	return $r;
}


# return a list of submodule+commit for a given parent module+commit
sub get_submodule_list {
	my ($program,$project) = @_;
	my $r;

	# no need to get submodule differences if the submodule revision doesn't change
	return if $project->{'revision'} and $project->{'revision'} eq $project->{'target'};

	chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");

	for my $v ('revision','target') {
		next unless $project->{$v};

		# get submodule list for this version
		my $o = execute_git($program,['ls-tree','--full-tree','-r',$project->{$v}]);
		for my $line (@{$o}) {
			if ($line->{'stdout'} and my ($commit,$name) = $line->{'stdout'} =~/^160000\s+\S+\s+([0-9a-f]{40})\s+(.+)$/) {
				$r->{$name}->{$v}->{'commit'} = $commit;
			}
		}

		# get submodule URL for this version, but don't die() trying
		my $name;
		$o = execute_shell($program,['/usr/bin/git','show',"$project->{$v}:.gitmodules"]);
		for my $line (@{$o}) {
			next unless $line->{'stdout'};
			if ($line->{'stdout'} =~ /^\s+path = (.+)/) {
				$name = $1;
			} elsif ($line->{'stdout'} =~ /^\s+url = (.+)/) {
				$r->{$name}->{$v}->{'url'} = $1 if $r->{$name};
				undef $name;
			}
		}

	}

	return $r if $r;
}


# hack to get md5 checksum for a file on disk
sub getMD5 {
	my $f = shift;
	return (-e $f and `/usr/bin/md5sum "$f"` =~ /^([a-f0-9]+)/) ? $1 : "\0";
}


# determine the current commit
sub git_info {
	my ($program,$project) = @_;
	my $r;
	if (-d "$project->{'install'}/.git") {
		chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");
		$r->{'revision'} = verify_commit_id($program);
	}
	if ($project->{'revision'}) {
		if (not $r->{'revision'}) {
			$r->{'warning'} = 'installed revision (' . substr($project->{'revision'},0,10) . ') was unexpectedly removed';
		} elsif ($r->{'revision'} ne $project->{'revision'}) {
			$r->{'warning'} = 'installed revision (' . substr($project->{'revision'},0,10) .  ') was unexpectedly changed';
		}
	}
	return $r;
}


# this subroutine does git update and revision checks
sub git_update {
	my ($program,$project) = @_;
	my $r;

	# clone/refresh project, disable filemode control recursively
	if (-d "$project->{'install'}/.git") {
		chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");
		if (not defined $project->{'new-revision'} and defined $project->{'revision-lock'}) {
			print " * revision is locked, skipping git fetch\n";
		} else {
			print ' * git fetch';
			print ', lint ' . $project->{'lint'} if $project->{'lint'};
			print "\n";
			execute_git($program,['fetch','--quiet']);
			execute_git($program,['submodule','--quiet','foreach','git fetch --quiet']);
			execute_git($program,['submodule','--quiet','foreach','--recursive','git','config','core.filemode','false']);
		}
	} else {
		print ' * git clone';
		print ', lint ' . $project->{'lint'} if $project->{'lint'};
		print "\n";
		FrDeploy::rmkdir($program,$project->{'dir'});
		chdir $project->{'dir'} or fatal($program,"can't chdir to $project->{'dir'}: $!");
		execute_git($program,['clone','--quiet',$project->{'repo'},'-b',$project->{'branch'},$project->{'install'}]);
		chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");
		execute_git($program,['config','core.filemode','false']);
		execute_git($program,['submodule','--quiet','update','--init','--recursive']);
		execute_git($program,['submodule','--quiet','foreach','--recursive','git','config','core.filemode','false']);
		# adjust attributes for project_subdir
		print " * checking attributes\n";
		check_attribs($project);
	}

	# remove cruft that will get in git's way
	$r = get_project_file_list($program,$project);
	if ($r->{'extraneous_files'}) {
		print " * found extraneous files/dirs in project tree...\n";
		my $interactively_deleted;
		for ((sort keys %{$r->{'extraneous_files'}->{'dir'}}), (sort keys %{$r->{'extraneous_files'}->{'file'}})) {
			$interactively_deleted += remove($project,$_);
		}
		print "\n" if $interactively_deleted;
	}

	# make sure we're starting at the stored revision, and that revision is viable
	$r = git_info($program,$project);
	if ($project->{'revision'} and $project->{'revision'} ne $r->{'revision'}) {
		if (verify_commit_id($program,$project->{'revision'})) {
			execute_git($program,['checkout','--quiet',$project->{'revision'}]);
			execute_git($program,['submodule','--quiet','update','--init','--recursive']);
			execute_git($program,['submodule','--quiet','foreach','--recursive','git','config','core.filemode','false']);
		} else {
			print "   [31mIgnoring stored revision (" . substr($project->{'revision'},0,10) . ") because it isn't in git logs![0m\n";
			delete $project->{'revision'};
		}
	}

	# get latest info from origin(s) and decide the appropriate commit hash to checkout
	my $o = execute_git($program,['log',"remotes/origin/$project->{'branch'}",'-1']);
	if ($o->[0]->{'stdout'} and $o->[0]->{'stdout'} =~ /^commit\s+([0-9a-f]{40})$/) {
		debug("remotes/origin/$project->{'branch'} is $1") if defined $program->{'debug'};
		$project->{'head'} = $1;
	}

	if ($project->{'new-revision'}) {
		if ($project->{'new-revision'} eq 'head') {
			$project->{'target'} = $project->{'head'};
		} elsif (verify_commit_id($program,$project->{'new-revision'})) {
			$project->{'target'} = $project->{'new-revision'};
		} else {
			print "   [31merror: commit $project->{'new-revision'} does not exist in git[0m\n";
		}
	} elsif (defined $project->{'revision-lock'}) {
		# already rev-locked, outcome should be a no-op checkout
		$project->{'target'} = $project->{'revision'};
	} else {
		$project->{'target'} = $project->{'head'};
	}
	undef $r;

	if ($project->{'target'}) {

		# show changes for the main repo
		my $changes_to_review;
		my $pc = preview_changes($program,$project);
		$changes_to_review->{$pc}++ if $pc;

		# show changes for submodules
		my $pmc = preview_module_changes($program,$project);
		if ($pmc->{'changes'}) {
			for (keys %{$pmc->{'changes'}}) {
				$changes_to_review->{$_} += $pmc->{'changes'}->{$_};
			}
		}

		# do confirmation step if there are changes to be reviewed
		my $apply_git_changes;
		if (keys %{$changes_to_review}) {
			print "\n [31m******************************[0m\n",
				" [31m* BEWARE: LINT FOUND ISSUES! *[0m\n",
				" [31m******************************[0m\n" if $changes_to_review->{2};
			my $key = random_key(3);
			$apply_git_changes = affirm("Enter the following 3-digit key to continue. [ $key / n ]",$key);
		} else {
			$apply_git_changes = 'yes';
		}

		# do the actual git stuff
		if ($apply_git_changes eq 'yes') {

			# remove deleted submodules before git complains about doing it
			if ($pmc->{'delete'}) {
				for (sort keys %{$pmc->{'delete'}}) {
					debug(getcwd . "\$ rm -fr $_") if defined $program->{'debug'};
					remove_tree("$project->{'install'}/$_") if -d "$project->{'install'}/$_";
				}
			}

			# fetch specified revision for main module
			execute_git($program,['checkout','--quiet',$project->{'target'}]);

			# synchronize submodules to parent commit
			execute_git($program,['submodule','--quiet','update','--init','--recursive']);

		}

	}

	# make sure we're back in the base dir of the project
	chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");

	# set revision lock file if configured
	if (defined $project->{'versionfile'}) {
		print " * writing revision to $project->{'versionfile'}\n";
		open VF, "> $project->{'versionfile'}" or fatal($program,$!);
		print VF "$project->{'revision'}\n";
		close VF;
	}

	# return current project info
	$r = get_project_file_list($program,$project);
	my $return = git_info($program,$project);
	$return->{'git_files'} = $r->{'git_files'};
	return $return;
}


# convert filename glob characters * and ? to the equivalent regular
# expression, essentially a simpler non-recursive adaptation of the glob2pat
# example from Perl Cookbook
sub glob_to_rx_pattern {
	my $glob = shift;
	my %pattern_map = (
		'*' => '[^\/]*',
		'?' => '[^\/]',
	);
	$glob =~ s{(.)} { $pattern_map{$1} || "\Q$1" }ge;
	my $regex_pattern = '^' . $glob . '$';
	return $regex_pattern;
}


# do lint checks as necessary, return info about results
# 'outcome' (scalar): ok|!!|--
# 'report' (array)
sub lint {
	my ($program,$project,$file,$commit) = @_;
	my (@lint_command,@report,$errors,$r);

	if ($project->{'lint-php'} eq 'y' and $file =~ /\.php$/i) {
		@lint_command = ('/usr/bin/php', '-l');
	} elsif ($project->{'lint-yaml'} eq 'y' and $file =~ /\.yaml$/i) {
		@lint_command = ('/usr/bin/yamllint');
	} else {
		return {'outcome' => '--'};
	}

	# fetch a temp file if we're examining a different commit
	my $lint_file = $commit ? extract_temp_file($program,$file,$commit) : $file;
	push @lint_command, $lint_file if $lint_file;
	my $o = execute_shell($program,\@lint_command);
	for my $line (@{$o}) {
		if ($line->{'stdout'}) {
			$line->{'stdout'} =~ s/^  //; # yamllint indents everything
			push @report, $line->{'stdout'};
		} elsif ($line->{'stderr'}) {
			push @report, "error: $line->{'stderr'}";
			$errors++;
		}
	}

	# munge output into standard response
	if ($errors) {
		$r->{'report'} = \@report;
	} elsif ($project->{'lint-php'} eq 'y' and $file =~ /\.php$/i) {
		$r->{'report'} = \@report unless $report[0] =~ /^No syntax errors/;
	} elsif ($project->{'lint-yaml'} eq 'y' and $file =~ /\.yaml$/i) {
		if (@report and $report[0] eq $lint_file) {
			shift @report;
			pop @report;
		}
		$r->{'report'} = \@report if $#report >= 0;
	}
	$r->{'outcome'} = (defined $r->{'report'}) ? '!!' : 'ok';

	# clean up and return
	unlink $lint_file if $commit;
	return $r;

}


# preview changes, do lint checks as appropriate
# returns:
#   no change: (nothing)
#   change, no error: 1
#   lint error: 2
sub preview_changes {
	my ($program,$project) = @_;
	my ($baseline_commit,$changes,$print_alert);
	my $change_string_length = 0;

	my $display_dir = $project->{'module_subdir'} ? "submodule $project->{'module_subdir'}" : 'root project';

	if (not $project->{'revision'}) {
		print " * $display_dir (absent -> " . substr($project->{'target'},0,10) . ")\n";
		# no comparison revision means we should diff against an empty tree
		# https://stackoverflow.com/questions/14564034/creating-a-git-diff-from-nothing
		$baseline_commit = '4b825dc642cb6eb9a060e54bf8d69288fbee4904';
		debug("using empty tree ref $baseline_commit as baseline for comparison") if defined $program->{'debug'};
	} elsif ($project->{'revision'} =~ /^$project->{'target'}/) {
		print " * $display_dir (" . substr($project->{'target'},0,10) . ")\n";
		return;
	} else {
		print " * $display_dir (" . substr($project->{'revision'},0,10) . " --> " . substr($project->{'target'},0,10) . ")\n";
		$baseline_commit = $project->{'revision'};
	}

	chdir $project->{'install'} or fatal($program, "chdir to '$project->{'install'}' failed: $!");

	# get info on files that changed between commits, with delete/insert counts
	my $o = execute_git($program,['diff','--numstat','-z',$baseline_commit,$project->{'target'}]);
	for my $line (@{$o}) {
		if ($line->{'stdout'}) {
			for (split "\0", $line->{'stdout'}) {
				my ($add,$delete,$file) = split "\t";
				my @changes;
				push @changes, "+$add" if $add =~ /^\d+$/ and $add > 0;
				push @changes, "-$delete" if $delete =~ /^\d+$/ and $delete > 0;
				push @changes, '--' unless $changes[0];
				$changes->{$file} = join ',', @changes;
				$change_string_length = ( length($changes->{$file}) > $change_string_length ) ? length($changes->{$file}) : $change_string_length;
			}
		} elsif ($line->{'stderr'} and $line->{'stderr'} =~ /^fatal/) {
			fatal($program,$line->{'stderr'});
		}
	}

	# lint check modified files and display results
	# do lint check as appropriate, display results
	$o = execute_git($program,['diff','--name-status','-z',$baseline_commit,$project->{'target'}]);
	for my $line (@{$o}) {
		if ($line->{'stdout'}) {
			my @mess = split "\0", $line->{'stdout'};
			while (@mess) {
				my ($status,$file) = (shift @mess, shift @mess);
				my $lint_result = ($status eq 'D') ? {'outcome' => '--'} : lint($program,$project,$file,$project->{'target'});
				my $delta = sprintf("%-${change_string_length}s", $changes->{$file});
				if ($project->{'lint-yaml'} eq 'y' or $project->{'lint-php'} eq 'y') {
					if ($lint_result->{'outcome'} eq '!!') {
						print "   [31m$status $delta $lint_result->{'outcome'} | $file[0m\n";
						$print_alert++;
					} else {
						print "   $status $delta $lint_result->{'outcome'} | $file\n";
					}
					print "    [31m" . join("\n    ", @{$lint_result->{'report'}}) . "[0m\n" if defined $lint_result->{'report'};
				} else {
					print "   $status $delta | $file\n";
				}
			}
		} elsif ($line->{'stderr'} and $line->{'stderr'} =~ /^fatal/) {
			fatal($program,$line->{'stderr'});
		}
	}

	# trigger banner+review or just review depending on errors
	$print_alert ? return 2 : return 1;

}


# show changes for submodules, recursively
# return information on deleted submodules, and most dire change/lint check result
sub preview_module_changes {
	my ($program,$project) = @_;
	my $r;

	chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");

	if (my $submodules = get_submodule_list($program,$project)) {

		for my $name (sort keys %{$submodules}) {

			my $sm;
			$sm->{'target'} = $submodules->{$name}->{'target'}->{'commit'};
			$sm->{'target_url'} = $submodules->{$name}->{'target'}->{'url'};
			if ($submodules->{$name}->{'revision'} and $submodules->{$name}->{'revision'}->{'commit'}) {
				$sm->{'revision'} = $submodules->{$name}->{'revision'}->{'commit'};
			}
			$sm->{'dir'} = $project->{'install'};
			$sm->{'name'} = $name;
			$sm->{'install'} = "$project->{'install'}/$name";
			$sm->{'module_subdir'} = $project->{'module_subdir'} ? "$project->{'module_subdir'}/$name" : $name;
			$sm->{'project_subdir'} = "$project->{'project_subdir'}/$name";
			$sm->{'lint-yaml'} = $project->{'lint-yaml'};
			$sm->{'lint-php'} = $project->{'lint-php'};

			if ($sm->{'revision'} and $sm->{'target'}) {

				if (-l $sm->{'install'} or not -d $sm->{'install'}) {

					print " * submodule $name module isn't properly attached,\n" .
						"   maybe it's in .gitmodules but not in .git/config\n";

				} else {

					# check for changes in this module
					my $pc = preview_changes($program,$sm);
					$r->{'changes'}->{$pc}++ if $pc;

					# check for changes in submodules of the current module
					my $pmc = preview_module_changes($program,$sm);
					if ($pmc->{'changes'}) {
						for (keys %{$pmc->{'changes'}}) {
							$r->{'changes'}->{$_} += $pmc->{'changes'}->{$_};
						}
					}
					if ($pmc->{'delete'}) {
						for (keys %{$pmc->{'delete'}}) {
							$r->{'delete'}->{$_} = 1;
						}
					}

				}
				chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");

			} elsif ($sm->{'target'}) {

				# submodule doesn't exist in current revision, so we have to clone it
				# and do the comparison using an empty branch as a baseline

				# override install stuff for temporary clone
				$sm->{'install'} = "/tmp/$$." . substr($project->{'target'},0,10) .  '.lint';

				# make the temporary clone in /tmp, and set it to the target commit
				chdir '/tmp' or fatal($program,"can't chdir to /tmp: $!");
				execute_git($program,['clone','--quiet',$sm->{'target_url'},$sm->{'install'}]);
				chdir $sm->{'install'} or fatal($program,"can't chdir to $sm->{'install'}: $!");
				execute_git($program,['checkout','--quiet',$sm->{'target'}]);
				execute_git($program,['submodule','--quiet','update','--init','--recursive','--force']);

				# check for changes in this module
				my $pc = preview_changes($program,$sm);
				$r->{'changes'}->{$pc}++ if $pc;

				# clean up
				chdir $project->{'install'} or fatal($program,"can't chdir to $project->{'install'}: $!");
				remove_tree($sm->{'install'});

			} else {

				# submodule gets deleted in this change
				print " * submodule $name (" . substr($sm->{'revision'},0,10) . " --> absent)\n";
				$r->{'delete'}->{$sm->{'module_subdir'}} = 1;

			}

		}

	}

	return $r;
}


sub printlog {
	my ($ident,$msg,$severity) = @_;
	$msg = '' unless $msg;
	$severity = 'info' unless $severity; # notice warning err etc.
	Sys::Syslog::setlogsock('unix');
	Sys::Syslog::openlog($ident,'ndelay,pid','user');
	Sys::Syslog::syslog($severity,$msg);
	Sys::Syslog::closelog();
}


sub print_project_info {
	my $project = shift;
	print "\n[1m$project->{'name'}[0m\n";
	print " repo:       $project->{'repo'}\n" if $project->{'repo'};
	print " branch:     $project->{'branch'}\n" if $project->{'branch'};
	print " install:    $project->{'install'}\n";
	print " autoupdate: $project->{'autoupdate'}\n" if $project->{'autoupdate'} eq 'y';
	print " tidy:       $project->{'tidy'}\n" if $project->{'tidy'} =~ /^(y|auto)$/;
	print " lint:       $project->{'lint'}\n" if $project->{'lint'};
	print " rollback:   " . substr($project->{'rollback'},0,10) . "\n" if $project->{'rollback'};
	if ($project->{'revision'}) {
		print " revision:   " . substr($project->{'revision'},0,10);
		print " (locked)" if $project->{'locked'};
		print "\n";
	}
	print " [31mwarning:    $project->{'warning'}[0m\n" if $project->{'warning'};
}


sub random_key {
	my $length = shift;
	my @tokens = ('a'..'k', 'm', 'o'..'z', 2..9);
	my $key;
	my $i = 0;
	while ($i < $length) {
		$key .= $tokens[rand(@tokens)];
		$i++;
	}
	return $key;
}


sub readconf {

	# hardcoded script config path
	my $config_file = '/etc/FrDeploy.conf';

	# short name for use as script identifier
	my $ident = ($0 =~ /([^\/]+)$/) ? $1 : $0;

	# quick sanity check of privs for config file
	my ($mode,$uid) = (stat($config_file))[2,4];
	my $perms = sprintf "%04o", Fcntl::S_IMODE($mode);
	if ((not S_ISREG($mode) or ($uid != 0) or ($mode & S_IWGRP) or ($mode & S_IWOTH))) {
		fatal({'ident' => $ident}, "$ident will only run if $config_file is owned by root and set go-r.");
	}

	# read config, grab environment variables
	my $conf = do($config_file) or die "can't read $config_file: $@";
	my $project = $conf->{'project_settings'};
	my $program = $conf->{'program_settings'};
	my $sync = $conf->{'sync_settings'};

	# pick up some info about operating environment
	$program->{'ident'} = $ident;
	$program->{'interactive'} = 'y' if (-t STDIN && -t STDOUT);

	# load up previous state if state_file exists
	$program->{'state_file'} = "$program->{'state_dir'}/$ident.state";
	rmkdir($program->{'state_dir'}) unless -d $program->{'state_dir'};
	my $state = Storable::retrieve($program->{'state_file'}) if -e $program->{'state_file'};

	# prepopulate a couple handy config_repository variables
	$program->{'config_repository'}->{'attr'} = $program->{'default_attributes'} unless defined $program->{'config_repository'}->{'attr'};
	$program->{'config_repository'}->{'autoupdate'} = 'y';
	$program->{'config_repository'}->{'install'} = "$program->{'config_repository'}->{'dir'}/$program->{'config_repository'}->{'project_subdir'}";
	$program->{'config_repository'}->{'lint-php'} = 'n' unless $program->{'config_repository'}->{'lint-php'} and $program->{'config_repository'}->{'lint-php'} eq 'y';
	$program->{'config_repository'}->{'lint-yaml'} = 'n' unless $program->{'config_repository'}->{'lint-yaml'} and $program->{'config_repository'}->{'lint-yaml'} eq 'y';
	$program->{'config_repository'}->{'name'} = 'Config Tree';
	$program->{'config_repository'}->{'revision'} = $state->{'Config Tree'}->{'revision'} if $state->{'Config Tree'}->{'revision'};
	$program->{'config_repository'}->{'tidy'} = 'y';
	my @lints;
	push @lints, 'PHP' if $program->{'config_repository'}->{'lint-php'} eq 'y';
	push @lints, 'YAML' if $program->{'config_repository'}->{'lint-yaml'} eq 'y';
	$program->{'config_repository'}->{'lint'} = join(',',@lints) if @lints;

	# prepopulate a couple handy project variables
	my $lc_project;
	for my $proj (keys %{$project}) {
		$project->{$proj}->{'name'} = $proj;
		$project->{$proj}->{'rollback'} = $state->{$proj}->{'rollback'} if $state->{$proj}->{'rollback'};

		# commit ID is stored as 'revision-lock' if revision is locked, otherwise it is stored as 'revision'
		if ($state->{$proj}->{'revision-lock'} and $state->{$proj}->{'revision-lock'} =~ /^[0-9a-f]{40}$/) {
			$project->{$proj}->{'revision-lock'} = $state->{$proj}->{'revision-lock'};
			$project->{$proj}->{'revision'} = $state->{$proj}->{'revision-lock'};
		} elsif ($state->{$proj}->{'revision'} and $state->{$proj}->{'revision'} =~ /^[0-9a-f]{40}$/) {
			$project->{$proj}->{'revision'} = $state->{$proj}->{'revision'};
		}

		# populate a couple handy project variables
		$project->{$proj}->{'install'} = "$project->{$proj}->{'dir'}/$project->{$proj}->{'project_subdir'}";
		$project->{$proj}->{'attr'} = $program->{'default_attributes'} unless defined $project->{$proj}->{'attr'};
		$project->{$proj}->{'config_dir'} = "$program->{'config_repository'}->{'install'}/$proj";
		$project->{$proj}->{'tidy'} = $program->{'tidy'} unless defined $project->{$proj}->{'tidy'};
		$project->{$proj}->{'lint-yaml'} = 'n' unless $project->{$proj}->{'lint-yaml'} and $project->{$proj}->{'lint-yaml'} eq 'y';
		$project->{$proj}->{'lint-php'} = 'n' unless $project->{$proj}->{'lint-php'} and $project->{$proj}->{'lint-php'} eq 'y';
		$project->{$proj}->{'autoupdate'} = 'n' unless $project->{$proj}->{'autoupdate'} and $project->{$proj}->{'autoupdate'} eq 'y';

		my @lints;
		push @lints, 'PHP' if $project->{$proj}->{'lint-php'} eq 'y';
		push @lints, 'YAML' if $project->{$proj}->{'lint-yaml'} eq 'y';
		$project->{$proj}->{'lint'} = join(',',@lints) if @lints;

		# sanity check project location spec
		fatal($program,"no 'project_subdir' defined for $proj") unless $project->{$proj}->{'project_subdir'};

		$lc_project->{lc($proj)}->{$proj} = 1;
	}

	# create a case-insensitive-sort project list
	for my $lc (sort keys %{$lc_project}) {
		for my $proj (sort keys %{$lc_project->{$lc}}) {
			push @{$program->{'sorted_project_list'}}, $proj;
		}
	}

	# sanity check only one role per host
	my $defined_host;
	for my $role (sort keys %{$sync}) {
		for my $host (@{$sync->{$role}->{'hosts'}}) {
			if (defined $defined_host) {
				die "host $host already defined in $defined_host\n";
				$defined_host = $role;
			}
		}
	}

	# Config Tree is a special project for installable configuration files
	# - always refreshed before other projects
	# - doesn't use revision rollback/locking or post-install
	return ($program,$project,$sync);
}


# (optionally) confirm and delete files/directories
sub remove {
	my ($project,$file) = @_;
	return 0 unless -e "$project->{'install'}/$file";
	my $interactively_deleted = 0;
	my $delete;
	if ($project->{'tidy'} eq 'y') {
		print "\n [31m$file is not in git![0m";
		$delete = affirm(" Remove $file? [y/n]",'y','n');
		$interactively_deleted = 1;
	}
	if (($delete eq 'yes') or ($project->{'tidy'} eq 'auto')) {
		if (-d "$project->{'install'}/$file") {
			remove_tree("$project->{'install'}/$file");
		} else {
			unlink "$project->{'install'}/$file";
		}
	}
	return $interactively_deleted;
}


# recursive directory maker
sub rmkdir {
	my ($program,$dir) = @_;
	if ($dir =~ /^(.+)\/[^\/]+$/) {
		rmkdir($program,$1) or fatal($program,"mkdir(1) $1 failed: $!") unless -d $1;
	}
	unless (-d $dir) {
		$! = 0;
		my $umask = umask 002;
		mkdir $dir or fatal($program,"mkdir(2) $1 failed: $!");
		umask $umask;
	}
}


# refresh project tree, checking:
# - files match revision control
# - owner and permissions are correct
sub postinstall {
	my ($program,$project) = @_;
	my $f = get_project_file_list($program,$project);

	# check for cruft for projects where there git_update() isn't already doing so
	if ($f->{'extraneous_files'} and not $project->{'repo'}) {
		print " * found extraneous files/dirs in project tree...\n";
		my $interactive_deletes;
		for ((sort keys %{$f->{'extraneous_files'}->{'dir'}}), (sort keys %{$f->{'extraneous_files'}->{'file'}})) {
			$interactive_deletes += remove($project,$_);
			print "   $_ removed\n" if $project->{'tidy'} eq 'auto';
		}
		print "\n" if $interactive_deletes;
	}

	if (defined $project->{'postinstall'}) {

		# get list of all files in projects config tree
		my @config_files = File::Find::Rule->file->relative->in($project->{'config_dir'});

		print " * postinstall\n" if defined $project->{'postinstall'};
		for (@{$project->{'postinstall'}}) {
			my (@arg) = split(/\s+/);
			if ($arg[0] eq 'install') {
				my $rx = glob_to_rx_pattern($arg[1]);
				my $matches;
				for my $file (@config_files) {
					if ($file =~ /$rx/) {
						$matches++;
						if (getMD5("$project->{'config_dir'}/$file") ne getMD5("$project->{'install'}/$file")) {
							my $e = copy "$project->{'config_dir'}/$file",  "$project->{'install'}/$file";
							if ($e == 1) {
								print "   $file updated\n";
							} else {
								print "   [31merror updating $file: $![0m\n";
							}
							check_attribs($project,$file);
						} else {
							print "   $file already up to date\n";
						}
					}
				}
				print "   $arg[1] no matches found in config tree\n" unless $matches;
			} elsif ($arg[0] eq 'mkdir') {
				if (not -e "$project->{'install'}/$arg[1]") {
					print "   mkdir $project->{'install'}/$arg[1]\n";
					rmkdir($program,"$project->{'install'}/$arg[1]");
				} elsif (not -d "$project->{'install'}/$arg[1]") {
					print "   oops, $arg[1] is in the way\n";
				}
				check_attribs($project,$arg[1]);
			} elsif ($arg[0] eq 'symlink') {
				# make the symlink relative unless it starts with a leading slash
				my $link = ($arg[2] =~ /^\//) ? $arg[2] : "$project->{'install'}/$arg[2]";
				if (not -e $link) {
					print "   create symlink $link -> $arg[1]\n";
					symlink $arg[1], $link;
				} elsif (! -l $link) {
					print "   oops, $link is in the way\n";
				}
			}
		}

	}

	# check attributes for files under the project
	print " * checking attributes\n";
	for (sort keys %{$f->{'git_files'}}) {
		next if /(^|\/)\.git(\/|$)/;
		check_attribs($project,$_);
	}

}


# check for a commit_id in the current checkout
sub verify_commit_id {
	my ($program,$sha1) = @_;
	if (not $sha1) {
		$sha1 = 'HEAD';
	} elsif ($sha1 =~ /^([0-9a-f]{8,40})$/) {
		$sha1 = "$sha1^{commit}";
	} else {
		debug("bad commit ID $sha1") if defined $program->{'debug'};
		return;
	}
	my $o = execute_git($program,['rev-parse','--quiet','--verify',$sha1]);
	for my $line (@{$o}) {
		if ($line->{'stdout'} and $line->{'stdout'} =~ /^([0-9a-f]{40})$/) {
			debug("found commit ID $1") if defined $program->{'debug'};
			return $1;
		}
	}
	debug("commit ID $sha1 not found") if defined $program->{'debug'};
}


# store the current state
sub write_state {
	my ($program,$project) = @_;
	my $state;
	$state->{'Config Tree'}->{'revision'} = $program->{'config_repository'}->{'revision'};
	for my $proj (@{$program->{'sorted_project_list'}}) {
		for ('revision','revision-lock','rollback') {
			$state->{$proj}->{$_} = $project->{$proj}->{$_} if $project->{$proj}->{$_};
		}
	}
	Storable::nstore $state, $program->{'state_file'} or fatal($program,"couldn't write $program->{'state_file'}: $!") if $state;
}

1;
