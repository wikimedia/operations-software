#!/bin/bash

set -e

usage() {
    echo $0 --host=... --db=...
    exit 1
}

user="root"
host=""
port="3306"
db=""

for var in "$@"; do

    if [[ "$var" =~ ^--host=(.+) ]]; then
        host="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--port=(.+) ]]; then
        port="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--user=(.+) ]]; then
        user="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--db=(.+) ]]; then
        db="${BASH_REMATCH[1]}"
    fi

done

[ "$db"   ] || usage
[ "$host" ] || usage

my="mysql -h $host -P $port -u $user --skip-column-names"

today=$($my -e "select to_days(now())")
tomorrow=$((today+1))

$my <<EOD

set session sql_log_bin = 0;

create database if not exists ${db};
use ${db};

drop table if exists repl_tables;
create table if not exists repl_tables (
    table_name varchar(100) not null primary key,
    table_stamp datetime not null,
    table_md5 binary(16) not null,
    index (table_name),
    index (table_md5)
) engine=innodb default charset=binary;

drop trigger if exists repl_tables_ins;
create trigger repl_tables_ins before insert on repl_tables
    for each row set new.table_stamp = now(), new.table_md5 = unhex(md5(new.table_name));

drop table if exists repl_ignore;
create table if not exists repl_ignore (
    table_name varchar(100) not null,
    primary key (table_name)
) engine=innodb default charset=binary;

replace into repl_ignore values ('accountaudit_login');
replace into repl_ignore values ('arbcom1_vote');
replace into repl_ignore values ('archive_old');
replace into repl_ignore values ('blob_orphans');
replace into repl_ignore values ('blob_tracking');
replace into repl_ignore values ('bv2009_edits');
replace into repl_ignore values ('categorylinks_old');
replace into repl_ignore values ('click_tracking');
replace into repl_ignore values ('cu_changes');
replace into repl_ignore values ('cu_log');
replace into repl_ignore values ('cur');
replace into repl_ignore values ('edit_page_tracking');
replace into repl_ignore values ('email_capture');
replace into repl_ignore values ('exarchive');
replace into repl_ignore values ('exrevision');
replace into repl_ignore values ('filejournal');
replace into repl_ignore values ('globalnames');
replace into repl_ignore values ('hidden');
replace into repl_ignore values ('image_old');
replace into repl_ignore values ('job');
replace into repl_ignore values ('linkscc');
replace into repl_ignore values ('localnames');
replace into repl_ignore values ('log_search');
replace into repl_ignore values ('logging_old');
replace into repl_ignore values ('long_run_profiling');
replace into repl_ignore values ('migrateuser_medium');
replace into repl_ignore values ('moodbar_feedback');
replace into repl_ignore values ('moodbar_feedback_response');
replace into repl_ignore values ('objectcache');
replace into repl_ignore values ('old_growth');
replace into repl_ignore values ('oldimage_old');
replace into repl_ignore values ('optin_survey');
replace into repl_ignore values ('pr_index');
replace into repl_ignore values ('prefstats');
replace into repl_ignore values ('prefswitch_survey');
replace into repl_ignore values ('profiling');
replace into repl_ignore values ('querycache');
replace into repl_ignore values ('querycache_info');
replace into repl_ignore values ('querycache_old');
replace into repl_ignore values ('querycachetwo');
replace into repl_ignore values ('securepoll_cookie_match');
replace into repl_ignore values ('securepoll_elections');
replace into repl_ignore values ('securepoll_entity');
replace into repl_ignore values ('securepoll_lists');
replace into repl_ignore values ('securepoll_msgs');
replace into repl_ignore values ('securepoll_options');
replace into repl_ignore values ('securepoll_properties');
replace into repl_ignore values ('securepoll_questions');
replace into repl_ignore values ('securepoll_strike');
replace into repl_ignore values ('securepoll_voters');
replace into repl_ignore values ('securepoll_votes');
replace into repl_ignore values ('spoofuser');
replace into repl_ignore values ('text');
replace into repl_ignore values ('titlekey');
replace into repl_ignore values ('transcache');
replace into repl_ignore values ('uploadstash');
replace into repl_ignore values ('user_newtalk');
replace into repl_ignore values ('vote_log');
replace into repl_ignore values ('watchlist');

drop table if exists repl_filter;
create table if not exists repl_filter (
    table_name varchar(100) not null,
    column_name varchar(100) not null,
    empty_string varchar(10) not null,
    primary key (table_name, column_name)
) engine=innodb default charset=binary;

replace into repl_filter values ('aft_article_feedback','af_user_ip',"''");
replace into repl_filter values ('archive','ar_text',"''");
replace into repl_filter values ('archive','ar_comment',"''");
replace into repl_filter values ('mark_as_helpful','mah_system_type',"''");
replace into repl_filter values ('mark_as_helpful','mah_user_agent',"''");
replace into repl_filter values ('mark_as_helpful','mah_locale',"''");
replace into repl_filter values ('recentchanges','rc_ip',"''");
replace into repl_filter values ('revision','rev_text_id',"0");
replace into repl_filter values ('user','user_password',"''");
replace into repl_filter values ('user','user_newpassword',"''");
replace into repl_filter values ('user','user_email',"''");
replace into repl_filter values ('user','user_options',"''");
replace into repl_filter values ('user','user_touched',"''");
replace into repl_filter values ('user','user_token',"''");
replace into repl_filter values ('user','user_email_authenticated',"''");
replace into repl_filter values ('user','user_email_token',"''");
replace into repl_filter values ('user','user_email_token_expires',"''");
replace into repl_filter values ('user','user_newpass_time',"''");
replace into repl_filter values ('user_old','user_password',"''");
replace into repl_filter values ('user_old','user_newpassword',"''");
replace into repl_filter values ('user_old','user_email',"''");
replace into repl_filter values ('user_old','user_options',"''");
replace into repl_filter values ('user_old','user_newtalk',"''");
replace into repl_filter values ('user_old','user_touched',"''");
replace into repl_filter values ('user_old','user_token',"''");

drop table if exists repl_records;
drop table if exists repl_deletes;
create table if not exists repl_records (
    record_uuid binary(16) not null,
    record_stamp datetime not null,
    table_md5 binary(16) not null,
    index (table_md5, record_stamp),
    index (record_uuid)
) engine=innodb default charset=binary
partition by range(to_days(record_stamp)) (
    partition p${today} values less than (${tomorrow})
);

drop trigger if exists abuse_filter_log_insert;
drop trigger if exists abuse_filter_log_update;
drop trigger if exists archive_insert;
drop trigger if exists archive_update;
drop trigger if exists mark_as_helpful_insert;
drop trigger if exists mark_as_helpful_update;
drop trigger if exists recentchanges_insert;
drop trigger if exists recentchanges_update;
drop trigger if exists revision_insert;
drop trigger if exists revision_update;
drop trigger if exists user_insert;
drop trigger if exists user_update;

delimiter ;;

drop event if exists repl_records_partition;;
drop event if exists repl_deletes_partition;;

create event repl_records_partition
    on schedule every 1 hour starts now() + interval 10 second
    do begin

        declare pname varchar(20) default null;
        declare tomorrow int;

        set tomorrow = to_days(now())+1;

        set pname = (
            select partition_name from information_schema.partitions
                where table_schema = database()
                and table_name = 'repl_records'
                and partition_name = concat('p',tomorrow)
        );

        if (pname is null) then

            set @sql = concat(
                'alter table repl_records add partition (partition p', tomorrow, ' values less than (', tomorrow+1, '))'
            );

            prepare stmt from @sql; execute stmt; deallocate prepare stmt;

        end if;

        set pname = (
            select partition_name from information_schema.partitions
                where table_schema = database()
                and table_name = 'repl_records'
                and partition_name regexp '^p[0-9]+$'
                and cast(substr(partition_name,2) as unsigned) < to_days(now())-6
                order by partition_name
                limit 1
        );

        if (pname is not null) then

            set @sql = concat(
                'alter table repl_records drop partition ', pname
            );

            prepare stmt from @sql; execute stmt; deallocate prepare stmt;

        end if;

    end ;;

delimiter ;

EOD
