-- Events for s[1-7] masters

set @cache_sql_log_bin := @@session.sql_log_bin;
set @@session.sql_log_bin = 0;

set @cache_event_scheduler := @@global.event_scheduler;
set @@global.event_scheduler = 0;

create database if not exists ops;

use ops;

-- Remember, table is replicated!
-- https://wikitech.wikimedia.org/wiki/MariaDB#Schema_Changes
-- note from Jaime: it is not, because it creates GTID issues
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

drop event if exists wmf_slave_overload;;
drop event if exists wmf_slave_wikiuser_sleep;;
drop event if exists wmf_slave_wikiuser_slow;;
drop event if exists wmf_slave_purge;;

drop event if exists wmf_master_purge;;

create event wmf_master_purge

    on schedule every 15 minute starts date(now())

    do begin

        declare sid int;

        set sid := @@server_id;
        set @@session.sql_log_bin := 0;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end ;;

-- wikiuser sleepers get killed at 300s
-- time < 1000000 mariadb 5.5 bug allows new connections to be 2147483647 briefly

drop event if exists wmf_master_wikiuser_sleep;;

create event wmf_master_wikiuser_sleep

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

        if (get_lock('wmf_master_wikiuser_sleep', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set sid := @@server_id;
        set @@session.sql_log_bin = 0;

        set all_done = 0;
        open threads_sleeping;

        repeat fetch threads_sleeping into thread_id;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_master_wikiuser_sleep',
                    concat('kill ',thread_id)
                );

            end if;

            until all_done
        end repeat;

        close threads_sleeping;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_master_wikiuser_sleep');

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
