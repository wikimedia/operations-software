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

create table if not exists slave_status
engine=connect default charset=binary
connection='mysql://status:status@localhost/test'
table_type='mysql' srcdef='show all slaves status';

create table if not exists slave_delay (
  server_id int unsigned  not null,
  stamp     datetime      not null,
  con       varchar(5)    not null,
  lag       int,
  primary key (server_id, con)
) engine=InnoDB default charset=binary;

-- Avoid replicating event DDL. Delayed events should only be created
-- on dbstore1001 though they may rely on replicated tables like event_log.

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

drop event if exists wmf_dbstore_delay;;

create event wmf_dbstore_delay

    on schedule every 5 second starts date(now())

    do begin

        declare sid       int;
        declare all_done  int default 0;
        declare con_name  varchar(10);
        declare io_state  varchar(5);
        declare sql_state varchar(5);
        declare sql_error int;
        declare lag_secs  int;
        declare sd_stamp  datetime;
        declare sd_lag    int;

        declare sql_threads cursor for
            select
                ss.Connection_Name,
                ss.Slave_IO_Running,
                ss.Slave_SQL_Running,
                ss.Last_SQL_Errno,
                ss.Seconds_Behind_Master,
                sd.stamp,
                sd.lag
            from slave_status ss
            left join slave_delay sd
            on ss.Connection_Name = sd.con
            and sd.server_id = @@server_id;

        declare continue handler for not found set all_done = 1;

        set sid := @@server_id;

        if (get_lock('wmf_dbstore_delay', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set all_done = 0;
        open sql_threads;

        repeat fetch sql_threads into con_name, io_state, sql_state, sql_error, lag_secs, sd_stamp, sd_lag;

            if (con_name is not null and io_state = 'Yes' and sql_error = 0) then

                if (sql_state = 'Yes' and lag_secs is not null) then

                    replace into slave_delay values (sid, now(), con_name, lag_secs);

                    if (lag_secs < 86400) then

                        set @sql := concat(
                            'stop slave "', con_name, '" sql_thread'
                        );

                        prepare stmt from @sql; execute stmt; deallocate prepare stmt;

                        insert into event_log values (sid, now(), 'wmf_dbstore_delay',
                            concat(@sql)
                        );

                    end if;

                end if;

                if (sql_state = 'No' and (sd_stamp is null or sd_lag is null or sd_stamp < now() - interval 5 minute or sd_lag > 87400)) then

                    set @sql := concat(
                        'start slave "', con_name, '" sql_thread'
                    );

                    prepare stmt from @sql; execute stmt; deallocate prepare stmt;

                    insert into event_log values (sid, now(), 'wmf_dbstore_delay',
                        concat(@sql)
                    );

                end if;

            end if;

            until all_done
        end repeat;

        close sql_threads;

        -- https://mariadb.atlassian.net/browse/MDEV-4602
        select 1 from (select 1) as t;

        do release_lock('wmf_dbstore_delay');

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
