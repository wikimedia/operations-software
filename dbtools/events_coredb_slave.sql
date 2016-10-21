-- Events for s[1-7] slaves

set @cache_sql_log_bin := @@session.sql_log_bin;
set @@session.sql_log_bin = 0;

set @cache_event_scheduler := @@global.event_scheduler;
set @@global.event_scheduler = 0;

create database if not exists ops;

use ops;

-- Remember, table is replicated!
-- https://wikitech.wikimedia.org/wiki/MariaDB#Schema_Changes
-- Note from Jaime: I am going to disable binary log, it
-- breaks gtid

create table if not exists event_log (
  server_id int unsigned  not null,
  stamp     datetime      not null,
  event     varchar(100)  not null,
  content   varchar(1024) not null,
  index server_stamp (server_id, stamp)
) engine=innodb default charset=binary;

-- Avoid replicating event DDL. Coredb events should only be created
-- on s[1-7] though they may rely on replicated tables like event_log.

delimiter ;;

-- Housekeeping


drop event if exists wmf_master_wikiuser_sleep;;
drop event if exists wmf_master_purge;;

drop event if exists wmf_slave_purge;;

create definer='root'@'localhost' event wmf_slave_purge

    on schedule every 15 minute starts date(now())

    do begin

        declare sid int;

        set sid := @@server_id;
        set @@session.sql_log_bin := 0;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end ;;

-- NOTE: information_schema.processlist
-- MariaDB must generate information_schema.processlist every time it is accessed.
-- That involves various locks which start to matter during high traffic, so stagger
-- events appropriately, at least several seconds apart.

-- wikiuser slow queries get killed at 300s
-- time < 1000000 mariadb 5.5 bug allows new connections to be 2147483647 briefly

drop event if exists wmf_slave_wikiuser_slow;;

create definer='root'@'localhost' event wmf_slave_wikiuser_slow

    on schedule every 30 second starts date(now()) + interval 3 second

    do begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;
        declare thread_query varchar(100);

        declare slow_queries cursor for
            select ps.id, substring(info,1,100)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.user = 'wikiuser'
                and ps.time between 300 and 1000000
                and ps.info is not null
                and lower(ps.info) regexp '^[[:space:]]*select'
                and not lower(ps.info) regexp 'wikiexporter'
                and not lower(ps.info) regexp 'master_pos_wait'
            order by ps.time desc;

        declare continue handler for not found set all_done = 1;

        set sid := @@server_id;
        set @@session.sql_log_bin := 0;

        if (get_lock('wmf_slave_wikiuser_slow', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set all_done = 0;
        open slow_queries;

        repeat fetch slow_queries into thread_id, thread_query;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_slave_wikiuser_slow',
                    concat('kill ',thread_id, '; ',thread_query)
                );

            end if;

            until all_done
        end repeat;

        close slow_queries;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_slave_wikiuser_slow');

    end ;;

-- wikiuser sleepers get killed at 300s
-- time < 1000000 mariadb 5.5 bug allows new connections to be 2147483647 briefly

drop event if exists wmf_slave_wikiuser_sleep;;

create definer='root'@'localhost' event wmf_slave_wikiuser_sleep

    on schedule every 30 second starts date(now()) + interval 5 second

    do begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;

        declare threads_sleeping cursor for
            select ps.id
            from information_schema.processlist ps
            where ps.command = 'Sleep'
                and ps.user = 'wikiuser'
                and ps.time between 300 and 1000000
                and ps.info is null
            order by ps.time desc;

        declare continue handler for not found set all_done = 1;

        if (get_lock('wmf_slave_wikiuser_sleep', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set sid := @@server_id;
        set @@session.sql_log_bin := 0;

        set all_done = 0;
        open threads_sleeping;

        repeat fetch threads_sleeping into thread_id;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_slave_wikiuser_sleep',
                    concat('kill ',thread_id)
                );

            end if;

            until all_done
        end repeat;

        close threads_sleeping;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_slave_wikiuser_sleep');

    end ;;

-- Identify a general overload

drop event if exists wmf_slave_overload;;

create definer='root'@'localhost' event wmf_slave_overload

    on schedule every 10 second starts date(now()) + interval 1 second

    do begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;
        declare thread_query varchar(100);
        declare active_count bigint default null;

        declare active_queries cursor for
            select ps.id, substring(info,1,100)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.user = 'wikiuser'
                and ps.time between 10 and 1000000
                and ps.info is not null
                and lower(ps.info) regexp '^[[:space:]]*select'
                and not lower(ps.info) regexp 'wikiexporter'
                and not lower(ps.info) regexp 'master_pos_wait'
            order by ps.time desc
            limit 100;

        declare continue handler for not found set all_done = 1;

        if (get_lock('wmf_slave_overload', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set sid := @@server_id;
        set @@session.sql_log_bin := 0;

        set active_count := (
            select count(ps.id)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.info is not null
        );

        -- While a server usually has hundreds of open client connections, the number
        -- of concurrent active queries is much lower during normal load. If we find a
        -- spike, be nastier than normal and kill the slowest running over 30s.

        if (active_count is not null and active_count > 300) then

            set all_done = 0;
            open active_queries;

            repeat fetch active_queries into thread_id, thread_query;

                if (thread_id is not null) then

                    kill thread_id;

                    insert into event_log values (sid, now(), 'wmf_slave_overload (300)',
                        concat('kill ',thread_id,'; ',thread_query)
                    );

                end if;

                until all_done
            end repeat;

            close active_queries;

        end if;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_slave_overload');

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
