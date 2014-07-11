-- Events for labsdb100[123]

set @cache_sql_log_bin := @@session.sql_log_bin;
set @@session.sql_log_bin = 1;

set @cache_event_scheduler := @@global.event_scheduler;
set @@global.event_scheduler = 0;

create database if not exists ops;

use ops;

-- Remember, table is replicated!
-- https://wikitech.wikimedia.org/wiki/MariaDB#Schema_Changes

create table if not exists event_log (
  server_id int unsigned  not null,
  stamp     datetime      not null,
  event     varchar(100)  not null,
  content   varchar(1024) not null,
  index server_stamp (server_id, stamp)
) engine=innodb default charset=binary;

-- Avoid replicating event DDL. Labs events should only be created on labsdb
-- though they may rely on replicated tables like event_log.

set @@session.sql_log_bin = 0;

delimiter ;;

-- Housekeeping

drop event if exists wmf_labs_purge;;

create event wmf_labs_purge

    on schedule every 15 minute starts date(now())

    do begin

        declare sid int;

        set sid := @@server_id;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end ;;

-- Kill connections from labs users sleeping for over 300s with an open transaction.
-- These cause innodb purge lag and can block replication, DDL metadata locking, etc.
-- This /does not/ affect users legitimately running slow queries, or maintaining
-- persistent connections, for more than 300s.

drop event if exists wmf_labs_sleepers_txn;;

create event wmf_labs_sleepers_txn

    on schedule every 10 second starts date(now()) + interval 1 second

    do begin

        declare sid int;
        declare thread_id bigint;

        set thread_id := ( select ps.id
            from information_schema.processlist ps
            inner join information_schema.innodb_trx trx
                on ps.id = trx.trx_mysql_thread_id
            where ps.command = 'Sleep'
                and ps.time between 300 and 1000000
                and ps.user regexp '^[usp][0-9]+'
                and ps.user not regexp '^(system|root|dbmanager|watchdog)'
            order by ps.time desc
            limit 1
        );

        set sid := @@server_id;

        if (thread_id is not null) then

            kill thread_id;

            insert into event_log values (sid, now(), 'wmf_labs_sleepers_txn',
                concat('kill ',thread_id)
            );

        end if;

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
