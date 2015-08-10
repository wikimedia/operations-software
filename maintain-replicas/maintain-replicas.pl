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
## maintain-replicas.pl
##
##  This script maintains the databases containing sanitized views to
##  the replicated databases (in the form <db>_p for every <db>), and
##  sets up tables of metainformation on each slice (in the meta_p
##  database).
##
##  By default, it processes every shard but it accepts a list of
##  slices to process (s[1-7]) or to exclude (-s[1-7]) on the command
##  line.
##
##  The script excpects to be invoked in a fresh copy of
##  operations/mediawiki-config where it will get most of its
##  information, ##  and will connect to each wiki through the API to
##  get the rest.
##
##  It connects to the slices with the credentials in the invoking
##  user's .my.cnf, but is probably only useful if those credentials
##  have full control over the slices to be processed.
##

use strict;
use DBI();
use Data::Dumper;
use LWP::UserAgent;
use JSON;
use Encode;

my %update;

if($ARGV[0] eq '-u') {
    shift;
    my $views = shift;
    foreach my $view (split /,/, $views) {
        $update{$view} = 1;
    }
}

my %slices = (
    'c1' => [ 'labsdb1001.eqiad.wmnet', 3306 ],
    'c2' => [ 'labsdb1002.eqiad.wmnet', 3306 ],
    'c3' => [ 'labsdb1003.eqiad.wmnet', 3306 ],
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
    "flaggedtemplates", "geo_killlist", "geo_tags", "geo_updates", "globalimagelinks", "global_block_whitelist",
    "hashs", "hitcounter", "image", "imagelinks", "imagelinks_old", "interwiki", "iwlinks",
    "l10n_cache", "langlinks", "links", "localisation", "localisation_file_hash",
    "math", "module_deps", "msg_resource", "msg_resource_links", "namespaces",
    "page", "page_broken", "pagelinks", "page_props", "page_restrictions", "pagetriage_log",
    "pagetriage_page", "pagetriage_page_tags", "pagetriage_tags", "pif_edits", "povwatch_log",
    "povwatch_subscribers", "protected_titles", 'pr_index', "redirect", 'renameuser_status', "site_identifiers",
    "sites", "site_stats", "tag_summary", "templatelinks", "transcode", "updatelog", "updates",
    "user_daily_contribs", "user_former_groups", "user_groups", "valid_tag", "wikilove_image_log",
    "wikilove_log", 'global_group_permissions', 'global_group_restrictions', 'global_user_groups',
    'globalblocks', 'localuser', 'wikiset', 'wb_changes', 'wb_changes_dispatch', 'wb_changes_subscription',
    'wb_entity_per_page', 'wb_id_counters', 'wb_items_per_site', 'wb_property_info', 'wb_terms',
    'wbc_entity_usage', 'wbs_propertypairs',
);

my @logging_whitelist = (
    'gblrights', 'globalauth', 'close', 'lock', 'gblblock', 'managetags', 'gather', 'campus',
    'institution', 'instructor', 'online', 'merge', 'massmessage', 'course', 'stable', 'import',
    'abusefilter', 'student', 'eparticle', 'rights', 'pagetriage-deletion', 'protect',
    'pagetriage-curation', 'thanks', 'renameuser', 'review', 'block', 'upload', 'move',
    'delete', 'patrol', 'newusers'
);

my $safelog = "log_type IN ('" . join("', '", @logging_whitelist) . "')";

my %customviews = (

    'abuse_filter' => {
        'source' => 'abuse_filter',
        'view' => 'select af_id, if(af_hidden,null,af_pattern) as af_pattern, af_user, af_user_text,
                    af_timestamp, af_enabled, if(af_hidden,null,af_comments) as af_comments,
                    af_public_comments, af_hidden, af_hit_count, af_throttled, af_deleted, af_actions,
                    af_global, af_group' },

    'abuse_filter_log' => {
        'source' => 'abuse_filter_log',
        'view' => 'select afl_id, afl_filter, afl_user, afl_user_text, NULL as afl_ip, afl_action,
                    afl_actions, afl_var_dump, afl_timestamp, afl_namespace, afl_title, afl_wiki,
                    afl_deleted, afl_patrolled_by, afl_rev_id, afl_log_id', },

    'aft_article_feedback' => {
        'source' => 'aft_article_feedback',
        'view' => 'select af_id, af_page_id, af_user_id, NULL as af_user_ip, af_user_anon_token,
                    af_revision_id, af_cta_id, af_link_id, af_created, af_abuse_count,
                    af_helpful_count, af_unhelpful_count, af_oversight_count, af_is_deleted,
                    af_is_hidden, af_net_helpfulness, af_has_comment, af_is_unhidden, af_is_undeleted,
                    af_is_declined, af_activity_count, af_form_id, af_experiment, af_suppress_count,
                    af_last_status, af_last_status_user_id, af_last_status_timestamp, af_is_autohide,
                    af_is_unrequested, af_is_featured, af_is_unfeatured, af_is_resolved,
                    af_is_unresolved, af_relevance_score, af_relevance_sort, af_last_status_notes', },

    'archive' => {
        'source' => 'archive',
        'view' => 'select ar_id, ar_namespace, ar_title, NULL as ar_text,
                    NULL as ar_comment,
                    if(ar_deleted&4,null,ar_user) as ar_user,
                    if(ar_deleted&4,null,ar_user_text) as ar_user_text,
                    ar_timestamp, ar_minor_edit, ar_flags, ar_rev_id,
                    if(ar_deleted&1,null,ar_text_id) as ar_text_id,
                    ar_deleted, if(ar_deleted&1,null,ar_len) as ar_len,
                    ar_page_id, ar_parent_id,
                    if(ar_deleted&1,null,ar_sha1) as ar_sha1' },

    'archive_userindex' => {
        'source' => 'archive',
        'view' => 'select ar_id, ar_namespace, ar_title, NULL as ar_text,
                    NULL as ar_comment,
                    ar_user, ar_user_text,
                    ar_timestamp, ar_minor_edit, ar_flags, ar_rev_id,
                    if(ar_deleted&1,null,ar_text_id) as ar_text_id,
                    ar_deleted, if(ar_deleted&1,null,ar_len) as ar_len,
                    ar_page_id, ar_parent_id,
                    if(ar_deleted&1,null,ar_sha1) as ar_sha1',
        'where' => '(ar_deleted&4)=0' },

    'filearchive' => {
        'source' => 'filearchive',
        'view' => 'select
                    fa_id, fa_name, fa_archive_name,
                    fa_storage_group, NULL as fa_storage_key,
                    fa_deleted_user, fa_deleted_timestamp, fa_deleted_reason,
                    if(fa_deleted&1,null,fa_size) as fa_size, if(fa_deleted&1,null,fa_width) as fa_width,
                    if(fa_deleted&1,null,fa_height) as fa_height, if(fa_deleted&1,null,fa_metadata) as fa_metadata,
                    if(fa_deleted&1,null,fa_bits) as fa_bits, if(fa_deleted&1,null,fa_media_type) as fa_media_type,
                    if(fa_deleted&1,null,fa_major_mime) as fa_major_mime,
                    if(fa_deleted&1,null,fa_minor_mime) as fa_minor_mime,
                    if(fa_deleted&2,null,fa_description) as fa_description,
                    if(fa_deleted&4,null,fa_user)as fa_user, if(fa_deleted&4,null,fa_user_text) as fa_user_text,
                    fa_timestamp, fa_deleted, if(fa_deleted&1,null,fa_sha1) as fa_sha1', },

    'filearchive_userindex' => {
        'source' => 'filearchive',
        'view' => 'select
                    fa_id, fa_name, fa_archive_name,
                    fa_storage_group, NULL as fa_storage_key,
                    fa_deleted_user, fa_deleted_timestamp, fa_deleted_reason,
                    if(fa_deleted&1,null,fa_size) as fa_size, if(fa_deleted&1,null,fa_width) as fa_width,
                    if(fa_deleted&1,null,fa_height) as fa_height, if(fa_deleted&1,null,fa_metadata) as fa_metadata,
                    if(fa_deleted&1,null,fa_bits) as fa_bits, if(fa_deleted&1,null,fa_media_type) as fa_media_type,
                    if(fa_deleted&1,null,fa_major_mime) as fa_major_mime,
                    if(fa_deleted&1,null,fa_minor_mime) as fa_minor_mime,
                    if(fa_deleted&2,null,fa_description) as fa_description,
                    fa_user, fa_user_text,
                    fa_timestamp, fa_deleted, if(fa_deleted&1,null,fa_sha1) as fa_sha1',
        'where' =>  '(fa_deleted&4)=0' },

    'globaluser' => {
        'source' => 'globaluser',
        'view' => 'select gu_id, gu_name, gu_enabled, gu_enabled_method, gu_home_db,
                    NULL as gu_email, NULL as gu_email_authenticated,
                    NULL as gu_salt, NULL as gu_password,
                    gu_locked, gu_hidden, gu_registration,
                    NULL as gu_password_reset_key, NULL as gu_password_reset_expiration,
                    NULL as gu_auth_token',
        'where' => "gu_hidden=''" },

    'ipblocks' => {
        'source' => 'ipblocks',
        'view' => 'select ipb_id, if(ipb_auto<>0,null,ipb_address) as ipb_address, ipb_user,
                    ipb_by, ipb_reason, ipb_timestamp, ipb_auto, ipb_anon_only, ipb_create_account,
                    ipb_expiry, if(ipb_auto<>0,null,ipb_range_start) as ipb_range_start,
                    if(ipb_auto<>0,null,ipb_range_end) as ipb_range_end, ipb_enable_autoblock,
                    ipb_deleted, ipb_block_email, ipb_by_text, ipb_allow_usertalk, ipb_parent_block_id',
        'where' => 'ipb_deleted=0' },

    'ipblocks_ipindex' => {
        'source' => 'ipblocks',
        'view' => 'select ipb_id, ipb_address, ipb_user, ipb_by, ipb_reason, ipb_timestamp,
                    ipb_auto, ipb_anon_only, ipb_create_account, ipb_expiry, ipb_range_start,
                    ipb_range_end, ipb_enable_autoblock, ipb_deleted, ipb_block_email,
                    ipb_by_text, ipb_allow_usertalk, ipb_parent_block_id',
        'where' => 'ipb_deleted=0 and ipb_auto=0' },

    'logging' => {
        'source' => 'logging',
        'view' => 'select log_id, log_type, if(log_deleted&1,null,log_action) as log_action,
                    log_timestamp, if(log_deleted&4,null,log_user) as log_user,
                    if(log_deleted&1,null,log_namespace) as log_namespace,
                    if(log_deleted&1,null,log_title) as log_title,
                    if(log_deleted&2,null,log_comment) as log_comment,
                    if(log_deleted,null,log_params) as log_params, log_deleted,
                    if(log_deleted&4,null,log_user_text) as log_user_text,
                    if(log_deleted&1,null,log_page) as log_page',
        'where' => $safelog },


    'logging_logindex' => {
        'source' => 'logging',
        'view' => 'select log_id, log_type, log_action, log_timestamp,
                    if(log_deleted&4,null,log_user) as log_user, log_namespace, log_title,
                    if(log_deleted&2,null,log_comment) as log_comment,
                    if(log_deleted,null,log_params) as log_params, log_deleted,
                    if(log_deleted&4,null,log_user_text) as log_user_text, log_page',
        'where' => "(log_deleted&1)=0 and $safelog" },

    'logging_userindex' => {
        'source' => 'logging',
        'view' => 'select log_id, log_type, if(log_deleted&1,null,log_action) as log_action,
                    log_timestamp, log_user, if(log_deleted&1,null,log_namespace) as log_namespace,
                    if(log_deleted&1,null,log_title) as log_title,
                    if(log_deleted&2,null,log_comment) as log_comment,
                    if(log_deleted,null,log_params) as log_params, log_deleted,
                    log_user_text as log_user_text, if(log_deleted&1,null,log_page) as log_page',
        'where' => "(log_deleted&4)=0 and $safelog" },

    'mark_as_helpful' => {
        'source' => 'mark_as_helpful',
        'view' => 'select mah_id, mah_type, mah_item, mah_user_id, mah_user_editcount,
                    mah_namespace, mah_title, mah_timestamp,
                    NULL as mah_system_type, NULL as mah_user_agent, NULL as mah_locale', },

    'oldimage' => {
        'source' => 'oldimage',
        'view' => 'select oi_name, oi_archive_name, oi_size, oi_width, oi_height, oi_bits,
                    if(oi_deleted&2,null,oi_description) as oi_description,
                    if(oi_deleted&4,null,oi_user) as oi_user,
                    if(oi_deleted&4,null,oi_user_text) as oi_user_text,
                    oi_timestamp, oi_metadata, oi_media_type,
                    oi_major_mime, oi_minor_mime, oi_deleted, oi_sha1', },

    'oldimage_userindex' => {
        'source' => 'oldimage',
        'view' => 'select oi_name, oi_archive_name, oi_size, oi_width, oi_height, oi_bits,
                    if(oi_deleted&2,null,oi_description) as oi_description,
                    oi_user, oi_user_text, oi_timestamp, oi_metadata, oi_media_type,
                    oi_major_mime, oi_minor_mime, oi_deleted, oi_sha1',
        'where' => '(oi_deleted&4)=0' },

    'recentchanges' => {
        'source' => 'recentchanges',
        'view' => 'select rc_id, rc_timestamp, if(rc_deleted&4,null,rc_user) as rc_user,
                    if(rc_deleted&4,null,rc_user_text) as rc_user_text, rc_namespace, rc_title,
                    if(rc_deleted&2,null,rc_comment) as rc_comment, rc_minor, rc_bot, rc_new, rc_cur_id,
                    rc_this_oldid, rc_last_oldid, rc_type, rc_source, rc_patrolled, null as rc_ip,
                    rc_old_len, rc_new_len, rc_deleted, rc_logid, rc_log_type, rc_log_action, rc_params' },

    'recentchanges_userindex' => {
        'source' => 'recentchanges',
        'view' => 'select rc_id, rc_timestamp, rc_user,
                    rc_user_text, rc_namespace, rc_title,
                    if(rc_deleted&2,null,rc_comment) as rc_comment, rc_minor, rc_bot, rc_new, rc_cur_id,
                    rc_this_oldid, rc_last_oldid, rc_type, rc_source, rc_patrolled, null as rc_ip,
                    rc_old_len, rc_new_len, rc_deleted, rc_logid, rc_log_type, rc_log_action, rc_params',
        'where' => '(rc_deleted&4)=0' },

    'revision' => {
        'source' => 'revision',
        'view' => 'select rev_id, rev_page, if(rev_deleted&1,null,rev_text_id) as rev_text_id,
                    if(rev_deleted&2,null,rev_comment) as rev_comment,
                    if(rev_deleted&4,null,rev_user) as rev_user,
                    if(rev_deleted&4,null,rev_user_text) as rev_user_text, rev_timestamp,
                    rev_minor_edit, rev_deleted, if(rev_deleted&1,null,rev_len) as rev_len,
                    rev_parent_id, if(rev_deleted&1,null,rev_sha1) as rev_sha1,
                    rev_content_model, rev_content_format' },

    'revision_userindex' => {
        'source' => 'revision',
        'view' => 'select rev_id, rev_page, if(rev_deleted&1,null,rev_text_id) as rev_text_id,
                    if(rev_deleted&2,null,rev_comment) as rev_comment, rev_user, rev_user_text,
                    rev_timestamp, rev_minor_edit, rev_deleted,
                    if(rev_deleted&1,null,rev_len) as rev_len, rev_parent_id,
                    if(rev_deleted&1,null,rev_sha1) as rev_sha1,
                    rev_content_model, rev_content_format',
        'where' => '(rev_deleted&4)=0' },

    'user' => {
        'source' => 'user',
        'view' => 'select user_id, user_name, user_real_name,
                    NULL as user_password, NULL as user_newpassword, NULL as user_email,
                    NULL as user_options, NULL as user_touched, NULL as user_token,
                    NULL as user_email_authenticated, NULL as user_email_token,
                    NULL as user_email_token_expires,
                    user_registration, NULL as user_newpass_time, user_editcount,
                    NULL as user_password_expires', },

    'user_old' => {
        'source' => 'user_old',
        'view' => 'select user_id, user_name,
                    NULL as user_password, NULL as user_newpassword, NULL as user_email,
                    NULL as user_options, NULL as user_newtalk, NULL as user_touched,
                    user_real_name, NULL as user_token', },

    'user_properties' => {
        'source' => 'user_properties',
        'view' => 'select up_user, up_property, up_value',
        'where' => "up_property in ( 'disablemail', 'fancysig', 'gender',
                        'language', 'nickname', 'skin', 'timecorrection',
                        'variant' )", },

    'user_properties_anon' => {
        'limit' => 2,
        'source' => [ 'user_properties', 'user', 'meta_p.properties_anon_whitelist' ],
        'view' => 'select cast(extract(year_month from user_touched)*100+1 as date) upa_touched,
                    up_property, up_value',
        'where' => 'user_id=up_user and up_property like pw_property', },

);

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

chdir "mediawiki-config";

#system "/usr/bin/git pull -ff";

my %db;

open ALL, "<all.dblist" or die "all.dblist: $!";
while(<ALL>) {
    chomp;
    $db{$_} = {};
}
close ALL;

sub dbprop($$$) {
    my($list, $prop, $val) = @_;
    open DBLIST, "<$list.dblist" or die "$list.dblist: $!";
    while(<DBLIST>) {
        chomp;
        next unless defined $db{$_};
        $db{$_}->{$prop} = $val;
    }
    close DBLIST;
}

dbprop "closed", "closed", 1;
dbprop "deleted", "deleted", 1;
dbprop "small", "size", 1;
dbprop "medium", "size", 2;
dbprop "large", "size", 3;
dbprop "private", "private", 1;
dbprop "special", "family", "special";
dbprop "flaggedrevs", "has_flaggedrevs", 1;
dbprop "visualeditor-default", "has_visualeditor", 1;
dbprop "wikidataclient", "has_wikidata", 1;
for my $slice ('s1', 's2', 's3', 's4', 's5', 's6', 's7') {
    dbprop $slice, "slice", $slice;
}
for my $family ("wikibooks", "wikidata", "wikinews", "wikiquote", "wikisource",
                "wikiversity", "wikivoyage", "wiktionary", "wikimania", "wikimedia",
                "wikipedia") {
    dbprop $family, "family", "$family";
}

$db{'centralauth'} = {
    'family' => 'centralauth',
    'slice' => 's7',
};

# Sadly, case sensitivity of titles isn't in a .dblist, nor is it
# exposed through the API so we have to hardcode it here to match
# what is in InitialiseSettings.php
dbprop "wiktionary", "sensitive", 1;
$db{'jbowiki'}->{'sensitive'} = 1;

open IS, "<wmf-config/InitialiseSettings.php" or die "InitializeSettings.php: $!\n";
my $curvar = undef;
my %canonical;
while(<IS>) {
    if(m/array\(/) {
        $curvar = undef;
        $curvar = \%canonical if  m/'wgCanonicalServer'/;
        next;
    }
    next unless defined $curvar;
    $curvar->{$1} = $2  if m/^\s+'(.*)'\s+=>\s+'(.*)'\s*,\s*$/;
};

my $wua = LWP::UserAgent->new();
$wua->agent("dbinfo.pl/1.0");

my %cached;
if(open CACHE, "<:encoding(UTF-8)", "wiki.cache") {
    while(<CACHE>) {
        $cached{$1} = { 'lang' => $2, 'name' => $3 } if m/^(\S+)\s+(\S+)\s+(.*)$/;
    }
    close CACHE;
}

foreach my $dbk (keys %db) {
    my $db = $db{$dbk};
    next if defined $db->{'deleted'};
    next if defined $db->{'private'};
    my $canon = $canonical{$dbk};
    if(not defined $canon) {
        my $lang = undef;
        $lang = $1 if $dbk =~ m/^(.*)(wik[it].*)/;
        if(defined $lang) {
            $canon = (defined $canonical{$db->{'family'}})? $canonical{$db->{'family'}}: $canonical{'default'};
            $canon =~ s/\$lang/$lang/;
        }
    }

    if(defined $canon) {
        $canon =~ s/_/-/g;
        $db->{'url'} = $canon;
        if($cached{$canon}) {
            $db->{'lang'} = $cached{$canon}->{'lang'};
            $db->{'name'} = $cached{$canon}->{'name'};
        } else {
            my $req = HTTP::Request->new(POST => "$canon/w/api.php");
            $req->content_type('application/x-www-form-urlencoded');
            $req->content('action=query&meta=siteinfo&siprop=general&format=json');
            print "Querying $canon...\n";
            my $res = $wua->request($req);
            if($res->is_success) {
                $res = decode_json($res->content)->{'query'};
                $cached{$canon}->{'lang'} = $db->{'lang'} = $res->{'general'}->{'lang'};
                $cached{$canon}->{'name'} = $db->{'name'} = $res->{'general'}->{'sitename'};
            }
        }
    }
}

if(open CACHE, ">:encoding(UTF-8)", "wiki.cache") {
    foreach my $c (keys %cached) {
        print CACHE "$c $cached{$c}->{'lang'} $cached{$c}->{'name'}\n";
    }
  close CACHE;
}

my $dbh;

sub sql($) {
    my ($query) = @_;
    return $dbh->do($query);
}

sub quote($) {
    my ($string) = @_;
    #return "'$string'";
    return $dbh->quote(Encode::encode_utf8($string));
}

my $twiddlum = 0;
sub twiddle() {
    print substr("/-\\|", $twiddlum, 1), "\010";
    $twiddlum = 0  if ++$twiddlum == 4;
}

my %hosts;

foreach my $slice (sort keys %slices) {
    my ($dbhost, $dbport) = @{$slices{$slice}};
    $dbh = DBI->connect("DBI:mysql:host=$dbhost;port=$dbport;mysql_enable_utf8=1", $dbuser, $dbpassword, {'RaiseError' => 0});
    sql("SET NAMES 'utf8';");

    $| = 1;
    foreach my $dbk (keys %db) {
        sql("CREATE DATABASE ${dbk}_p;") if sql("SHOW DATABASES LIKE '${dbk}_p';") == 0;
        print "Views for ${dbk}: ";
        foreach my $view (@fullviews) {
            twiddle;
            my $q = "SELECT table_name FROM information_schema.tables "
                  . "WHERE table_name='$view' and table_schema='$dbk';";
            if(sql($q) == 1) {
                $q = "SELECT table_name FROM information_schema.views "
                   . "WHERE table_name='$view' and table_schema='${dbk}_p';";
                next if sql($q) == 1 and not defined $update{$view};
                print "[$view] ";
                $q = "CREATE OR REPLACE DEFINER=viewmaster VIEW ${dbk}_p.$view AS SELECT * FROM $dbk.$view;\n";
                sql($q);
            }
        }
        VIEW: foreach my $view (keys %customviews) {
            twiddle;
            my $source = $customviews{$view}->{'source'};
            my @sources;

            next if ($customviews{$view}->{'limit'}//1) > ($db{$dbk}->{'size'}//1);

            my $q = "SELECT table_name FROM information_schema.views "
                . "WHERE table_name='$view' and table_schema='${dbk}_p';";
            next if sql($q) == 1 and not defined $update{$view};

            foreach ((ref($source) eq 'ARRAY')? @$source: $source) {
                die "Odd table source '$_'\n" unless m/^(?:(.*)\.)?([^.]+)$/;
                my($db, $table) = ($1, $2);
                $db = $dbk unless defined $db;
                my $q = "SELECT table_name FROM information_schema.tables "
                      . "WHERE table_name='$table' and table_schema='$db';";
                next VIEW unless sql($q) == 1;
                push @sources, "$db.$table";
            }
            print "[$view] ";
            $q = "CREATE OR REPLACE DEFINER=viewmaster VIEW ${dbk}_p.$view AS "
               . $customviews{$view}->{'view'}
               . " FROM " . join(',', @sources);
            $q .= " WHERE " . $customviews{$view}->{'where'} if defined $customviews{$view}->{'where'};
            $q =~ s/\s+/ /g;
            $q .= ";";
            sql($q);
        }
        print " \n";
    }

    print "Update/create meta tables on $slice...\n";
    sql("CREATE DATABASE meta_p DEFAULT CHARACTER SET utf8;") if sql("SHOW DATABASES LIKE 'meta_p';") == 0;
    sql("CREATE TABLE meta_p.wiki (
        dbname varchar(32) PRIMARY KEY,
        lang varchar(12) NOT NULL DEFAULT 'en',
        name text,
        family text,
        url text,
        size numeric(1) NOT NULL DEFAULT 1,
        slice text NOT NULL,
        is_closed numeric(1) NOT NULL DEFAULT 0,
        has_echo numeric(1) NOT NULL DEFAULT 1,
        has_flaggedrevs numeric(1) NOT NULL DEFAULT 0,
        has_visualeditor numeric(1) NOT NULL DEFAULT 0,
        has_wikidata numeric(1) NOT NULL DEFAULT 0,
        is_sensitive numeric(1) NOT NULL DEFAULT 0);")
      if sql("SELECT table_name FROM information_schema.tables
              WHERE table_name='wiki' AND table_schema='meta_p';") == 0;
    sql("CREATE OR REPLACE VIEW meta_p.legacy AS
        SELECT dbname, lang, family, NULL AS domain, size, 0 AS is_meta,
               is_closed, 0 AS is_multilang, (family='wiktionary') AS is_sensitive,
               NULL AS root_category, slice AS server, '/w/' AS script_path
            FROM meta_p.wiki;");
    sql("CREATE TABLE meta_p.properties_anon_whitelist (
        pw_property varbinary(255) PRIMARY KEY);")
      if sql("SELECT table_name FROM information_schema.tables
              WHERE table_name='properties_anon_whitelist' AND table_schema='meta_p';") == 0;
    sql("START TRANSACTION;");
    sql("DELETE FROM meta_p.wiki;");
    foreach my $dbk (keys %db) {
        twiddle;

        my $db = $db{$dbk};
        next unless defined $db->{'slice'};
        next if defined $db->{'deleted'};
        next if defined $db->{'private'};

        my $ldb = 'c3';
        $ldb = 'c2' if $db->{'slice'} =~ m/^s[245]/;
        $ldb = 'c1' if $db->{'slice'} eq 's1';
        $hosts{$ldb} = {} unless defined $hosts{$ldb};
        $hosts{$ldb}->{$dbk} = 1;
        my %fields = (
            'dbname' => quote($dbk),
            'slice' => quote($db->{'slice'}.".labsdb"),
            'family' => quote('wikipedia'),
        );
        $fields{'has_flaggedrevs'} = '1' if $db->{'has_flaggedrevs'};
        $fields{'has_visualeditor'} = '1' if $db->{'has_visualeditor'};
        $fields{'has_wikidata'} = '1' if $db->{'has_wikidata'};
        $fields{'url'} = quote($db->{url}) if defined $db->{'url'};
        $fields{'family'} = quote($db->{family}) if defined $db->{'family'};
        $fields{'lang'} = quote($db->{lang}) if defined $db->{'lang'};
        $fields{'name'} = quote($db->{name}) if defined $db->{'lang'};
        $fields{'is_closed'} = quote($db->{'closed'}) if defined $db->{'closed'};
        $fields{'is_sensitive'} = quote($db->{'sensitive'}) if defined $db->{'sensitive'};
        $fields{'size'} = quote($db->{'size'}) if defined $db->{'size'};
        my $q = "INSERT INTO meta_p.wiki(".join(',',keys %fields).") VALUES (".join(',',values %fields).");";
        sql($q);
    }
    sql("COMMIT;");
    sql("START TRANSACTION;");
    sql("DELETE FROM meta_p.properties_anon_whitelist;");
    # This is hardcoded for now
    sql("INSERT INTO meta_p.properties_anon_whitelist VALUES ('gadget-%');");
    sql("COMMIT;");
    $dbh->disconnect();
}

$hosts{'c1'}->{'meta'} = 1;
open H, ">dbs.tmpl" or die "dbs.tmpl: $!\n";
foreach my $ldb (sort keys %hosts) {
    my $num = 0;
    print H "{% set ${ldb}databases = [\n       ";
    foreach my $db (sort keys %{$hosts{$ldb}}) {
        print H "\n       " unless $num;
        print H " '$db',";
        $num = 0 if ++$num > 3;
    }
    print H "\n] %}\n";
}
close H;

print "All done.\n";
