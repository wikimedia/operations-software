#! /usr/bin/perl
#
#  Copyright © 2013 Marc-André Pelletier <mpelletier@wikimedia.org>
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
##
## fedtables.pl
##

use strict;
use DBI();
use Data::Dumper;

my %slices = (
    's1' => [ 'labsdb1001.eqiad.wmnet', 3306 ],
    's2' => [ 'labsdb1002.eqiad.wmnet', 3306 ],
    's3' => [ 'labsdb1003.eqiad.wmnet', 3306 ],
    's4' => [ 'labsdb1002.eqiad.wmnet', 3307 ],
    's5' => [ 'labsdb1002.eqiad.wmnet', 3308 ],
    's6' => [ 'labsdb1003.eqiad.wmnet', 3307 ],
    's7' => [ 'labsdb1003.eqiad.wmnet', 3308 ],
);

my @fullviews = (
    "abuse_filter_action", "abuse_filter_history",
    "aft_article_answer", "aft_article_answer_text",
    "aft_article_feedback_properties", "aft_article_feedback_ratings_rollup",
    "aft_article_feedback_select_rollup", "aft_article_field", "aft_article_field_group",
    "aft_article_field_option", "aft_article_filter_count", "aft_article_revision_feedback_ratings_rollup",
    "aft_article_revision_feedback_select_rollup", "article_assessment", "article_assessment_pages",
    "article_assessment_ratings", "article_feedback", "article_feedback_pages",
    "article_feedback_properties", "article_feedback_ratings", "article_feedback_revisions",
    "article_feedback_stats", "article_feedback_stats_types", "category", "categorylinks", "change_tag",
    "ep_articles", "ep_cas", "ep_courses", "ep_events", "ep_instructors", "ep_oas", "ep_orgs",
    "ep_revisions", "ep_students", "ep_users_per_course", "externallinks", "flaggedimages",
    "flaggedpage_config", "flaggedpage_pending", "flaggedpages", "flaggedrevs", "flaggedrevs_promote",
    "flaggedrevs_statistics", "flaggedrevs_stats", "flaggedrevs_stats2", "flaggedrevs_tracking",
    "flaggedtemplates", "geo_killlist", "geo_tags", "geo_updates", "global_block_whitelist", "hashs",
    "hitcounter", "image", "imagelinks", "imagelinks_old", "interwiki", "iwlinks",
    "l10n_cache", "langlinks", "links", "localisation", "localisation_file_hash",
    "math", "module_deps", "msg_resource", "msg_resource_links", "namespaces",
    "page", "page_broken", "pagelinks", "page_props", "page_restrictions", "pagetriage_log",
    "pagetriage_page", "pagetriage_page_tags", "pagetriage_tags", "pif_edits", "povwatch_log",
    "povwatch_subscribers", "protected_titles", "redirect", "site_identifiers", "sites", "site_stats",
    "tag_summary", "templatelinks", "transcode", "updatelog", "updates", "user_former_groups",
    "user_groups", "valid_tag", "wikilove_image_log", "wikilove_log",
    'global_group_permissions', 'global_group_restrictions', 'global_user_groups',
    'globalblocks', 'localuser', 'wikiset', 'wb_property_info',
    'wb_changes', 'wb_changes_dispatch', 'wb_entity_per_page',
    'wb_id_counters', 'wb_items_per_site', 'wb_terms',
);

my %customviews = (
    'abuse_filter' => 'abuse_filter',
    'abuse_filter_log' => 'abuse_filter_log',
    'aft_article_feedback' => 'aft_article_feedback',
    'archive' => 'archive',
    'archive_userindex' => 'archive',
    'globaluser' => 'globaluser',
    'ipblocks' => 'ipblocks',
    'ipblocks_ipindex' => 'ipblocks',
    'logging' => 'logging',
    'logging_logindex' => 'logging',
    'logging_userindex' => 'logging',
    'mark_as_helpful' => 'mark_as_helpful',
    'oldimage' => 'oldimage',
    'oldimage_userindex' => 'oldimage',
    'recentchanges' => 'recentchanges',
    'recentchanges_userindex' => 'recentchanges',
    'revision' => 'revision',
    'revision_userindex' => 'revision',
    'user' => 'user',
    'user_old' => 'user_old',
);

$| = 1;
my $table;
my @def;
my %commons;
my %wikidata;
my %centralauth;

sub consume($) {
    my $hash = $_[0];
    while(<DUMP>) {
        chomp;

        next if m/^--/;
        next if m/^\/\*/;
        next if m/^\s*$/;
    
        if(m/^CREATE TABLE `(.*)` \(\s*$/) {
            $table = $1;
            $#def = -1;
            next;
        }
        if(m/^\) ENGINE.*;$/) {
            if($table~~@fullviews or defined $customviews{$table}) {
                print " [$table]";
                print defined $customviews{$table}? '+': '*';
                $hash->{$table} = [ @def ];
            }
            undef $table;
            next;
        }
        push @def, $_ if defined $table;
    }
    print "\n";
    close DUMP;
}

print "Grabbing commons definitions...";
open DUMP, 'mysqldump -h 10.64.37.4 -P 3307 --no-data --databases commonswiki|' or die "mysqldump: $!\n";
consume(\%commons);

print "Grabbing wikidata definitions...";
open DUMP, 'mysqldump -h 10.64.37.4 -P 3308 --no-data --databases wikidatawiki|' or die "mysqldump: $!\n";
consume(\%wikidata);

print "Grabbing centralauth definitions...";
open DUMP, 'mysqldump -h 10.64.37.5 -P 3308 --no-data --databases centralauth|' or die "mysqldump: $!\n";
consume(\%centralauth);


my $dbuser;
my $dbpassword;
my $mycnf = $ENV{'HOME'} . "/.my.cnf";
if(open MYCNF, "<$mycnf") {
    my $client = 0;
    while(<MYCNF>) {
        if(m/^\[client\]\s*$/) {
            $client = 1;
            next;
        }
        $client = 0 if m/^\[/;
        next unless $client;
        $dbuser = $1 if m/^\s*user\s*=\s*'(.*)'\s*$/;
        $dbpassword = $1 if m/^\s*password\s*=\s*'(.*)'\s*$/;
    }
    close MYCNF;
}
die "No credentials for connecting to databases.\n" unless defined $dbuser and defined $dbpassword;

my $dbh;

sub sql($) {
    my ($query) = @_;
    return $dbh->do($query);
}

sub addtable($$$) {
    my ($db, $name, $tbl) = @_;
    sql("DROP TABLE IF EXISTS $name;");
    my $q = "CREATE TABLE $name ( "
          . join(' ', @$tbl)
          . ") ENGINE=FEDERATED CONNECTION='$db';";
    sql($q);
}

sub dofed($$$) {
    my ($db, $dbn, $tbl) = @_;
    print "$db:";
    sql("CREATE DATABASE ${dbn};") if sql("SHOW DATABASES LIKE '${dbn}';") == 0;
    foreach my $tn (keys %$tbl) {
        if($tn ~~ @fullviews) {
            addtable $db, "$dbn.$tn", $tbl->{$tn};
            print " [$tn]+";
        }
        foreach my $bv (keys %customviews) {
            next unless $tn eq $customviews{$bv};
            addtable $db, "$dbn.$bv", $tbl->{$tn};
            print " [$bv]*";
        }
    }
    print "\n";
}

foreach my $slice (keys %slices) {
    print "=== slice $slice ===\n";
    my ($dbhost, $dbport) = @{$slices{$slice}};
    $dbh = DBI->connect("DBI:mysql:host=$dbhost;port=$dbport;mysql_enable_utf8=1",
        $dbuser, $dbpassword, {'RaiseError' => 0});
    sql("SET NAMES 'utf8';");

    dofed 'commons',     'commonswiki_f_p',  \%commons      unless $slice eq 's4';
    dofed 'wikidata',    'wikidatawiki_f_p', \%wikidata     unless $slice eq 's5';
    dofed 'centralauth', 'centralauth_f_p',  \%centralauth  unless $slice eq 's7';

    sql("COMMIT;");
    $dbh->disconnect();
}

print "All done.\n";


