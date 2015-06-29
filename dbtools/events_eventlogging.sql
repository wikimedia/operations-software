-- Events for all eventlogging boxes

set @cache_sql_log_bin := @@session.sql_log_bin;
set @@session.sql_log_bin = 0;

set @cache_event_scheduler := @@global.event_scheduler;
set @@global.event_scheduler = 0;

use log;

create table if not exists purge_schedule (
  table_name varchar(100) not null primary key,
  after_days int unsigned default null,
  before_stamp varbinary(14) default null,
  batch_size int unsigned default 10000
) engine=innodb default charset=binary;

delimiter ;;

drop event if exists delete_schedule;;

create event delete_schedule

    on schedule every 30 second starts date(now())

    do begin

        declare all_done int default 0;
        declare table_name varchar(100) default null;
        declare after_days int unsigned default null;
        declare batch_size int unsigned default null;

        declare purge_tables cursor for
            select p.table_name, p.after_days, p.batch_size from purge_schedule p where p.after_days is not null;

        declare continue handler for not found set all_done = 1;

        if (get_lock('log_delete_schedule', 1) = 1) then

            set @@session.autocommit = 1;
            set @@session.sql_log_bin = 0;

            set all_done = 0;
            open purge_tables;

            repeat fetch purge_tables into table_name, after_days, batch_size;

                if (all_done = 0 and table_name is not null and after_days is not null and after_days > 30) then

                    set @stamp := date_format(
                        now() - interval after_days day, '%Y%m%d%H%i%s'
                    );

                    set @sql := concat(
                        ' delete from ', table_name,
                        ' where timestamp < "', @stamp, '"'
                        ' order by timestamp limit ', batch_size
                    );

                    prepare stmt from @sql;
                    execute stmt;
                    deallocate prepare stmt;

                end if;

                until all_done
            end repeat;

            close purge_tables;

            -- https://mariadb.atlassian.net/browse/MDEV-4602
            select 1 from (select 1) as t;

            do release_lock('log_delete_schedule');

        end if;

    end ;;

drop event if exists delete_schedule2;;

create event delete_schedule2

    on schedule every 30 second starts date(now())

    do begin

        declare all_done int default 0;
        declare table_name varchar(100) default null;
        declare before_stamp varbinary(14) default null;
        declare batch_size int unsigned default null;

        declare purge_tables cursor for
            select p.table_name, p.before_stamp, p.batch_size from purge_schedule p where p.before_stamp is not null;

        declare continue handler for not found set all_done = 1;

        if (get_lock('log_delete_schedule2', 1) = 1) then

            set @@session.autocommit = 1;
            set @@session.sql_log_bin = 0;

            set all_done = 0;
            open purge_tables;

            repeat fetch purge_tables into table_name, before_stamp, batch_size;

                if (all_done = 0 and table_name is not null and before_stamp is not null) then

                    set @sql := concat(
                        ' delete from ', table_name,
                        ' where timestamp < "', before_stamp, '"'
                        ' order by timestamp limit ', batch_size
                    );

                    prepare stmt from @sql;
                    execute stmt;
                    deallocate prepare stmt;

                end if;

                until all_done
            end repeat;

            close purge_tables;

            -- https://mariadb.atlassian.net/browse/MDEV-4602
            select 1 from (select 1) as t;

            do release_lock('log_delete_schedule2');

        end if;

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
