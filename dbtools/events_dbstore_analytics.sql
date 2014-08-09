-- Events for dbstore1001

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

-- Avoid replicating event DDL. Delayed events should only be created
-- on dbstore1002 though they may rely on replicated tables like event_log.

set @@session.sql_log_bin = 0;

delimiter ;;

-- Housekeeping

drop event if exists wmf_dbstore_purge;;

create event wmf_dbstore_purge

    on schedule every 15 minute starts date(now())

    do begin

        declare sid int;

        set sid := @@server_id;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end ;;

drop event if exists wmf_eventlogging;;

create event wmf_eventlogging

    on schedule every 15 minute starts date(now())

    do begin

        declare sid       int;
        declare all_done  int default 0;
        declare log_table varchar(100);

        declare log_tables cursor for
            select table_name
            from information_schema.tables
            where table_schema = 'log'
                and engine <> 'TokuDB';

        -- Use schema name constants everywhere rather than rely on equality propagation.
        -- Information_schema is likely to spend ages "checking permissions" unless explicit.
        declare log_indexes cursor for
            select t.table_name
            from information_schema.tables t
            left join information_schema.statistics i
                on t.table_name = i.table_name
                and i.index_name like '%wiki\_timestamp%'
                and i.table_schema = 'log'
            where t.table_schema = 'log'
            and i.index_name is null;

        declare continue handler for not found set all_done = 1;

        set sid := @@server_id;

        if (get_lock('wmf_eventlogging', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set all_done = 0;
        open log_tables;

        repeat fetch log_tables into log_table;

            if (all_done = 0 and log_table is not null) then

                set @sql := concat(
                    'alter table log.`', log_table, '` engine=tokudb'
                );

                prepare stmt from @sql; execute stmt; deallocate prepare stmt;

                insert into event_log values (sid, now(), 'wmf_eventlogging',
                    concat(@sql)
                );

            end if;

            until all_done
        end repeat;

        close log_tables;

        set all_done = 0;
        open log_indexes;

        repeat fetch log_indexes into log_table;

            if (all_done = 0 and log_table is not null) then

                set @sql := concat(
                    'alter table log.`', log_table, '` add index wiki_timestamp (wiki, timestamp)'
                );

                prepare stmt from @sql; execute stmt; deallocate prepare stmt;

                insert into event_log values (sid, now(), 'wmf_eventlogging',
                    concat(@sql)
                );

            end if;

            until all_done
        end repeat;

        close log_indexes;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_eventlogging');

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
